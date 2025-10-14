import csv
import logging
import re
from unittest.mock import Mock, call, patch

import numpy as np
import polars as pl
import pytest
from polars.testing import assert_frame_equal
from voyager import Index, Space

from remarx.quotation.pairs import (
    build_vector_index,
    compile_quote_pairs,
    find_quote_pairs,
    get_sentence_pairs,
    load_sent_df,
)


@patch("remarx.quotation.pairs.Index")
def test_build_vector_index(mock_index_class, caplog):
    mock_index = Mock(spec=Index)
    mock_index_class.return_value = mock_index
    test_embeddings = np.ones([10, 50])
    mock_index.num_elements = 10

    # Default case
    result = build_vector_index(test_embeddings)
    assert result is mock_index
    mock_index_class.assert_called_once_with(
        Space.InnerProduct, num_dimensions=50, max_elements=10
    )
    assert mock_index.add_items.call_count == 1

    # can't use assert call due to numpy array equality check
    # get args and check for expected match
    args, _kwargs = mock_index.add_items.call_args
    assert np.array_equal(args[0], test_embeddings)

    # Check logging
    caplog.clear()
    with caplog.at_level(logging.INFO):
        _ = build_vector_index(test_embeddings)
    assert len(caplog.record_tuples) == 1
    assert caplog.record_tuples[0][1] == logging.INFO
    expected_msg = r"Created index with 10 items and 50 dimensions in \d+.\d seconds"
    assert re.fullmatch(expected_msg, caplog.record_tuples[0][2])


@patch("remarx.quotation.pairs.get_sentence_embeddings")
@patch("remarx.quotation.pairs.build_vector_index")
def test_get_sentence_pairs(mock_build_index, mock_embeddings, caplog):
    # setup mock index
    mock_index = Mock(spec=Index)
    # list of lists of ids, distances
    test_results = ([[0], [5], [1]], [[0.7], [0.4], [0.18]])
    mock_index.query.return_value = test_results
    mock_build_index.return_value = mock_index

    # setup mock embeddings
    original_vecs = np.array([[5], [10]])
    reuse_vecs = np.array([[0], [1], [2]])
    mock_embeddings.side_effect = [original_vecs, reuse_vecs]

    # Case: Basic
    expected = pl.DataFrame(
        [{"reuse_index": 2, "original_index": 1, "match_score": 0.18}]
    ).cast({"reuse_index": pl.UInt32})  # cast to match row index type
    results = get_sentence_pairs("original_sents", "reuse_sents", 0.2)
    assert_frame_equal(results, expected)
    ## check mock calls
    assert mock_embeddings.call_count == 2
    mock_embeddings.assert_has_calls(
        [
            call("original_sents", show_progress_bar=False),
            call("reuse_sents", show_progress_bar=False),
        ]
    )
    mock_build_index.assert_called_once_with(original_vecs)
    assert mock_index.query.call_count == 1
    mock_index.query.assert_called_with(reuse_vecs, k=1)

    # Case: Check logging
    mock_embeddings.side_effect = [original_vecs, reuse_vecs]
    caplog.clear()
    with caplog.at_level(logging.INFO):
        _ = get_sentence_pairs("original_sents", "reuse_sents", 0.2)

    # currently all logging is info level
    assert len(caplog.record_tuples) == 4
    assert all(log[1] == logging.INFO for log in caplog.record_tuples)
    # check log messages for expected text;
    # order agnostic; just check for presence of expected messages
    log_messages = [log[2] for log in caplog.record_tuples]
    assert "Now generating sentence embeddings" in log_messages
    assert any(
        re.fullmatch(r"Generated 5 sentence embeddings in \d+\.\d seconds", log)
        for log in log_messages
    )
    assert any(
        re.fullmatch(r"Queried 3 sentence embeddings in \d+\.\d seconds", log)
        for log in log_messages
    )
    assert "Identified 1 sentence pair under score cutuff 0.2" in log_messages


