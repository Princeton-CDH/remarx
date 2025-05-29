"""
Parse documents into a sentence corpus file (JSONL).

NOTE: Not being used for title mentions because it's
too slow (need to pass each "sentence" to stanza).
"""

import argparse
import pathlib
import sys
from typing import Generator

import orjsonl
import stanza
from tqdm import tqdm


def get_sentences(
    input_dir: pathlib.Path,
    lang: str,
) -> Generator[dict[str : str | int], None, None]:
    """
    Split each document into sentences. Yield these sentences as
    JSON objects containing the sentence's text along with its
    file and offset information.
    """
    pipeline = stanza.Pipeline(lang=lang, processors="tokenize")

    file_progress = tqdm(input_dir.rglob("*.txt"))

    for text in file_progress:
        file_progress.set_description_str(f"Processing {text.name}")
        for i, sentence in enumerate(pipeline(text.read_text()).sentences):
            entry = {
                "file": text.name,
                "sent_id": f"{text.stem}:{i:04d}",
                "sent_idx": i,
                "char_idx": sentence.tokens[0].start_char,
                "text": sentence.text,
            }
            yield entry


def save_sentences(
    input_dir: pathlib.Path,
    out_filename: pathlib.Path,
    lang: str = "de",
):
    orjsonl.save(out_filename, get_sentences(input_dir, lang))


def main():
    """
    Command-line access for parsing documents into a sentences corpus file (JSONL).
    """
    parser = argparse.ArgumentParser(
        description="Build sentence corpus",
    )
    parser.add_argument(
        "input",
        help="Input directory containing texts to search",
        metavar="input_dir",
        type=pathlib.Path,
    )
    parser.add_argument(
        "output",
        metavar="output_file",
        help="Filename where resulting sentence corpus should be saved (JSONL; compressed or not)",
        type=pathlib.Path,
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.input.is_dir():
        print(f"Error: input directory {args.input} does not exist", file=sys.stderr)
        sys.exit(1)
    if args.output.is_file():
        print(
            f"Error: output file {args.output} exsts. Will not overwrite.",
            file=sys.stderr,
        )
        sys.exit(1)

    save_sentences(
        args.input,
        args.output,
    )


if __name__ == "__main__":
    main()
