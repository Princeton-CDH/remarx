"""functionality for consolidating sequential quotes into passages"""

import polars as pl


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
        df.sort(field)
        .with_columns(
            # use shift + add to add columns with the expected value if sequential
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
