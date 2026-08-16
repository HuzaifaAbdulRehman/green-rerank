"""Classical families, chosen for the shape of their cost rather than their accuracy.

Three families with deliberately opposite cost profiles, because a break-even point only
exists if the curves actually cross:

===============  ===================  ==========================================
family           training             serving
===============  ===================  ==========================================
``popularity``   negligible           negligible -- one vector, same for everyone
``itemknn``      one similarity fit   **expensive**: profile x item-item matrix
``als``          **expensive**: iterative  cheap: one thin dot product
===============  ===================  ==========================================

ItemKNN and ALS are the interesting pair. ItemKNN front-loads almost nothing and pays on
every request; ALS front-loads a great deal and then serves almost free. Which is
cheaper is therefore not a property of the model at all -- it is a property of how many
requests you expect to serve, which is exactly the question the literature does not ask.

The similarity computation is imported from the companion project rather than written
again here. It is already tested there, including an assertion that its sparse and dense
paths agree exactly -- a test that caught a real bug.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse

from green_rerank.companion import ensure_importable
from green_rerank.families.base import Family


def _companion_similarity():
    """Import the companion's ItemKNN similarity, deferred until actually needed.

    Deferred so that importing this module -- and therefore running most of the test
    suite -- does not require the companion checkout to be present.
    """
    ensure_importable()
    from benchmarks.loader import (
        cosine_similarity,
        cosine_similarity_sparse,
        top_k_neighbours,
        top_k_neighbours_sparse,
    )

    return cosine_similarity, cosine_similarity_sparse, top_k_neighbours, top_k_neighbours_sparse


# --------------------------------------------------------------------- popularity


class Popularity(Family):
    """Recommend the globally most popular items, identically to everyone.

    Not a strawman. It is the floor the whole comparison is read against: any family
    whose accuracy does not beat this is spending energy for nothing, and the Green
    RecSys literature's central finding is that this happens more often than it should.
    Its cost is the zero point of both axes.
    """

    name = "popularity"
    _model_attrs = ("_popularity",)

    def __init__(self) -> None:
        super().__init__()
        self._popularity: np.ndarray | None = None

    def fit(self, matrix: sparse.csr_matrix, sequences=None) -> Popularity:
        self._popularity = np.asarray(matrix.sum(axis=0), dtype=float).ravel()
        self._n_items = matrix.shape[1]
        self._fitted = True
        return self

    def _scores(self, matrix: sparse.csr_matrix, user_rows: np.ndarray) -> np.ndarray:
        # Every user gets the same row. Broadcast rather than tile: materialising
        # identical rows would charge this family memory it does not actually need,
        # and memory is one of the costs being reported.
        assert self._popularity is not None
        return np.broadcast_to(self._popularity, (len(user_rows), self._n_items))


# ------------------------------------------------------------------------ ItemKNN


class ItemKNN(Family):
    """Shrunk-cosine item-item neighbourhood model.

    Training is a single sparse product; serving multiplies each user's profile by the
    similarity matrix, so **cost per request scales with catalogue size**. That is the
    property that makes it lose to a factor model at high request volume, and it is
    invisible in any table reporting one number per run.
    """

    name = "itemknn"
    _model_attrs = ("_similarity",)

    def __init__(
        self,
        topk: int = 100,
        shrink: float = 100.0,
        sparse_similarity: bool | None = None,
    ) -> None:
        super().__init__()
        self.topk = topk
        self.shrink = shrink
        # None chooses from the catalogue size actually produced, matching the
        # companion's rule: a dense matrix is 15 MB at 1,366 items and 1,016 MB at
        # 11,269.
        self.sparse_similarity = sparse_similarity
        self._similarity = None

    def fit(self, matrix: sparse.csr_matrix, sequences=None) -> ItemKNN:
        dense_fn, sparse_fn, topk_dense, topk_sparse = _companion_similarity()
        n_items = matrix.shape[1]

        use_sparse = (
            (n_items * n_items * 8) > 256_000_000
            if self.sparse_similarity is None
            else self.sparse_similarity
        )
        if use_sparse:
            similarity = sparse_fn(matrix, shrink=self.shrink)
            self._similarity = topk_sparse(similarity, topk=self.topk)
        else:
            similarity = dense_fn(matrix, shrink=self.shrink)
            self._similarity = topk_dense(similarity, topk=self.topk)

        self._n_items = n_items
        self._fitted = True
        return self

    def _scores(self, matrix: sparse.csr_matrix, user_rows: np.ndarray) -> np.ndarray:
        profiles = matrix[user_rows]
        scored = profiles @ self._similarity
        # A sparse similarity makes this product sparse too, and np.asarray on a sparse
        # matrix yields a 0-d object array rather than the scores -- so densify
        # explicitly rather than coerce.
        return scored.toarray() if sparse.issparse(scored) else np.asarray(scored)


# ---------------------------------------------------------------------------- ALS


class ImplicitALS(Family):
    """Implicit-feedback alternating least squares (Hu, Koren & Volinsky, 2008).

    Written directly against numpy for the same reason the companion project declined
    RecBole: the algorithm is a few dozen lines of dense linear algebra, and pulling in a
    compiled dependency to reach it would buy a dependency rather than a capability. It
    also keeps the training cost *ours* to measure rather than a black box's.

    Training is **work-bounded, not time-bounded**: it runs ``epochs`` passes and stops.
    A wall-clock stopping rule would make quality depend on how fast the machine is,
    which is precisely what made the companion project's tabu solver's results
    non-portable across machines -- it got measurably better on a faster CPU at identical
    settings.
    """

    name = "als"
    iterative = True
    _model_attrs = ("_user_factors", "_item_factors")

    def __init__(
        self,
        factors: int = 64,
        epochs: int = 15,
        regularisation: float = 0.01,
        alpha: float = 40.0,
        seed: int = 0,
    ) -> None:
        super().__init__()
        self.factors = factors
        self.epochs = epochs
        self.regularisation = regularisation
        # Confidence scaling from the paper: an observed interaction is evidence of
        # preference, an absent one is weak evidence of its absence, and alpha sets how
        # much more the observations count.
        self.alpha = alpha
        self.seed = seed
        self._user_factors: np.ndarray | None = None
        self._item_factors: np.ndarray | None = None

    def fit(self, matrix: sparse.csr_matrix, sequences=None) -> ImplicitALS:
        matrix = matrix.tocsr().astype(float)
        n_users, n_items = matrix.shape

        rng = np.random.default_rng(self.seed)
        # Small random init: exactly zero would make the first solve singular under low
        # regularisation, and a fixed seed keeps runs comparable across repeats.
        self._user_factors = rng.normal(0, 0.01, (n_users, self.factors))
        self._item_factors = rng.normal(0, 0.01, (n_items, self.factors))

        transposed = matrix.T.tocsr()
        for _ in range(self.epochs):
            self._solve(matrix, self._user_factors, self._item_factors)
            self._solve(transposed, self._item_factors, self._user_factors)

        self._n_items = n_items
        self._fitted = True
        return self

    def _solve(self, matrix: sparse.csr_matrix, target: np.ndarray, other: np.ndarray) -> None:
        """One half-iteration: refit ``target`` with ``other`` held fixed.

        The paper's efficiency trick is the whole reason this is tractable. The exact
        solution weights *every* item, including the overwhelming majority the user never
        touched, which would be an ``n_items``-sized sum per user. Splitting confidence
        as ``C = I + (C - I)`` makes the first part identical for every user -- computed
        once as ``YtY`` -- leaving a correction over only the non-zeros.
        """
        gram = other.T @ other
        regularised = gram + self.regularisation * np.eye(self.factors)

        indptr, indices, data = matrix.indptr, matrix.indices, matrix.data
        for row in range(matrix.shape[0]):
            start, end = indptr[row], indptr[row + 1]
            if start == end:
                target[row] = 0.0
                continue

            picked = other[indices[start:end]]
            confidence = 1.0 + self.alpha * data[start:end]

            a = regularised + picked.T @ ((confidence - 1.0)[:, None] * picked)
            b = picked.T @ confidence
            target[row] = np.linalg.solve(a, b)

    def _scores(self, matrix: sparse.csr_matrix, user_rows: np.ndarray) -> np.ndarray:
        # The entire serving cost: one (n_users x f) by (f x n_items) product. Unlike
        # ItemKNN this does not touch the interaction matrix at all.
        return self._user_factors[user_rows] @ self._item_factors.T
