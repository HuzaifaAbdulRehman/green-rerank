"""Run one pipeline end to end, costing each stage separately.

The order of operations here is the experiment's design, not an implementation detail:

1. ``TRAIN`` -- measured, paid once.
2. ``RERANK_SETUP`` -- measured, paid once, and only when a reranker is used.
3. ``RETRIEVE`` -- measured, paid per request.
4. ``RERANK`` -- measured, paid per request.
5. scoring -- **not measured**, and deliberately last.

Step 5 is the one that is easy to get wrong and expensive to get wrong. Intra-list
similarity alone is O(k^2) per user in pure Python. Inside the window it would be noise
against a neural training run and the *majority* of the reading against popularity's
retrieve stage -- so it would not merely add error, it would add error concentrated
exactly where the comparison between families is decided.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy import sparse

from green_rerank.companion import ensure_importable
from green_rerank.data import Dataset
from green_rerank.families.base import Family, Recommendations
from green_rerank.measure import MeasurementSession, Reading
from green_rerank.pipeline.rerankers import build_reranker, is_time_bounded
from green_rerank.pipeline.stages import Amortisation, Stage


@dataclass
class PipelineResult:
    """One family, on one dataset, costed by stage and scored afterwards."""

    dataset: str
    family: str
    reranker: str | None
    n_users: int
    n_candidates: int
    k: int
    readings: list[Reading]
    final_items: np.ndarray
    metrics: dict[str, float] = field(default_factory=dict)

    #: Per-user metric vectors, aligned with :attr:`user_rows`. Carried so that accuracy
    #: differences can be tested on the *same users* rather than compared as means.
    per_user: dict[str, np.ndarray] = field(default_factory=dict)

    #: The users served, in the order every per-user vector uses. Without this the
    #: vectors cannot be paired across two runs, and pairing the wrong users together
    #: would produce a difference distribution that looks entirely normal.
    user_rows: np.ndarray | None = None

    notes: dict[str, Any] = field(default_factory=dict)

    #: Default cost field. ``cpu_seconds_each`` rather than ``cpu_seconds`` because
    #: cheap stages are measured by repetition to clear the clock quantum, and the raw
    #: total would then be the cost of however many repetitions happened to be needed.
    COST_ATTR = "cpu_seconds_each"

    def cost(self, stage: Stage, attr: str = COST_ATTR) -> float:
        """Cost of one stage, or 0.0 if the stage did not run."""
        return float(
            sum(getattr(r, attr) for r in self.readings if r.stage == stage.label)
        )

    def once_cost(self, attr: str = COST_ATTR) -> float:
        """Cost paid at deployment regardless of traffic."""
        return float(
            sum(
                getattr(r, attr)
                for r in self.readings
                if Stage.from_label(r.stage).amortisation is Amortisation.ONCE
            )
        )

    def below_quantum_stages(self) -> list[str]:
        """Stages whose reading could not be grown above the clock's quantum.

        Reported rather than hidden: such a reading is a tick count, and any conclusion
        resting on it is resting on the scheduler's accounting granularity.
        """
        return [r.stage for r in self.readings if r.meta.get("below_quantum")]

    def per_request_cost(self, attr: str = COST_ATTR) -> float:
        """Cost of serving **one** request.

        The measured per-request stages divided by the number of users actually served.
        Dividing here rather than at the call site means the request count and the cost
        can never drift apart in a results table.
        """
        if self.n_users <= 0:
            return 0.0
        served = sum(
            getattr(r, attr)
            for r in self.readings
            if Stage.from_label(r.stage).amortisation is Amortisation.PER_REQUEST
        )
        return float(served / self.n_users)

    def total_cost(self, n_requests: int, attr: str = COST_ATTR) -> float:
        """``E_once + N * E_per_request`` -- the whole point of the stage split."""
        return self.once_cost(attr) + n_requests * self.per_request_cost(attr)

    def as_row(self) -> dict[str, Any]:
        row: dict[str, Any] = {
            "dataset": self.dataset,
            "family": self.family,
            "reranker": self.reranker or "none",
            "n_users": self.n_users,
            "n_candidates": self.n_candidates,
            "k": self.k,
        }
        for stage in Stage:
            row[f"cpu_{stage.label}"] = self.cost(stage)
            row[f"wall_{stage.label}"] = self.cost(stage, "wall_seconds")
        row["cpu_once"] = self.once_cost()
        row["cpu_per_request"] = self.per_request_cost()
        row.update(self.metrics)
        row.update({f"note.{k}": v for k, v in self.notes.items()})
        return row


def _candidate_similarity(similarity, candidates: np.ndarray) -> np.ndarray:
    """The dense candidate-by-candidate block the reranker needs."""
    if sparse.issparse(similarity):
        return np.asarray(similarity[candidates][:, candidates].todense(), dtype=float)
    return similarity[np.ix_(candidates, candidates)]


def _normalise(scores: np.ndarray) -> np.ndarray:
    """Rescale candidate scores to [0, 1].

    The reranker's diversity and fairness weights are defined against a similarity
    matrix already bounded in [0, 1]. Feeding it raw scores -- whose scale differs by
    orders of magnitude between a popularity count and a factor dot product -- would
    silently mean a different objective for every family, so the comparison would be of
    operating points rather than of families.
    """
    if not np.isfinite(scores).all():
        # Raised rather than patched. A non-finite score here means the candidate set
        # contains items the user has already seen -- they carry -inf from the exclusion
        # mask -- and the arithmetic below would turn that into NaN silently:
        # -inf minus -inf is NaN, so the reranker would receive a relevance vector of
        # NaNs, rank on them, and return a list that looks entirely ordinary while
        # possibly containing items the user has already interacted with.
        #
        # The condition is prevented upstream by capping the candidate set to the items
        # a user could actually be shown. This is the assertion that the cap holds.
        raise ValueError(
            "candidate scores contain non-finite values, which means the candidate set "
            "includes items excluded as already-seen. Reduce n_candidates: the "
            "catalogue is too small for the requested retrieval depth."
        )
    span = scores.max() - scores.min()
    if span <= 0:
        return np.ones_like(scores)
    return (scores - scores.min()) / span


def run_pipeline(
    dataset: Dataset,
    family: Family,
    *,
    reranker: str | None = None,
    n_candidates: int = 200,
    k: int = 10,
    n_users: int | None = 200,
    seed: int = 0,
    session: MeasurementSession | None = None,
    lam: float = 0.0,
    mu: float = 1.0,
    reranker_kwargs: dict[str, Any] | None = None,
) -> PipelineResult:
    """Train, retrieve, optionally rerank, then score -- costing each stage.

    Args:
        dataset: the catalogue and its leave-one-out targets.
        family: an unfitted model family.
        reranker: name of a companion reranker, or ``None`` to take the top-k of
            retrieval directly.
        n_candidates: retrieval depth, the reranker's problem size.
        k: final list length.
        n_users: how many users to serve; ``None`` serves everyone with a target.
        seed: user-sample seed.
        session: an existing measurement session, so several runs share one energy
            backend and one preflight record.
        lam: reranker diversity weight.
        mu: reranker fairness weight.
        reranker_kwargs: overrides for the reranker's own constructor.

    Returns:
        A :class:`PipelineResult` whose metrics were computed **after** every window
        closed.
    """
    session = session or MeasurementSession(label=family.name)
    # Where this run's readings begin. A session is meant to be shared across a sweep so
    # that one energy backend and one preflight record cover the whole batch -- but that
    # makes `session.readings` cumulative, and taking all of it would fold every earlier
    # family's training cost into this result. The totals would climb monotonically
    # through a sweep with every individual number still looking entirely reasonable.
    first_reading = len(session.readings)
    user_rows = dataset.eval_users(n_users, seed=seed)
    if user_rows.size == 0:
        raise ValueError(f"{dataset.name} has no users with a held-out item")

    # Cap retrieval depth at what every served user can actually be shown.
    #
    # Seen items are excluded by scoring them -inf, so a user with 5 interactions in a
    # 147-item catalogue has only 142 candidates that mean anything. Asking for more
    # does not fail: it returns those 142 plus some -inf entries, which are items the
    # user has already interacted with. Downstream that is a NaN in the reranker's
    # relevance vector at best, and a seen item in the final recommendation list at
    # worst -- the leakage this pipeline exists to avoid, arriving through the back door
    # on the smallest catalogues.
    #
    # The minimum across served users, not the mean: the cap has to hold for every user
    # in the batch, and the heaviest user is the binding one.
    seen_counts = np.diff(dataset.train.indptr)[user_rows]
    usable = int(dataset.n_items - seen_counts.max())
    requested = n_candidates
    n_candidates = min(n_candidates, dataset.n_items, usable)

    if k > n_candidates:
        raise ValueError(
            f"k={k} exceeds the candidate set size {n_candidates}"
            + (
                f" (requested {requested}, capped at {usable} by the busiest user's "
                f"history in a {dataset.n_items}-item catalogue)"
                if n_candidates < requested
                else ""
            )
        )

    # ------------------------------------------------------------------ 1. train
    session.measure_repeated(
        Stage.TRAIN.label,
        family.name,
        family.fit,
        dataset.train,
        dataset.sequences if family.needs_sequences else None,
    )

    # -------------------------------------------------- 2. reranker setup (once)
    similarity = None
    if reranker is not None:
        ensure_importable()
        from benchmarks.loader import cosine_similarity, cosine_similarity_sparse

        def build_similarity():
            # The reranker needs item-item similarity, and it must be the *same*
            # similarity for every family -- otherwise the rerank stage would be
            # solving a different problem per family and its cost would not be
            # comparable across them.
            dense_bytes = dataset.n_items * dataset.n_items * 8
            if dense_bytes > 256_000_000:
                return cosine_similarity_sparse(dataset.train)
            return cosine_similarity(dataset.train)

        similarity, _ = session.measure_repeated(
            Stage.RERANK_SETUP.label, family.name, build_similarity
        )

    # --------------------------------------------------------------- 3. retrieve
    # Measured in two halves. Selection is shared by every family and dominates the
    # total, so a single retrieve figure would compress the families toward each other
    # and attribute most of their serving cost to code none of them owns.
    scores, _ = session.measure_repeated(
        Stage.RETRIEVE_SCORE.label,
        family.name,
        family.score_users,
        dataset.train,
        user_rows,
    )
    recommendations, _ = session.measure_repeated(
        Stage.RETRIEVE_SELECT.label,
        family.name,
        family.select,
        scores,
        user_rows,
        n_candidates,
    )

    # ----------------------------------------------------------------- 4. rerank
    if reranker is None:
        final_items = recommendations.items[:, :k]
        selections = [list(range(k)) for _ in range(len(user_rows))]
    else:
        final_items, selections = _run_rerank(
            session=session,
            dataset=dataset,
            family=family,
            recommendations=recommendations,
            similarity=similarity,
            reranker=reranker,
            reranker_kwargs=reranker_kwargs or {},
            k=k,
            lam=lam,
            mu=mu,
        )

    # ------------------------------------------------- 5. score, outside the window
    metrics, per_user = score(
        dataset=dataset,
        recommendations=recommendations,
        selections=selections,
        final_items=final_items,
        similarity=similarity,
        k=k,
    )

    notes: dict[str, Any] = {"seed": seed, "lam": lam, "mu": mu}
    if n_candidates < requested:
        # Carried on the row, because a reranker's cost scales with its problem size:
        # a run that silently retrieved 142 candidates instead of 200 is not comparable
        # to one that got all 200, and nothing else in the output would reveal it.
        notes["n_candidates_requested"] = requested
        notes["n_candidates_capped_by"] = "user history in a small catalogue"
    if reranker is not None and is_time_bounded(reranker):
        # Recorded on the row itself, not only in prose: this reranker stops on
        # wall-clock, so its quality is hardware-dependent and its cost is not
        # comparable to a work-bounded method's on the time axis.
        notes["time_bounded_reranker"] = True

    return PipelineResult(
        dataset=dataset.name,
        family=family.name,
        reranker=reranker,
        n_users=int(user_rows.size),
        n_candidates=int(n_candidates),
        k=int(k),
        readings=list(session.readings[first_reading:]),
        final_items=final_items,
        metrics=metrics,
        per_user=per_user,
        user_rows=user_rows,
        notes=notes,
    )


def _run_rerank(
    *,
    session: MeasurementSession,
    dataset: Dataset,
    family: Family,
    recommendations: Recommendations,
    similarity,
    reranker: str,
    reranker_kwargs: dict[str, Any],
    k: int,
    lam: float,
    mu: float,
) -> tuple[np.ndarray, list[list[int]]]:
    """Rerank every user's candidate set, measured as one per-request window.

    Instance construction is inside the window on purpose. Extracting the candidate
    similarity block is real work a deployment would have to do, and excluding it would
    understate reranking exactly the way excluding the tracker's probe overstated it in
    the companion project.
    """
    ensure_importable()
    from qubo_rerank.problem import RerankInstance

    solver = build_reranker(reranker, **reranker_kwargs)
    instances: list[RerankInstance] = []

    def rerank_all() -> list[list[int]]:
        chosen: list[list[int]] = []
        for position in range(recommendations.items.shape[0]):
            candidates = recommendations.items[position]
            instance = RerankInstance(
                relevance=_normalise(recommendations.scores[position]),
                similarity=_candidate_similarity(similarity, candidates),
                k=k,
                groups=dataset.groups[candidates],
                lam=lam,
                mu=mu,
                item_ids=[int(c) for c in candidates],
            )
            instances.append(instance)
            chosen.append(list(solver.solve(instance).selection))
        return chosen

    selections, _ = session.measure_repeated(Stage.RERANK.label, family.name, rerank_all)

    # Presented in descending relevance. A reranker selects a *set* and says nothing
    # about display order; scoring the raw output would charge it for an ordering it
    # never claimed to produce -- worth up to 0.09 NDCG in the companion project, larger
    # than several of the differences being reported.
    ordered: list[list[int]] = []
    final = np.empty((len(selections), k), dtype=np.int64)
    for position, selection in enumerate(selections):
        scores = recommendations.scores[position]
        by_relevance = sorted(selection, key=lambda i: -scores[i])
        ordered.append(by_relevance)
        final[position] = recommendations.items[position][by_relevance]

    return final, ordered


def score(
    *,
    dataset: Dataset,
    recommendations: Recommendations,
    selections: list[list[int]],
    final_items: np.ndarray,
    similarity,
    k: int,
) -> dict[str, float]:
    """Quality metrics, computed strictly outside every measured window.

    Every metric is imported from the companion project. A second implementation that
    disagreed with the first is the precise failure this pair of projects is built to be
    above, and it would be invisible: both would return plausible numbers.
    """
    ensure_importable()
    from qubo_rerank.metrics import (
        catalogue_coverage,
        exposure_parity,
        gini,
        intra_list_similarity,
        item_exposure,
        ndcg_at_k,
        recall_at_k,
    )
    from qubo_rerank.metrics.relevance import dcg

    relevant = dataset.relevant_items(recommendations.user_rows)

    ndcg_truth: list[float] = []
    ndcg_retrieval: list[float] = []
    recall: list[float] = []
    parity: list[float] = []
    ils: list[float] = []
    hits = 0

    for position, selection in enumerate(selections):
        candidate_scores = recommendations.scores[position]
        candidates = recommendations.items[position]

        # Two different NDCGs, and conflating them is a real trap.
        #
        # `ndcg_vs_retrieval` grades the list against the retrieval model's *own*
        # scores, so taking the top-k of retrieval scores exactly 1.0 by construction.
        # That makes it the right measure of what reranking *costs* in relevance -- and
        # useless for comparing families, because every family is graded against itself.
        # The first smoke test of this pipeline returned 1.000 for all three families,
        # which is the metric working correctly and answering the wrong question.
        ndcg_retrieval.append(ndcg_at_k(candidate_scores, selection, k))

        # Ground truth arrives as catalogue ids; the metrics work in candidate-set
        # index space, so the target has to be located within the candidate set. A
        # target that retrieval never surfaced is simply not there -- which is the
        # ceiling on recall, reported below rather than hidden.
        targets = relevant[position]
        found = {int(i) for i, item in enumerate(candidates) if int(item) in targets}
        hits += 1 if found else 0
        recall.append(recall_at_k(selection, found, k))

        # `ndcg` grades against the genuinely held-out interaction, so it is comparable
        # across families and is the accuracy axis the efficiency frontier is drawn on.
        # Under leave-one-out there is at most one relevant item, so the ideal ranking
        # puts it first and the ideal DCG is dcg([1.0]).
        gains = [1.0 if index in found else 0.0 for index in list(selection)[:k]]
        ideal = dcg([1.0]) if found else 0.0
        ndcg_truth.append(dcg(gains) / ideal if ideal > 0 else 0.0)

        parity.append(exposure_parity(dataset.groups[candidates], selection))
        if similarity is not None:
            ils.append(
                intra_list_similarity(_candidate_similarity(similarity, candidates), selection)
            )

    catalogue_lists = [[int(i) for i in row] for row in final_items]
    exposure = item_exposure(catalogue_lists, dataset.n_items)

    metrics = {
        "ndcg": float(np.mean(ndcg_truth)),
        "ndcg_vs_retrieval": float(np.mean(ndcg_retrieval)),
        "recall": float(np.mean(recall)),
        "exposure_parity": float(np.mean(parity)),
        "catalogue_coverage": float(catalogue_coverage(catalogue_lists, dataset.n_items)),
        "gini": float(gini(exposure)),
        # The ceiling on recall: reranking cannot recover an item retrieval never
        # surfaced, so recall must be read against this and not against 1.0.
        "candidate_hit_rate": float(hits / max(len(selections), 1)),
    }
    if ils:
        metrics["intra_list_similarity"] = float(np.mean(ils))

    # Kept alongside the means, because a mean cannot be tested.
    #
    # Two families' NDCG differing by 0.01 says nothing on its own: the question is
    # whether it differs *per user*, on the same users, more often than not. That is a
    # paired comparison and it needs the vector, which the mean has already discarded.
    # Cost figures in this project carry bootstrap intervals; reporting accuracy as a
    # bare mean beside them would apply two different standards of evidence within one
    # table.
    #
    # `catalogue_coverage` and `gini` are deliberately absent: they are properties of
    # the whole set of recommendation lists, not of any one user, so there is no
    # per-user value to pair and averaging one into existence would invent data.
    per_user: dict[str, np.ndarray] = {
        "ndcg": np.asarray(ndcg_truth, dtype=float),
        "ndcg_vs_retrieval": np.asarray(ndcg_retrieval, dtype=float),
        "recall": np.asarray(recall, dtype=float),
        "exposure_parity": np.asarray(parity, dtype=float),
    }
    if ils:
        per_user["intra_list_similarity"] = np.asarray(ils, dtype=float)

    return metrics, per_user
