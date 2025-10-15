"""
Tests for sentence embedding functionality.
"""

import logging
import re
from unittest.mock import Mock, patch

from remarx.quotation.embeddings import get_sentence_embeddings


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
