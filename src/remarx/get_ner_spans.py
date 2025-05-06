"""
Script for gathering the NER spans of a collection of sentences (CSV) using flair.
The input sentence file must have the following fields:
file, sent_idx, char_idx, sentence.

Examples:

    python get_ner_spans.py candidate_sentences.csv candidate_ner.csv

"""

import argparse
import csv
import pathlib
import sys
from typing import Generator

from flair.data import Sentence
from flair.nn import Classifier
from tqdm import tqdm


def get_ner_spans(
    text: str, tagger: None | Classifier = None
) -> Generator[dict[str, str | int], None, None]:
    """
    Yields an NER span struct for each NER span identified by flair.

    Optionally, the flair NER tagger (Classifier) may be provided.
    If none is provided, "de-ner-large" is used.
    """
    # Construct flair sentence
    sentence = Sentence(text, language_code="de")

    # Initialize tagger if needed
    if tagger is None:
        tagger = Classifier.load("de-ner-large")

    # Run NER tagger over sentence
    tagger.predict(sentence)

    # Construct span object all spans with NER tags
    for span in sentence.get_spans(label_type="ner"):
        span_struct = {
            "span_text": span.text,
            "ner_tag": span.tag,
            "start_idx": span.start_position,
            "end_idx": span.end_position,
        }
        yield span_struct


def save_ner_spans(
    input_csv: pathlib.Path,
    output_csv: pathlib.Path,
):
    """
    For each sentence (row) of the input CSV file, use flair to identify its NER spans.
    Results are written to an output CSV file with each row corresponding to
    a single NER span with the following fields:

        * file: the file name of the original text
        * sent_idx: the sentence-level index of the sentence containing this NER span
        * span_text: the span's text
        * ner_tag: the span's NER tag
        * start_idx: the starting character-level index of the span
        * end_idx: the (Pythonic) ending character-level index of the spanb

    """
    tagger = Classifier.load("de-ner-large")

    fieldnames = ["file", "sent_idx", "span_text", "ner_tag", "start_idx", "end_idx"]
    with open(output_csv, mode="w", newline="") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()
        with open(input_csv, encoding="utf-8-sig", newline="") as in_f:
            reader = csv.DictReader(in_f)
            for sent in tqdm(reader, desc="Processing sentences"):
                entry_pfx = {key: sent[key] for key in ["file", "sent_idx"]}
                for ner_span in get_ner_spans(sent["sentence"], tagger=tagger):
                    writer.writerow(entry_pfx | ner_span)


def main():
    """
    Command line access for gathering NER spans for a collection of sentences using flair
    """
    parser = argparse.ArgumentParser(
        description="Get NER spans for a collection of sentences using flair",
    )

    parser.add_argument(
        "input",
        help="Input CSV file containing sentences to process",
        type=pathlib.Path,
    )
    parser.add_argument(
        "output",
        help="Filename where the NER spans data should be saved (CSV)",
        type=pathlib.Path,
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.input.is_file():
        print(f"Error: input CSV {args.input} does not exist", file=sys.stderr)
        sys.exit(1)
    if args.output.is_file():
        print(
            f"Error: output CSV {args.output} exists. Will not overwrite",
            file=sys.stderr,
        )
        sys.exit(1)

    save_ner_spans(
        args.input,
        args.output,
    )


if __name__ == "__main__":
    main()
