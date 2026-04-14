from pathlib import Path
from typing import Annotated

import typer

from tigerflow.tasks import SlurmTask
from tigerflow.utils import SetupContext


class EmbedSentences(SlurmTask):
    class Params:
        model_name: Annotated[
            str,
            typer.Option(help="SentenceTransformers model name"),
        ] = "paraphrase-multilingual-mpnet-base-v2"

    @staticmethod
    def setup(context: SetupContext):
        from sentence_transformers import SentenceTransformer

        # Model is loaded once per worker and stored on the context,
        # so it is reused across all files processed by the same worker.
        context.model = SentenceTransformer(context.model_name)
        print(f"Model '{context.model_name}' loaded successfully")

    @staticmethod
    def run(context: SetupContext, input_file: Path, output_file: Path):
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
        with open(output_file, "wb") as f:
            np.save(f, embeddings)
        print(f"Saved {len(sentences)} embeddings for {input_file.name}")


EmbedSentences.cli()
