#!/usr/bin/env python
"""
Preliminary script and method to create sentence corpora from input
files in supported formats.
"""

import argparse
import csv
import pathlib

from remarx.sentence.corpus.tei_input import TEIinput
from remarx.sentence.corpus.text_input import TextInput


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
        "format", choices=["text", "tei"], help="Input file format", default="text"
    )

    args = parser.parse_args()

    input_class = TextInput
    if args.format == "tei":
        input_class = TEIinput

    # initialize appropriate text input class
    text_input = input_class(args.input_file)
    # Determine output csv path based on input file
    output_csv = (args.input_file).with_suffix(".csv")

    with output_csv.open(mode="w", newline="") as csvfile:
        # field names may vary depending on input format
        csvwriter = csv.DictWriter(csvfile, fieldnames=text_input.field_names)
        csvwriter.writeheader()
        csvwriter.writerows(text_input.get_sentences())

    print(f"\nSaved sentence corpus as {output_csv}")


if __name__ == "__main__":
    main()
