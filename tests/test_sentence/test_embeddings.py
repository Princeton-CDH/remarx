"""
Tests for sentence embedding functionality.
"""

import csv
import pathlib
import sys
import tempfile
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from remarx.sentence.corpus.base_input import FileInput
from remarx.sentence.embeddings import get_sentence_embeddings, validate_sentence_corpus


@pytest.fixture(autouse=True)
def mock_sentence_transformers():
    """Mock sentence_transformers to avoid heavy dependencies in tests."""
    if "sentence_transformers" not in sys.modules:
        sys.modules["sentence_transformers"] = MagicMock()


@pytest.fixture
def create_test_corpus():
    """Fixture to create test CSV corpus files."""

    def _create_test_corpus(
        temp_dir: pathlib.Path, sentences: list[str] | None = None
    ) -> pathlib.Path:
        """Helper to create a test CSV corpus file."""
        if sentences is None:
            sentences = [
                "Das ist ein Test.",  # codespell:ignore
                "Dies ist ein weiterer Test.",  # codespell:ignore
            ]

        corpus_file = temp_dir / "test_corpus.csv"
        with corpus_file.open("w", encoding="utf-8", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FileInput.field_names)
            writer.writeheader()
            for i, sentence in enumerate(sentences):
                writer.writerow({"file": "test.txt", "sent_index": i, "text": sentence})
        return corpus_file

    return _create_test_corpus


class TestValidateSentenceCorpus:
    def test_validate_sentence_corpus_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent file."""

        non_existent_file = pathlib.Path("non_existent_corpus.csv")

        with pytest.raises(FileNotFoundError, match="Sentence corpus file not found"):
            validate_sentence_corpus(non_existent_file)

    def test_validate_sentence_corpus_missing_required_columns(self):
        """Test that ValueError is raised when CSV lacks required columns."""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)

            # Test missing 'text' column
            corpus_file = temp_path / "missing_text.csv"
            with corpus_file.open("w", encoding="utf-8", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["file", "sent_index"])
                writer.writeheader()
                writer.writerow({"file": "test.txt", "sent_index": 0})

            with pytest.raises(
                ValueError, match="CSV file is missing required columns: \\['text'\\]"
            ):
                validate_sentence_corpus(corpus_file)

    def test_validate_sentence_corpus_no_columns(self):
        """Test that ValueError is raised for CSV with no columns."""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            corpus_file = temp_path / "no_columns.csv"

            # Create empty CSV file
            with corpus_file.open("w", encoding="utf-8", newline="") as csvfile:
                csvfile.write("")

            with pytest.raises(
                ValueError,
                match="CSV file is missing required columns: \\['file', 'sent_index', 'text'\\]",
            ):
                validate_sentence_corpus(corpus_file)

    def test_validate_sentence_corpus_empty(self):
        """Test that ValueError is raised for corpus file with no data rows."""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            corpus_file = temp_path / "empty_corpus.csv"

            # Create empty CSV with headers only
            with corpus_file.open("w", encoding="utf-8", newline="") as csvfile:
                writer = csv.DictWriter(
                    csvfile, fieldnames=["file", "sent_index", "text"]
                )
                writer.writeheader()

            with pytest.raises(
                ValueError, match="No sentences found in the corpus file"
            ):
                validate_sentence_corpus(corpus_file)


class TestGetSentenceEmbeddings:
    @patch("remarx.sentence.embeddings.SentenceTransformer")
    def test_get_sentence_embeddings_basic(
        self, mock_transformer_class, create_test_corpus
    ):
        """Test basic sentence embedding generation from CSV file."""

        # Mock the sentence transformer
        mock_model = Mock()
        mock_embeddings = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        mock_model.encode.return_value = mock_embeddings
        mock_transformer_class.return_value = mock_model

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            corpus_file = create_test_corpus(temp_path)

            result = get_sentence_embeddings(corpus_file)

            np.testing.assert_array_equal(result, mock_embeddings)

    @patch("remarx.sentence.embeddings.SentenceTransformer")
    def test_get_sentence_embeddings_custom_model(
        self, mock_transformer_class, create_test_corpus
    ):
        """Test sentence embedding generation with custom model."""

        # Mock the sentence transformer
        mock_model = Mock()
        mock_embeddings = np.array([[0.1, 0.2]])
        mock_model.encode.return_value = mock_embeddings
        mock_transformer_class.return_value = mock_model

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            corpus_file = create_test_corpus(temp_path, ["Test sentence."])

            custom_model = "paraphrase-multilingual-MiniLM-L12-v2"
            result = get_sentence_embeddings(corpus_file, model_name=custom_model)

            # Verify custom model was used
            mock_transformer_class.assert_called_once_with(custom_model)

            np.testing.assert_array_equal(result, mock_embeddings)


@patch("remarx.sentence.embeddings.get_sentence_embeddings")
@patch("numpy.save")
def test_main(mock_np_save, mock_get_embeddings):
    """Test the main command-line interface."""
    import numpy as np

    from remarx.sentence.embeddings import main

    mock_embeddings = np.array([[0.1, 0.2, 0.3]])
    mock_get_embeddings.return_value = mock_embeddings

    with patch("sys.argv", ["remarx-generate-embeddings", "input.csv", "output.npy"]):
        main()
        mock_get_embeddings.assert_called_once_with(
            pathlib.Path("input.csv"),
            model_name="paraphrase-multilingual-mpnet-base-v2",
        )
        mock_np_save.assert_called_once_with(
            pathlib.Path("output.npy"), mock_embeddings
        )
