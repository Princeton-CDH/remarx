"""
Tests for sentence embedding functionality.
"""

import logging
import re
from unittest.mock import Mock, patch

from remarx.quotation.embeddings import get_sentence_embeddings


@patch("remarx.quotation.embeddings.SentenceTransformer")
def test_get_sentence_embeddings(mock_transformer_class, caplog, tmp_path):
    """Test sentence embedding generation from list of sentences."""

    # Mock the sentence transformer
    mock_model = Mock()
    mock_embeddings = "mock_embeddings"
    mock_model.encode.return_value = mock_embeddings
    mock_transformer_class.return_value = mock_model

    sentences = ["Test sentence 1", "Test sentence 2"]

    # Use a temporary cache directory for this test
    with patch("remarx.quotation.embeddings._CACHE_DIR", tmp_path):
        with caplog.at_level(logging.INFO):
            result = get_sentence_embeddings(sentences)
        first_messages = [log[2] for log in caplog.record_tuples]
        assert any(
            re.fullmatch(
                rf"Generated {len(mock_embeddings)} embeddings in \d+\.\d seconds",
                message,
            )
            for message in first_messages
        )
        assert any(
            "Saved embeddings to cache file" in message for message in first_messages
        )

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

        # Test logging for cache hit
        caplog.clear()
        with caplog.at_level(logging.INFO):
            result = get_sentence_embeddings(sentences)
        cache_messages = [log[2] for log in caplog.record_tuples]
        assert any(
            "Loaded embeddings from cache file" in message for message in cache_messages
        )

        # Test with custom model
        mock_transformer_class.reset_mock()
        custom_model = "paraphrase-multilingual-mpnet-base-v3"

        caplog.clear()
        with caplog.at_level(logging.INFO):
            result = get_sentence_embeddings(sentences, model_name=custom_model)

        # Verify custom model was used for cache miss
        mock_transformer_class.assert_called_once_with(custom_model)
        assert result == mock_embeddings
