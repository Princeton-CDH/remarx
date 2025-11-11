import polars as pl

from remarx.quotation.consolidate import consolidate_quotes, identify_sequences


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


def test_consolidate_quotes():
    #  simple case: two rows, sequential on both sides
    df = pl.from_dicts(
        [
            {
                "match_score": 0.6,
                "reuse_id": "r1",
                "reuse_sent_index": 1,
                "reuse_text": "first part of a sentence",
                "original_id": "o1",
                "original_sent_index": 5,
                "original_text": "First section of my sentence",
            },
            {
                "match_score": 0.4,
                "reuse_id": "r2",
                "reuse_sent_index": 2,
                "reuse_text": "continuation text",
                "original_id": "o2",
                "original_sent_index": 6,
                "original_text": "continuing text",
            },
        ]
    )

    df_consolidated = consolidate_quotes(df)
    assert len(df_consolidated) == 1
    result = df_consolidated.to_dicts()[0]
    assert result["match_score"] == 0.5
    assert result["num_sentences"] == 2
    # first for id fields
    assert result["reuse_id"] == "r1"
    assert result["original_id"] == "o1"
    # consolidate/combine other fields
    assert result["reuse_text"] == "first part of a sentence continuation text"
    assert result["original_text"] == "First section of my sentence continuing text"

    # confirm columns are as expected (no extra beyond num_sentences)

    # NEXT: test that non-sequential rows returned as-is (doesn't work yet)
