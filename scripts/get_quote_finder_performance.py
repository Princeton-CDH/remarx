"""
Performance benchmark script for quote pair detection.
"""

import logging
import pathlib
from timeit import default_timer as time

from remarx.quotation.pairs import find_quote_pairs

# Configure logging to show INFO level messages
logging.basicConfig(level=logging.INFO, format="%(levelname)s::%(message)s")

logger = logging.getLogger(__name__)


def run_benchmark() -> None:
    """Run performance benchmark on test datasets."""

    # Define input files
    original_corpus = pathlib.Path("test_input/Das_Kapital_MEGA_A2_B005-00_ETX.csv")
    reuse_corpus = pathlib.Path("test_input/1896-97a XML Output-835pages.csv")
    output_file = pathlib.Path("quote_pairs.csv")

    # Verify input files exist
    if not original_corpus.exists():
        logger.error(f"Original corpus not found: {original_corpus}")
        return

    if not reuse_corpus.exists():
        logger.error(f"Reuse corpus not found: {reuse_corpus}")
        return

    logger.info("Starting Performance Benchmark")
    logger.info(f"Original corpus: {original_corpus}")
    logger.info(f"Reuse corpus: {reuse_corpus}")
    logger.info(f"Output file: {output_file}")

    # Run quote pair detection with timing
    start_time = time()

    find_quote_pairs(
        original_corpus=original_corpus,
        reuse_corpus=reuse_corpus,
        out_csv=output_file,
        score_cutoff=0.225,
        show_progress_bar=False,
    )

    total_time = time() - start_time

    logger.info(
        f"Total benchmark time: {total_time:.1f} seconds ({total_time / 60:.2f} minutes)"
    )
    logger.info(f"Quote pairs saved to: {output_file}")


if __name__ == "__main__":
    run_benchmark()
