"""
Library for generating sentence embeddings from pretrained Sentence Transformer models.
"""

import logging
import pathlib
from timeit import default_timer as time

import numpy as np
import numpy.typing as npt
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "paraphrase-multilingual-mpnet-base-v2"


def get_cached_embeddings(
    source_file: pathlib.Path,
    sentences: list[str],
    model_name: str = DEFAULT_MODEL,
    show_progress_bar: bool = False,
) -> tuple[npt.NDArray, bool]:
    """
    Get sentence embeddings, with file caching based on source file.

    Returns a tuple of embeddings array and a boolean indicating whether
    the data was loaded from cache.
    """

    # cache embeddings in the same location as the source file,
    # with the same base filename
    cache_file = source_file.parent / f"{source_file.stem}_{model_name}.npy"
    # if file exists and has non-zero size, check modification time
    if cache_file.exists() and cache_file.stat().st_size:
        if cache_file.stat().st_mtime > source_file.stat().st_mtime:
            with cache_file.open("rb") as cache_filehandle:
                logger.info(f"Loading embeddings from {cache_file}")
                return (np.load(cache_filehandle), True)
        else:
            logger.info(
                f"Cached embeddings file {cache_file} exists but source file {source_file} is newer"
            )

    # otherwise: generate embeddings, save, and return
    embeddings = get_sentence_embeddings(
        sentences, model_name=model_name, show_progress_bar=show_progress_bar
    )
    with cache_file.open("wb") as cache_filehandle:
        logger.info(f"Caching embeddings to {cache_file}")
        np.save(cache_filehandle, embeddings, allow_pickle=True)
    return (embeddings, False)


def get_sentence_embeddings(
    sentences: list[str],
    model_name: str = DEFAULT_MODEL,
    show_progress_bar: bool = False,
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
    start = time()
    model = SentenceTransformer(model_name)
    embeddings = model.encode(
        sentences,
        normalize_embeddings=True,
        show_progress_bar=show_progress_bar,
    )
    n_vecs = len(embeddings)
    elapsed_time = time() - start
    logger.info(f"Generated {n_vecs:,} embeddings in {elapsed_time:.1f} seconds")
    return embeddings
