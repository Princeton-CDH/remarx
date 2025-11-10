"""
Command-line script to identify sentence-level quotation pairs between corpora.

NOTE: Currently this script always writes a file named `quote_pairs.csv` in the
provided output directory.

Example Usage:

    `remarx-find-quotes original_sentences.csv reuse_sentences.csv out_dir`

"""

import argparse
import logging
import pathlib
import sys
from timeit import default_timer as time

from remarx.quotation.pairs import find_quote_pairs
from remarx.utils import configure_logging

DEFAULT_OUTPUT_FILENAME = "quote_pairs.csv"
logger = logging.getLogger(__name__)


def run_find_quotes(
    original_corpus: pathlib.Path,
    reuse_corpus: pathlib.Path,
    output_dir: pathlib.Path,
    *,
    benchmark: bool = False,
) -> pathlib.Path:
    """Run quotation detection and write results into the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / DEFAULT_OUTPUT_FILENAME

    logger.info("Running quotation detection")
    logger.info("Original corpus: %s", original_corpus)
    logger.info("Reuse corpus: %s", reuse_corpus)
    logger.info("Output file: %s", output_path)

    start = time()
    metrics = find_quote_pairs(
        original_corpus=original_corpus,
        reuse_corpus=reuse_corpus,
        out_csv=output_path,
    )
    elapsed = time() - start

    if benchmark:
        minutes = elapsed / 60
        logger.info(
            "Benchmark summary: wall=%.2fs (%.2fm); embeddings=%.2fs; index=%.2fs; query=%.2fs",
            elapsed,
            minutes,
            metrics.embedding_seconds,
            metrics.index_seconds,
            metrics.query_seconds,
        )

    return output_path


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the quotation script."""
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
        "output_dir",
        type=pathlib.Path,
        help="Directory where the quote pairs CSV will be written",
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
    return parser


def main() -> None:
    """Command-line access to quotation detection for sentence corpora."""
    parser = build_parser()
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    configure_logging(sys.stdout, log_level=log_level)

    run_find_quotes(
        original_corpus=args.original_corpus,
        reuse_corpus=args.reuse_corpus,
        output_dir=args.output_dir,
        benchmark=args.benchmark,
    )


if __name__ == "__main__":
    main()
