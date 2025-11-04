"""
Library for generating sentence embeddings from pretrained Sentence Transformer models.
"""

import json
import logging
import pathlib
import zlib
from timeit import default_timer as time

import numpy as np
import numpy.typing as npt
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Cache directory
_CACHE_DIR = pathlib.Path.home() / ".remarx_cache" / "embeddings"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_sentence_embeddings(
    sentences: list[str],
    model_name: str = "paraphrase-multilingual-mpnet-base-v2",
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
    # Generate cache key from JSON serialization to avoid newline collisions
    content = json.dumps(sentences)
    cache_key = f"{zlib.crc32(content.encode('utf-8')):08x}"
    cache_file = _CACHE_DIR / f"{cache_key}.npz"

    # Check cache first
    if cache_file.exists():
        with np.load(cache_file) as cached:
            embeddings = cached["embeddings"]
        logger.info(f"Loaded {len(embeddings):,} embeddings from cache")
        return embeddings

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

    # Cache for next time
    np.savez_compressed(cache_file, embeddings=embeddings)

    return embeddings
