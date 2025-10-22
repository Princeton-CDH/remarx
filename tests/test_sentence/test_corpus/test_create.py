import logging
import pathlib
import sys
from unittest.mock import Mock, patch

import pytest

from remarx.sentence.corpus.base_input import FileInput
from remarx.sentence.corpus.create import create_corpus, main


@patch("remarx.sentence.corpus.create.FileInput", spec=FileInput)
def test_create_corpus(mock_file_input, tmp_path: pathlib.Path):
    # Raise error when given dir
    with pytest.raises(ValueError, match=f"Input file {tmp_path} does not exist"):
        create_corpus(tmp_path, "out_path")

    # Raise error when given path to a non-existent file
    missing_file = tmp_path / "missing.txt"
    with pytest.raises(ValueError, match=f"Input file {missing_file} does not exist"):
        create_corpus(missing_file, "out_path")

    # Regular case
    ## File setup
    input_file = tmp_path / "input.txt"
    input_file.touch()
    out_csv = tmp_path / "out.csv"
    ## Mock input text
    mock_input = Mock()
    mock_file_input.create.return_value = mock_input
    mock_input.field_names = ["some", "field", "names"]
    mock_input.get_sentences.return_value = [
        {"some": "a", "field": "b", "names": "c"},
        {"some": "1", "field": "2", "names": "3"},
    ]

    create_corpus(input_file, out_csv)

    assert out_csv.is_file()
    mock_file_input.create.assert_called_once_with(input_file, filename_override=None)
    mock_input.get_sentences.assert_called_once_with()
    assert out_csv.read_text() == "some,field,names\na,b,c\n1,2,3\n"


@patch("remarx.sentence.corpus.create.FileInput", spec=FileInput)
def test_create_corpus_filename_override(mock_file_input, tmp_path: pathlib.Path):
    # test that filename override is passed through
    input_file = tmp_path / "tmp_foo_input_bar.txt"
    input_file.touch()
    out_csv = tmp_path / "out.csv"
    real_filename = "input.txt"
    create_corpus(input_file, out_csv, filename_override=real_filename)
    mock_file_input.create.assert_called_once_with(
        input_file, filename_override=real_filename
    )


@patch("remarx.sentence.corpus.create.configure_logging")
@patch("remarx.sentence.corpus.create.create_corpus", spec=create_corpus)
def test_main(mock_create_corpus, mock_config_logging):
    with patch("sys.argv", ["create_corpus.py", "input", "output"]):
        main()
        mock_create_corpus.assert_called_once_with(
            pathlib.Path("input"), pathlib.Path("output")
        )
        mock_config_logging.assert_called_once_with(sys.stdout, log_level=logging.INFO)

    mock_config_logging.reset_mock()
    # test verbose arg
    with patch("sys.argv", ["create_corpus.py", "input", "output", "-v"]):
        main()
        mock_config_logging.assert_called_once_with(sys.stdout, log_level=logging.DEBUG)
