import logging
import sys
from unittest.mock import patch

import pytest

from remarx.quotation import find_quotes
from remarx.utils import CorpusPath


@patch("remarx.quotation.find_quotes.configure_logging")
@patch("remarx.quotation.find_quotes.find_quote_pairs")
def test_main(mock_find_quote_pairs, mock_configure_logging, tmp_path):
    orig_input = tmp_path / "orig.csv"
    orig_input.touch()
    reuse_input = tmp_path / "reuse.csv"
    reuse_input.touch()
    # output = tmp_path / "out" / "pairs.csv"
    output = tmp_path / "pairs.csv"
    # default options
    args = [
        "remarx-find-quotes",
        "-o",
        str(orig_input),
        str(reuse_input),
        str(output),
    ]
    with patch("sys.argv", args):
        find_quotes.main()

    mock_configure_logging.assert_called_with(sys.stdout, log_level=logging.INFO)
    # consolidate and benchmark are default options
    mock_find_quote_pairs.assert_called_with(
        original_corpus=[orig_input],
        reuse_corpus=reuse_input,
        out_csv=output,
        consolidate=True,
        benchmark=False,
    )

    # verbose
    verbose_args = [*args, "--verbose"]
    with patch("sys.argv", verbose_args):
        find_quotes.main()
    mock_configure_logging.assert_called_with(sys.stdout, log_level=logging.DEBUG)

    # no consolidate, benchmark
    verbose_args = [*args, "--no-consolidate", "--benchmark"]
    with patch("sys.argv", verbose_args):
        find_quotes.main()
    mock_find_quote_pairs.assert_called_with(
        original_corpus=[orig_input],
        reuse_corpus=reuse_input,
        out_csv=output,
        consolidate=False,
        benchmark=True,
    )


@patch("remarx.quotation.find_quotes.configure_logging")
@patch("remarx.quotation.find_quotes.find_quote_pairs")
def test_main_check_paths(
    mock_find_quote_pairs, mock_configure_logging, tmp_path, capsys
):
    orig_input = tmp_path / "orig.csv"
    reuse_input = tmp_path / "reuse.csv"
    output = tmp_path / "out" / "pairs.csv"
    args = [
        "remarx-find-quotes",
        "-o",
        str(orig_input),
        str(reuse_input),
        str(output),
    ]
    with patch("sys.argv", args):
        # input files and output directory do not exist
        with pytest.raises(SystemExit):
            find_quotes.main()
        captured = capsys.readouterr()
        assert captured.err == f"Error: input file {orig_input} does not exist\n"

        # reuse input file does not exist
        orig_input.touch()
        with pytest.raises(SystemExit):
            find_quotes.main()
        captured = capsys.readouterr()
        assert captured.err == f"Error: input file {reuse_input} does not exist\n"

        # output directory does not exist
        reuse_input.touch()
        with pytest.raises(SystemExit):
            find_quotes.main()
        captured = capsys.readouterr()
        assert (
            captured.err == f"Error: output directory {output.parent} does not exist\n"
        )


@patch("remarx.quotation.find_quotes.configure_logging")
@patch("remarx.quotation.find_quotes.find_quote_pairs")
def test_main_default_original_directory(
    mock_find_quote_pairs, mock_configure_logging, tmp_path, monkeypatch
):
    default_dir = tmp_path / "default"
    default_dir.mkdir()
    default_file = default_dir / "default.csv"
    default_file.touch()
    # Create a CorpusPath object with the test directory as the original path
    test_corpus_paths = CorpusPath(original=default_dir)
    monkeypatch.setattr(
        find_quotes, "DEFAULT_CORPUS_DIRS", test_corpus_paths, raising=False
    )

    reuse_input = tmp_path / "reuse.csv"
    reuse_input.touch()
    output = tmp_path / "pairs.csv"

    args = ["remarx-find-quotes", str(reuse_input), str(output)]
    with patch("sys.argv", args):
        find_quotes.main()

    mock_find_quote_pairs.assert_called_with(
        original_corpus=[default_file],
        reuse_corpus=reuse_input,
        out_csv=output,
        consolidate=True,
        benchmark=False,
    )


