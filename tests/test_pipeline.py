"""Invariants for the staged pipeline and its cost arithmetic.

The arithmetic tests matter more than they look. ``E_once + N * E_per_request`` is the
project's headline claim, and every part of it is a place where a stage could be counted
twice, counted in the wrong bucket, or divided by the wrong request count -- none of
which would make a results table look wrong.
"""

from __future__ import annotations

import numpy as np
import pytest

from green_rerank.data import synthetic
from green_rerank.families import build
from green_rerank.measure import MeasurementSession, Reading
from green_rerank.pipeline import (
    ONCE_STAGES,
    PER_REQUEST_STAGES,
    Amortisation,
    PipelineResult,
    Stage,
    run_pipeline,
)
from green_rerank.pipeline.rerankers import KNOWN, build_reranker, is_time_bounded

# --------------------------------------------------------------------------- stages


class TestStages:
    def test_every_stage_is_classified(self):
        # A stage with no amortisation class could not be placed in the break-even
        # model at all, and would silently vanish from the totals.
        assert set(ONCE_STAGES) | set(PER_REQUEST_STAGES) == set(Stage)
        assert not set(ONCE_STAGES) & set(PER_REQUEST_STAGES)

    def test_training_is_paid_once_and_retrieval_per_request(self):
        assert Stage.TRAIN.amortisation is Amortisation.ONCE
        assert Stage.RERANK_SETUP.amortisation is Amortisation.ONCE
        assert Stage.RETRIEVE_SCORE.amortisation is Amortisation.PER_REQUEST
        assert Stage.RETRIEVE_SELECT.amortisation is Amortisation.PER_REQUEST
        assert Stage.RERANK.amortisation is Amortisation.PER_REQUEST

    def test_there_is_no_scoring_stage(self):
        """Scoring must not be measurable even by accident.

        Metric computation is O(k^2) per user in Python. Having no enum member for it
        means no call site can pass it to a measured window.
        """
        assert "score" not in {stage.label for stage in Stage}

    def test_labels_round_trip(self):
        for stage in Stage:
            assert Stage.from_label(stage.label) is stage
        with pytest.raises(KeyError):
            Stage.from_label("nonsense")


# ------------------------------------------------------------------ cost arithmetic


def _reading(stage: Stage, cpu: float, repeats: int = 1) -> Reading:
    return Reading(
        stage=stage.label,
        label="x",
        wall_seconds=cpu,
        cpu_seconds=cpu,
        repeats=repeats,
    )


def _result(**overrides) -> PipelineResult:
    defaults = dict(
        dataset="synthetic",
        family="x",
        reranker=None,
        n_users=10,
        n_candidates=20,
        k=5,
        readings=[
            _reading(Stage.TRAIN, 100.0),
            _reading(Stage.RETRIEVE_SCORE, 10.0),
        ],
        final_items=np.zeros((10, 5), dtype=np.int64),
    )
    defaults.update(overrides)
    return PipelineResult(**defaults)


class TestCostArithmetic:
    def test_once_and_per_request_are_separated(self):
        result = _result()
        assert result.once_cost() == 100.0
        # 10 CPU-seconds of retrieval spread over 10 users.
        assert result.per_request_cost() == pytest.approx(1.0)

    def test_total_is_linear_in_request_count(self):
        result = _result()
        assert result.total_cost(0) == pytest.approx(100.0)
        assert result.total_cost(50) == pytest.approx(150.0)

    def test_repeated_measurement_is_divided_out(self):
        """A stage measured 200 times must not report 200x its cost.

        Cheap stages are repeated to clear the clock quantum. If the raw total leaked
        into the cost, a *cheaper* stage would look more expensive purely because it
        needed more repetitions -- an exactly inverted result.
        """
        result = _result(readings=[_reading(Stage.TRAIN, 20.0, repeats=200)])
        assert result.once_cost() == pytest.approx(0.1)

    def test_zero_users_does_not_divide_by_zero(self):
        result = _result(n_users=0)
        assert result.per_request_cost() == 0.0

    def test_missing_stage_costs_nothing_rather_than_raising(self):
        # A run with no reranker has no rerank readings at all; asking for its cost is
        # legitimate and must answer zero.
        assert _result().cost(Stage.RERANK) == 0.0

    def test_below_quantum_stages_are_reported(self):
        reading = _reading(Stage.RETRIEVE_SCORE, 0.001)
        reading.meta["below_quantum"] = True
        result = _result(readings=[reading])
        assert result.below_quantum_stages() == [Stage.RETRIEVE_SCORE.label]

    def test_crossover_can_be_computed_from_two_results(self):
        """The break-even claim, in its smallest form.

        Cheap to train and expensive to serve, against the opposite. They must cross,
        and at the analytically correct place: (100-10)/(5-1) = 22.5 requests.
        """
        knn = _result(
            family="itemknn",
            readings=[_reading(Stage.TRAIN, 10.0), _reading(Stage.RETRIEVE_SCORE, 50.0)],
        )
        als = _result(
            family="als",
            readings=[_reading(Stage.TRAIN, 100.0), _reading(Stage.RETRIEVE_SCORE, 10.0)],
        )
        assert knn.per_request_cost() == pytest.approx(5.0)
        assert als.per_request_cost() == pytest.approx(1.0)
        assert knn.total_cost(10) < als.total_cost(10)
        assert knn.total_cost(30) > als.total_cost(30)


