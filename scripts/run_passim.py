#!/usr/bin/env python3
"""
Run Passim on a combined JSONL corpus to detect text reuse.

Usage:
    python scripts/run_passim.py input.jsonl output_dir

Arguments:
    input_file: Path to the input JSONL file (e.g., combined_passim_input.jsonl)
    output_dir: Directory where Passim results will be saved

Usage Example:
    python scripts/run_passim.py texts_json_for_passim/combined_passim_input.jsonl passim_output
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_passim(
    input_file: Path,
    output_dir: Path,
    min_df: int = 2,
    min_match: int = 5,
    ngram_size: int = 15,
    min_align: int = 50,
    driver_memory: str = "16g",
    executor_memory: str = "16g",
) -> None:
    """Run Passim with specified parameters."""

    # Remove output directory if it exists
    if output_dir.exists():
        print(f"Removing existing output directory: {output_dir}")
        shutil.rmtree(output_dir)

    # Passim parameters
    passim_args = [
        "--pairwise",
        "--minDF",
        str(min_df),
        "-m",
        str(min_match),
        "-n",
        str(ngram_size),
        "-a",
        str(min_align),
        str(input_file),  # <input_path>
        str(output_dir),  # <output_path>
    ]

    cmd = ["passim"] + passim_args

    print(f"Command: {' '.join(cmd)}")
    print("\n⏱️ Starting Passim... (this may take a few minutes)")

    # Set environment variables for Spark
    env = os.environ.copy()
    env.update(
        {
            "SPARK_LOCAL_IP": "127.0.0.1",
            "PYSPARK_DRIVER_PYTHON": "python3",
            "PYSPARK_PYTHON": "python3",
            "SPARK_DRIVER_MEMORY": driver_memory,
            "SPARK_EXECUTOR_MEMORY": executor_memory,
        }
    )

    try:
        result = subprocess.run(
            cmd, cwd=Path.cwd(), env=env, capture_output=True, text=True
        )

        if result.returncode == 0:
            print("Passim completed successfully!")
            print(f"Output is saved in: {output_dir.resolve()}")
        else:
            print("Passim failed.")
            print("Error message:", result.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error running Passim: {e}")
        sys.exit(1)


def main():
    """Main function."""
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--min-df", type=int, default=2)
    parser.add_argument("--min-match", type=int, default=5)
    parser.add_argument("--ngram-size", type=int, default=15)
    parser.add_argument("--min-align", type=int, default=50)
    parser.add_argument("--driver-memory", type=str, default="16g")
    parser.add_argument("--executor-memory", type=str, default="16g")

    args = parser.parse_args()

    # Validate input file
    if not args.input_file.exists():
        print(f"Error: Input file does not exist: {args.input_file}")
        sys.exit(1)

    if not args.input_file.suffix == ".jsonl":
        print(f"Error: Input file must be a .jsonl file: {args.input_file}")
        sys.exit(1)

    print("Running Passim on JSONL corpus:")
    print(f"Input file: {args.input_file.resolve()}")
    print(f"Output directory: {args.output_dir.resolve()}")

    # Run Passim
    run_passim(
        input_file=args.input_file,
        output_dir=args.output_dir,
        min_df=args.min_df,
        min_match=args.min_match,
        ngram_size=args.ngram_size,
        min_align=args.min_align,
        driver_memory=args.driver_memory,
        executor_memory=args.executor_memory,
    )


if __name__ == "__main__":
    main()
