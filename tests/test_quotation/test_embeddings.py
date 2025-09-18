"""
Tests for sentence embedding functionality.
"""

from unittest.mock import Mock, patch

import pytest

from remarx.quotation.embeddings import get_sentence_embeddings


@pytest.mark.parametrize(
    "sentences,model_name,expected_model",
    [
        (
            ["Test sentence 1", "Test sentence 2"],
            None,
            "paraphrase-multilingual-mpnet-base-v2",
        ),
        (
            ["Test sentence 1", "Test sentence 2"],
            "paraphrase-multilingual-mpnet-base-v3",
            "paraphrase-multilingual-mpnet-base-v3",
        ),
    ],
)
@patch("remarx.quotation.embeddings.SentenceTransformer")
def test_get_sentence_embeddings(
    mock_transformer_class, sentences, model_name, expected_model
):
    """Test sentence embedding generation with different models and inputs."""

    # Mock the sentence transformer
    mock_model = Mock()
    mock_embeddings = "mock_embeddings"
    mock_model.encode.return_value = mock_embeddings
    mock_transformer_class.return_value = mock_model

    # Call function with or without model_name
    if model_name is None:
        result = get_sentence_embeddings(sentences)
    else:
        result = get_sentence_embeddings(sentences, model_name=model_name)

    # Verify the model was initialized with expected model name
    mock_transformer_class.assert_called_once_with(expected_model)

    # Verify encode was called with correct parameters
    mock_model.encode.assert_called_once_with(
        sentences,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    assert result == mock_embeddings
