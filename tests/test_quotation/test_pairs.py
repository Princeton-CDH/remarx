import csv
import logging
import re
from unittest.mock import Mock, call, patch

import numpy as np
import polars as pl
import pytest
from annoy import AnnoyIndex
from polars.testing import assert_frame_equal

from remarx.quotation.pairs import (
    build_annoy_index,
    compile_quote_pairs,
    find_quote_pairs,
    get_sentence_pairs,
    load_sent_df,
)


@patch("remarx.quotation.pairs.AnnoyIndex")
def test_build_annoy_index(mock_index_class):
    mock_index = Mock(spec=AnnoyIndex)
    mock_index_class.return_value = mock_index
    test_embeddings = np.ones([10, 50])

    # Default case
    result = build_annoy_index(test_embeddings, 10)
    assert result is mock_index
    mock_index_class.assert_called_once_with(50, "dot")
    mock_index.set_seed.assert_not_called()
    assert mock_index.add_item.call_count == 10
    mock_index.build.assert_called_once_with(10)

    # Provide random seed
    mock_index_class.reset_mock()
    result = build_annoy_index(test_embeddings, 5, random_seed=42)
    assert result is mock_index
    mock_index_class.assert_called_once_with(50, "dot")
    mock_index.set_seed.assert_called_once_with(42)
    assert mock_index.add_item.call_count == 10
    mock_index.build.assert_called_once_with(5)


@patch("remarx.quotation.pairs.get_sentence_embeddings")
@patch("remarx.quotation.pairs.build_annoy_index")
def test_get_sentence_pairs(mock_build_index, mock_embeddings, caplog):
    # setup mock index
    mock_index = Mock(spec=AnnoyIndex)
    # will return a tuple of two lists corresponding to indices and distances
    test_ann_results = [([0], [0.7]), ([5], [0.4]), ([1], [0.99])]
    mock_index.get_nns_by_vector.side_effect = test_ann_results
    mock_build_index.return_value = mock_index

    # setup mock embeddings
    original_vecs = np.array([[5], [10]])
    reuse_vecs = np.array([[0], [1], [2]])
    mock_embeddings.side_effect = [original_vecs, reuse_vecs]

    # Case: Basic
    expected = pl.DataFrame(
        [{"reuse_index": 2, "original_index": 1, "match_score": 0.99}]
    )
    with caplog.at_level(logging.INFO):
        results = get_sentence_pairs("original_sents", "reuse_sents", 0.8)
    assert_frame_equal(results, expected)
    ## check mock calls
    assert mock_embeddings.call_count == 2
    mock_embeddings.assert_has_calls(
        [
            call("original_sents", show_progress_bar=False),
            call("reuse_sents", show_progress_bar=False),
        ]
    )
    mock_build_index.assert_called_once_with(original_vecs, 10, random_seed=None)
    assert mock_index.get_nns_by_vector.call_count == 3
    mock_index.get_nns_by_vector.assert_has_calls(
        [call(x, 1, search_k=-1, include_distances=True) for x in reuse_vecs]
    )
    ## check logs
    logs = caplog.record_tuples
    assert len(logs) == 3
    assert all(log[0] == "remarx.quotation.pairs" for log in logs)
    assert all(log[1] == logging.INFO for log in logs)
    ### check log messages
    assert logs[0][2] == "Now generating sentence embeddings"
    assert re.fullmatch(
        r"Generated 5 sentence embeddings in \d+\.\d seconds", logs[1][2]
    )
    assert re.fullmatch(r"Built Annoy index in \d+\.\d seconds", logs[2][2])

    # Case: specify annoy parameters
    mock_build_index.reset_mock()
    mock_index.get_nns_by_vector.side_effect = test_ann_results
    mock_embeddings.side_effect = [original_vecs, reuse_vecs]

    _ = get_sentence_pairs("original_sents", "reuse_sents", 0.8, search_k=4, n_trees=3)
    mock_build_index.assert_called_once_with(original_vecs, 3, random_seed=None)
    assert mock_index.get_nns_by_vector.call_count == 3
    mock_index.get_nns_by_vector.assert_has_calls(
        [call(x, 1, search_k=4, include_distances=True) for x in reuse_vecs]
    )

    # Case: set random seed
    mock_build_index.reset_mock()
    mock_index.get_nns_by_vector.side_effect = test_ann_results
    mock_embeddings.side_effect = [original_vecs, reuse_vecs]

    _ = get_sentence_pairs("original_sents", "reuse_sents", 0.8, random_seed=42)
    mock_build_index.assert_called_once_with(original_vecs, 10, random_seed=42)

    # Case: show progress bar
    mock_index.get_nns_by_vector.side_effect = test_ann_results
    mock_embeddings.reset_mock()
    mock_embeddings.side_effect = [original_vecs, reuse_vecs]

    results = get_sentence_pairs(
        "original_sents", "reuse_sents", 0.8, show_progress_bar=True
    )
    # check mocks
    assert mock_embeddings.call_count == 2
    mock_embeddings.assert_has_calls(
        [
            call("original_sents", show_progress_bar=True),
            call("reuse_sents", show_progress_bar=True),
        ]
    )


def test_load_sent_df(tmp_path):
    # Setup test sentence corpus
    test_csv = tmp_path / "sent_corpus.csv"
    test_data = {
        "sent_id": ["a", "b", "c"],
        "text": ["foo", "bar", "baz"],
        "other": ["x", "y", "z"],
    }

    test_df = pl.DataFrame(test_data)
    test_df.write_csv(test_csv)

    # Case: No prefix
    expected_data = {
        "index": [0, 1, 2],
        "id": test_data["sent_id"],
        "text": test_data["text"],
    }
    expected = pl.DataFrame(expected_data)
    result = load_sent_df(test_csv)
    assert_frame_equal(result, expected, check_dtypes=False)

    # Case: With prefix
    expected = pl.DataFrame({f"test_{k}": v for k, v in expected_data.items()})
    result = load_sent_df(test_csv, col_pfx="test_")
    assert_frame_equal(result, expected, check_dtypes=False)


