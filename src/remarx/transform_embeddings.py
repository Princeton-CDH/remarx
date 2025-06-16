"""
A collection of post-processing methods for embeddings.
"""

import numpy as np
import numpy.typing as npt
from scipy.stats import rankdata
from sklearn.decomposition import PCA
from sklearn.random_projection import SparseRandomProjection


def pca(embeddings: npt.NDArray, n_dims: int) -> npt.NDArray:
    """
    Use principal component analysis (PCA) to reduce embeddings to given number
    of dimensions. Returns the reduced embeddings as a numpy array. Note that this
    cannot be performed incrementally.
    """
    transformer = PCA(n_components=n_dims)
    return transformer.fit_transform(embeddings)


def sparse_random_projection(
    embeddings: npt.NDArray, n_dims, random_seed: int = 42
) -> npt.NDArray:
    """
    Use sparse random projections to reduce embeddings to given number of dimensions.
    Returns the reduced embeddings as a numpy array. Note that this transformation
    can be performed incrementally as long as the same random seed is used.
    """
    rng = np.random.RandomState(random_seed)
    transformer = SparseRandomProjection(n_components=n_dims, random_state=rng)
    return transformer.fit_transform(embeddings)


def rank_normalize(embeddings: npt.NDArray) -> npt.NDArray:
    """
    Transform embeddings for computing Spearman correlation (Spearman's rho).
    Specifically, each embedding is transformed into its rank form and then l2
    normalized. Returns the transformed embbedings as a numpy array. Note that
    this transformation can be performed incrementally.
    """
    new_embeddings = rankdata(embeddings, axis=1)
    return new_embeddings / np.linalg.norm(new_embeddings, axis=1, keepdims=True)
