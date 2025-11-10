"""
Command-line script to identify sentence-level quotation pairs between corpora.

Example Usage:

    `remarx-find-quotes original_sentences.csv reuse_sentences.csv output.csv`
"""

import argparse
import logging
import pathlib
import sys
from timeit import default_timer as time
from typing import NoReturn

from remarx.utils import configure_logging

try:
    from remarx.quotation.pairs import find_quote_pairs
except (
    ModuleNotFoundError
) as exc:  # pragma: no cover - exercised when optional deps missing
    _pairs_import_error = exc

    def find_quote_pairs(
        original_corpus: pathlib.Path,
        reuse_corpus: pathlib.Path,
        out_csv: pathlib.Path,
        score_cutoff: float = 0.225,
        show_progress_bar: bool = False,
    ) -> NoReturn:
        """Fallback when quotation dependencies are missing."""
        msg = (
            "remarx.quotation.pairs dependencies are not available. "
            "Install the project with its optional requirements."
        )
        raise ModuleNotFoundError(msg) from _pairs_import_error


logger = logging.getLogger(__name__)


def run_find_quotes(
    original_corpus: pathlib.Path,
    reuse_corpus: pathlib.Path,
    output_path: pathlib.Path,
    *,
    benchmark: bool = False,
) -> pathlib.Path:
    """Run quotation detection and write results into the output directory."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

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
        "output_path",
        type=pathlib.Path,
        help="Path where the quote pairs CSV will be written",
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
        output_path=args.output_path,
        benchmark=args.benchmark,
    )


if __name__ == "__main__":
    main()
