import csv
import logging
import re
from time import sleep
from unittest.mock import Mock, patch

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
    load_sent_corpus,
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

    # Case: Basic
    expected = pl.DataFrame(
        [{"reuse_index": 2, "original_index": 1, "match_score": 0.18}]
    ).cast({"reuse_index": pl.UInt32})  # cast to match row index type
    results = get_sentence_pairs(original_vecs, reuse_vecs, 0.2)
    assert_frame_equal(results, expected)

    ## check mock calls
    # - embeddings is no longer called by this method
    assert mock_embeddings.call_count == 0
    # - index created with original vectors
    mock_build_index.assert_called_once_with(original_vecs)
    # - query called with reuse vectors
    assert mock_index.query.call_count == 1
    mock_index.query.assert_called_with(reuse_vecs, k=1)

    # Case: Check logging
    caplog.clear()
    with caplog.at_level(logging.INFO):
        get_sentence_pairs(original_vecs, reuse_vecs, 0.2)

    # check log messages for expected messages (order agnostic)
    log_messages = [log[2] for log in caplog.record_tuples]
    assert any(
        re.fullmatch(r"Indexed 2 sentence embeddings in \d+\.\d seconds", log)
        for log in log_messages
    )
    assert any(
        re.fullmatch(r"Queried 3 sentence embeddings in \d+\.\d seconds", log)
        for log in log_messages
    )
    assert "Identified 1 sentence pair with distance less than 0.2" in log_messages


@patch("remarx.quotation.pairs.get_sentence_embeddings")
def test_load_sent_corpus(mock_get_sentence_embed, tmp_path):
    # Setup test sentence corpus
    test_csv = tmp_path / "sent_corpus.csv"
    test_data = {
        "sent_id": ["a", "b", "c"],
        "text": ["foo", "bar", "baz"],
    }

    test_df = pl.DataFrame(test_data)
    test_df.write_csv(test_csv)
    test_text = test_df["text"].to_list()

    # Basic case (minimal fields)
    ## No prefix
    expected_data = {
        "index": [0, 1, 2],
        "id": test_data["sent_id"],
        "text": test_data["text"],
    }
    expected = pl.DataFrame(expected_data)
    result, vec = load_sent_corpus(test_csv)
    assert vec == mock_get_sentence_embed.return_value
    mock_get_sentence_embed.assert_called_with(test_text, show_progress_bar=False)
    assert_frame_equal(result, expected, check_dtypes=False)

    ## With prefix
    mock_get_sentence_embed.reset_mock()
    pfx_expected = pl.DataFrame({f"test_{k}": v for k, v in expected_data.items()})
    result, vec = load_sent_corpus(test_csv, "test_")
    assert_frame_equal(result, pfx_expected, check_dtypes=False)
    # embeddings still called correctly with text content
    mock_get_sentence_embed.assert_called_with(test_text, show_progress_bar=False)

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
    result, vec = load_sent_corpus(test_csv)
    assert_frame_equal(result, expected, check_dtypes=False)
    ## With prefix
    pfx_expected = pfx_expected.with_columns(
        expected.get_column("other").rename("test_other"),
        expected.get_column("misc").rename("test_misc"),
    )
    result, vec = load_sent_corpus(test_csv, "test_")
    assert_frame_equal(result, pfx_expected, check_dtypes=False)

    # test with progress bar enabled
    load_sent_corpus(test_csv, show_progress_bar=True)
    mock_get_sentence_embed.assert_called_with(test_text, show_progress_bar=True)


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
    assert_frame_equal(result, expected, check_row_order=False)


