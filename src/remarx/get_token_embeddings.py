"""
Script to build embeddings of a specific term for each sentence in a
sentence-level corpus file (JSONL). The resulting embeddings are saves as a .npy
binary file. By default the  MT5-XL model (google/mt5-xl) is used, but this can
be changed to another pretrained model. Since term instances and sentences are
unlikely to have a one-to-one correspondence, a metadata file (CSV) identifying
each embedding is also generated.

See https://huggingface.co/docs/transformers/main/en/model_doc/mt5 for more on MT5.

Example:

    python get_token_embeddings sents.jsonl Kapital output_dir output_stem

"""

import argparse
import csv
import pathlib
import re
import sys
from typing import cast

import numpy as np
import numpy.typing as npt
import orjsonl
from tqdm import tqdm
from transformers import (
    FeatureExtractionPipeline,
    PreTrainedTokenizer,
    T5Tokenizer,
    pipeline,
)


def normalize_text(text: str) -> str:
    """
    Normalizes text so that it will align with its tokenized version.
    """
    # Remove any outer whitespace, consolidate multiple whitespace characters, and add a leading space
     return " " + " ".join(text.strip().split())


def get_term_spans(text: str, term: str) -> list[tuple[int, int]]:
    """
    Finds all instances of the provided term within the input text.
    Returns a list of span start and end indices for each identified instance.
    """
    pattern = r"(\b|^)" + term + r"(\b|$)"
    term_indices = []
    for match in re.finditer(pattern, text):
        term_indices.append(match.span())
    return term_indices


def get_subtoken_alignment(
    tokenizer: PreTrainedTokenizer,
    sentence: str,
    spans: list[tuple[int, int]],
) -> list[list[int]]:
    """
    For a sentence, determine the correspondence between each given span and
    the given T5 tokenizer's subtokens. In cases where span and subtoken boundaries
    are misaligned, all subtokens that contain chracters within the span are included.
    Returns the span's subtoken positions as a list of lists of integers.
    """
    # Check that tokenized text aligns with original
    subtokens = tokenizer.tokenize(sentence)
    if len("".join(subtokens)) != len(sentence):
        raise ValueError(
            "Error: Tokenized sentence does not align with input. "
            "Trying applying normalize_text first."
        )

    # Initialize span to subtoken correspondence
    span2subtokens: list[list[int]] = [[] for x in spans]
    # Calculate subtoken start indices
    subtoken_starts: list[int] = []
    for i, subtoken in enumerate(subtokens):
        if i == 0:
            start = 0
        else:
            start = subtoken_starts[i - 1] + len(subtoken)
        subtoken_starts.append(start)

    i_subtoken = 0
    j_token = 0
    while i_subtoken < len(subtokens) and j_token < len(spans):
        sub_start = subtoken_starts[i_subtoken]
        sub_end = (
            subtoken_starts[i_subtoken + 1]
            if i_subtoken < len(subtokens) - 1
            else len(subtokens)
        )

        token_start, token_end = spans[j_token]

        # Subtoken overlaps token span
        if sub_start < token_end and token_start < token_end:
            # Map subtoken to token
            span2subtokens[j_token].append(i_subtoken)

        # Increment subtoken if it doesn't continue past the current token
        if sub_end <= token_end:
            i_subtoken += 1

        # Increment token if it doesn't continue past the current subtoken
        if token_end < sub_end:
            j_token += 1

    return span2subtokens


def extract_span_embeddings(
    extractor: FeatureExtractionPipeline,
    sentence: str,
    span_to_subtokens: list[list[int]],
) -> npt.NDArray:
    """
    For a sentence, extract the span embeddings using a given hugging face feature
    extraction pipeline. The spans of interest are represented by a list of their
    subtokens which were determined using `get_subtoken_alignment`. A span's
    embedding is the average of its subtokens' embeddings.
    Returns a numpy array of the resulting span embeddings.
    """
    subtoken_embeddings = extractor(sentence)

    # Build the specific token embeddings
    token_embeddings = []
    for subtoken_positions in span_to_subtokens:
        n_subtokens = len(subtoken_positions)

        # Token embedding is average of its subtoken embeddings
        token_sum = None
        for pos in subtoken_positions:
            if token_sum is None:
                token_sum = subtoken_embeddings[pos]
            else:
                token_sum = subtoken_embeddings[pos]
        if token_sum is None:
            print("Warning: encountered a span with no subtokens", file=sys.stderr)
        else:
            token_embeddings.append(token_sum / n_subtokens)

    return np.vstack(token_embeddings)


