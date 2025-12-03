"""
Command-line script to identify sentence-level quotation pairs between corpora.

Example Usage:

    # Single original corpus
    `remarx-find-quotes -o original_sentences.csv reuse_sentences.csv output.csv`

    # Multiple original corpora (use separate -o flags)
    `remarx-find-quotes -o original1.csv -o original2.csv reuse_sentences.csv output.csv`

    # Directory of original corpora
    `remarx-find-quotes -o /path/to/originals reuse_sentences.csv output.csv`

    # Use default original directory (omit -o flag)
    `remarx-find-quotes reuse_sentences.csv output.csv`
"""

import argparse
import logging
import pathlib
import sys

from remarx.quotation.pairs import find_quote_pairs
from remarx.utils import CorpusPath, configure_logging

logger = logging.getLogger(__name__)


def gather_csv_files(paths: list[pathlib.Path]) -> list[pathlib.Path]:
    """
    Takes a list of CSV files or directories and return list of CSV files,
    including all`.csv` files included in any of the specified directories.
    Raises ValueError if a specified path is missing, a directory has no CSV files,
    or no input paths are specified.
    """
    if not paths:
        raise ValueError("Error: no paths specified")

    resolved_inputs: list[pathlib.Path] = []
    for input_path in paths:
        if not input_path.exists():
            raise ValueError(f"Error: input file {input_path} does not exist")

        if input_path.is_dir():
            # If a directory is specified, find all .csv files anywhere under it
            csv_files = list(input_path.glob("**/*.csv"))
            if not csv_files:
                raise ValueError(
                    f"Error: directory {input_path} does not contain any CSV files"
                )
            resolved_inputs.extend(csv_files)
        else:
            resolved_inputs.append(input_path)

    return resolved_inputs


def _error_exit(message: str) -> None:
    """Log error, write message to stderr, and exit."""
    logger.error(message)
    sys.stderr.write(f"{message}\n")
    raise SystemExit(1)


def main() -> None:
    """
    Detect quotations from reuse sentence corpus across multiple original
    sentence corpora.
    """
    # init default corpus path for display in help text
    corpus_paths = CorpusPath()

    parser = argparse.ArgumentParser(
        description="Find quotations between original and reuse sentence corpora."
    )
    parser.add_argument(
        "-o",
        "--original",
        action="append",
        type=pathlib.Path,
        metavar="PATH",
        default=[],
        help=(
            "Original corpus CSV file or directory. Repeat -o/--original for each file or directory "
            f"(e.g., -o file1.csv -o file2.csv). If omitted, the default directory is used ({corpus_paths.original})."
        ),
    )
    parser.add_argument(
        "reuse_corpus",
        type=pathlib.Path,
        help="Path to the reuse sentence corpus CSV",
    )
    parser.add_argument(
        "output_path",
        type=pathlib.Path,
        help="Path where the detected quotes CSV will be written",
    )
    parser.add_argument(
        "--consolidate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Consolidate quotes that are sequential in both corpora (on by default).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Verbose output (debug logging)",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        default=False,
        help="Log benchmark timing information",
    )
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    configure_logging(sys.stdout, log_level=log_level)

    original_inputs = args.original
    reuse_corpus = args.reuse_corpus
    output_path = args.output_path

    if not original_inputs:
        print(f"No original corpora specified; defaulting to {corpus_paths.original}")
        original_inputs = [corpus_paths.original]

    # simple checks first
    if not reuse_corpus.exists():
        _error_exit(f"Error: input file {reuse_corpus} does not exist")

    # Validate output directory exists
    output_dir = output_path.parent
    if not output_dir.exists():
        _error_exit(f"Error: output directory {output_dir} does not exist")

    try:
        original_corpora = gather_csv_files(original_inputs)
    except ValueError as err:
        _error_exit(str(err))

    # report on collected original corpora to be used
    original_file_count = len(original_corpora)
    if original_file_count == 1:
        print(f"Original corpus: {original_corpora[0]}")
    else:
        # Provide more details when multiple original files are used
        file_list = ", ".join(str(path) for path in original_corpora)
        print(f"Original corpora ({original_file_count} files): {file_list}")

    find_quote_pairs(
        original_corpus=original_corpora,
        reuse_corpus=reuse_corpus,
        output_path=output_path,
        consolidate=args.consolidate,
        benchmark=args.benchmark,
    )


if __name__ == "__main__":
    main()
