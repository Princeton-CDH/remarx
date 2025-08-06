"""
Unit tests for sentence segmentation functionality.
"""

import pathlib
import tempfile
from collections.abc import Generator
from unittest.mock import Mock

import pytest

from remarx.sentence_segmentation import SentenceSegmenter


@pytest.fixture
def segmenter() -> SentenceSegmenter:
    """Provide a SentenceSegmenter instance for testing."""
    return SentenceSegmenter()


@pytest.fixture
def temp_text_file() -> Generator[pathlib.Path, None, None]:
    """Create a temporary text file for testing."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write("Erster Satz. Zweiter Satz.")
        temp_path = pathlib.Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


def create_mock_sentence(text: str, start_char: int = 0) -> Mock:
    """Helper function: create a mock sentence with the given text and start character."""
    mock_sentence = Mock()
    mock_sentence.text = text
    mock_sentence.tokens = [Mock()]
    mock_sentence.tokens[0].start_char = start_char
    return mock_sentence


class TestSentenceSegmenter:
    """Test cases for the SentenceSegmenter class."""

    def test_init_default(self, segmenter: SentenceSegmenter) -> None:
        """Test SentenceSegmenter initialization with default parameters."""
        assert segmenter.lang == "de"
        assert segmenter.pipeline is not None

    def test_segment_file_success(
        self, segmenter: SentenceSegmenter, temp_text_file: pathlib.Path
    ) -> None:
        """Test successful file segmentation."""
        # Mock the pipeline
        mock_sentence1 = create_mock_sentence("Erster Satz.", 0)
        mock_sentence2 = create_mock_sentence("Zweiter Satz.", 14)

        mock_doc = Mock()
        mock_doc.sentences = [mock_sentence1, mock_sentence2]
        segmenter.pipeline = Mock(return_value=mock_doc)

        result = segmenter.segment_file(temp_text_file)

        assert len(result) == 2
        assert result[0]["file"] == temp_text_file.stem
        assert result[0]["text"] == "Erster Satz."
        assert result[1]["file"] == temp_text_file.stem
        assert result[1]["text"] == "Zweiter Satz."

    def test_segment_file_not_found(self, segmenter: SentenceSegmenter) -> None:
        """Test file segmentation with non-existent file."""
        with pytest.raises(FileNotFoundError):
            segmenter.segment_file(pathlib.Path("nonexistent_file.txt"))

    def test_segment_file_is_directory(self, segmenter: SentenceSegmenter) -> None:
        """Test file segmentation when path points to a directory."""
        with tempfile.TemporaryDirectory() as temp_dir, pytest.raises(ValueError):
            segmenter.segment_file(pathlib.Path(temp_dir))

    def test_segment_files_nonexistent_directory(
        self, segmenter: SentenceSegmenter
    ) -> None:
        """Test directory segmentation with non-existent directory."""
        with pytest.raises(ValueError, match="Directory does not exist"):
            list(segmenter.segment_files(pathlib.Path("nonexistent_directory")))

    def test_segment_files_not_directory(self, segmenter: SentenceSegmenter) -> None:
        """Test directory segmentation when path is not a directory."""
        with (
            tempfile.NamedTemporaryFile() as temp_file,
            pytest.raises(ValueError, match="Path is not a directory"),
        ):
            list(segmenter.segment_files(pathlib.Path(temp_file.name)))
