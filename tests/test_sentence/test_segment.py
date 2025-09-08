"""
Unit tests for sentence segmentation functionality.
"""

from unittest.mock import Mock, patch

from stanza import DownloadMethod, Pipeline
from stanza.models.common.doc import Document, Sentence

from remarx.sentence.segment import segment_text


def create_mock_sentence(text: str, start_char: int = 0) -> Mock:
    """Helper function: create a mock sentence with the given text and start character."""
    return Mock(spec=Sentence, text=text, tokens=[Mock(start_char=start_char)])


class TestSegmentTextIntoSentences:
    """Test cases for the segment_text_into_sentences function."""

    @patch("remarx.sentence.segment.stanza.Pipeline")
    def test_segment_text_indices(self, mock_pipeline_class: Mock) -> None:
        """Test text segmentation with character indices."""
        # Setup mock
        mock_sentence1 = create_mock_sentence("Erster Satz.", 0)
        mock_sentence2 = create_mock_sentence("Zweiter Satz.", 14)

        mock_doc = Mock(spec=Document, sentences=[mock_sentence1, mock_sentence2])

        mock_pipeline = Mock(spec=Pipeline, return_value=mock_doc)
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
        mock_doc = Mock(spec=Document, sentences=[])

        mock_pipeline = Mock(spec=Pipeline, return_value=mock_doc)
        mock_pipeline_class.return_value = mock_pipeline

        # Test
        result = segment_text("")

        # Assertions
        assert result == []

    @patch("remarx.sentence.segment.stanza.Pipeline")
    def test_segment_text_language_parameter(self, mock_pipeline_class: Mock) -> None:
        """Test that language parameter works or not."""
        # Setup mock
        mock_sentence = create_mock_sentence("Hallo Welt.", 0)
        mock_doc = Mock(spec=Document, sentences=[mock_sentence])
        mock_pipeline = Mock(spec=Pipeline, return_value=mock_doc)
        mock_pipeline_class.return_value = mock_pipeline

        # Test with explicit "en" language
        segment_text("Hello world.", language="en")
        mock_pipeline_class.assert_called_with(
            lang="en",
            processors="tokenize",
            download_method=DownloadMethod.REUSE_RESOURCES,
        )

        # Reset mock for second test
        mock_pipeline_class.reset_mock()

        # Test with default language (should be "de")
        segment_text("Hallo Welt.")
        mock_pipeline_class.assert_called_with(
            lang="de",
            processors="tokenize",
            download_method=DownloadMethod.REUSE_RESOURCES,
        )
