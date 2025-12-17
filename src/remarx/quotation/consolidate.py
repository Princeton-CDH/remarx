"""functionality for consolidating sequential quotes into passages"""

import logging

import polars as pl

logger = logging.getLogger(__name__)


def identify_sequences(df: pl.DataFrame, field: str, group_field: str) -> pl.DataFrame:
    """
    Given a polars dataframe, identify and label rows that are sequential
    for the specified field, within the specified group field.
    Returns a modified dataframe with the following columns, prefixed by field name:

    -  `_sequential` : boolean indicating whether a row is in a sequence,
    - `_group` : group identifier; uses field value for first in sequence
    """

    df_seq = (
        df.with_columns(
            # use shift + add to create columns with the expected value if rows are sequential
            seq_follow=pl.col(field).shift().add(1),
            seq_precede=pl.col(field).shift(-1).sub(1),
            # add shifted fields for comparing group membership
            group_follow=pl.col(group_field).shift(),
            group_precede=pl.col(group_field).shift(-1),
        )
        .with_columns(
            # use ne_missing & eq_missing so null values are compared instead of propagated
            # add a boolean sequential field with name based on input field
            # a row is sequential if it matches *either* the value based on following or preceding row
            # AND belongs to the same group field (e.g., filename)
            (
                (
                    pl.col(field).eq_missing(pl.col("seq_follow"))
                    & pl.col(group_field).eq(pl.col("group_follow"))
                )
                | (
                    pl.col(field).eq_missing(pl.col("seq_precede"))
                    & pl.col(group_field).eq(pl.col("group_precede"))
                )
            ).alias(f"{field}_sequential")
        )
        .with_columns(
            # create a group field; name based on input field and group
            # - if row is not part of a sequence OR is the first in a sequence
            #   (i.e., does not match expected following value), then
            #   set group id to field value AND group field value, to ensure uniqueness
            # - use forward fill to propagate first value for all rows in a sequence
            pl.when(
                ~pl.col(f"{field}_sequential")
                | pl.col(field).ne_missing(pl.col("seq_follow"))
            )
            .then(pl.concat_str([pl.col(field), pl.col(group_field)], separator=":"))
            .otherwise(pl.lit(None))
            .alias(f"{field}_group")
            .forward_fill(),
        )
        .drop("seq_follow", "seq_precede", "group_follow", "group_precede")
    )  # drop interim fields
    return df_seq


def consolidate_quotes(df: pl.DataFrame) -> pl.DataFrame:
    """
    Consolidate quotes that are sequential in both original and reuse texts.
    Required fields:

    - `reuse_sent_index` and `original_sent_index` must be present for aggregation,
       and must be numeric
    - `reuse_file` and `original_file` must be present to ensure aggregation
       only happens for sequences within specific input files

    If required fields are not present, raises `polars.exceptions.ColumnNotFoundError`.
    Raises `ValueError` when called on an empty dataframe.

    Consolidation only occurs when:

    - Sentences are sequential in both reuse and original corpora
    - All sentences within a sequence belong to a single reuse corpus and original corpus
      (seemingly sequential sentences that span multiple files are not consolidated)

    DataFrame is expected to include standard quote pair fields; for consolidated
    quotes, fields are aggregated as follows:

    - `match_score` average across the group
    - `id` and `sent_index` (both `reuse` and `original`): first value in group
    - `reuse_text` and `original_text`: combined with whitespace delimiter
    - For all other fields, unique values are combined, delimited by semicolon and space

    The returned DataFrame includes a new column `num_sentences` which documents
    the number of sentences in a group (1 for unconsolidated quotes).
    """
    if df.is_empty():
        raise ValueError("Cannot consolidate quotes in empty DataFrame")

    # first identify sequential reuse sentences
    df_seq = identify_sequences(
        df.sort("reuse_file", "reuse_sent_index"), "reuse_sent_index", "reuse_file"
    )
    # filter to groups that are sequential - candidates for consolidating further
    df_reuse_sequential = df_seq.filter(pl.col("reuse_sent_index_sequential"))
    # report how many we found at this stage ?
    total_reuse_seqs = df_reuse_sequential["reuse_sent_index_group"].n_unique()
    # maybe report out of total rows to start with?
    logger.info(
        f"Identified {total_reuse_seqs:,} groups of sequential sentences in reuse text ({df.height:,} total rows)"
    )
    df_reuse_sequential = identify_sequences(
        df_reuse_sequential.sort("original_file", "original_sent_index"),
        "original_sent_index",
        "original_file",
    )

    aggregate_fields = []
    # generate a list of fields for aggregation, which will be output
    # based on in the order they appear in the input dataframe
    for field in df.columns:
        if field == "match_score":
            # average match score within the group
            aggregate_fields.append(pl.col(field).mean())
        elif field in [
            "reuse_id",
            "original_id",
            "reuse_sent_index",
            "original_sent_index",
        ]:
            # use the first ids and indices within the group
            aggregate_fields.append(pl.first(field))

        elif field in ["reuse_text", "original_text"]:
            # combine text content across all sentences in the group
            aggregate_fields.append(pl.col(field).str.join(" "))

        # for all other fields, combine unique values; preserve input order
        else:
            aggregate_fields.append(
                pl.col(field).unique(maintain_order=True).str.join("; ")
            )

    # last: add a count of the number of sentences in the group
    aggregate_fields.append(pl.len().alias("num_sentences").cast(pl.Int64))

    # group sentences that are sequential in both original and reuse
    df_consolidated = (
        df_reuse_sequential.group_by(
            "reuse_sent_index_group",
            "original_sent_index_group",
        )
        .agg(*aggregate_fields)
        .drop(
            # drop grouping fields after aggregation is complete
            "reuse_sent_index_group",
            "original_sent_index_group",
        )
    )

    # include non-sequential sentences & sort (columns must match)
    df_nonseq = (
        df_seq.filter(~pl.col("reuse_sent_index_sequential"))
        .with_columns(num_sentences=pl.lit(1).cast(pl.Int64))
        .drop("reuse_sent_index_group", "reuse_sent_index_sequential")
    )

    # combine the consolidated and single sentences and sort by reuse index
    df_combined = pl.concat([df_nonseq, df_consolidated]).sort("reuse_sent_index")
    # total consolidated is not everything grouped! only things with more than one sentence
    total_consolidated = df_consolidated.filter(pl.col("num_sentences").gt(1)).height
    logger.info(
        f"{total_consolidated:,} consolidated quotes ({df_combined.height:,} total rows)"
    )
    return df_combined
