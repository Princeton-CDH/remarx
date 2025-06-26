"""
Methods for evaluating the (approximate) nearest neighbor results for our sentences task.
These methods generally assume the data has the sentence-pairs format.
"""

import polars as pl


def recall_at_k(pairs_df: pl.DataFrame, k: int, n_matches: int | None = None) -> float:
    """
    Calculates recall for sentence pairs at rank k or less (recall@k). Optionally,
    the number of matching pairs can be provided; this is crucial when the results
    do not retrieve all matching pairs.

    Note that ranks are 1-indexed.
    """
    # Infer number of matches if not provided
    if n_matches is None:
        n_matches = pairs_df.filter(pl.col("is_match")).shape[0]
    # Determine number of the matches at rank <= k
    n_matches_at_k = pairs_df.filter(pl.col("is_match"), pl.col("rank") < k).shape[0]
    return n_matches_at_k / n_matches


def precision_at_distance(pairs_df: pl.DataFrame, distance: float) -> float:
    """
    Calculates the precision for sentence pairs at most a given distance apart.
    """
    retrieved_pairs = pairs_df.filter(pl.col("distance") <= distance)
    n_matches = retrieved_pairs.filter(pl.col("is_match")).shape[0]
    return n_matches / retrieved_pairs.shape[0]


def recall_at_distance(
    pairs_df: pl.DataFrame, distance: float, n_matches: int | None = None
) -> float:
    """
    Calculates the recall for a sentence pairs at most a given distance apart. Optionally,
    the number of matching pairs can be provided; this is crucial when the results
    do not retrieve all matching pairs.
    """
    # Infer number of matches if not provided
    if n_matches is None:
        n_matches = pairs_df.filter(pl.col("is_match")).shape[0]
    n_matches_at_dist = pairs_df.filter(
        pl.col("is_match"), pl.col("distance") <= distance
    ).shape[0]
    return n_matches_at_dist / n_matches
