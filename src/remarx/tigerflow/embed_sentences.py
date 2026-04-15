"""TigerFlow task for generating sentence embeddings from corpus CSVs."""

from pathlib import Path
from typing import Annotated

import typer
from tigerflow.tasks import SlurmTask
from tigerflow.utils import SetupContext


class EmbedSentences(SlurmTask):
    """TigerFlow task that encodes a sentence corpus CSV into a numpy embedding file."""

    class Params:
        """Configurable parameters for the embedding task."""

        model_name: Annotated[
            str,
            typer.Option(help="SentenceTransformers model name"),
        ] = "paraphrase-multilingual-mpnet-base-v2"

        hf_home: Annotated[
            str | None,
            typer.Option(help="Path to HuggingFace cache directory (HF_HOME)"),
        ] = None

    @staticmethod
    def setup(context: SetupContext) -> None:
        """Load the sentence-transformers model once per worker."""
        import os

        # On clusters where worker nodes lack internet access, point HuggingFace
        # to a pre-populated cache directory and disable all network requests.
        # These must be set before importing sentence_transformers, as the library
        # may attempt network access at import time.
        if context.hf_home:
            os.environ["HF_HOME"] = context.hf_home
            os.environ["HF_HUB_CACHE"] = f"{context.hf_home}/hub"
            os.environ["HF_HUB_OFFLINE"] = "1"

        from sentence_transformers import SentenceTransformer

        # Model is loaded once per worker and stored on the context,
        # so it is reused across all files processed by the same worker.
        context.model = SentenceTransformer(context.model_name)
        print(f"Model '{context.model_name}' loaded successfully")

    @staticmethod
    def run(context: SetupContext, input_file: Path, output_file: Path) -> None:
        """Encode sentences from input CSV and write L2-normalized embeddings to output."""
        import numpy as np
        import polars as pl

        # TigerFlow passes input_file as a symlink inside its internal .tigerflow/
        # directory. resolve() converts it to the real path so polars can read it.
        df = pl.read_csv(input_file.resolve())
        sentences = df["text"].to_list()

        embeddings = context.model.encode(
            sentences,
            normalize_embeddings=True,  # L2-normalize so cosine similarity == dot product
            show_progress_bar=False,
        )

        # TigerFlow's LocalTask/SlurmTask already wraps run() in atomic_write,
        # so output_file is a temp path that gets renamed on success.
        # We open it as a binary file to avoid np.save appending an extra .npy suffix.
        with output_file.open("wb") as f:
            np.save(f, embeddings)
        print(f"Saved {len(sentences)} embeddings for {input_file.name}")


EmbedSentences.cli()
