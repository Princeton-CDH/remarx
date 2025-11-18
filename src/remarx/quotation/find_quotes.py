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

    # check input files (possibly multiples in future...)
    for input_file in [args.original_corpus, args.reuse_corpus]:
        if not input_file.is_file():
            print(f"Error: input file {input_file} does not exist", file=sys.stderr)
            sys.exit(1)
    # check output path directory exists
    if not args.output_path.parent.is_dir():
        print(
            f"Error: output directory {args.output_path.parent} does not exist",
            file=sys.stderr,
        )
        sys.exit(1)

    find_quote_pairs(
        # for now, pass single file as a list; in future, support multifile
        original_corpus=[args.original_corpus],
        reuse_corpus=args.reuse_corpus,
        out_csv=args.output_path,
        consolidate=args.consolidate,
        benchmark=args.benchmark,
    )


if __name__ == "__main__":
    main()
