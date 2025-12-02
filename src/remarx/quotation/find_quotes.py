"""
Command-line script to identify sentence-level quotation pairs between corpora.

Example Usage:

    `remarx-find-quotes original_sentences.csv reuse_sentences.csv output.csv`
"""

import argparse
import logging
import pathlib
import sys

from remarx.quotation.pairs import find_quote_pairs
from remarx.utils import configure_logging

logger = logging.getLogger(__name__)


def _error_exit(message: str) -> None:
    """Log error, write to stderr, and exit."""
    logger.error(message)
    sys.stderr.write(f"{message}\n")
    raise SystemExit(1)


def run_find_quotes(
    original_corpus: pathlib.Path,
    reuse_corpus: pathlib.Path,
    output_path: pathlib.Path,
    *,
    consolidate: bool = True,
    benchmark: bool = False,
) -> pathlib.Path:
    """Run quotation detection and write results into the output directory."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Running quotation detection")
    logger.info("Original corpus: %s", original_corpus)
    logger.info("Reuse corpus: %s", reuse_corpus)
    logger.info("Output file: %s", output_path)

    find_quote_pairs(
        # for now, pass single file as a list; in future, support multifile
        original_corpus=[original_corpus],
        reuse_corpus=reuse_corpus,
        out_csv=output_path,
        consolidate=consolidate,
        benchmark=benchmark,
    )

    return output_path


def main() -> None:
    """Command-line access to quotation detection for sentence corpora."""
    parser = argparse.ArgumentParser(
        description="Find quotation pairs between two sentence corpora"
    )
    parser.add_argument(
        "original_corpus",
        type=pathlib.Path,
        help="Path to the original sentence corpus CSV",
    )
    parser.add_argument(
        "reuse_corpus",
        type=pathlib.Path,
        help="Path to the reuse sentence corpus CSV",
    )
    parser.add_argument(
        "output_path",
        type=pathlib.Path,
        help="Path where the quote pairs CSV will be written",
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

    # Validate input paths exist
    if not args.original_corpus.exists():
        _error_exit(f"Error: input file {args.original_corpus} does not exist")

    if not args.reuse_corpus.exists():
        _error_exit(f"Error: input file {args.reuse_corpus} does not exist")

    # Validate output directory exists
    output_dir = args.output_path.parent
    if not output_dir.exists():
        _error_exit(f"Error: output directory {output_dir} does not exist")

    run_find_quotes(
        original_corpus=args.original_corpus,
        reuse_corpus=args.reuse_corpus,
        output_path=args.output_path,
        consolidate=args.consolidate,
        benchmark=args.benchmark,
    )


if __name__ == "__main__":
    main()
