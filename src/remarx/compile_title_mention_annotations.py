"""
Script for compiling title mention annotations from
manual annotation data (CSVs) downloaded from Recogito.

Example:

    python compile_title_mention_annotations.py annotation_dir output_mentions.csv

"""

import argparse
import csv
import pathlib
import sys
from typing import Generator


def has_title_mention(tags: list[str], title: str) -> str:
    """
    Determines if the annotation tags indicate that the input title is mentioned.
    This returns one of three possible strings: "Yes", "Maybe", "No".
    """
    if title not in tags:
        return "No"
    # If this is a title reference, return "Yes"
    if "Title Reference" in tags:
        return "Yes"
    # If this is a direct quotation, return "Maybe"
    if len(tags) == 1:
        return "Maybe"
    # For other annotations types (e.g., Concept or Allusion) assume there is no mention
    return "No"


def get_title_mentions(
    input_csv: pathlib.Path,
) -> Generator[dict[str, str | int], None, None]:
    """
    Generates title mention structs from Recogito annotation file (CSV). These
    structs have the following fields:

        * uiud: UIUD of the annotation
        * file: file name of the annotation file
        * start_idx: the starting character index of the annotation
        * end_idx: the (Pythonic) ending chracter index of the annotation
        * mentions_kapital: ternary value indicating if Das Kapital is mentioned
        * mentions_manifest: ternary value indicating if the Communist Manifesto is mentioned

    """
    with open(input_csv, newline="") as f:
        print(input_csv.stem)
        reader = csv.DictReader(f)
        for row in reader:
            tags = row["TAGS"].split("|")
            mentions_kapital = has_title_mention(tags, "Kapital")
            mentions_manifest = has_title_mention(
                tags, "Manifest der Kommunistischen Partei"
            )
            # Only yield annotations containing title mentions
            if mentions_kapital != "No" or mentions_manifest != "No":
                # Determine character indices
                start_idx = int(row["ANCHOR"].split("char-offset:", 1)[1])
                end_idx = start_idx + len(row["QUOTE_TRANSCRIPTION"])
                title_mentions = {
                    "uuid": row["UUID"],
                    "file": input_csv.stem,
                    "start_idx": start_idx,
                    "end_idx": end_idx,
                    "mentions_kapital": mentions_kapital,
                    "mentions_manifest": mentions_manifest,
                }
                yield title_mentions


def compile_title_mentions(input_dir: pathlib.Path, output_csv: pathlib.Path):
    """
    Compile Das Kapital and Communist Manifesto title mention annotations and
    save result to a CSV.
    """
    fieldnames = [
        "uuid",
        "file",
        "start_idx",
        "end_idx",
        "mentions_kapital",
        "mentions_manifest",
    ]

    with open(output_csv, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for csv_file in input_dir.rglob("*.csv"):
            for row in get_title_mentions(csv_file):
                writer.writerow(row)


def main():
    """
    Command line access for compiling title mention annotations
    from Recogiton annotation data (CSVs).
    """
    parser = argparse.ArgumentParser(
        description="Compiles title mention annotation data",
    )
    parser.add_argument(
        "input",
        help="Input directory containing annotation data (CSVs)",
        type=pathlib.Path,
    )
    parser.add_argument(
        "output",
        help="Filename where the compiled title mention data should be saved (CSV)",
        type=pathlib.Path,
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.input.is_dir():
        print(f"Error: input directory {args.input} does not exist", file=sys.stderr)
        sys.exit(1)
    if args.output.is_file():
        print(
            f"Error: output file {args.output} exists. Will not overwrite.",
            file=sys.stderr,
        )
        sys.exit(1)

    compile_title_mentions(args.input, args.output)


if __name__ == "__main__":
    main()
