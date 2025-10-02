"""
Library for finding sentence-level quote pairs.

Note: Currently this script only supports one original and reuse corpus.
"""

import logging
import pathlib
from timeit import default_timer as time

import numpy.typing as npt
import polars as pl
from voyager import Index, Space

from remarx.quotation.embeddings import get_sentence_embeddings

logger = logging.getLogger(__name__)


def build_vector_index(embeddings: npt.NDArray) -> Index:
    """
    Builds an index for a given set of embeddings with the specified
    number of trees.
    """
    # TODO: Add relevant voyager parameters
    start = time()
    # Instantiate annoy index using dot product
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
    original_sents: list[str],
    reuse_sents: list[str],
    score_cutoff: float,
    show_progress_bar: bool = False,
) -> pl.DataFrame:
    """
    For a set of original and reuse sentences, identify pairs of original-reuse
    sentence pairs where quotation is likely. Returns these sentence pairs as
    a polars DataFrame including for each pair:

    - `original_index`: the index of the original sentence
    - `reuse_index`: the index of the reuse sentence
    - `match_score`: the quality of the match

    Likely quote pairs are identified through the sentences' embeddings. The Annoy
    library is used to find the nearest original sentence for each reuse sentence.
    Then likely quote pairs are determined by those sentence pairs with a match score
    (cosine similarity) above the specified cutoff.
    Optionally, the parameters for Annoy may be specified.
    """
    # Generate embeddings
    logger.info("Now generating sentence embeddings")
    start = time()
    original_vecs = get_sentence_embeddings(
        original_sents, show_progress_bar=show_progress_bar
    )
    reuse_vecs = get_sentence_embeddings(
        reuse_sents, show_progress_bar=show_progress_bar
    )
    n_vecs = len(original_vecs) + len(reuse_vecs)
    elapsed_time = time() - start
    logger.info(
        f"Generated {n_vecs:,} sentence embeddings in {elapsed_time:.1f} seconds"
    )

    # Build search index
    # NOTE: An index only needs to be generated once for a set of embeddings.
    #       Perhaps there's some potential reuse between runs?
    index = build_vector_index(original_vecs)

    # Get sentence matches; query all vectors at once
    # returns a list of lists with results for each reuse vector
    start = time()
    all_neighbor_ids, all_distances = index.query(reuse_vecs, k=1)
    elapsed_time = time() - start
    logger.info(
        f"Queried {len(reuse_vecs):,} sentence embeddings in {elapsed_time:.1f} seconds"
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
    logger.info(
        f"Identified {total:,} sentence pair{'' if total == 1 else 's'} under score cutuff {score_cutoff}"
    )
    return result


def load_sent_df(sentence_corpus: pathlib.Path, col_pfx: str = "") -> pl.DataFrame:
    """
    For a given sentence corpus, create a polars DataFrame suitable for finding
    sentence-level quote pairs. Optionally, a prefix can be added to all column names.

    The resulting dataframe has the same fields as the input corpus except with:

    - a new field `index` corresponding to the row index
    - the sentence id field `sent_id` is renamed to `id`

    """
    start_cols = ["index", "sent_id", "text"]
    return (
        # Since all required fields are strings, there's no need to infer schema
        pl.read_csv(sentence_corpus, row_index_name="index", infer_schema=False)
        .select(*start_cols, pl.all().exclude(start_cols))
        .rename({"sent_id": "id"})
        .rename(lambda x: f"{col_pfx}{x}")
    )


def compile_quote_pairs(
    original_corpus: pl.DataFrame,
    reuse_corpus: pl.DataFrame,
    detected_pairs: pl.DataFrame,
) -> pl.DataFrame:
    """
    Link sentence metadata to the detected sentence pairs from the given original
    and reuse sentence corpus dataframes to form quote pairs. The original and reuse
    corpus dataframes must contain a row index column named `original_index` and
    `reuse_index` respectively. Ideally, these dataframes should be built using
    [load_sent_df][remarx.quotation.pairs.load_sent_df].

    Returns a dataframe with the following fields:

    - `match_score`: Estimated quality of the match
    - All other fields in order from the reuse corpus except its row index
    - All other fields in order from the original corpus except its row index
    """
    # Build and return quote pairs
    return (
        detected_pairs.join(reuse_corpus, on="reuse_index")
        .join(original_corpus, on="original_index")
        .drop(["reuse_index", "original_index"])
    )


def find_quote_pairs(
    original_corpus: pathlib.Path,
    reuse_corpus: pathlib.Path,
    out_csv: pathlib.Path,
    score_cutoff: float = 0.225,
    show_progress_bar: bool = False,
) -> None:
    """
    For a given original and reuse sentence corpus, finds the likely sentence-level
    quote pairs. These quote pairs are saved as a CSV. Optionally, the required
    quality for quote pairs can be modified via `score_cutoff`.
    """

    # Build sentence dataframes
    original_df = load_sent_df(original_corpus, col_pfx="original_")
    reuse_df = load_sent_df(reuse_corpus, col_pfx="reuse_")

    # Determine sentence pairs
    # TODO: Add support for relevant voyager parameters
    sent_pairs = get_sentence_pairs(
        original_df.get_column("original_text").to_list(),
        reuse_df.get_column("reuse_text").to_list(),
        score_cutoff,
        show_progress_bar=show_progress_bar,
    )

    # Build and save quote pairs if any are found
    if len(sent_pairs):
        quote_pairs = compile_quote_pairs(original_df, reuse_df, sent_pairs)
        # NOTE: Perhaps this should return a DataFrame rather than creating a CSV?
        quote_pairs.write_csv(out_csv)
        logger.info(f"Saved {len(quote_pairs):,} quote pairs to {out_csv}")
    else:
        logger.info(
            f"No sentence pairs for score cutoff = {score_cutoff} ; output file not created."
        )
