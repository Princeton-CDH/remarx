"""
Script to build embeddings of a specific term for each sentence in a
sentence-level corpus file (JSONL). The resulting embeddings are saves as a .npy
binary file. By default the MT5-XL model (google/mt5-xl) is used, but this can
be changed to another MT5 variants. Since term instances and sentences are
unlikely to have a one-to-one correspondence, a metadata file (CSV) identifying
each embedding is also generated.

Note: Embeddings are extracted from the model's initial token embedding layer

See https://huggingface.co/docs/transformers/main/en/model_doc/mt5 for more on MT5.

Example:

    python get_token_embeddings sents.jsonl Kapital output_dir output_stem

"""

import argparse
import csv
import pathlib
import re
import sys
import unicodedata
from itertools import accumulate
from typing import cast

import numpy as np
import numpy.typing as npt
import orjsonl
from tqdm import tqdm

# NOTE: mypy typing fails on these paths, but succeeds with the fine-grained ones
from transformers import (
    MT5EncoderModel,
    PreTrainedModel,
    PreTrainedTokenizer,
    T5Tokenizer,
)


def normalize_text(text: str) -> str:
    """
    Normalizes text so that it will align with its tokenized version.

    Since we assume we're using a T5Tokenizer for tokenization, we want to
    ensure that our text will not change length when sentencepiece's (default)
    normalization is applied.
    """
    # First, perform NFKC unicode normalization
    new_text = unicodedata.normalize("NFKC", text)

    # Then, remove any outer whitespace, convert whitespace sequences to a
    # single space, and add a leading space
    return " " + " ".join(new_text.strip().split())


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
    tokenizer: T5Tokenizer,
    sentence: str,
    spans: list[tuple[int, int]],
) -> list[list[int]]:
    """
    Given a sentence and a list of spans for terms (or phrases) of interest
    within the sentence (i.e., produced by `get_term_spans`), returns a list
    of subtoken indices within the subtoken sequence produced by the tokenizer.
    In cases where span and subtoken boundaries are misaligned, all subtokens
    that contain chracters within the span are included.

    Assumes:
      * The pretrained tokenizer is a T5Tokenizer, so encoding only adds a special
        subtoken (</s>) at the end, so it will not impact alignment.
      * The sentence has been normalized using `normalize_text`
      * Spans are consecutive and non-overlapping
    """
    # Note: this does not include the special tokens added when encoding
    subtokens = tokenizer.tokenize(sentence)  # type: ignore

    # Check that tokenized text aligns with original
    if len("".join(subtokens)) != len(sentence):
        raise ValueError(
            "Error: Tokenized sentence does not align with input. "
            "Try applying normalize_text first."
        )

    # Initialize span to subtoken correspondence
    span2subtokens: list[list[int]] = []
    # Calculate subtoken start indices
    subtoken_lens = [len(s) for s in subtokens]
    subtoken_starts = list(accumulate(subtoken_lens, initial=0))[:-1]

    i_subtoken = 0
    j_span = 0
    while i_subtoken < len(subtokens) and j_span < len(spans):
        # Check if new subtoken list needs to be created
        if j_span == len(span2subtokens):
            span2subtokens.append([])
        # Get subtoken's character-level indices
        sub_start = subtoken_starts[i_subtoken]
        sub_end = (
            subtoken_starts[i_subtoken + 1]
            if i_subtoken + 1 < len(subtokens)
            else len(sentence)
        )
        # Get span's character-level indices
        span_start, span_end = spans[j_span]

        # Subtoken overlaps with span
        if sub_start < span_end and span_start < sub_end:
            # Map subtoken to span
            span2subtokens[-1].append(i_subtoken)

        # Increment subtoken if it doesn't continue past the current span
        if sub_end <= span_end:
            i_subtoken += 1

        # Increment span if it doesn't continue past the current subtoken
        if span_end <= sub_end:
            j_span += 1

    return span2subtokens


def extract_subtoken_embeddings(
    tokenizer: PreTrainedTokenizer,
    model: PreTrainedModel,
    sentence: str,
    layer: int = -1,
):
    """
    For a sentence, extract its subtoken embeddings (i.e., hiddens states) from
    a specific layer of a given model. By default, this is the final layer.
    Returns a numpy array of the resulting subtoken embeddings.

    Note that the first (0) layer will correspond to the initial token embedding
    layer and so the hidden states of the model layers are offset by one.

    """
    # Note: assuming the encoded sentence is shorter than the model's max length
    input_ids = tokenizer(sentence, return_tensors="pt").input_ids

    if layer == -1:
        # Tensor shape ( # blocks = 1, # subtokens, # dimensions )
        return model(input_ids).last_hidden_state[0].cpu().detach().numpy()  # type: ignore

    # Tensor shape: ( # layers, # blocks =1, # subtokens, # dimensions )
    hidden_states = model(input_ids, output_hidden_states=True).hidden_states  # type: ignore
    return hidden_states[layer][0].cpu().detach().numpy()


