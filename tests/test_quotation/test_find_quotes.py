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
    output = tmp_path / "pairs.csv"
    # standard options
    args = ["find-qs", "-o", str(orig_input), str(reuse_input), str(output)]
    with patch("sys.argv", args):
        find_quotes.main()

    mock_configure_logging.assert_called_with(sys.stdout, log_level=logging.INFO)
    # consolidate and benchmark are default options
    mock_find_quote_pairs.assert_called_with(
        original_corpus=[orig_input],
        reuse_corpus=reuse_input,
        output_path=output,
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
        output_path=output,
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
        # reuse input file does not exist
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

        # single original input file specified, does not exist
        output.parent.mkdir()
        with pytest.raises(SystemExit):
            find_quotes.main()
        captured = capsys.readouterr()
        assert captured.err == f"Error: input file {orig_input} does not exist\n"


@patch("remarx.quotation.find_quotes.configure_logging")
@patch("remarx.quotation.find_quotes.find_quote_pairs")
@patch("remarx.quotation.find_quotes.gather_csv_files")
@patch("remarx.quotation.find_quotes.CorpusPath", spec=CorpusPath)
def test_main_default_original_directory(
    mock_corpus_paths,
    mock_gather_csvs,
    mock_find_quote_pairs,
    mock_configure_logging,
    tmp_path,
    capsys,
):
    default_dir = tmp_path / "default"
    default_dir.mkdir()
    default_file = default_dir / "default.csv"
    default_file.touch()

    reuse_input = tmp_path / "reuse.csv"
    reuse_input.touch()
    output = tmp_path / "pairs.csv"

    # patch corpus path object to return tmp default path
    mock_corpus_paths.return_value.original = default_dir
    mock_gather_csvs.return_value = [default_file]

    args = ["remarx-find-quotes", str(reuse_input), str(output)]
    with patch("sys.argv", args):
        find_quotes.main()

    mock_gather_csvs.assert_called_with([default_dir])

    mock_find_quote_pairs.assert_called_with(
        original_corpus=[default_file],
        reuse_corpus=reuse_input,
        output_path=output,
        consolidate=True,
        benchmark=False,
    )

    # original corpus reported
    captured = capsys.readouterr()
    assert captured.out.startswith(
        f"No original corpora specified; defaulting to {default_dir}"
    )
    assert captured.out.endswith(f"Original corpus: {default_file}\n")


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
    assert call_args.kwargs["output_path"] == output
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
@patch("remarx.quotation.find_quotes.gather_csv_files")
def test_main_multiple_original_files(
    mock_gather_csvs, mock_find_quote_pairs, mock_configure_logging, tmp_path
):
    orig_input = tmp_path / "orig.csv"
    second_input = tmp_path / "orig2.csv"
    orig_input.touch()
    second_input.touch()
    reuse_input = tmp_path / "reuse.csv"
    reuse_input.touch()
    output = tmp_path / "pairs.csv"
    mock_gather_csvs.return_value = [orig_input, second_input]

    args = [
        "find-qs",
        "-o",
        str(orig_input),
        "-o",
        str(second_input),
        str(reuse_input),
        str(output),
    ]
    with patch("sys.argv", args):
        find_quotes.main()

    mock_find_quote_pairs.assert_called_with(
        original_corpus=[orig_input, second_input],
        reuse_corpus=reuse_input,
        output_path=output,
        consolidate=True,
        benchmark=False,
    )


def test_gather_csv_files(tmp_path):
    # mix of files, dirs, nested dirs
    expected_csv_files = set()
    # single file
    toplevel_csv = tmp_path / "single.csv"
    toplevel_csv.touch()
    # directory
    expected_csv_files.add(toplevel_csv)
    csv_dir = tmp_path / "input_files"
    csv_dir.mkdir()
    for name in ["file_a", "file_b", "file_c"]:
        csv_file = csv_dir / f"{name}.csv"
        csv_file.touch()
        expected_csv_files.add(csv_file)
    # non-csv file should be ignored
    (csv_dir / "test.txt").touch()
    # nested directory
    nested_dir = csv_dir / "nested"
    nested_dir.mkdir()
    nested_csv_file = nested_dir / "another.csv"
    nested_csv_file.touch()
    expected_csv_files.add(nested_csv_file)

    gathered_csvs = find_quotes.gather_csv_files([toplevel_csv, csv_dir])
    # order is not guaranteed, but doesn't matter
    assert set(gathered_csvs) == expected_csv_files


def test_gather_csv_files_errors(tmp_path):
    missing = tmp_path / "missing.csv"
    with pytest.raises(ValueError, match="does not exist"):
        find_quotes.gather_csv_files([missing])

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    with pytest.raises(ValueError, match="does not contain any CSV"):
        find_quotes.gather_csv_files([empty_dir])

    with pytest.raises(ValueError, match="no paths specified"):
        find_quotes.gather_csv_files([])
