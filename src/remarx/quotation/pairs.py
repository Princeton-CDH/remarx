"""
Library for finding sentence-level quote pairs.

Note: Currently this script only supports one original and reuse corpus.
"""

import logging
import pathlib
from timeit import default_timer as time

import numpy as np
import numpy.typing as npt
import polars as pl
from voyager import Index, Space

from remarx.quotation.consolidate import consolidate_quotes
from remarx.quotation.embeddings import get_sentence_embeddings

logger = logging.getLogger(__name__)


def build_vector_index(embeddings: npt.NDArray) -> Index:
    """
    Builds an index for a given set of embeddings with the specified
    number of trees.
    """
    start = time()
    # Instantiate index using inner product / cosine similarity
    n_vecs, n_dims = embeddings.shape
    index = Index(Space.InnerProduct, num_dimensions=n_dims, max_elements=n_vecs)
    # more efficient to add all vectors at once
    index.add_items(embeddings)
    # Return the index
    # NOTE: index could be saved to disk, which may be helpful in future
    elapsed_time = time() - start
    logger.info(
        f"Created index with {index.num_elements} items and {n_dims} dimensions in {elapsed_time:.1f} seconds"
    )
    return index


def get_sentence_pairs(
    original_vecs: npt.NDArray,
    reuse_vecs: npt.NDArray,
    score_cutoff: float,
    show_progress_bar: bool = False,
) -> pl.DataFrame:
    """
    Given an array of original and reuse sentence embeddings, identify pairs
    of original-reuse pairs with high similarity (i.e., likely quotation).
    Returns a polars DataFrame of sentence pairs with the following information:

    - `original_index`: the index of the original sentence
    - `reuse_index`: the index of the reuse sentence
    - `match_score`: the quality of the match

    Uses embeddings and a vector index to find the nearest original sentence
    for each reuse sentence. Sentence pairs are filtered to those pairs with a match score
    (cosine similarity) above the specified cutoff.
    """
    # Build search index
    # NOTE: An index only needs to be generated once for a set of embeddings.
    #       Perhaps there's some potential reuse between runs?
    start = time()
    index = build_vector_index(original_vecs)
    index_elapsed = time() - start
    logger.info(
        f"Indexed {len(original_vecs):,} sentence embeddings in {index_elapsed:.1f} seconds"
    )

    # Get sentence matches; query all vectors at once
    # returns a list of lists with results for each reuse vector
    start = time()
    all_neighbor_ids, all_distances = index.query(reuse_vecs, k=1)
    query_elapsed = time() - start
    logger.info(
        f"Queried {len(reuse_vecs):,} sentence embeddings in {query_elapsed:.1f} seconds"
    )

    result = (
        pl.DataFrame(
            data={"original_index": all_neighbor_ids, "match_score": all_distances}
        )
        # add row index
        .with_row_index(name="reuse_index")
        # since we requested k=1, explode the lists to get single value result
        .explode("original_index", "match_score")
        # then filter by specified match score cutoff
        .filter(pl.col("match_score").lt(score_cutoff))
    )
    total = result.height
    pluralize = "" if total == 1 else "s"
    logger.info(
        f"Identified {total:,} sentence pair{pluralize} with distance less than {score_cutoff}"
    )
    return result


def load_sent_corpus(
    sentence_corpus: pathlib.Path,
    col_pfx: str | None = None,
    show_progress_bar: bool = False,
) -> tuple[pl.DataFrame, npt.NDArray]:
    """
    Takes a sentence corpus file and loads it into a polars DataFrame,
    and generates sentence embeddings for the text of each sentence in the corpus.
    Optionally supports adding a prefix to all column names in the DataFrame.

    The resulting dataframe has the same fields as the input corpus, with the
    following adjustments:

    - a new field `index` corresponding to the row index
    - the sentence id field `sent_id` is renamed to `id`
    - all field names are prefixed if a column prefix is specified

    Returns a tuple of DataFrame and numpy array with embeddings vectors
    """
    # TODO: in future should add an option to specify the model
    # to pass through to embeddings

    start_cols = ["index", "sent_id", "text"]
    df = (
        # Most required fields are strings; don't infer schema, but
        # configure sentence index as an integer for later consolidation
        pl.read_csv(
            sentence_corpus,
            row_index_name="index",
            infer_schema=False,
            schema_overrides={"sent_index": pl.Int32},
        )
        .select(*start_cols, pl.all().exclude(start_cols))
        .rename({"sent_id": "id"})
    )
    start = time()
    vectors = get_sentence_embeddings(
        df["text"].to_list(), show_progress_bar=show_progress_bar
    )
    elapsed = time() - start
    logger.info(
        f"Generated {len(vectors):,} sentence embeddings from {sentence_corpus} in {elapsed:.1f} seconds"
    )
    if col_pfx:
        df = df.rename(lambda x: f"{col_pfx}{x}")
    return (df, vectors)


