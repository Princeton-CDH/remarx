"""
Tests for sentence embedding functionality.
"""

from unittest.mock import Mock, patch

import numpy as np
import pytest

from remarx.sentence.embeddings import get_sentence_embeddings


class TestGetSentenceEmbeddings:
    @patch("remarx.sentence.embeddings.SentenceTransformer")
    def test_get_sentence_embeddings_basic(self, mock_transformer_class):
        """Test basic sentence embedding generation from list of sentences."""

        # Mock the sentence transformer
        mock_model = Mock()
        mock_embeddings = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        mock_model.encode.return_value = mock_embeddings
        mock_transformer_class.return_value = mock_model

        sentences = [
            "Das ist ein Test.",  # codespell:ignore
            "Dies ist ein weiterer Test.",  # codespell:ignore
        ]

        result = get_sentence_embeddings(sentences)

        # Verify the model was initialized with default model name
        mock_transformer_class.assert_called_once_with(
            "paraphrase-multilingual-mpnet-base-v2"
        )

        # Verify encode was called with correct parameters
        mock_model.encode.assert_called_once_with(
            sentences,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        np.testing.assert_array_equal(result, mock_embeddings)

    @patch("remarx.sentence.embeddings.SentenceTransformer")
    def test_get_sentence_embeddings_custom_model(self, mock_transformer_class):
        """Test sentence embedding generation with custom model."""

        # Mock the sentence transformer
        mock_model = Mock()
        mock_embeddings = np.array([[0.1, 0.2]])
        mock_model.encode.return_value = mock_embeddings
        mock_transformer_class.return_value = mock_model

        sentences = ["Test sentence."]
        custom_model = "paraphrase-multilingual-MiniLM-L12-v2"

        result = get_sentence_embeddings(sentences, model_name=custom_model)

        # Verify custom model was used
        mock_transformer_class.assert_called_once_with(custom_model)

        # Verify encode was called with correct parameters
        mock_model.encode.assert_called_once_with(
            sentences,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        np.testing.assert_array_equal(result, mock_embeddings)

    @patch("remarx.sentence.embeddings.SentenceTransformer")
    def test_get_sentence_embeddings_empty_list(self, mock_transformer_class):
        """Test sentence embedding generation with empty sentence list."""

        # Mock the sentence transformer
        mock_model = Mock()
        mock_embeddings = np.array([]).reshape(0, 384)  # Empty array with proper shape
        mock_model.encode.return_value = mock_embeddings
        mock_transformer_class.return_value = mock_model

        sentences = []

        result = get_sentence_embeddings(sentences)

        # Verify the model was initialized
        mock_transformer_class.assert_called_once_with(
            "paraphrase-multilingual-mpnet-base-v2"
        )

        # Verify encode was called with empty list
        mock_model.encode.assert_called_once_with(
            sentences,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        np.testing.assert_array_equal(result, mock_embeddings)

    @patch("remarx.sentence.embeddings.SentenceTransformer")
    def test_get_sentence_embeddings_single_sentence(self, mock_transformer_class):
        """Test sentence embedding generation with single sentence."""

        # Mock the sentence transformer
        mock_model = Mock()
        mock_embeddings = np.array([[0.1, 0.2, 0.3]])
        mock_model.encode.return_value = mock_embeddings
        mock_transformer_class.return_value = mock_model

        sentences = ["Single test sentence."]

        result = get_sentence_embeddings(sentences)

        # Verify the model was initialized
        mock_transformer_class.assert_called_once_with(
            "paraphrase-multilingual-mpnet-base-v2"
        )

        # Verify encode was called with single sentence
        mock_model.encode.assert_called_once_with(
            sentences,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        np.testing.assert_array_equal(result, mock_embeddings)


def test_sentence_transformers_import_error():
    """Test that ImportError is raised when sentence-transformers is not available."""

    with patch.dict("sys.modules", {"sentence_transformers": None}):
        # Force reimport to trigger the ImportError
        import importlib

        import remarx.sentence.embeddings

        with pytest.raises(
            ImportError, match="sentence-transformers library is required"
        ):
            importlib.reload(remarx.sentence.embeddings)
