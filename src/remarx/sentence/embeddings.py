"""
Provides functionality to generate sentence embeddings from sentence corpora
using pretrained models from the sentence-transformers library.
"""

import argparse
import csv
import pathlib
import sys

import numpy.typing as npt

from remarx.sentence.corpus.base_input import FileInput

try:
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    raise ImportError(
        "The sentence-transformers library is required for embedding functionality. "
        "Install it with: pip install remarx[embeddings] or uv add --optional embeddings"
    ) from e


def get_sentence_embeddings(
    sentence_corpus: pathlib.Path,
    model_name: str = "paraphrase-multilingual-mpnet-base-v2",
) -> npt.NDArray:
    """
    Extract sentence embeddings for each sentence in the input sentence corpus file using the specified pretrained Sentence
    Transformers model and return them as a 2-dimensional numpy array.

    :param sentence_corpus: Path to the input CSV file containing sentences
    :param model_name: Name of the pretrained sentence transformer model to use (leave as default for German)
    :return: 2-dimensional numpy array of normalized sentence embeddings
    """
    # Validate the corpus file structure
    validate_sentence_corpus(sentence_corpus)

    # Load sentences from CSV file
    sentences = []
    with sentence_corpus.open("r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        # Extract sentence texts
        sentences.extend(row["text"] for row in reader)

    # Generate embeddings using the specified model
    model = SentenceTransformer(model_name)
    embeddings = model.encode(
        sentences,
        normalize_embeddings=True,
        show_progress_bar=True,  # Output progress bar in console
    )

    return embeddings


def main() -> None:
    """
    Command-line access to sentence embedding generation from CSV corpus files.
    """
    parser = argparse.ArgumentParser(
        description="Generate sentence embeddings from a CSV sentence corpus file"
    )
    parser.add_argument(
        "input_csv", type=pathlib.Path, help="Input sentence corpus (CSV)"
    )
    parser.add_argument(
        "output_npy", type=pathlib.Path, help="Output embeddings file (.npy)"
    )
    parser.add_argument(
        "--model",
        default="paraphrase-multilingual-mpnet-base-v2",
        help="Pretrained model name",
    )

    args = parser.parse_args()

    try:
        embeddings = get_sentence_embeddings(args.input_csv, model_name=args.model)

        import numpy as np

        np.save(args.output_npy, embeddings)

        print(f"Saved embeddings to {args.output_npy}")
        print(f"Shape: {embeddings.shape}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def validate_sentence_corpus(corpus_file: pathlib.Path) -> None:
    """
    Helper function to validate that a CSV sentence corpus file has the required structure from the corpus creation process, and is not empty.

    :raises FileNotFoundError: If the corpus file does not exist
    :raises ValueError: If the corpus file doesn't contain required columns or is empty
    :raises ValueError: If the corpus file has no data rows
    """
    # check if file exists
    if not corpus_file.exists():
        raise FileNotFoundError(f"Sentence corpus file not found: {corpus_file}")

    # check for required columns
    required_columns = set(FileInput.field_names)

    with corpus_file.open("r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        found_columns = set(reader.fieldnames or [])
        missing_columns = required_columns - found_columns

        if missing_columns:
            raise ValueError(
                f"CSV file is missing required columns: {sorted(missing_columns)}. "
                f"Found columns: {sorted(found_columns)}"
                f"Please ensure the corpus file is created using the corpus creation process."
            )

        # Check if file has any data rows
        try:
            next(reader)
        except StopIteration as err:
            raise ValueError("No sentences found in the corpus file") from err
