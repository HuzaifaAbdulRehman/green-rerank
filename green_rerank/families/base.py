"""One interface every model family implements.

The split that matters is **fit versus recommend**. Prior work reports energy per run,
which folds a one-off training cost together with a per-request serving cost and makes
the sum uninterpretable: a model that trains for an hour and then serves for free looks
identical to one that trains instantly and burns the same total answering queries. They
are opposite deployment decisions.

Keeping them apart is what lets the pipeline ask ``E_train + N * E_serve`` and solve for
the ``N`` at which two families cross.

Subclasses implement :meth:`Family._scores` only. Candidate truncation and the exclusion
of already-seen items live here, in one place, because "never recommend something the
user already interacted with" is a leakage rule -- a family that forgot it would post
better accuracy for a reason that has nothing to do with being a better model, and the
error is invisible in the output.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from scipy import sparse


@dataclass(frozen=True)
class Sequences:
    """Time-ordered interactions per user.

    Kept separate from the interaction matrix rather than replacing it, because the two
    encode genuinely different things and most families only need the weaker one. A
    matrix says *which* items a user touched; this says in what order.

    Attributes:
        by_user: ``user_row -> list of item indices``, oldest first. Users absent from
            the mapping have no usable history.
        max_length: longest history retained, for models with a fixed context window.
    """

    by_user: dict[int, list[int]]
    max_length: int = 200

    def truncated(self, user_row: int) -> list[int]:
        """The most recent ``max_length`` items for one user.

        Recent rather than earliest: a fixed window that kept the *oldest* interactions
        would train the model on history the user has moved on from, and would do so
        silently.
        """
        history = self.by_user.get(int(user_row), [])
        return history[-self.max_length :]

    @classmethod
    def from_frame(cls, frame, user_index, item_index, max_length: int = 200) -> Sequences:
        """Build from a ``user_id / item_id / timestamp`` frame.

        ``mergesort`` is stable, so interactions sharing a timestamp get a deterministic
        -- if arbitrary -- order rather than a run-dependent one, matching the companion
        project's leave-one-out split.
        """
        ordered = frame.sort_values(["user_id", "timestamp"], kind="mergesort")
        by_user: dict[int, list[int]] = {}
        for user_id, item_id in zip(ordered.user_id, ordered.item_id, strict=True):
            if user_id not in user_index or item_id not in item_index:
                continue
            by_user.setdefault(user_index[user_id], []).append(item_index[item_id])
        return cls(by_user=by_user, max_length=max_length)


@dataclass(frozen=True)
class Recommendations:
    """Top-n items per user, and the scores that ranked them.

    Attributes:
        items: ``(n_users, n)`` catalogue item indices, best first.
        scores: ``(n_users, n)`` scores aligned with ``items``.
        user_rows: the matrix rows these correspond to, so a result can be traced back
            to a user after any resampling.
    """

    items: np.ndarray
    scores: np.ndarray
    user_rows: np.ndarray

    def __post_init__(self) -> None:
        if self.items.shape != self.scores.shape:
            raise ValueError(
                f"items {self.items.shape} and scores {self.scores.shape} disagree"
            )
        if self.items.shape[0] != self.user_rows.shape[0]:
            raise ValueError("one row of recommendations is required per user")


class Family(ABC):
    """A recommender model family.

    The name is deliberately "family" rather than "model": the comparison is between
    *classes* of approach -- neighbourhood, latent factor, neural -- and the point is
    the shape of their cost, not a leaderboard between two tuned instances.
    """

    #: Short identifier used in results tables.
    name: str = "family"

    #: Whether training is iterative, i.e. its cost scales with an epoch budget the
    #: experimenter chose. Recorded because a stopping rule that depends on wall-clock
    #: rather than work makes quality hardware-dependent -- the companion project's
    #: tabu solver, whose 20 ms timeout made its results non-portable across machines.
    iterative: bool = False

    def __init__(self) -> None:
        self._fitted = False
        self._n_items = 0

    # ------------------------------------------------------------------- training

    #: Whether this family needs interaction *order*, not just co-occurrence.
    #: Declared rather than inferred: a matrix carries no order, so a sequential model
    #: handed one would have to invent an ordering, and an invented ordering produces a
    #: plausible-looking model trained on an artefact.
    needs_sequences: bool = False

    @abstractmethod
    def fit(self, matrix: sparse.csr_matrix, sequences: Sequences | None = None) -> Family:
        """Train on a ``(n_users, n_items)`` implicit-feedback matrix.

        Args:
            matrix: implicit feedback, one row per user.
            sequences: time-ordered interactions, required by families with
                :attr:`needs_sequences` set. Matrix-based families ignore it.

        Implementations must set ``self._fitted`` and ``self._n_items``. Everything the
        model needs at serving time has to be built here, not lazily on first request,
        or training cost leaks into the serving measurement.
        """

    def _require_sequences(self, sequences: Sequences | None) -> Sequences:
        if sequences is None:
            raise ValueError(
                f"{self.name} is a sequential model and needs ordered interactions. "
                "Pass sequences=; deriving an order from the interaction matrix would "
                "mean inventing one."
            )
        return sequences

    # -------------------------------------------------------------------- serving

    @abstractmethod
    def _scores(self, matrix: sparse.csr_matrix, user_rows: np.ndarray) -> np.ndarray:
        """Dense ``(len(user_rows), n_items)`` scores. The family's actual work."""

    def score_users(
        self,
        matrix: sparse.csr_matrix,
        user_rows: np.ndarray,
        exclude_seen: bool = True,
    ) -> np.ndarray:
        """Dense catalogue-wide scores, with seen items masked out.

        Separated from :meth:`select` because they are the two halves of retrieval and
        only *this* half is family-specific. Profiling showed selection is the majority
        of retrieval cost for every family -- 99.9 % for popularity, whose scoring is a
        single broadcast -- so reporting them as one number would hide that most of the
        measured difference between families comes from work they all share.
        """
        self._require_fitted()
        user_rows = np.asarray(user_rows, dtype=np.int64)

        scores = np.asarray(self._scores(matrix, user_rows), dtype=float)
        if scores.shape != (len(user_rows), self._n_items):
            raise ValueError(
                f"{self.name}._scores returned {scores.shape}, expected "
                f"{(len(user_rows), self._n_items)}"
            )

        if exclude_seen:
            # Copy before masking, always. Two distinct hazards make this non-optional:
            # a family may return a read-only view (Popularity broadcasts one row to
            # every user), and a family may return a reference to its own cached state,
            # which masking in place would poison for every later request. Either bug
            # would leave the first call correct and the model quietly wrong afterwards.
            scores = scores.copy()

            # -inf rather than 0: a family may legitimately produce negative scores, and
            # zeroing would leave a seen item ranked above them.
            for position, row in enumerate(user_rows):
                scores[position, matrix[row].indices] = -np.inf

        return scores

    def select(self, scores: np.ndarray, user_rows: np.ndarray, n: int) -> Recommendations:
        """Turn catalogue-wide scores into the top-``n`` candidate set.

        Shared by every family and deliberately identical for all of them, so that the
        comparison between families is a comparison of their scoring, not of who happens
        to have a better selection routine.
        """
        if n < 1:
            raise ValueError("n must be at least 1")
        if n > self._n_items:
            raise ValueError(f"n={n} exceeds the catalogue size {self._n_items}")

        items, ordered = self._top_n(scores, n)
        return Recommendations(
            items=items, scores=ordered, user_rows=np.asarray(user_rows, dtype=np.int64)
        )

    def recommend(
        self,
        matrix: sparse.csr_matrix,
        user_rows: np.ndarray,
        n: int,
        exclude_seen: bool = True,
    ) -> Recommendations:
        """Top-``n`` items per user: :meth:`score_users` then :meth:`select`.

        The convenience path. The measured pipeline calls the two halves separately so
        it can cost them separately.

        Args:
            matrix: the training matrix, needed both for the user profiles a
                neighbourhood model scores against and for the exclusion mask.
            user_rows: rows of ``matrix`` to serve.
            n: candidate-set size (the retrieval stage's output).
            exclude_seen: never return an item the user already interacted with.
                Defaults on; turning it off is only for tests that need to check the
                raw ranking.
        """
        self._require_fitted()
        user_rows = np.asarray(user_rows, dtype=np.int64)
        if n > self._n_items:
            raise ValueError(f"n={n} exceeds the catalogue size {self._n_items}")
        scores = self.score_users(matrix, user_rows, exclude_seen=exclude_seen)
        return self.select(scores, user_rows, n)

    @staticmethod
    def _top_n(scores: np.ndarray, n: int) -> tuple[np.ndarray, np.ndarray]:
        """Top ``n`` per row, best first, with deterministic tie-breaking.

        Ties are common -- a popularity model gives whole blocks of items the same score
        -- and ``argpartition`` breaks them by memory order, which silently depends on
        how the matrix was built. The rule is therefore ``(-score, index)``, matching the
        companion project's ``top_k_neighbours``.

        **Why this is not a sort.** The first version looped over users calling
        ``np.lexsort((columns, -scores[row]))``. Profiling the retrieve stage showed that
        loop was **99.8 %** of popularity's measured serving cost and 93 % of ALS's -- so
        the per-request cost was almost entirely this function, and the family comparison
        it was meant to support was really one shared sorting routine compared against
        itself. It produced a confident and meaningless break-even figure.

        Vectorising the sort did not help either: the cost is the sorting, not the Python
        loop. Retrieval needs the top ``n`` of a catalogue, not a full ranking of it, so
        the fix is to stop sorting the other ``n_items - n``. ``argpartition`` is linear,
        and only the selected ``n`` are then ordered.

        The subtlety is tie-breaking at the partition boundary, which ``argpartition``
        resolves by memory order. Ties are not an edge case here -- a popularity model
        gives whole blocks of items identical scores -- so the boundary group is
        resolved explicitly by ascending index, reproducing the ``(-score, index)`` rule
        exactly. ``tests/test_families.py`` asserts equality against the reference
        lexsort on tie-saturated input.

        Excluded items carry ``-inf``, which negates to ``+inf`` and sorts last.
        """
        n_users, n_items = scores.shape
        negated = -scores
        if n >= n_items:
            order = np.argsort(negated, axis=1, kind="stable")
            return order.astype(np.int64), np.take_along_axis(scores, order, axis=1)

        # The value sitting exactly on the cut. Everything strictly better is in;
        # everything equal to it competes for the remaining slots.
        partitioned = np.argpartition(negated, n - 1, axis=1)
        threshold = np.take_along_axis(negated, partitioned[:, n - 1 : n], axis=1)

        strictly_better = negated < threshold
        tied = negated == threshold

        # Fill the remaining slots from the tied group in ascending index order, which
        # is what the reference rule does. cumsum gives each tie its position within its
        # own row without a Python loop.
        remaining = n - strictly_better.sum(axis=1, keepdims=True)
        tie_position = np.cumsum(tied, axis=1) - 1
        selected = strictly_better | (tied & (tie_position < remaining))

        # Exactly n per row by construction, and np.nonzero yields them row-major with
        # column indices ascending, so the reshape is well defined.
        chosen = np.nonzero(selected)[1].reshape(n_users, n)

        # Order the chosen few. A stable sort keeps the already-ascending indices as the
        # tie-break, which is again the reference rule.
        order = np.argsort(np.take_along_axis(negated, chosen, axis=1), axis=1, kind="stable")
        items = np.take_along_axis(chosen, order, axis=1).astype(np.int64)
        return items, np.take_along_axis(scores, items, axis=1)

    # ---------------------------------------------------------------- bookkeeping

    def _require_fitted(self) -> None:
        if not self._fitted:
            raise RuntimeError(f"{self.name} must be fitted before serving")

    @property
    def model_bytes(self) -> int:
        """Size of the trained model held in memory.

        A serving cost that is not CPU time. A neighbourhood model carrying an item-item
        similarity matrix and a factor model carrying two thin matrices can have similar
        per-request compute and wildly different memory, and memory is what decides how
        many models fit on one machine.
        """
        return sum(self._array_bytes(getattr(self, attr)) for attr in self._model_attrs)

    #: Attributes counted by :attr:`model_bytes`. Declared per subclass so the figure is
    #: an explicit statement about what the model *is*, rather than whatever happened to
    #: be left on the instance.
    _model_attrs: tuple[str, ...] = ()

    @staticmethod
    def _array_bytes(value: object) -> int:
        if value is None:
            return 0
        if sparse.issparse(value):
            return int(value.data.nbytes + value.indices.nbytes + value.indptr.nbytes)
        if isinstance(value, np.ndarray):
            return int(value.nbytes)
        return 0