@patch("remarx.quotation.pairs.consolidate_quotes")
@patch("remarx.quotation.pairs.compile_quote_pairs")
@patch("remarx.quotation.pairs.get_sentence_pairs")
@patch("remarx.quotation.pairs.load_sent_corpus")
def test_find_quote_pairs(
    mock_load_corpus,
    mock_sent_pairs,
    mock_compile_pairs,
    mock_consolidate_quotes,
    caplog,
    tmp_path,
):
    # setup mocks
    # - mock embeddings
    orig_vecs = np.array([[5], [10]])
    reuse_vecs = np.array([[0], [1], [2]])
    # - mock sentence data
    orig_df = pl.DataFrame({"original_text": ["some", "text"]})
    reuse_df = pl.DataFrame({"reuse_text": ["some", "other", "texts"]})
    mock_load_corpus.side_effect = [(orig_df, orig_vecs), (reuse_df, reuse_vecs)]
    mock_sent_pairs.return_value = ["sent_pairs"]
    mock_compile_pairs.return_value = pl.DataFrame({"foo": 1, "bar": "a"})

    # Basic
    out_csv = tmp_path / "out.csv"
    find_quote_pairs(["original"], "reuse", out_csv, consolidate=False)
    assert out_csv.read_text() == "foo,bar\n1,a\n"
    ## check mocks
    assert mock_load_corpus.call_count == 2
    # expect to be called with:
    #    orig_vecs, reuse_vecs, 0.225, show_progress_bar=False
    # can't use assert_called_with due to numpy array equality check,
    # so inspect arguments individually
    np.testing.assert_array_equal(mock_sent_pairs.call_args.args[0], orig_vecs)
    np.testing.assert_array_equal(mock_sent_pairs.call_args.args[1], reuse_vecs)
    assert mock_sent_pairs.call_args.args[2] == 0.225
    assert mock_sent_pairs.call_args.kwargs == {"show_progress_bar": False}

    mock_compile_pairs.assert_called_once_with(orig_df, reuse_df, ["sent_pairs"])
    mock_consolidate_quotes.assert_not_called()

    # Consolidate enabled: should be called with result of compile pairs method
    mock_load_corpus.side_effect = [(orig_df, orig_vecs), (reuse_df, reuse_vecs)]
    mock_sent_pairs.reset_mock()
    find_quote_pairs(["original"], "reuse", out_csv, consolidate=True)
    mock_consolidate_quotes.assert_called_with(mock_compile_pairs.return_value)
    mock_consolidate_quotes.return_value.write_csv.assert_called_with(out_csv)

    ## check logging
    mock_load_corpus.side_effect = [(orig_df, orig_vecs), (reuse_df, reuse_vecs)]
    with caplog.at_level(logging.INFO):
        caplog.clear()
        find_quote_pairs(["original"], "reuse", out_csv, consolidate=False)
    logs = caplog.record_tuples
    ### check log messages
    assert len(logs) == 1
    assert re.fullmatch(f"Saved 1 quote pairs to {out_csv}", logs[0][2])

    # Specify cutoff
    mock_load_corpus.side_effect = [(orig_df, orig_vecs), (reuse_df, reuse_vecs)]
    mock_sent_pairs.reset_mock()
    out_csv = tmp_path / "cutoff.csv"
    find_quote_pairs(
        ["original"], "reuse", out_csv, score_cutoff=0.4, consolidate=False
    )
    # since we can't assert args with numpy arrays, check the one value we changed
    assert mock_sent_pairs.call_args.args[2] == 0.4

    # Case: show progress bar
    mock_load_corpus.side_effect = [(orig_df, orig_vecs), (reuse_df, reuse_vecs)]
    mock_sent_pairs.reset_mock()
    out_csv = tmp_path / "progress.csv"
    find_quote_pairs(
        ["original"], "reuse", out_csv, show_progress_bar=True, consolidate=False
    )
    # check mocks call kwargs
    assert mock_sent_pairs.call_args.kwargs == {"show_progress_bar": True}

    # Case no results
    mock_load_corpus.side_effect = [(orig_df, orig_vecs), (reuse_df, reuse_vecs)]
    mock_sent_pairs.return_value = []
    with caplog.at_level(logging.INFO):
        caplog.clear()
        find_quote_pairs(["original"], "reuse", out_csv, consolidate=False)

    last_log_message = caplog.records[-1].message
    assert (
        last_log_message
        == "No sentence pairs for score cutoff=0.225; output file not created."
    )


