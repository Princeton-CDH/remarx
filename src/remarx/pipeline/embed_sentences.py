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

        context.model = SentenceTransformer(context.model_name)
        print(f"Model '{context.model_name}' loaded successfully")

    @staticmethod
    def run(context: SetupContext, input_file: Path, output_file: Path):
        import numpy as np
        import polars as pl

        df = pl.read_csv(input_file.resolve())
        sentences = df["text"].to_list()

        embeddings = context.model.encode(
            sentences,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        with open(output_file, "wb") as f:
            np.save(f, embeddings)
        print(f"Saved {len(sentences)} embeddings for {input_file.name}")


EmbedSentences.cli()
