"""
Unit tests for sentence segmentation functionality.
"""

from unittest.mock import Mock, patch

from remarx.sentence.segment import segment_text


def create_mock_sentence(text: str, start_char: int = 0) -> Mock:
    """Helper function: create a mock sentence with the given text and start character."""
    mock_sentence = Mock()
    mock_sentence.text = text
    mock_sentence.tokens = [Mock()]
    mock_sentence.tokens[0].start_char = start_char
    return mock_sentence


class TestSegmentTextIntoSentences:
    """Test cases for the segment_text_into_sentences function."""

    @patch("remarx.sentence.segment.stanza.Pipeline")
    def test_segment_text_indices(self, mock_pipeline_class: Mock) -> None:
        """Test text segmentation with character indices."""
        # Setup mock
        mock_sentence1 = create_mock_sentence("Erster Satz.", 0)
        mock_sentence2 = create_mock_sentence("Zweiter Satz.", 14)

        mock_doc = Mock()
        mock_doc.sentences = [mock_sentence1, mock_sentence2]

        mock_pipeline = Mock(return_value=mock_doc)
        mock_pipeline_class.return_value = mock_pipeline

        # Test
        text = "Erster Satz. Zweiter Satz."
        result = segment_text(text)

        # Assertions
        assert len(result) == 2
        assert result[0] == (0, "Erster Satz.")
        assert result[1] == (14, "Zweiter Satz.")

    @patch("remarx.sentence.segment.stanza.Pipeline")
    def test_segment_text_empty_text(self, mock_pipeline_class: Mock) -> None:
        """Test segmentation of empty text."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.sentences = []

        mock_pipeline = Mock(return_value=mock_doc)
        mock_pipeline_class.return_value = mock_pipeline

        # Test
        result = segment_text("")

        # Assertions
        assert result == []
