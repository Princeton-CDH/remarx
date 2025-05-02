"""
This script identifies candidate sentences within a collection of texts
that contain phrases of interest (e.g., title or concept references)
ignoring inflection and capitalization.

This script takes as input:

* a directory containing the text files to search,
* a filepath to where the results will be saved as a CSV,
* and one or more search phrases

Examples: ::

    python candidate_mentions.py texts/ results.csv --phrase "Kapital"

    python candidate_mentions.py texts/ results.csv --phrase "Kapital" --phrase "Das Kapital"

    python candidate_mentions.py texts/ results.csv --phrase "Kapital" "Das Kapital"

"""

import argparse
import csv
import pathlib
import sys
from collections.abc import Iterable

from stanza import DownloadMethod, Pipeline
from stanza.models.common.doc import Document, Sentence
from tqdm import tqdm

#: The language for the default stanza pipeline
LANG = "de"
#: The processors for the default stanza pipeline
PROCS = "tokenize,mwt,pos,lemma"


def lemmatize_sentence(
    sentence: Sentence, drop_punct: bool = True, lowercase: bool = True
) -> str:
    """
    Converts a stanza sentence into its lemmatized form with each word
    separated by a space. By default, punctuation (as determined by part-of-speech)
    is removed and resulting string is lowercased.
    """
    result = " ".join(
        w.lemma for w in sentence.words if w.pos != "PUNCT" or not drop_punct
    )
    return result.lower() if lowercase else result


def lemmatize_text(
    text: str | Document,
    pipeline: None | Pipeline = None,
    drop_punct: bool = True,
    lowercase: bool = True,
) -> str:
    """
    Lemmatizes a text using `lemmatize_sentence` with sentences separated
    by a single space.
    """
    # Intialize pipeline if one not given
    if pipeline is None:
        pipeline = Pipeline(
            lang=LANG, processors=PROCS, download_method=DownloadMethod.REUSE_RESOURCES
        )

    # Construct stanza document if needed
    doc = pipeline(text) if isinstance(text, str) else text

    return " ".join(
        [
            lemmatize_sentence(s, drop_punct=drop_punct, lowercase=lowercase)
            for s in doc.sentences
        ]
    )


def check_sentence_for_phrases(
    sentence: Sentence,
    lemmatized_phrases: Iterable[str],
    ignore_punct: bool = True,
    lowercase: bool = True,
) -> list[str]:
    """
    Checks if a sentence contains any of the provided *lemmatized* phrases
    ignoring inflection and capitalization. It returns a list of the matched
    phrases. By default, punctuation (as determined by part-of-speech) is
    ignored and the sentence is lowercased before performing the search.

    NOTE: Search phrases must  processed (e.g., lemmatized, lowercased) in a
    similar way as the sentence to produce meaningful results.
    """
    # Lemmatize & lowercase sentence
    lem_sent = lemmatize_sentence(
        sentence, drop_punct=ignore_punct, lowercase=lowercase
    )
    # Check if any of the phrases occur within the sentence
    matches = []
    for lem_phrase in lemmatized_phrases:
        if f" {lem_phrase} " in f" {lem_sent} ":
            matches.append(lem_phrase)
    return matches


def save_candidate_sentences(
    input_texts: Iterable[pathlib.Path],
    search_phrases: list[str],
    output_csv: pathlib.Path,
    ignore_punct: bool = True,
    case_sensitive: bool = False,
    delimiter: str = " | ",
) -> None:
    """
    Finds sentences within the input texts that contain the search phrases and
    saves the results as a CSV file with the following fields:

    * file: name of text file
    * sent_idx: sentence-level index within text file
    * char_idx: character-level index within text file
    * sentence: sentence text
    * phrases: list of matching phrases
    * lem_phrases: list of matching lemmatized phrases (same order as phrases)

    By default, punctuation (as determined by part-of-speech) is ignored and the
    search is case insensitive.
    """
    # Initialize stanza pipeline
    pipeline = Pipeline(
        lang=LANG, processors=PROCS, download_method=DownloadMethod.REUSE_RESOURCES
    )

    # Lemmatize search phrases, save as map from lemma to phrase
    lem_phrases = {}
    for phrase in search_phrases:
        lem_phrase = lemmatize_text(
            phrase,
            pipeline=pipeline,
            drop_punct=ignore_punct,
            lowercase=not case_sensitive,
        )
        lem_phrases[lem_phrase] = phrase

    fieldnames = ["file", "sent_idx", "char_idx", "sentence", "phrases", "lem_phrases"]
    with open(output_csv, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        file_progress = tqdm(input_texts)
        for text_file in file_progress:
            file_progress.set_description(f"Processing {text_file.stem}")
            doc = pipeline(text_file.read_text())
            for i, sentence in enumerate(doc.sentences):
                # Determine which phrases the sentence contains
                lem_matches = check_sentence_for_phrases(
                    sentence,
                    lem_phrases.keys(),
                    ignore_punct=ignore_punct,
                    lowercase=not case_sensitive,
                )
                # Construct row if there are any matches
                if lem_matches:
                    phrase_matches = [lem_phrases[lm] for lm in lem_matches]
                    entry = {
                        "file": text_file.stem,
                        "sent_idx": i,
                        "char_idx": sentence.tokens[0].start_char,
                        "sentence": sentence.text,
                        "phrases": delimiter.join(phrase_matches),
                        "lem_phrases": delimiter.join(lem_matches),
                    }
                    writer.writerow(entry)


def main():
    """
    Command-line access for finding and saving sentences containing search phrases.
    This search ignores inflection and capitalization.
    """
    parser = argparse.ArgumentParser(
        description="Find candidate mentions",
    )
    parser.add_argument(
        "input",
        help="Input directory containing texts to search",
        type=pathlib.Path,
    )
    parser.add_argument(
        "output",
        help="Filename where resulting matches should be saved (CSV)",
        type=pathlib.Path,
    )
    parser.add_argument(
        "--phrase",
        action="extend",
        nargs="+",
        type=str,
        required=True,
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

    save_candidate_sentences(
        args.input.rglob("*.txt"),
        list(args.phrase),
        args.output,
    )


if __name__ == "__main__":
    main()
