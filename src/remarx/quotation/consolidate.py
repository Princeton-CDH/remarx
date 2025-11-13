"""functionality for consolidating sequential quotes into passages"""

import logging

import polars as pl

logger = logging.getLogger(__name__)


def identify_sequences(df: pl.DataFrame, field: str) -> pl.DataFrame:
    """
    Given a polars dataframe, identify and label rows that are sequential
    for the specified field. Returns a modified dataframe with
    the following columns, prefixed by field name:
    -  `_sequential` : boolean indicating whether a row is in a sequence,
    - `_group` : group identifier; uses field value for first in sequence
    """
    # sort by the field, since sequential test requires rows to be ordered by field
    df_seq = (
        df.with_columns(
            # use shift + add to create columns with the expected value if rows are sequential
            seq_follow=pl.col(field).shift().add(1),
            seq_precede=pl.col(field).shift(-1).sub(1),
        )
        .with_columns(
            # use ne_missing & eq_missing so null values are compared instead of propagated
            # add a boolean sequential field with name based on input field
            # a row is sequential if it matches *either* the value based on following or preceding row
            (
                pl.col(field).eq_missing(pl.col("seq_follow"))
                | pl.col(field).eq_missing(pl.col("seq_precede"))
            ).alias(f"{field}_sequential"),
            # create a group field; name based on input field
            # - identify first in sequence (does not match expected following value)
            # - set group value to first in sequence and use forward fill to propagate for all rows in sequence
            pl.when(pl.col(field).ne_missing(pl.col("seq_follow")))
            .then(pl.col(field))
            .otherwise(pl.lit(None))
            .alias(f"{field}_group")
            .forward_fill(),
        )
        .drop("seq_follow", "seq_precede")
    )  # drop interim fields
    return df_seq


def consolidate_quotes(df: pl.DataFrame) -> pl.DataFrame:
    """
    Consolidate quotes that are sequential in both original and reuse texts.
    Required fields:
        - `reuse_sent_index` and `original_sent_index` must be present for aggregation
    Expected fields:
        -
    """
    # first identify sequential reuse sentences
    df_seq = identify_sequences(df.sort("reuse_sent_index"), "reuse_sent_index")
    # filter to groups that are sequential - candidates for consolidating further
    df_reuse_sequential = df_seq.filter(pl.col("reuse_sent_index_sequential"))
    # report how many we found at this stage ?
    total_reuse_seqs = df_reuse_sequential["reuse_sent_index_group"].unique().count()
    # maybe report out of total rows to start with?
    logger.debug(
        f"Identified {total_reuse_seqs:,} groups of sequential sentences in reuse text"
    )

    # NOTE: import that the method does not re-sort on original sentence index!
    df_reuse_sequential = identify_sequences(df_reuse_sequential, "original_sent_index")
    # ? report how many found?

    aggregate_fields = []
    # generate a list of aggregate fields, based on in the order they appear
    # in the input dataframe
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

        # for all other fields, combine unique values
        else:
            aggregate_fields.append(pl.col(field).unique().str.join("; "))

    # last: add a count of the number of sentences in the group
    aggregate_fields.append(pl.len().alias("num_sentences").cast(pl.Int64))

    # group sentences that are sequential in both original and reuse
    df_consolidated = (
        df_reuse_sequential.group_by(
            "reuse_sent_index_group", "original_sent_index_group"
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
    return pl.concat([df_nonseq, df_consolidated]).sort("reuse_sent_index")
