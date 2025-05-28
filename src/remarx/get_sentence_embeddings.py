"""
Script to build sentence embeddings for each sentence in a sentence-level
corpus file (JSONL). The resulting embeddings are saved as a .npy binary
file.

Example:

    python get_sentence_embeddings sents.jsonl sent_vecs.npy 

    python get_sentence_embeddings sents.jsonl sent_vecs \
        --model paraphrase-multilingual-MiniLM-L12-v2 --no-progress
"""

import argparse
import pathlib
import sys

import numpy as np
import numpy.typing as npt
import orjsonl
from sentence_transformers import SentenceTransformer


def extract_sentence_embeddings(
    sentences: list[str],
    model_name: str = "paraphrase-multilingual-mpnet-base-v2",
    show_progress: bool = True,
) -> npt.NDArray:
    """
    Extract embeddings for each sentence using the specified pretrained Sentence
    Transformers model (default is paraphrase-multilingual-mpnet-base-v2).
    Returns a numpy array of the embeddings with shape [# sents, # dims].
    """
    model = SentenceTransformer(model_name)
    embeddings = model.encode(
        sentences, normalize_embeddings=True, show_progress_bar=show_progress
    )
    return embeddings


def save_sentence_embeddings(
    sentence_corpus: pathlib.Path,
    output_filename: pathlib.Path,
    pretrained_model: str = "paraphrase-multilingual-mpnet-base-v2",
    show_progress: bool = True,
):
    """
    Extracts sentence embeddings for each sentence in a
    sentence corpus file (JSONL) using a specificed pretrained model (defaults
    to paraphrase-multilingual-mpnet-base-v2). The resulting embeddings are
    saved as a numpy array within a .npy binary file.
    """
    # Load sentence texts
    sents = []
    for row in orjsonl.stream(sentence_corpus):
        sents.append(row["sentence"])

    # Extract and save embeddings
    embeddings = extract_sentence_embeddings(
        sents, pretrained_model, show_progress=show_progress
    )
    np.save(output_filename, embeddings, allow_pickle=True)


def main():
    """
    Command-line access for extracting sentence embeddings from a
    sentence-level corpus file (JSONL).
    """
    parser = argparse.ArgumentParser(
        description="Extract sentence embeddings",
    )
    # Required arguments
    parser.add_argument(
        "input",
        help="Input sentence-level corpus file (JSONL)",
        type=pathlib.Path,
    )
    parser.add_argument(
        "output",
        help="Output sentence embeddings file (.npy)",
        type=pathlib.Path,
    )
    # Optional arguments
    parser.add_argument(
        "--model",
        help="Pre-trained Sentence Transformer model to use."
        "Defaults to paraphrase-multilingual-mpnet-base-v2",
        type=str,
        default="paraphrase-multilingual-mpnet-base-v2",
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
    if args.output.suffix == ".npy":
        if args.output.is_file():
            print(f"Error: output file {args.output} exists. Will not overwrite.")
            sys.exit(1)
    else:
        if args.output.with_suffix(args.output.suffix + ".npy").is_file():
            print(f"Error: output file {args.output}.npy exists. Will not overwrite.")
            sys.exit(1)

    save_sentence_embeddings(
        args.input,
        args.output,
        pretrained_model=args.model,
        show_progress=args.progress,
    )


if __name__ == "__main__":
    main()