# ------------------------------------------------------------------------ rerankers


@pytest.mark.needs_companion
class TestRerankers:
    def test_every_reranker_builds_under_its_own_name(self):
        """Also documents a design assumption this test disproved.

        The mapping originally named submodules rather than the ``solvers`` package so
        that the three pure-numpy rerankers could run without the D-Wave stack. Python
        executes a package's ``__init__`` when importing any submodule of it, and that
        ``__init__`` imports ``neal`` -- so the dependency is required for *all* of them.
        It is now declared that way instead of being wished away.
        """
        for name in ("greedy_topk", "mmr", "quota_mmr"):
            assert build_reranker(name).name == name

    def test_unknown_reranker_lists_the_known_ones(self):
        with pytest.raises(KeyError, match="unknown reranker"):
            build_reranker("nope")

    def test_time_bounded_rerankers_are_flagged(self):
        # qubo_tabu stops on wall-clock, so its quality is hardware-dependent. In a cost
        # study that inverts the usual relationship and has to travel with the row.
        assert is_time_bounded("qubo_tabu")
        assert not is_time_bounded("mmr")
        assert set(KNOWN) >= {"greedy_topk", "mmr", "quota_mmr"}


# --------------------------------------------------------------------- the full run


@pytest.fixture(scope="module")
def dataset():
    return synthetic(n_users=60, n_items=40, blocks=4, seed=0)


