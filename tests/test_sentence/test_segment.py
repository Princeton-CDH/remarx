"""
Unit tests for sentence segmentation functionality.
"""

from unittest.mock import Mock, patch

from spacy.tokens import Span

from remarx.sentence.segment import segment_text


def create_mock_sentence(text: str, start_char: int = 0) -> Mock:
    """Helper function: create a mock sentence with the given text and start character."""
    return Mock(spec=Span, text=text, start_char=start_char)


class TestSegmentTextIntoSentences:
    """Test cases for the segment_text_into_sentences function."""

    @patch("remarx.sentence.segment.spacy.load")
    def test_segment_text_indices(self, mock_spacy_load: Mock) -> None:
        """Test text segmentation with character indices."""
        # Setup mock
        mock_sentence1 = create_mock_sentence("Erster Satz.", 0)
        mock_sentence2 = create_mock_sentence("Zweiter Satz.", 14)

        mock_doc = Mock()
        mock_doc.sents = [mock_sentence1, mock_sentence2]

        mock_nlp = Mock(return_value=mock_doc)
        mock_spacy_load.return_value = mock_nlp

        # Test
        text = "Erster Satz. Zweiter Satz."
        result = segment_text(text)

        # Assertions
        assert len(result) == 2
        assert result[0] == (0, "Erster Satz.")
        assert result[1] == (14, "Zweiter Satz.")

    @patch("remarx.sentence.segment.spacy.load")
    def test_segment_text_empty_text(self, mock_spacy_load: Mock) -> None:
        """Test segmentation of empty text."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.sents = []

        mock_nlp = Mock(return_value=mock_doc)
        mock_spacy_load.return_value = mock_nlp

        # Test
        result = segment_text("")

        # Assertions
        assert result == []

    @patch("remarx.sentence.segment.spacy.load")
    def test_segment_text_model_parameter(self, mock_spacy_load: Mock) -> None:
        """Test that model parameter works or not."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.sents = []

        mock_nlp = Mock(return_value=mock_doc)
        mock_spacy_load.return_value = mock_nlp

        # Test with explicit model
        segment_text("Hello world.", model="en_core_web_sm")
        mock_spacy_load.assert_called_with("en_core_web_sm")

        # Reset mock for second test
        mock_spacy_load.reset_mock()

        # Test with default model (should be "de_core_news_sm")
        segment_text("Hallo Welt.")
        mock_spacy_load.assert_called_with("de_core_news_sm")

    @patch("remarx.sentence.segment.logger")
    @patch("remarx.sentence.segment.download")
    @patch("remarx.sentence.segment.spacy.load")
    def test_segment_text_downloads_model_if_missing(
        self,
        mock_spacy_load: Mock,
        mock_spacy_download: Mock,
        mock_logger: Mock,
    ) -> None:
        """Test that the model is downloaded automatically if not installed."""
        # First call to spacy.load -> simulate missing model
        # Second call -> simulate successful load after download
        mock_sentence = Mock(spec=Span, text="Erster Satz.", start_char=0)
        mock_doc = Mock()
        mock_doc.sents = [mock_sentence]

        # Configure load() to fail once, then succeed
        mock_spacy_load.side_effect = [
            OSError("model not installed"),  # first call raises
            Mock(return_value=mock_doc),  # second call returns nlp()
        ]

        result = segment_text("Erster Satz.")
        assert result == [(0, "Erster Satz.")]

        # spacy.load called twice: before and after download
        assert mock_spacy_load.call_count == 2

        # download called once with default model
        mock_spacy_download.assert_called_once_with("de_core_news_sm")

        # logger.info called once with download message
        mock_logger.info.assert_called_once_with(
            "Downloading spaCy model: 'de_core_news_sm'"
        )
