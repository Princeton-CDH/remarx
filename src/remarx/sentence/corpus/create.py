#!/usr/bin/env python
"""
Preliminary script and method to create sentence corpora from input
files in supported formats.
"""

import argparse
import pathlib

from remarx.sentence.corpus.input import TextInput
from remarx.sentence.corpus.tei_input import TEIinput


def main() -> None:
    """
    command-line access to sentence corpus creation for supported input formats
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

    text_input = input_class(args.input_file)
    for i, sent in enumerate(text_input.get_sentences()):
        print(f"{i}: length = {len(sent)}")


if __name__ == "__main__":
    main()