@patch("remarx.quotation.pairs.compile_quote_pairs")
@patch("remarx.quotation.pairs.get_sentence_pairs")
@patch("remarx.quotation.pairs.load_sent_corpus")
def test_find_quote_pairs_benchmark_logs(
    mock_load_corpus, mock_sent_pairs, mock_compile_pairs, caplog, tmp_path
):
    df = pl.DataFrame({"text": ["some text"]})
    # mock embeddings
    vecs = np.array([[5], [10]])

    def mock_load_corpus_slowly(*args, **kwargs):
        # add a slight delay to test benchmark value
        sleep(0.1)
        return (df, vecs)

    mock_load_corpus.side_effect = mock_load_corpus_slowly

    def mock_get_sent_pairs_slowly(*args, **kwargs):
        sleep(0.05)
        return ["pair 1", "pair 2"]  # mock result

    mock_sent_pairs.side_effect = mock_get_sent_pairs_slowly
    mock_compile_pairs.return_value = pl.DataFrame({"foo": [1, 2]})

    out_csv = tmp_path / "bench.csv"
    with caplog.at_level(logging.INFO):
        caplog.clear()
        find_quote_pairs(
            ["original"], "reuse", out_csv, benchmark=True, consolidate=False
        )

    # last log record should be the benchmark summary
    benchmark_info = caplog.records[-1].message
    assert benchmark_info.startswith("Benchmark summary")
    assert "corpus size: original=1; reuse=1; pairs=2;" in benchmark_info
    # on my machine, timing is 0.21 - 0.31; should be at least 0.2
    assert re.search(r" embeddings=0\.[234]\ds", benchmark_info)
    # query should be around 0.05
    assert re.search(r" search=0\.0[567]s", benchmark_info)


# original and reuse content for integration test
orig_sentences = [
    "Und nun sollen seine Geister Auch nach meinem Willen leben.",
    "Hat der alte Hexenmeister Sich doch einmal wegbegeben!",
    "Seine Wort und Werke Merkt ich und den Brauch, Und mit Geistesstärke Tu ich Wunder auch.",
]
reuse_sentences = [
    "Hat der alte Hexenmeister Sich doch einmal wegbegeben!",
    "Komm zurück zu mir",
]


def test_find_quote_pairs_integration(tmp_path):
    """
    Tests the full quote detection pipeline. Checks that all functions within this
    library work as expected in combination. This tests behavior that is otherwise
    masked by mocking.
    """
    test_orig = pl.DataFrame(
        data={"sent_id": ["B", "A", "C"], "text": orig_sentences}
    ).with_columns(corpus=pl.lit("original"))

    test_reuse = pl.DataFrame(
        data={"sent_id": ["a", "b"], "text": reuse_sentences}
    ).with_columns(corpus=pl.lit("reuse"))

    # Create files
    orig_csv = tmp_path / "original.csv"
    test_orig.write_csv(orig_csv)
    reuse_csv = tmp_path / "reuse.csv"
    test_reuse.write_csv(reuse_csv)

    out_csv = tmp_path / "out.csv"
    find_quote_pairs([orig_csv], reuse_csv, out_csv, consolidate=False)
    with out_csv.open(newline="") as file:
        reader = csv.DictReader(file)
        results = list(reader)
        assert len(results) == 1
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


def test_find_quote_pairs_integration_multifile(tmp_path):
    # same as above, but with multiple files for original content
    test_orig1 = pl.DataFrame(
        data={"sent_id": ["B", "A"], "text": orig_sentences[:2]}
    ).with_columns(corpus=pl.lit("original"))
    test_orig2 = pl.DataFrame(
        data={"sent_id": ["C"], "text": orig_sentences[2:]}
    ).with_columns(corpus=pl.lit("original"))

    test_reuse = pl.DataFrame(
        data={"sent_id": ["a", "b"], "text": reuse_sentences}
    ).with_columns(corpus=pl.lit("reuse"))

    # Create files
    orig1_csv = tmp_path / "original1.csv"
    test_orig1.write_csv(orig1_csv)
    orig2_csv = tmp_path / "original2.csv"
    test_orig2.write_csv(orig2_csv)
    reuse_csv = tmp_path / "reuse.csv"
    test_reuse.write_csv(reuse_csv)

    out_csv = tmp_path / "out.csv"
    find_quote_pairs([orig1_csv, orig2_csv], reuse_csv, out_csv, consolidate=False)
    # load and inspect to check for our one expected match
    results_df = pl.read_csv(out_csv)
    result = results_df.to_dicts()[0]
    assert result["reuse_id"] == "a"
    assert result["original_id"] == "A"
    # check with tolerance because 0 is a special case
    assert float(result["match_score"]) == pytest.approx(0, rel=1e-6, abs=1e-6)
