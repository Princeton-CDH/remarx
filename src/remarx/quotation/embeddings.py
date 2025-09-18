"""
Library for generating sentence embeddings from pretrained Sentence Transformer models.
"""

import numpy.typing as npt
from sentence_transformers import SentenceTransformer


def get_sentence_embeddings(
    sentences: list[str],
    model_name: str = "paraphrase-multilingual-mpnet-base-v2",
) -> npt.NDArray:
    """
    Extract embeddings for each sentence using the specified pretrained Sentence
    Transformers model (default is paraphrase-multilingual-mpnet-base-v2).
    Returns a numpy array of the embeddings with shape [# sents, # dims].

    :param sentences: List of sentences to generate embeddings for
    :param model_name: Name of the pretrained sentence transformer model to use (default: paraphrase-multilingual-mpnet-base-v2)
    :return: 2-dimensional numpy array of normalized sentence embeddings with shape [# sents, # dims]
    """
    # Generate embeddings using the specified model
    model = SentenceTransformer(model_name)
    embeddings = model.encode(
        sentences,
        normalize_embeddings=True,
        show_progress_bar=False,  # default to False to disable progress bar output in unit tests
    )
    return embeddings