def extract_span_embeddings(
    tokenizer: PreTrainedTokenizer,
    model: PreTrainedModel,
    sentence: str,
    span_to_subtokens: list[list[int]],
    layer: int = -1,
) -> npt.NDArray:
    """
    For a sentence, extract the span embeddings using a given pretrained Hugging Face
    tokenizer and model. The spans of interest are represented by a list of their
    subtokens which were determined using `get_subtoken_alignment`. A span's
    embedding is the average of its subtokens' embeddings. The extracted subtoken
    embeddings correspond to the hidden states of a specific layer of the model. By
    default, this is the final layer.
    Returns a numpy array of the resulting span embeddings.

    Assumes:
      * span_to_subtokens is not empty
      * span_to_subtokens sublits are non-empty and contain valid subtoken ids
    """
    # Using the initial token embedding layer
    subtoken_embeddings = extract_subtoken_embeddings(
        tokenizer, model, sentence, layer=layer
    )

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


def get_term_embeddings(
    tokenizer: T5Tokenizer,
    model: MT5EncoderModel,
    sentence: str,
    term: str,
) -> npt.NDArray | None:
    """
    For a sentence, extract the token-level embeddings for each instance of a
    given term within the sentence using a given pretrained T5 tokenizer and MT5
    encoder model (loaded from Hugging Face).
    Returns a numpy array of the resulting token embeddings

    Note:
      * The resulting array's rows correspond to distinct embeddings
      * Embedding ordering corresponds to the relative position of its token within
        the sentence
    """
    # Normalize sentence text
    sent = normalize_text(sentence)
    # Identify indices for term's tokens (if any)
    term_spans = get_term_spans(sent, term)
    # Determine how these term spans align with T5's (sub)tokenization
    span2subtokens = get_subtoken_alignment(tokenizer, sent, term_spans)

    if span2subtokens:
        return extract_span_embeddings(tokenizer, model, sent, span2subtokens)  # type: ignore
    else:
        return None


def save_token_embeddings(
    sentence_corpus: pathlib.Path,
    term: str,
    output_pfx: pathlib.Path,
    model_name: str = "google/mt5-xl",
    show_progress: bool = True,
):
    """
    Extracts and saves the embeddings of each instance of a given term within
    each sentence (if any) for a pretrained MT5 model (by default MT5-XL).
    Since there may not be a one-to-one correspondence between sentences and
    term instances, a CSV containing metadata to identify these embeddings is also
    saved.

    Note:
       * Assumes that the pretrained model uses T5's tokenizer.
    """
    # Check model name has correct prefix
    if not model_name.startswith("google/mt5-"):
        raise ValueError(
            f"Pretrained model {model_name} is not part of the MT5 family."
            " These models begin with 'google/mt5-'"
        )

    # Construct the tokenizer and model
    # Note: We have to use the not-fast, not-legacy version of the T5 tokenizer to
    # use the fixed version. For more details, see the following link:
    # https://github.com/huggingface/transformers/pull/24565
    tokenizer = T5Tokenizer.from_pretrained(model_name, legacy=False)
    model = MT5EncoderModel.from_pretrained(model_name)

    # Output CSV containing metadata to identify the resulting embeddings
    out_meta = output_pfx.with_suffix(output_pfx.suffix + ".csv")
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
            # Extract the term embeddings
            term_embeddings = get_term_embeddings(tokenizer, model, row["text"], term)

            # Continue if no instances found
            if term_embeddings is None:
                continue

            # Write term's metadata to the output CSV
            n_instances = term_embeddings.shape[0]
            for i in range(n_instances):
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
    np.save(output_pfx, np.vstack(token_embeddings))


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
    if out_pfx.with_suffix(out_pfx.suffix + ".csv").is_file():
        print(
            f"Error: output metadata file {out_pfx}.csv exists. Will not overwrite",
            file=sys.stderr,
        )
        sys.exit(1)
    if out_pfx.with_suffix(out_pfx.suffix + ".npy").is_file():
        print(
            f"Error: output embeddings file {out_pfx}.npy exists. Will not overwrite",
            file=sys.stderr,
        )
        sys.exit(1)

    save_token_embeddings(
        args.input,
        args.term,
        out_pfx,
        model_name=args.model,
        show_progress=args.progress,
    )


if __name__ == "__main__":
    main()
