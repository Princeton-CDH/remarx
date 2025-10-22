"""
Preliminary script and method to create sentence corpora from input
files in supported formats.

NOTE: Currently this script can only take single input file

Example Usage:

    `create.py input_text.txt out.csv`

"""

import argparse
import csv
import logging
import pathlib
import sys

from remarx.sentence.corpus.base_input import FileInput
from remarx.utils import configure_logging


def create_corpus(
    input_file: pathlib.Path,
    output_csv: pathlib.Path,
    filename_override: str | None = None,
) -> None:
    """
    Create and save a sentence corpus from the provided input file to the
    provided output path `output_csv`.

    NOTE: An error will be raised if the input file is not a type supported by
    `FileInput`.
    """
    if not input_file.is_file():
        raise ValueError(f"Input file {input_file} does not exist")

    text_input = FileInput.create(input_file, filename_override=filename_override)
    field_names = text_input.field_names

    with output_csv.open(mode="w", newline="") as csvfile:
        csvwriter = csv.DictWriter(csvfile, field_names, extrasaction="ignore")
        csvwriter.writeheader()
        csvwriter.writerows(text_input.get_sentences())


def main() -> None:
    """
    Command-line access to sentence corpus creation for supported input formats
    """
    parser = argparse.ArgumentParser(
        description="Generate a sentence corpus from a supported input file"
    )
    parser.add_argument(
        "input_file",
        type=pathlib.Path,
        help="Path to input file",
    )
    parser.add_argument(
        "output_csv", type=pathlib.Path, help="Path to output sentence corpus (CSV)"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output (debug logging)",
        default=False,
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO

    configure_logging(sys.stdout, log_level=log_level)
    create_corpus(
        args.input_file,
        args.output_csv,
    )


if __name__ == "__main__":
    main()