def test_compile_quote_pairs():
    # Both corpora include unmatched sentences to ensure that the output
    # does not include unmatched sentences
    reuse_df = pl.DataFrame(
        # a, c are unmatched
        {
            "reuse_index": [0, 1, 2, 3, 4],
            "reuse_id": ["a", "b", "c", "d", "e"],
            "reuse_text": ["0", "1", "2", "3", "4"],
            "other": [0, 1, 2, 3, 4],
        }
    )
    orig_df = pl.DataFrame(
        # B is unmatched
        {
            "original_index": [0, 1, 2],
            "original_id": ["A", "B", "C"],
            "original_text": ["0", "1", "2"],
            "other": [0, 1, 2],
        }
    )

    # Includes two pairs with the same original sentence (A)
    detected_pairs = pl.DataFrame(
        {
            "reuse_index": [1, 3, 4],
            "original_index": [2, 0, 0],
            "match_score": [0.9, 0.8, 0.99],
        }
    )

    # Expecting 3 quote pairs: b-C, d-A, e-A
    expected = pl.DataFrame(
        {
            "reuse_id": ["b", "d", "e"],
            "reuse_text": ["1", "3", "4"],
            "original_id": ["C", "A", "A"],
            "original_text": ["2", "0", "0"],
            "match_score": [0.9, 0.8, 0.99],
        }
    )

    result = compile_quote_pairs(orig_df, reuse_df, detected_pairs)
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
    with caplog.at_level(logging.INFO):
        find_quote_pairs("original", "reuse", out_csv)
    assert out_csv.read_text() == "foo,bar\n1,a\n"
    ## check mocks
    assert mock_load_df.call_count == 2
    mock_sent_pairs.assert_called_once_with(
        orig_texts,
        reuse_texts,
        0.8,
        n_trees=10,
        search_k=-1,
        random_seed=None,
        show_progress_bar=False,
    )
    mock_compile_pairs.assert_called_once_with(orig_df, reuse_df, ["sent_pairs"])
    ## check logging
    logs = caplog.record_tuples
    assert len(logs) == 3
    assert all(log[0] == "remarx.quotation.pairs" for log in logs)
    assert all(log[1] == logging.INFO for log in logs)
    ### check log messages
    assert logs[0][2] == "Now identifying sentence pairs"
    assert re.fullmatch(r"Identified 1 sentence pairs in \d+\.\d seconds", logs[1][2])
    assert re.fullmatch(f"Saved 1 quote pairs to {out_csv}", logs[2][2])

    # Specify cutoff
    mock_load_df.side_effect = [orig_df, reuse_df]
    mock_sent_pairs.reset_mock()
    out_csv = tmp_path / "cutoff.csv"
    find_quote_pairs("original", "reuse", out_csv, score_cutoff=0.4)
    mock_sent_pairs.assert_called_once_with(
        orig_texts,
        reuse_texts,
        0.4,
        n_trees=10,
        search_k=-1,
        random_seed=None,
        show_progress_bar=False,
    )

    # Case: show progress bar
    mock_load_df.side_effect = [orig_df, reuse_df]
    mock_sent_pairs.reset_mock()
    out_csv = tmp_path / "progress.csv"
    find_quote_pairs("original", "reuse", out_csv, show_progress_bar=True)
    # check mocks
    mock_sent_pairs.assert_called_once_with(
        orig_texts,
        reuse_texts,
        0.8,
        n_trees=10,
        search_k=-1,
        random_seed=None,
        show_progress_bar=True,
    )


def test_find_quote_pairs_integration(tmp_path):
    """
    Tests the full quote detection pipeline. Checks that all functions within this
    library work as expected in combination. This tests behavior that is otherwise
    masked by mocking.
    """
    test_orig_data = [
        {
            "sent_id": "A",
            "corpus": "original",
            "text": "Und nun sollen seine Geister Auch nach meinem Willen leben.",
        },
        {
            "sent_id": "B",
            "corpus": "original",
            "text": "Hat der alte Hexenmeister Sich doch einmal wegbegeben!",
        },
        {
            "sent_id": "C",
            "corpus": "original",
            "text": "Seine Wort und Werke Merkt ich und den Brauch, Und mit Geistesstärke Tu ich Wunder auch.",
        },
    ]
    test_reuse_data = [
        {
            "sent_id": "a",
            "corpus": "reuse",
            "text": "Hat der alte Hexenmeister Sich doch einmal wegbegeben!",
        },
        {"sent_id": "b", "text": "Komm zurück zu mir", "corpus": "reuse"},
    ]

    # Create files
    orig_csv = tmp_path / "original.csv"
    pl.DataFrame(test_orig_data).write_csv(orig_csv)
    reuse_csv = tmp_path / "reuse.csv"
    pl.DataFrame(test_reuse_data).write_csv(reuse_csv)

    out_csv = tmp_path / "out.csv"
    find_quote_pairs(orig_csv, reuse_csv, out_csv)
    with out_csv.open(newline="") as file:
        reader = csv.reader(file)
        results = list(reader)
        assert len(results) == 2
        assert results[0] == [
            "reuse_id",
            "reuse_text",
            "original_id",
            "original_text",
            "match_score",
        ]
        assert results[1][0] == "a"
        assert results[1][1] == test_reuse_data[0]["text"]
        assert results[1][2] == "B"
        assert results[1][3] == test_orig_data[1]["text"]
        assert float(results[1][4]) == pytest.approx(1.0)