def compile_quote_pairs(
    original_corpus: pl.DataFrame,
    reuse_corpus: pl.DataFrame,
    detected_pairs: pl.DataFrame,
) -> pl.DataFrame:
    """
    Combine sentence metadata from original and reuse corpora with detected
    sentence pair identifiers to form quote pairs. The original and reuse
    corpus dataframes must contain a row index column named `original_index` and
    `reuse_index` respectively. Ideally, these dataframes should be built using
    [load_sent_corpus][remarx.quotation.pairs.load_sent_corpus].

    Returns a dataframe with the following fields:

    - `match_score`: Estimated quality of the match
    - All other fields in order from the reuse corpus except row index
    - All other fields in order from the original corpus except row index
    """
    # Build and return quote pairs
    return (
        detected_pairs.join(reuse_corpus, on="reuse_index")
        .join(original_corpus, on="original_index")
        .drop(["reuse_index", "original_index"])
    )


def find_quote_pairs(
    original_corpus: list[pathlib.Path],
    reuse_corpus: pathlib.Path,
    output_path: pathlib.Path,
    score_cutoff: float = 0.225,
    consolidate: bool = True,
    show_progress_bar: bool = False,
    benchmark: bool = False,
) -> None:
    """
    For a set of original sentence corpora and one reuse sentence corpus, finds
    the likely sentence-level quote pairs, which are saved as a CSV file.

    Optional parameters allow configuring the `score_cutoff` for threshold to
    include quote pairs, and consolidation of consecutive sentences (on by default).
    When `benchmark` is enabled, summary information is logged to report
    on corpus size and timings to generate embeddings and search for pairs.
    """
    # Load sentence data and generate embeddings
    # TODO: pass option for show_progress_bar

    # for each individual file specified, get data & embeddings
    start = time()
    original_dfs = []
    original_vecs = []
    for corpus_file in original_corpus:
        df, vecs = load_sent_corpus(
            corpus_file, col_pfx="original_", show_progress_bar=show_progress_bar
        )
        original_dfs.append(df)
        original_vecs.append(vecs)
    # combine dataframes and vectors, preserving order
    # use diagonal concat method, since fields may vary by input type
    original_df = pl.concat(original_dfs, how="diagonal")
    original_vecs = np.concatenate(original_vecs)
    reuse_df, reuse_vecs = load_sent_corpus(
        reuse_corpus, col_pfx="reuse_", show_progress_bar=show_progress_bar
    )
    embeddings_seconds = time() - start

    # Find sentence pairs
    # TODO: Add support for relevant voyager parameters
    start = time()
    sent_pairs = get_sentence_pairs(
        original_vecs,
        reuse_vecs,
        score_cutoff,
        show_progress_bar=show_progress_bar,  # NOTE: currently unused
    )
    query_seconds = time() - start

    # Build and save quote pairs if any are found
    if len(sent_pairs):
        quote_pairs = compile_quote_pairs(original_df, reuse_df, sent_pairs)
        # NOTE: Perhaps this should return a DataFrame rather than creating a CSV?

        # consolidate quotes when requested
        if consolidate:
            quote_pairs = consolidate_quotes(quote_pairs)
        quote_pairs.write_csv(output_path)
        logger.info(f"Saved {len(quote_pairs):,} quote pairs to {output_path}")
    else:
        logger.info(
            f"No sentence pairs for score cutoff={score_cutoff}; output file not created."
        )

    if benchmark:
        logger.info(
            f"Benchmark summary: corpus size: original={len(original_df):,}; "
            + f"reuse={len(reuse_df):,}; pairs={len(quote_pairs):,}; "
            + f"embeddings={embeddings_seconds:.2f}s; search={query_seconds:.2f}s"
        )