def test_load_sent_df(tmp_path):
    # Setup test sentence corpus
    test_csv = tmp_path / "sent_corpus.csv"
    test_data = {
        "sent_id": ["a", "b", "c"],
        "text": ["foo", "bar", "baz"],
    }

    test_df = pl.DataFrame(test_data)
    test_df.write_csv(test_csv)

    # Basic case (minimal fields)
    ## No prefix
    expected_data = {
        "index": [0, 1, 2],
        "id": test_data["sent_id"],
        "text": test_data["text"],
    }
    expected = pl.DataFrame(expected_data)
    result = load_sent_df(test_csv)
    assert_frame_equal(result, expected, check_dtypes=False)
    ## With prefix
    pfx_expected = pl.DataFrame({f"test_{k}": v for k, v in expected_data.items()})
    result = load_sent_df(test_csv, "test_")
    assert_frame_equal(result, pfx_expected, check_dtypes=False)

    # Case additional metadata fields
    test_df = test_df.with_columns(
        pl.Series("other", ["x", "y", "z"]),
        pl.Series("misc", [0, 1, 2]),
    )
    test_df.write_csv(test_csv)
    ## No prefix
    expected = expected.with_columns(
        pl.Series("other", ["x", "y", "z"]),
        # Values are strings because no schema inference
        pl.Series("misc", ["0", "1", "2"]),
    )
    result = load_sent_df(test_csv)
    assert_frame_equal(result, expected, check_dtypes=False)
    ## With prefix
    pfx_expected = pfx_expected.with_columns(
        expected.get_column("other").rename("test_other"),
        expected.get_column("misc").rename("test_misc"),
    )
    result = load_sent_df(test_csv, "test_")
    assert_frame_equal(result, pfx_expected, check_dtypes=False)


def test_compile_quote_pairs():
    # Both corpora include unmatched sentences to ensure that the output
    # does not include unmatched sentences
    reuse_df = pl.DataFrame(
        # a, c are unmatched
        {
            "reuse_index": [0, 1, 2, 3, 4],
            "reuse_id": ["a", "b", "c", "d", "e"],
            "reuse_text": ["0", "1", "2", "3", "4"],
            "reuse_other": [4, 3, 2, 1, 0],
        }
    )
    orig_df = pl.DataFrame(
        # B is unmatched
        {
            "original_index": [0, 1, 2],
            "original_id": ["A", "B", "C"],
            "original_text": ["0", "1", "2"],
            "original_other": [2, 1, 0],
        }
    )

    # Includes two pairs with the same original sentence (A)
    detected_pairs = pl.DataFrame(
        {
            "reuse_index": [1, 3, 4],
            "original_index": [2, 0, 0],
            "match_score": [0.1, 0.225, 0.01],
        }
    )

    # Expecting 3 quote pairs: b-C, d-A, e-A
    expected = pl.DataFrame(
        {
            "match_score": [0.1, 0.225, 0.01],
            "reuse_id": ["b", "d", "e"],
            "reuse_text": ["1", "3", "4"],
            "reuse_other": [3, 1, 0],
            "original_id": ["C", "A", "A"],
            "original_text": ["2", "0", "0"],
            "original_other": [0, 2, 2],
        }
    )

    result = compile_quote_pairs(orig_df, reuse_df, detected_pairs)
    print(f"result: {result.columns}")
    print(f"expected: {expected.columns}")
    assert_frame_equal(result, expected, check_row_order=False)