@patch("remarx.quotation.find_quotes.configure_logging")
@patch("remarx.quotation.find_quotes.find_quote_pairs")
def test_main_original_directory(
    mock_find_quote_pairs, mock_configure_logging, tmp_path
):
    orig_dir = tmp_path / "originals"
    orig_dir.mkdir()
    file_a = orig_dir / "a.csv"
    file_b = orig_dir / "b.csv"
    file_a.touch()
    file_b.touch()
    reuse_input = tmp_path / "reuse.csv"
    reuse_input.touch()
    output = tmp_path / "pairs.csv"

    args = [
        "remarx-find-quotes",
        "-o",
        str(orig_dir),
        str(reuse_input),
        str(output),
    ]
    with patch("sys.argv", args):
        find_quotes.main()

    # Verify the function was called with the correct arguments
    # Note: original_corpus order may vary, so we check that all expected files are present
    assert mock_find_quote_pairs.called
    call_args = mock_find_quote_pairs.call_args
    assert call_args.kwargs["reuse_corpus"] == reuse_input
    assert call_args.kwargs["out_csv"] == output
    assert call_args.kwargs["consolidate"] is True
    assert call_args.kwargs["benchmark"] is False

    # Check that both expected files are in the original_corpus, regardless of order
    actual_files = set(call_args.kwargs["original_corpus"])
    expected_files = {file_a, file_b}
    assert actual_files == expected_files


@patch("remarx.quotation.find_quotes.configure_logging")
@patch("remarx.quotation.find_quotes.find_quote_pairs")
def test_main_original_directory_without_csv(
    mock_find_quote_pairs, mock_configure_logging, tmp_path, capsys
):
    orig_dir = tmp_path / "originals"
    orig_dir.mkdir()
    reuse_input = tmp_path / "reuse.csv"
    reuse_input.touch()
    output = tmp_path / "pairs.csv"

    args = [
        "remarx-find-quotes",
        "-o",
        str(orig_dir),
        str(reuse_input),
        str(output),
    ]
    with patch("sys.argv", args), pytest.raises(SystemExit):
        find_quotes.main()

    captured = capsys.readouterr()
    assert (
        captured.err == f"Error: directory {orig_dir} does not contain any CSV files\n"
    )
    mock_find_quote_pairs.assert_not_called()


@patch("remarx.quotation.find_quotes.configure_logging")
@patch("remarx.quotation.find_quotes.find_quote_pairs")
def test_main_too_few_paths(mock_find_quote_pairs, mock_configure_logging, capsys):
    with (
        patch("sys.argv", ["remarx-find-quotes", "only_one_path"]),
        pytest.raises(SystemExit),
    ):
        find_quotes.main()
    assert "required: output_path" in capsys.readouterr().err
    mock_find_quote_pairs.assert_not_called()


@patch("remarx.quotation.find_quotes.configure_logging")
@patch("remarx.quotation.find_quotes.find_quote_pairs")
def test_main_multiple_original_files(
    mock_find_quote_pairs, mock_configure_logging, tmp_path
):
    orig_input = tmp_path / "orig.csv"
    second_input = tmp_path / "orig2.csv"
    orig_input.touch()
    second_input.touch()
    reuse_input = tmp_path / "reuse.csv"
    reuse_input.touch()
    output = tmp_path / "pairs.csv"

    args = [
        "remarx-find-quotes",
        "-o",
        str(orig_input),
        str(second_input),
        str(reuse_input),
        str(output),
    ]
    with patch("sys.argv", args):
        find_quotes.main()

    mock_find_quote_pairs.assert_called_with(
        original_corpus=[orig_input, second_input],
        reuse_corpus=reuse_input,
        out_csv=output,
        consolidate=True,
        benchmark=False,
    )


def test_gather_csv_files_errors(tmp_path):
    missing = tmp_path / "missing.csv"
    with pytest.raises(ValueError, match="does not exist"):
        find_quotes.gather_csv_files([missing])

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    with pytest.raises(ValueError, match="does not contain any CSV"):
        find_quotes.gather_csv_files([empty_dir])

    with pytest.raises(ValueError, match="no original corpora"):
        find_quotes.gather_csv_files([])
