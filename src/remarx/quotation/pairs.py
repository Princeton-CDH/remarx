"""
Library for finding sentence-level quote pairs.

Note: Currently this script only supports one original and reuse corpus.
"""

import pathlib
from timeit import default_timer as time

import numpy.typing as npt
import polars as pl
from annoy import AnnoyIndex
from tqdm import tqdm

from remarx.quotation.embeddings import get_sentence_embeddings


def build_annoy_index(embeddings: npt.NDArray, n_trees: int) -> AnnoyIndex:
    """
    Builds an Annoy index for a given set of embeddings with the specified
    number of trees.
    """
    # Instantiate annoy index using dot product
    n_dims = embeddings.shape[1]
    index = AnnoyIndex(n_dims, "dot")

    for i, vec in enumerate(embeddings):
        index.add_item(i, vec)

    # Build and return index
    # NOTE: An index can be built / written to disk. This could help with
    #       RAM constraints
    index.build(n_trees)
    return index


def get_sentence_pairs(
    original_sents: list[str],
    reuse_sents: list[str],
    score_cutoff: float,
    n_trees: int = 10,
    search_k: int = -1,
    show_progress: bool = False,
) -> pl.DataFrame:
    """
    For a set of original and reuse sentences, identify pairs of original-reuse
    sentence pairs where quotation is likely. Returns these sentence pairs as
    a polars DataFrame including for each pair:

        - original_index : the index of the original sentence
        - reuse_index : the index of the reuse sentence
        - match_score: the quality of the match

    Likely quote pairs are identified through the sentences' embeddings. The Annoy
    library is used to find the nearest original sentence for each reuse sentence.
    Then likely quote pairs are determined by those sentence pairs with a match score
    (cosine similarity) above the specified cutoff.
    Optionally, the parameters for Annoy may be specified.
    """
    # Generate embeddings
    if show_progress:
        start = time()
    original_vecs = get_sentence_embeddings(
        original_sents, show_progress_bar=show_progress
    )
    reuse_vecs = get_sentence_embeddings(reuse_sents, show_progress_bar=show_progress)
    if show_progress:
        print(f"Generated sentence embeddings in {time() - start: .1f} seconds")

    # Build Annoy index
    # NOTE: An index only needs to be generated once for a set of embeddings.
    #       Perhaps there's some potential reuse between runs?
    if show_progress:
        start = time()
    index = build_annoy_index(original_vecs, n_trees)
    if show_progress:
        print(f"Built Annoy index in {time() - start: .1f} seconds")

    # Get sentence matches
    matches = []
    progress_bar = tqdm(
        enumerate(reuse_vecs),
        desc="Finding sentence pairs",
        total=reuse_vecs.shape[0],
        disable=not show_progress,
    )

    for i, vec in progress_bar:
        # NOTE: May want to experiment with different search_k values
        #       search_k defaults to n_trees * n_neighbors
        ann_results = index.get_nns_by_vector(
            vec, 1, search_k=search_k, include_distances=True
        )
        match_score = ann_results[1][0]  # cosine similarity
        if match_score > score_cutoff:
            matches.append(
                {
                    "reuse_index": i,
                    "original_index": ann_results[0][0],
                    # NOTE: This score is subject to floating point / precision
                    #       issues, so its range is not [-1,1]
                    "match_score": match_score,
                }
            )
    return pl.DataFrame(matches)


# TODO: Modify to include additional fields
def load_sent_df(sentence_corpus: pathlib.Path, col_pfx: str = "") -> pl.DataFrame:
    """
    For a given sentence corpus, create a polars DataFrame with the fields needed
    for finding sentence-level quote pairs. Optionally, a prefix can be added to
    all column names.

    The resulting dataframe has the following fields:
        - index : row index
        - id : sentence id
        - text : sentence text

    """
    return (
        pl.read_csv(sentence_corpus, row_index_name="index")
        .select(["index", "sent_id", "text"])
        .rename(lambda x: "id" if x == "sent_id" else x)
        .rename(lambda x: f"{col_pfx}{x}")
    )


# TODO: Modify to include all fields in the expected order
def compile_quote_pairs(
    original_corpus: pl.DataFrame,
    reuse_corpus: pl.DataFrame,
    detected_pairs: pl.DataFrame,
) -> pl.DataFrame:
    """
    Link sentence metadata to the detected sentence pairs from the given original
    and reuse sentence corpus dataframes to form quote pairs.

    Returns a dataframe with the following fields:
        - reuse_id: ID of the reuse sentence
        - original_id: ID of the original sentence
        - match_score: Estimated quality of the match
    """
    # Build and return quote pairs
    return (
        detected_pairs.join(reuse_corpus, on="reuse_index")
        .join(original_corpus, on="original_index")
        .select(["reuse_id", "original_id", "match_score"])
    )


def find_quote_pairs(
    original_corpus: pathlib.Path,
    reuse_corpus: pathlib.Path,
    out_csv: pathlib.Path,
    score_cutoff: int = 0.8,
    show_progress: bool = False,
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
    if show_progress:
        print("Identifying sentence pairs...")
        start = time()
    # TODO: Add support for annoy parameters
    sent_pairs = get_sentence_pairs(
        original_df.get_column("original_text").to_list(),
        reuse_df.get_column("reuse_text").to_list(),
        score_cutoff,
        show_progress=show_progress,
    )
    if show_progress:
        print(f"...completed in {time() - start: .1f} seconds")

    # Build and save quote pairs
    quote_pairs = compile_quote_pairs(original_df, reuse_df, sent_pairs)
    # NOTE: Perhaps this should return a DataFrame rather than creating a CSV?
    quote_pairs.write_csv(out_csv)
    if show_progress:
        print(f"Quote pairs CSV saved to {out_csv}")
