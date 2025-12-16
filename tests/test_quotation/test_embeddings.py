"""
Tests for sentence embedding functionality.
"""

import io
import logging
import re
import time
from unittest.mock import Mock, patch

import numpy as np

from remarx.quotation.embeddings import (
    DEFAULT_MODEL,
    get_cached_embeddings,
    get_sentence_embeddings,
)


@patch("remarx.quotation.embeddings.SentenceTransformer")
def test_get_sentence_embeddings(mock_transformer_class, caplog):
    """Test sentence embedding generation from list of sentences."""

    # Mock the sentence transformer
    mock_model = Mock()
    mock_embeddings = "mock_embeddings"
    mock_model.encode.return_value = mock_embeddings
    mock_transformer_class.return_value = mock_model

    sentences = ["Test sentence 1", "Test sentence 2"]

    result = get_sentence_embeddings(sentences)

    # Verify the model was initialized with default model name
    mock_transformer_class.assert_called_once_with(
        "paraphrase-multilingual-mpnet-base-v2"
    )

    # Verify encode was called with correct parameters
    mock_model.encode.assert_called_once_with(
        sentences,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    assert result == mock_embeddings

    # Test logging
    caplog.clear()
    with caplog.at_level(logging.INFO):
        result = get_sentence_embeddings(sentences)
    assert len(caplog.record_tuples) == 1
    log = caplog.record_tuples[0]
    assert log[0] == "remarx.quotation.embeddings"
    assert log[1] == logging.INFO
    assert re.fullmatch(
        rf"Generated {len(mock_embeddings)} embeddings in \d+\.\d seconds", log[2]
    )

    # Test with custom model
    mock_transformer_class.reset_mock()
    custom_model = "paraphrase-multilingual-mpnet-base-v3"

    result = get_sentence_embeddings(sentences, model_name=custom_model)

    # Verify custom model was used
    mock_transformer_class.assert_called_once_with(custom_model)
    assert result == mock_embeddings


@patch("remarx.quotation.embeddings.np")
@patch("remarx.quotation.embeddings.get_sentence_embeddings")
def test_get_cached_embeddings(mock_get_sent_embeddings, mock_np, tmp_path):
    # create source file
    source_file = tmp_path / "sentences.csv"
    source_file.touch()
    sentences = ["one", "two"]
    # cache file named based on source file and model
    expected_cachefile = tmp_path / f"sentences_{DEFAULT_MODEL}.npy"

    # call with source file (no cache)
    embed, from_cache = get_cached_embeddings(source_file, sentences)
    assert not from_cache
    assert embed == mock_get_sent_embeddings.return_value
    # calls get embeddings, and then save
    mock_get_sent_embeddings.assert_called_once_with(
        sentences, model_name=DEFAULT_MODEL, show_progress_bar=False
    )
    # np.save called once with cache file handle and embeddings
    save_args, save_kwargs = mock_np.save.call_args
    assert isinstance(save_args[0], io.BufferedWriter)
    assert save_args[1] == mock_get_sent_embeddings.return_value
    assert save_kwargs["allow_pickle"]

    # cache file exists but is zero size
    mock_get_sent_embeddings.reset_mock()
    expected_cachefile.touch()
    embed, from_cache = get_cached_embeddings(source_file, sentences)
    assert not from_cache
    mock_get_sent_embeddings.assert_called_once_with(
        sentences, model_name=DEFAULT_MODEL, show_progress_bar=False
    )

    # cache file exists and has content
    mock_get_sent_embeddings.reset_mock()
    mock_np.reset_mock()
    expected_cachefile.write_text("test")
    embed, from_cache = get_cached_embeddings(source_file, sentences)
    assert from_cache
    mock_get_sent_embeddings.assert_not_called()
    # embeddings loaded from file and returned
    mock_np.load.assert_called_once()
    assert embed == mock_np.load.return_value
    load_args, _load_kwargs = mock_np.load.call_args
    assert isinstance(load_args[0], io.BufferedReader)
    # save not called
    mock_np.save.assert_not_called()

    # cache file exists but source file is newer
    mock_get_sent_embeddings.reset_mock()
    mock_np.reset_mock()
    source_file.touch()
    embed, from_cache = get_cached_embeddings(source_file, sentences)
    assert not from_cache
    mock_get_sent_embeddings.assert_called_once_with(
        sentences, model_name=DEFAULT_MODEL, show_progress_bar=False
    )

    # specify alternate model
    mock_get_sent_embeddings.reset_mock()
    mock_np.reset_mock()
    alt_model = "alt-paraphrase"
    embed, from_cache = get_cached_embeddings(
        source_file, sentences, model_name=alt_model
    )
    assert not from_cache
    assert embed == mock_get_sent_embeddings.return_value
    # calls get with specified model name
    mock_get_sent_embeddings.assert_called_once_with(
        sentences, model_name=alt_model, show_progress_bar=False
    )

    # enable progress bar
    mock_get_sent_embeddings.reset_mock()
    get_cached_embeddings(source_file, sentences, show_progress_bar=True)
    mock_get_sent_embeddings.assert_called_once_with(
        sentences, model_name=DEFAULT_MODEL, show_progress_bar=True
    )


@patch("remarx.quotation.embeddings.get_sentence_embeddings")
def test_get_cached_embeddings_np_integration(mock_get_sent_embeddings, tmp_path):
    # test saving and loading cached embeddings without mocking numpy save/load
    sample_vecs = np.array([[1], [3], [7]])
    # create source file
    source_file = tmp_path / "input.csv"
    source_file.touch()
    sentences = ["one", "two"]
    # cache file named based on source file and model
    expected_cachefile = tmp_path / f"input_{DEFAULT_MODEL}.npy"
    # return sample vector data
    mock_get_sent_embeddings.return_value = sample_vecs

    # call with source file (no cache)
    embed, from_cache = get_cached_embeddings(source_file, sentences)
    assert not from_cache
    assert np.array_equal(embed, sample_vecs)
    # cache file exists
    assert expected_cachefile.exists()
    # cache file has expected contents
    with expected_cachefile.open("rb") as cache_filehandle:
        saved_vecs = np.load(cache_filehandle)
    assert np.array_equal(saved_vecs, sample_vecs)

    # ensure cache file timestamp is newer than source file
    time.sleep(0.1)
    expected_cachefile.touch()

    # call again to load from cache
    embed, from_cache = get_cached_embeddings(source_file, sentences)
    assert from_cache
    assert np.array_equal(embed, sample_vecs)