@patch("remarx.quotation.pairs.compile_quote_pairs")
@patch("remarx.quotation.pairs.get_sentence_pairs")
@patch("remarx.quotation.pairs.load_sent_df")
def test_find_quote_pairs(
    mock_load_df, mock_sent_pairs, mock_compile_pairs, caplog, tmp_path
):
    # setup mocks
    orig_texts = ["some", "text"]
    reuse_texts = ["some", "other", "texts"]
    orig_df = pl.DataFrame({"original_text": orig_texts})
    reuse_df = pl.DataFrame({"reuse_text": reuse_texts})
    mock_load_df.side_effect = [orig_df, reuse_df]
    mock_sent_pairs.return_value = ["sent_pairs"]
    mock_compile_pairs.return_value = pl.DataFrame({"foo": 1, "bar": "a"})

    # Basic
    out_csv = tmp_path / "out.csv"
    find_quote_pairs("original", "reuse", out_csv)
    assert out_csv.read_text() == "foo,bar\n1,a\n"
    ## check mocks
    assert mock_load_df.call_count == 2
    mock_sent_pairs.assert_called_once_with(
        orig_texts, reuse_texts, 0.225, show_progress_bar=False
    )
    mock_compile_pairs.assert_called_once_with(orig_df, reuse_df, ["sent_pairs"])

    ## check logging
    mock_load_df.side_effect = [orig_df, reuse_df]
    with caplog.at_level(logging.INFO):
        caplog.clear()
        find_quote_pairs("original", "reuse", out_csv)
    logs = caplog.record_tuples
    assert len(logs) == 1
    assert logs[0][0] == "remarx.quotation.pairs"
    assert logs[0][1] == logging.INFO
    ### check log messages
    assert re.fullmatch(f"Saved 1 quote pairs to {out_csv}", logs[0][2])

    # Specify cutoff
    mock_load_df.side_effect = [orig_df, reuse_df]
    mock_sent_pairs.reset_mock()
    out_csv = tmp_path / "cutoff.csv"
    find_quote_pairs("original", "reuse", out_csv, score_cutoff=0.4)
    mock_sent_pairs.assert_called_once_with(
        orig_texts, reuse_texts, 0.4, show_progress_bar=False
    )

    # Case: show progress bar
    mock_load_df.side_effect = [orig_df, reuse_df]
    mock_sent_pairs.reset_mock()
    out_csv = tmp_path / "progress.csv"
    find_quote_pairs("original", "reuse", out_csv, show_progress_bar=True)
    # check mocks
    mock_sent_pairs.assert_called_once_with(
        orig_texts, reuse_texts, 0.225, show_progress_bar=True
    )

    # Case no results
    mock_load_df.side_effect = [orig_df, reuse_df]
    mock_sent_pairs.return_value = []
    with caplog.at_level(logging.INFO):
        caplog.clear()
        find_quote_pairs("original", "reuse", out_csv)
    assert len(caplog.record_tuples) == 1
    log = caplog.record_tuples[0]
    assert log[1] == logging.INFO
    assert "No sentence pairs for score cutoff = 0.225" in log[2]


def test_find_quote_pairs_integration(tmp_path):
    """
    Tests the full quote detection pipeline. Checks that all functions within this
    library work as expected in combination. This tests behavior that is otherwise
    masked by mocking.
    """
    test_orig = pl.DataFrame(
        [
            {
                "sent_id": "B",
                "corpus": "original",
                "text": "Und nun sollen seine Geister Auch nach meinem Willen leben.",
            },
            {
                "sent_id": "A",
                "corpus": "original",
                "text": "Hat der alte Hexenmeister Sich doch einmal wegbegeben!",
            },
            {
                "sent_id": "C",
                "corpus": "original",
                "text": "Seine Wort und Werke Merkt ich und den Brauch, Und mit Geistesstärke Tu ich Wunder auch.",
            },
        ]
    )
    test_reuse = pl.DataFrame(
        [
            {
                "sent_id": "a",
                "corpus": "reuse",
                "text": "Hat der alte Hexenmeister Sich doch einmal wegbegeben!",
            },
            {"sent_id": "b", "text": "Komm zurück zu mir", "corpus": "reuse"},
        ]
    )
    # Create files
    orig_csv = tmp_path / "original.csv"
    test_orig.write_csv(orig_csv)
    reuse_csv = tmp_path / "reuse.csv"
    test_reuse.write_csv(reuse_csv)

    out_csv = tmp_path / "out.csv"
    find_quote_pairs(orig_csv, reuse_csv, out_csv)
    with out_csv.open(newline="") as file:
        reader = csv.DictReader(file)
        results = list(reader)
        assert len(results) == 1
        print(results[0].keys())
        assert list(results[0].keys()) == [
            "match_score",
            "reuse_id",
            "reuse_text",
            "reuse_corpus",
            "original_id",
            "original_text",
            "original_corpus",
        ]
        assert results[0]["reuse_id"] == "a"
        assert results[0]["original_id"] == "A"
        # Need to specify the relative tolerance because 0 is a special case
        assert float(results[0]["match_score"]) == pytest.approx(0, rel=1e-6, abs=1e-6)
