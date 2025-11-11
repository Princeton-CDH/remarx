import polars as pl

from remarx.quotation.consolidate import identify_sequences


def test_identify_sequences():
    # create a dataframe with one column; start with sequential values
    df = pl.DataFrame(
        data={
            "idx": [
                1,
                2,
                3,
            ]
        }
    )
    df_seq = identify_sequences(df, "idx")
    # adds a group field based on the specified field
    assert "idx_group" in df_seq.columns
    assert "idx_sequential" in df_seq.columns
    # does not add any other columns
    # assert len(df_seq.columns) == 3  # original idx + two new

    # in this case, all rows are in a single sequence, starting with idx 1
    assert all(df_seq["idx_group"].eq(1))
    # all are sequential
    assert all(df_seq["idx_sequential"].eq(True))

    # test with a subset that is sequential
    df = pl.DataFrame(data={"idx": [1, 3, 4, 5, 7]})
    df_seq = identify_sequences(df, "idx")
    assert df_seq["idx_group"].to_list() == [1, 3, 3, 3, 7]
    assert df_seq["idx_sequential"].to_list() == [False, True, True, True, False]

    # test with non sequential
    df = pl.DataFrame(data={"idx": [2, 4, 6, 8]})
    df_seq = identify_sequences(df, "idx")
    assert df_seq["idx_group"].to_list() == [2, 4, 6, 8]
    # none are sequential
    assert all(df_seq["idx_sequential"].eq(False))
