"""
Provides functionality to generate sentence embeddings from sentence corpora
using pretrained models from the sentence-transformers library.
"""

import numpy.typing as npt

try:
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    raise ImportError(
        "The sentence-transformers library is required for embedding functionality. "
        "Install it by running: uv sync"
    ) from e


def get_sentence_embeddings(
    sentences: list[str],
    model_name: str = "paraphrase-multilingual-mpnet-base-v2",
) -> npt.NDArray:
    """
    Extract sentence embeddings for each sentence in the input list using the specified pretrained Sentence
    Transformers model and return them as a 2-dimensional numpy array.

    :param sentences: List of sentences to generate embeddings for
    :param model_name: Name of the pretrained sentence transformer model to use (leave as default for German)
    :return: 2-dimensional numpy array of normalized sentence embeddings
    """
    # Generate embeddings using the specified model
    model = SentenceTransformer(model_name)
    embeddings = model.encode(
        sentences,
        normalize_embeddings=True,
        show_progress_bar=True,  # Output progress bar in console
    )

    return embeddings