@pytest.mark.needs_companion
class TestEndToEnd:
    def test_runs_and_costs_every_stage(self, dataset):
        result = run_pipeline(
            dataset, build("popularity"), n_candidates=20, k=5, n_users=20
        )
        assert result.final_items.shape == (20, 5)
        assert result.cost(Stage.TRAIN) > 0
        assert result.cost(Stage.RETRIEVE_SCORE) > 0
        # Selection is shared by every family and is costed separately, because it turned
        # out to dominate retrieval for all of them -- 99.9 % of it for popularity.
        assert result.cost(Stage.RETRIEVE_SELECT) > 0
        # No reranker was requested, so those stages must be absent rather than zero-ish.
        assert result.cost(Stage.RERANK) == 0.0
        assert result.cost(Stage.RERANK_SETUP) == 0.0

    def test_final_items_never_include_a_seen_item(self, dataset):
        """End-to-end leakage check, after retrieval *and* ordering.

        The family-level test covers the model. This covers the pipeline: an indexing
        slip when mapping candidate-set positions back to catalogue ids would
        reintroduce seen items with everything still looking well-formed.
        """
        result = run_pipeline(dataset, build("itemknn"), n_candidates=20, k=5, n_users=20)
        rows = dataset.eval_users(20, seed=0)
        for position, row in enumerate(rows):
            seen = set(dataset.train[row].indices.tolist())
            assert not seen & set(result.final_items[position].tolist())

    def test_ndcg_against_retrieval_is_one_without_a_reranker(self, dataset):
        """Documents the trap this metric represents.

        Graded against the retrieval model's own scores, taking the top-k of retrieval
        is optimal by construction. The first smoke test of this pipeline reported
        1.000 for all three families -- the metric working correctly and answering a
        question nobody asked. It is kept because it measures what reranking *costs*.
        """
        result = run_pipeline(dataset, build("popularity"), n_candidates=20, k=5, n_users=20)
        assert result.metrics["ndcg_vs_retrieval"] == pytest.approx(1.0)

    def test_ground_truth_ndcg_discriminates_between_families(self, dataset):
        """The accuracy axis the frontier is drawn on has to separate the families.

        On block-structured data a neighbourhood model must beat recommending the
        globally most popular items to everyone. If this ties, the accuracy axis is not
        measuring anything and the frontier is a cost plot with a decorative y-axis.
        """
        popular = run_pipeline(dataset, build("popularity"), n_candidates=20, k=5, n_users=40)
        knn = run_pipeline(dataset, build("itemknn"), n_candidates=20, k=5, n_users=40)
        assert knn.metrics["ndcg"] > popular.metrics["ndcg"]

    def test_recall_is_reported_with_its_ceiling(self, dataset):
        # Reranking cannot recover an item retrieval never surfaced, so recall is
        # uninterpretable without the candidate hit rate next to it.
        result = run_pipeline(dataset, build("itemknn"), n_candidates=20, k=5, n_users=20)
        assert "candidate_hit_rate" in result.metrics
        assert result.metrics["recall"] <= result.metrics["candidate_hit_rate"] + 1e-9

    def test_reranking_adds_its_stages_and_costs_them(self, dataset):
        result = run_pipeline(
            dataset,
            build("itemknn"),
            reranker="quota_mmr",
            n_candidates=20,
            k=5,
            n_users=20,
        )
        assert result.cost(Stage.RERANK) > 0
        assert result.cost(Stage.RERANK_SETUP) > 0
        assert result.reranker == "quota_mmr"

    def test_reranking_improves_exposure_parity(self, dataset):
        """A sanity check on the rerank stage being wired up at all.

        A quota reranker exists to spread exposure across groups. If parity does not
        improve, the stage is being measured but is not doing its job -- the cost would
        be real and the benefit imaginary.
        """
        plain = run_pipeline(dataset, build("itemknn"), n_candidates=20, k=5, n_users=40)
        quota = run_pipeline(
            dataset, build("itemknn"), reranker="quota_mmr", n_candidates=20, k=5, n_users=40
        )
        assert quota.metrics["exposure_parity"] <= plain.metrics["exposure_parity"]

    def test_k_larger_than_the_candidate_set_is_refused(self, dataset):
        with pytest.raises(ValueError, match="exceeds the candidate set"):
            run_pipeline(dataset, build("popularity"), n_candidates=5, k=10, n_users=5)

    def test_a_shared_session_does_not_leak_readings_between_runs(self, dataset):
        """The bug this guards against inflates a sweep and looks fine doing it.

        Sessions are shared across a sweep so one energy backend and one preflight
        record cover the batch. That makes ``session.readings`` cumulative, so a result
        built from all of it absorbs every earlier family's training cost -- totals
        climbing monotonically down the results table with each row still plausible on
        its own. Popularity trains in microseconds; if its ``once_cost`` carries
        ItemKNN's training it will be off by four orders of magnitude.
        """
        session = MeasurementSession(label="shared")
        knn = run_pipeline(
            dataset, build("itemknn"), n_candidates=20, k=5, n_users=20, session=session
        )
        popular = run_pipeline(
            dataset, build("popularity"), n_candidates=20, k=5, n_users=20, session=session
        )

        assert {r.label for r in popular.readings} == {"popularity"}
        assert popular.once_cost() < knn.once_cost()

        alone = run_pipeline(dataset, build("popularity"), n_candidates=20, k=5, n_users=20)
        assert len(popular.readings) == len(alone.readings)

    def test_row_export_carries_costs_and_metrics(self, dataset):
        result = run_pipeline(dataset, build("popularity"), n_candidates=20, k=5, n_users=20)
        row = result.as_row()
        assert row["family"] == "popularity"
        assert row["cpu_once"] > 0
        assert "ndcg" in row and "cpu_train" in row


# ------------------------------------------------------------------------- datasets


class TestSyntheticDataset:
    def test_held_out_item_is_not_in_the_training_matrix(self, dataset):
        """Otherwise the target is trivially predictable and every metric is inflated.

        This is the leakage that invalidates a whole results table while leaving every
        number in it looking plausible.
        """
        for row, target in dataset.held_out.items():
            assert target not in set(dataset.train[row].indices.tolist())

    def test_every_user_has_a_target(self, dataset):
        assert len(dataset.held_out) == dataset.n_users

    def test_eval_users_is_reproducible_and_bounded(self, dataset):
        first = dataset.eval_users(10, seed=3)
        second = dataset.eval_users(10, seed=3)
        assert np.array_equal(first, second)
        assert first.size == 10
        assert not np.array_equal(first, dataset.eval_users(10, seed=4))

    def test_sequences_exclude_the_held_out_item(self, dataset):
        # A sequential family trained on a history containing the target would be
        # trained on the answer.
        for row, history in dataset.sequences.by_user.items():
            assert dataset.held_out[row] not in history
