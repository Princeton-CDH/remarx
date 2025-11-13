import logging
import sys
from unittest.mock import patch

import pytest

from remarx.quotation import find_quotes


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
    args = ["remarx-find-quotes", str(orig_input), str(reuse_input), str(output)]
    with patch("sys.argv", args):
        find_quotes.main()

    mock_configure_logging.assert_called_with(sys.stdout, log_level=logging.INFO)
    # consolidate and benchmark are default options
    mock_find_quote_pairs.assert_called_with(
        original_corpus=orig_input,
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
        original_corpus=orig_input,
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
    args = ["remarx-find-quotes", str(orig_input), str(reuse_input), str(output)]
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
