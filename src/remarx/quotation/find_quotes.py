"""
Command-line script to identify sentence-level quotation pairs between corpora.

Example Usage:

    `remarx-find-quotes original_sentences.csv reuse_sentences.csv output.csv`
"""

import argparse
import logging
import pathlib
import sys

from natsort import natsorted

from remarx.quotation.pairs import find_quote_pairs
from remarx.utils import configure_logging

logger = logging.getLogger(__name__)
DEFAULT_ORIGINAL_CORPUS_DIR = pathlib.Path.home() / "remarx-data/corpora/original"


def _list_original_corpora(original_inputs: list[pathlib.Path]) -> list[pathlib.Path]:
    """Return all original corpus CSV files, expanding a directory when needed."""

    resolved_inputs: list[pathlib.Path] = []
    for input_path in original_inputs:
        if not input_path.exists():
            raise ValueError(f"Error: input file {input_path} does not exist")

        if input_path.is_dir():
            # Allow users to point at a directory of corpora
            csv_files = natsorted(
                file_path
                for file_path in input_path.iterdir()
                if file_path.is_file() and file_path.suffix.lower() == ".csv"
            )
            if not csv_files:
                raise ValueError(
                    f"Error: directory {input_path} does not contain any CSV files"
                )
            resolved_inputs.extend(csv_files)
        else:
            resolved_inputs.append(input_path)

    if not resolved_inputs:
        raise ValueError("Error: no original corpora were provided")

    return resolved_inputs


def _error_exit(message: str) -> None:
    """Log error, write to stderr, and exit."""
    logger.error(message)
    sys.stderr.write(f"{message}\n")
    raise SystemExit(1)


def run_find_quotes(
    original_corpora: list[pathlib.Path],
    reuse_corpus: pathlib.Path,
    output_path: pathlib.Path,
    *,
    consolidate: bool = True,
    benchmark: bool = False,
) -> pathlib.Path:
    """Run quotation detection and write results into the output directory."""
    logger.info("Running quotation detection")
    if len(original_corpora) == 1:
        logger.info("Original corpus: %s", original_corpora[0])
    else:
        # Provide full context when multiple sources are supplied for easier debugging.
        logger.info(
            "Original corpora (%s files): %s",
            len(original_corpora),
            ", ".join(str(path) for path in original_corpora),
        )
    logger.info("Reuse corpus: %s", reuse_corpus)
    logger.info("Output file: %s", output_path)

    find_quote_pairs(
        original_corpus=original_corpora,
        reuse_corpus=reuse_corpus,
        out_csv=output_path,
        consolidate=consolidate,
        benchmark=benchmark,
    )

    return output_path


def main() -> None:
    """Command-line access to quotation detection for sentence corpora."""
    parser = argparse.ArgumentParser(
        description="Find quotation pairs between sentence corpora",
        epilog=(
            "Usage: remarx-find-quotes [ORIGINAL | ORIGINAL_DIR] REUSE OUTPUT. "
            "Provide one original corpus CSV file or directory before the reuse corpus. "
            "If omitted, the default path will be used."
        ),
    )
    parser.add_argument(
        "paths",
        nargs="+",
        metavar="PATH",
        help=(
            "Paths to corpora. Specify zero or one original corpus CSV file or "
            "directory followed by the reuse corpus CSV and output file."
        ),
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

    if len(args.paths) < 2:
        parser.error("reuse corpus and output path are required")

    if len(args.paths) > 3:
        _error_exit(
            "Error: specify at most one original corpus (file or directory) followed by reuse corpus and output path"
        )

    positional_paths = [pathlib.Path(p) for p in args.paths]
    if len(positional_paths) == 2:
        # When no original path is provided, fall back to the default directory
        reuse_corpus, output_path = positional_paths
        logger.info(
            "No original corpora specified; defaulting to %s",
            DEFAULT_ORIGINAL_CORPUS_DIR,
        )
        original_inputs = [DEFAULT_ORIGINAL_CORPUS_DIR]
    else:
        original_inputs = [positional_paths[0]]
        reuse_corpus = positional_paths[1]
        output_path = positional_paths[2]

    try:
        original_corpora = _list_original_corpora(original_inputs)
    except ValueError as err:
        _error_exit(str(err))

    if not reuse_corpus.exists():
        _error_exit(f"Error: input file {reuse_corpus} does not exist")

    # Validate output directory exists
    output_dir = output_path.parent
    if not output_dir.exists():
        _error_exit(f"Error: output directory {output_dir} does not exist")

    run_find_quotes(
        original_corpora=original_corpora,
        reuse_corpus=reuse_corpus,
        output_path=output_path,
        consolidate=args.consolidate,
        benchmark=args.benchmark,
    )


if __name__ == "__main__":
    main()
