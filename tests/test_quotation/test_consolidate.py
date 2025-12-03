import polars as pl
import pytest

from remarx.quotation.consolidate import consolidate_quotes, identify_sequences


def test_identify_sequences():
    # create a dataframe with one column; start with sequential values
    df = pl.DataFrame(
        data={
            "idx": [1, 2, 3],
            "group": ["a", "a", "a"],
        }
    )
    df_seq = identify_sequences(df, "idx", "group")
    print(df_seq)
    # adds a group field based on the specified field
    assert "idx_group" in df_seq.columns
    assert "idx_sequential" in df_seq.columns
    # only adds the expected additional columns
    assert len(df_seq.columns) == len(df.columns) + 2  #  two new columns

    # in this case, all rows are in a single sequence, starting with idx 1
    assert all(df_seq["idx_group"].eq("1:a"))
    # all are sequential
    assert all(df_seq["idx_sequential"].eq(True))

    # test with a subset that is sequential
    df = pl.DataFrame(data={"idx": [1, 3, 4, 5, 7], "group": ["a", "a", "a", "a", "a"]})
    df_seq = identify_sequences(df, "idx", "group")
    assert df_seq["idx_group"].to_list() == [f"{n}:a" for n in [1, 3, 3, 3, 7]]
    assert df_seq["idx_sequential"].to_list() == [False, True, True, True, False]

    # test with non sequential
    df = pl.DataFrame(data={"idx": [2, 4, 6, 8], "group": ["a", "a", "a", "a"]})
    df_seq = identify_sequences(df, "idx", "group")
    assert df_seq["idx_group"].to_list() == [f"{n}:a" for n in [2, 4, 6, 8]]
    # none are sequential
    assert all(df_seq["idx_sequential"].eq(False))

    # test sequential but different groups
    df = pl.DataFrame(data={"idx": [1, 2, 3], "group": ["a", "b", "c"]})
    df_seq = identify_sequences(df, "idx", "group")
    assert df_seq["idx_group"].to_list() == ["1:a", "2:b", "3:c"]
    # none are sequential
    assert all(df_seq["idx_sequential"].eq(False))

    # sequential with groups - one grouped sequence
    df = pl.DataFrame(data={"idx": [1, 2, 3], "group": ["a", "a", "b"]})
    df_seq = identify_sequences(df, "idx", "group")
    assert df_seq["idx_group"].to_list() == ["1:a", "1:a", "3:b"]
    # first two are part of a sequence
    assert df_seq["idx_sequential"].to_list() == [True, True, False]


def test_consolidate_quotes():
    #  simple case: two rows, sequential on both sides
    reuse_text = ["A sentence.", "Another."]
    orig_text = ["A short sentence.", "Another sentence."]
    orig_file = "one.txt"
    reuse_file = "abc.txt"
    df = pl.DataFrame(
        data={
            "match_score": [0.6, 0.4],
            "reuse_id": ["r1", "r2"],
            "reuse_sent_index": [1, 2],
            "reuse_text": reuse_text,
            "reuse_file": [reuse_file, reuse_file],  # same
            "original_id": ["o1", "o2"],
            "original_sent_index": [5, 6],
            "original_text": orig_text,
            "original_file": [orig_file, orig_file],  # same
        }
    )

    df_consolidated = consolidate_quotes(df)
    assert len(df_consolidated) == 1
    result = df_consolidated.to_dicts()[0]
    assert result["match_score"] == 0.5
    assert result["num_sentences"] == 2
    # first for id fields
    assert result["reuse_id"] == "r1"
    assert result["original_id"] == "o1"
    # text fields are combined with whitespace
    assert result["reuse_text"] == " ".join(reuse_text)
    assert result["original_text"] == " ".join(orig_text)
    # other fields are combined with semi-colon (unique values only)
    assert result["reuse_file"] == reuse_file  # both rows have the same
    assert result["original_file"] == orig_file

    # confirm columns are as expected (no extra beyond num_sentences)
    assert "num_sentences" in df_consolidated.columns
    assert len(df_consolidated.columns) == len(df.columns) + 1

    # test that sequential sentences in _different_ files are not consolidated
    # same test df, but update so original sentences are from different files
    orig_multifile = ["one.txt", "two.txt"]
    df_multifile = df.update(pl.DataFrame(data={"original_file": orig_multifile}))
    df_consolidated = consolidate_quotes(df_multifile)
    assert len(df_consolidated) == 2

    # test that non-sequential rows are returned as-is
    nonseq_df = pl.DataFrame(
        data={
            "match_score": 0.3,
            "reuse_id": "r3",
            "reuse_sent_index": 25,
            "reuse_text": "some text",
            "reuse_file": "input.txt",
            "original_id": "o7",
            "original_sent_index": 33,
            "original_text": "some other text",
            "original_file": "orig.txt",
        }
    )
    nonseq_df_consolidated = consolidate_quotes(nonseq_df)
    assert len(nonseq_df_consolidated) == 1

    # test mixed dataframe of sequential and non-sequential
    mixed_df = pl.concat([df, nonseq_df])
    mixed_df_consolidated = consolidate_quotes(mixed_df)
    # one consolidated quote and one unconsolidated
    assert len(mixed_df_consolidated) == 2

    # no data but required fields - should not error
    empty_df = pl.DataFrame(
        data={
            "reuse_sent_index": [],
            "original_sent_index": [],
            "reuse_file": [],
            "original_file": [],
        }
    )
    with pytest.raises(ValueError, match="Cannot consolidate"):
        consolidate_quotes(empty_df)

    with pytest.raises(ValueError, match="Cannot consolidate"):
        consolidate_quotes(pl.DataFrame())

    wrong_df = pl.DataFrame(data={"foo": ["bar", "baz"]})
    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        consolidate_quotes(wrong_df)