def save_term_embeddings(
    sentence_corpus: pathlib.Path,
    term: str,
    output_pfx: pathlib.Path,
    model: str = "google/mt5-xl",
    show_progress: bool = True,
):
    """
    Extracts and saves the embeddings of each instance of a given term within
    each sentence (if any) for a pretrained HuggingFace model (by default MT5-XL).
    Since there may not be a one-to-one correspondence between sentences and
    term instances, a CSV containing metadata to identify these embeddings is also
    saved.

    Note: Assumes that the pretrained model is compatible with T5's tokenizer.
    """
    # Instantiate tokenizer and feature extractor
    ## Set legacy flag to remove warning tied to this update:
    ## https://github.com/huggingface/transformers/pull/24565
    tokenizer = T5Tokenizer.from_pretrained(model, legacy=False)
    extractor = pipeline(model=model, tokenizer=tokenizer, task="feature-extraction")
    extractor = cast(FeatureExtractionPipeline, extractor)  # for mypy

    # Output CSV containing metadata to identify the resulting embeddings
    out_meta = output_pfx / ".csv"
    fieldnames = ["row_id", "file", "sent_id", "token_order"]

    token_embeddings = []
    embedding_index = 0
    with open(out_meta, mode="w", newline="") as csv_handler:
        writer = csv.DictWriter(csv_handler, fieldnames=fieldnames)
        writer.writeheader()
        sent_progress = tqdm(
            orjsonl.stream(sentence_corpus),
            desc="Processing sentences",
            disable=not show_progress,
        )
        for row in sent_progress:
            row = cast(dict[str, str], row)  # for mypy
            # Normalize sentence text
            sent = normalize_text(row["text"])
            # Identify indices for term's tokens (if any)
            term_spans = get_term_spans(sent, term)
            # Determine how these term spans align with T5's (sub)tokenizer
            span2subtokens = get_subtoken_alignment(tokenizer, sent, term_spans)
            # Extract the term embeddings
            term_embeddings = extract_span_embeddings(extractor, sent, span2subtokens)

            # Write term's metadata to the output CSV
            for i in range(len(term_spans)):
                entry = {
                    "row_id": embedding_index,
                    "file": row["file"],
                    "sent_id": row["sent_id"],
                    "token_order": i,
                }
                writer.writerow(entry)
                embedding_index += 1
            # Accumulate token embeddings
            token_embeddings.append(term_embeddings)

    # Write output embeddings array
    out_npy = output_pfx / ".npy"
    np.save(out_npy, np.vstack(token_embeddings))


def main():
    """
    Command-line access for extracting the token embeddings of a specific
    term from a sentence-level corpus file (JSONL).
    """
    parser = argparse.ArgumentParser(
        description="Extract token embeddings of a given term",
    )
    # Required parameters
    parser.add_argument(
        "input",
        help="Input sentence-level corpus file (JSONL)",
        metavar="input_sents",
        type=pathlib.Path,
    )
    parser.add_argument(
        "term",
        help="Term whose embeddings will be extracted",
        type=str,
    )
    parser.add_argument(
        "output_dir",
        help="Path to directory where output files should be saved.",
        type=pathlib.Path,
    )
    parser.add_argument(
        "output_name",
        help="The name (i.e. stem) to be used for the resulting metadata (CSV) "
        "and embeddings (NPY) files. File suffixes will be added.",
        type=str,
    )
    # Optional arguments
    parser.add_argument(
        "--model",
        help="Pretrained Hugging Face model. Model must be compatible with T5 tokenizer"
        "(e.g., t5 and mt5 models)",
        type=str,
        default="google/mt5-small",
    )
    parser.add_argument(
        "--progress",
        help="Show progress",
        action=argparse.BooleanOptionalAction,
        default=True,
    )

    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Error: input file {args.input_file} does not exist", file=sys.stderr)
        sys.exit(1)
    if not args.output_dir.is_dir():
        print(
            f"Error: output directory {args.output_dir} does not exist.",
            file=sys.stderr,
        )
        sys.exit(1)

    out_pfx = args.output_dir / args.output_name
    if (out_pfx / ".csv").is_file():
        print(
            f"Error: output metadata file {out_pfx}.csv exists. Will not overwrite",
            file=sys.stderr,
        )
        sys.exit(1)
    if (out_pfx / ".npy").is_file():
        print(
            f"Error: output embeddings file {out_pfx}.npy exists. Will not overwrite",
            file=sys.stderr,
        )
        sys.exit(1)

    save_term_embeddings(
        args.input,
        args.term,
        out_pfx,
        model=args.model,
        show_progress=args.progress,
    )


if __name__ == "__main__":
    main()
