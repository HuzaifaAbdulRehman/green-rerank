"""Datasets, as the *pipeline* needs them.

The companion project's loaders return ready-made reranking instances -- a candidate set
per user, already retrieved. That is exactly right when the reranker is the object of
study. Here it is not: retrieval is one of the stages being costed, so handing it a
pre-retrieved candidate set would measure everything except the thing in question.

So this module reuses the companion's *primitives* -- k-core filtering, the leave-one-out
split, the interaction matrix, genre groups, popularity tiers -- and stops short of
retrieval, which the pipeline performs under measurement.

That reuse is deliberate and load-bearing. The two projects must agree exactly on which
interactions survive filtering and which item is held out, or their results are not
comparable and the pair of them says less than either alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy import sparse

from green_rerank.companion import ensure_importable
from green_rerank.families.base import Sequences

MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-100k.zip"
AMAZON_URL = (
    "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_v2/categoryFilesSmall/"
)


@dataclass
class Dataset:
    """Everything a measured pipeline run needs, and nothing already retrieved.

    Attributes:
        name: label for results tables.
        train: ``(n_users, n_items)`` implicit-feedback matrix.
        held_out: ``user_row -> item index`` for the single leave-one-out target. Users
            whose held-out item did not survive filtering are absent.
        groups: one group index per catalogue item -- genres on MovieLens, popularity
            tiers on Amazon. Carried because the rerank stage optimises against them.
        sequences: time-ordered interactions, for the sequential families.
        item_ids: raw catalogue ids, positionally aligned with the matrix columns.
        stats: dataset shape, for the report's dataset table.
    """

    name: str
    train: sparse.csr_matrix
    held_out: dict[int, int]
    groups: np.ndarray
    sequences: Sequences
    item_ids: list[str]
    stats: dict = field(default_factory=dict)

    @property
    def n_users(self) -> int:
        return int(self.train.shape[0])

    @property
    def n_items(self) -> int:
        return int(self.train.shape[1])

    def eval_users(self, n_users: int | None = None, seed: int = 0) -> np.ndarray:
        """A reproducible sample of users that actually have a held-out item.

        Sampling only from users with a target avoids a silent dilution: including users
        with nothing to predict would drag every accuracy metric toward zero by an amount
        that depends on the sample, not on the model.
        """
        eligible = np.array(sorted(self.held_out), dtype=np.int64)
        if n_users is None or n_users >= eligible.size:
            return eligible
        rng = np.random.default_rng(seed)
        chosen = rng.choice(eligible.size, size=n_users, replace=False)
        return eligible[np.sort(chosen)]

    def relevant_items(self, user_rows: np.ndarray) -> list[set[int]]:
        """Held-out item per user, as the metric functions expect."""
        return [
            {self.held_out[int(row)]} if int(row) in self.held_out else set()
            for row in user_rows
        ]


def _companion_primitives():
    """Import the shared preprocessing, deferred so tests can run without a checkout."""
    ensure_importable()
    from benchmarks.loader import (
        interaction_matrix,
        k_core,
        leave_one_out,
        popularity_tiers,
    )

    return k_core, leave_one_out, interaction_matrix, popularity_tiers


def _assemble(
    name: str,
    raw,
    groups_fn,
    min_interactions: int,
    n_groups: int,
    binary: bool,
    max_sequence: int,
) -> Dataset:
    """Shared path from a ratings frame to a :class:`Dataset`.

    Kept common between MovieLens and Amazon on purpose: if a difference in results
    between the two datasets could be caused by a difference in preprocessing, the
    comparison across catalogues means nothing.
    """
    k_core, leave_one_out, interaction_matrix, _ = _companion_primitives()

    filtered = k_core(raw, min_interactions=min_interactions)
    train_frame, test_frame = leave_one_out(filtered)
    matrix, user_index, item_ids = interaction_matrix(train_frame, binary=binary)

    item_index = {item: position for position, item in enumerate(item_ids)}
    held_out = {
        user_index[row.user_id]: item_index[row.item_id]
        for row in test_frame.itertuples()
        if row.item_id in item_index and row.user_id in user_index
    }

    sequences = Sequences.from_frame(
        train_frame, user_index, item_index, max_length=max_sequence
    )
    groups = groups_fn(matrix, item_ids, n_groups)

    return Dataset(
        name=name,
        train=matrix,
        held_out=held_out,
        groups=groups,
        sequences=sequences,
        item_ids=list(item_ids),
        stats={
            "raw_interactions": len(raw),
            "core_interactions": len(filtered),
            "users": int(matrix.shape[0]),
            "items": int(matrix.shape[1]),
            "density": float(matrix.nnz / (matrix.shape[0] * matrix.shape[1])),
            "users_with_target": len(held_out),
            "n_groups": int(n_groups),
        },
    )


def _popularity_group_fn(matrix, item_ids, n_groups):
    _, _, _, popularity_tiers = _companion_primitives()
    popularity = np.asarray(matrix.sum(axis=0), dtype=float).ravel()
    return popularity_tiers(popularity, n_tiers=n_groups)


def load_movielens(
    path: str | Path = "data/ml100k/ml-100k",
    min_interactions: int = 5,
    n_groups: int = 4,
    binary: bool = True,
    max_sequence: int = 200,
) -> Dataset:
    """MovieLens 100K, with curator-assigned **genres** as the groups.

    Genres rather than popularity tiers matters for the rerank stage: a popularity
    partition is derived from the same interaction counts being evaluated, so a fairness
    result on it can always be argued to be structural. Genres are assigned
    independently of the data.
    """
    ensure_importable()
    from benchmarks.movielens import genre_groups, load_genres
    from benchmarks.movielens import load_ratings as load_ml_ratings

    path = Path(path)
    if not (path / "u.data").exists():
        raise FileNotFoundError(
            f"{path}/u.data not found. Download and unzip:\n"
            f"    curl -o ml-100k.zip {MOVIELENS_URL}\n"
            f"    unzip ml-100k.zip -d data/ml100k"
        )

    genres = load_genres(path)

    def groups_fn(matrix, item_ids, n_groups):
        return genre_groups(genres, list(item_ids), n_groups)

    return _assemble(
        "movielens100k",
        load_ml_ratings(path),
        groups_fn,
        min_interactions,
        n_groups,
        binary,
        max_sequence,
    )


def load_amazon(
    path: str | Path,
    name: str | None = None,
    min_interactions: int = 5,
    n_groups: int = 4,
    binary: bool = True,
    max_sequence: int = 200,
) -> Dataset:
    """An Amazon ratings-only export, with **popularity tiers** as the groups.

    The ratings export carries no product metadata, so the partition is the standard
    short-head/long-tail one. It makes the rerank stage fight the exact bias the
    retrieval model exhibits, rather than a partition chosen to flatter it.
    """
    ensure_importable()
    from benchmarks.loader import load_ratings

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. The McAuley ratings files live under:\n    {AMAZON_URL}"
        )
    return _assemble(
        name or path.stem.lower(),
        load_ratings(path),
        _popularity_group_fn,
        min_interactions,
        n_groups,
        binary,
        max_sequence,
    )


def synthetic(
    n_users: int = 120,
    n_items: int = 60,
    blocks: int = 4,
    per_user: int = 8,
    seed: int = 0,
) -> Dataset:
    """A block-structured dataset with a known answer, needing no download.

    Exists so the whole pipeline -- measurement, families, reranking, scoring -- can be
    exercised in CI, where no dataset is available. A harness whose end-to-end path only
    runs on a machine with the data downloaded is a harness whose end-to-end path is
    effectively untested.
    """
    rng = np.random.default_rng(seed)
    per_block = n_items // blocks

    rows: list[int] = []
    cols: list[int] = []
    sequences: dict[int, list[int]] = {}
    held_out: dict[int, int] = {}

    for user in range(n_users):
        block = user % blocks
        low, high = block * per_block, (block + 1) * per_block
        picked = rng.choice(np.arange(low, high), size=min(per_user, per_block), replace=False)
        # The last item of each user's block is held out, so the target is always
        # something a model that learned the block structure could have found.
        target, history = int(picked[-1]), [int(i) for i in picked[:-1]]
        rows.extend([user] * len(history))
        cols.extend(history)
        sequences[user] = history
        held_out[user] = target

    matrix = sparse.csr_matrix(
        (np.ones(len(rows)), (rows, cols)), shape=(n_users, n_items)
    )
    groups = np.repeat(np.arange(blocks), per_block)[:n_items]

    return Dataset(
        name="synthetic",
        train=matrix,
        held_out=held_out,
        groups=groups,
        sequences=Sequences(by_user=sequences, max_length=50),
        item_ids=[str(i) for i in range(n_items)],
        stats={
            "raw_interactions": len(rows),
            "core_interactions": len(rows),
            "users": n_users,
            "items": n_items,
            "density": float(matrix.nnz / (n_users * n_items)),
            "users_with_target": len(held_out),
            "n_groups": blocks,
        },
    )
