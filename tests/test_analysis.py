"""Invariants for the three claims' arithmetic.

Every function here produces a headline number, so each test is written against a case
whose answer is known by hand rather than against whatever the code happened to return.
"""

from __future__ import annotations

import numpy as np
import pytest

from green_rerank.analysis import (
    CostLine,
    CostSample,
    Point,
    accuracy_per_unit_cost,
    agreement,
    cheapest_at,
    crossover,
    crossover_interval,
    dominated,
    dominates,
    frontier,
    frontier_at,
    regime_table,
    retraining_table,
)
from green_rerank.analysis.validity import energy_axis_report
from green_rerank.measure import Reading

# ------------------------------------------------------------------------ breakeven


class TestCrossover:
    def test_finds_the_hand_computed_crossing(self):
        """(100 - 10) / (5 - 1) = 22.5 requests. Worked by hand, asserted exactly."""
        knn = CostLine("itemknn", once=10.0, per_request=5.0)
        als = CostLine("als", once=100.0, per_request=1.0)

        result = crossover(knn, als)
        assert result.exists
        assert result.n_requests == pytest.approx(22.5)
        assert result.cheaper_below == "itemknn"
        assert result.cheaper_above == "als"

    def test_costs_are_equal_at_the_crossing(self):
        # The definition, checked directly rather than via the formula that produced it.
        a = CostLine("a", once=7.0, per_request=3.0)
        b = CostLine("b", once=40.0, per_request=0.5)
        n = crossover(a, b).n_requests
        assert a.at(n) == pytest.approx(b.at(n))

    def test_domination_is_reported_as_no_crossing_not_a_negative_one(self):
        """A negative crossover is not a small crossover.

        It means one family is cheaper at every volume that can occur, which is a
        different finding and must not be presented as a crossing point that a reader
        could mistake for a real traffic level.
        """
        cheap = CostLine("cheap", once=1.0, per_request=1.0)
        dear = CostLine("dear", once=10.0, per_request=10.0)
        result = crossover(cheap, dear)
        assert not result.exists
        assert result.cheaper_below == result.cheaper_above == "cheap"
        assert "every non-negative" in result.reason

    def test_parallel_lines_never_cross(self):
        a = CostLine("a", once=1.0, per_request=2.0)
        b = CostLine("b", once=5.0, per_request=2.0)
        result = crossover(a, b)
        assert not result.exists
        assert result.cheaper_above == "a"

    def test_identical_models_are_reported_as_such(self):
        a = CostLine("a", once=1.0, per_request=2.0)
        b = CostLine("b", once=1.0, per_request=2.0)
        assert crossover(a, b).reason == "identical cost models"

    def test_mixing_units_is_refused(self):
        # Comparing CPU-seconds against joules would produce a plausible number that
        # means nothing at all.
        a = CostLine("a", once=1.0, per_request=1.0, unit="cpu_seconds")
        b = CostLine("b", once=1.0, per_request=2.0, unit="joules")
        with pytest.raises(ValueError, match="cannot compare"):
            crossover(a, b)

    def test_negative_traffic_is_rejected(self):
        with pytest.raises(ValueError):
            CostLine("a", once=1.0, per_request=1.0).at(-1)


class TestCrossoverInterval:
    """The bootstrap exists to stop a crossover being quoted more precisely than it is."""

    @staticmethod
    def _sample(label, once, per_request, spread=0.0, n=8, seed=0):
        rng = np.random.default_rng(seed)
        jitter = lambda base: [  # noqa: E731 - a one-line helper reads better inline here
            base * (1 + spread * rng.standard_normal()) for _ in range(n)
        ]
        return CostSample(label, jitter(once), jitter(per_request))

    def test_one_repeat_cannot_produce_an_interval(self):
        """``lo == hi`` from a single observation reads as certainty on the page.

        A bootstrap over one observation returns that observation every replicate, so
        the interval collapses to a point -- which in a table is indistinguishable from
        a very precisely determined crossover, and means the opposite.
        """
        knn = CostSample("knn", [10.0], [5.0])
        als = CostSample("als", [100.0], [1.0])
        result = crossover_interval(knn, als, n_bootstrap=100)

        assert result.n_requests == pytest.approx(22.5)
        assert result.lo == result.hi  # the collapse itself
        assert not result.has_interval
        assert not result.is_stable
        assert "no interval" in result.summary()

    def test_a_clean_crossover_brackets_the_analytic_answer(self):
        # (100-10)/(5-1) = 22.5 with no noise at all, so the interval must be a point.
        knn = CostSample("knn", [10.0] * 6, [5.0] * 6)
        als = CostSample("als", [100.0] * 6, [1.0] * 6)
        result = crossover_interval(knn, als, n_bootstrap=200)

        assert result.n_requests == pytest.approx(22.5)
        assert result.lo == pytest.approx(22.5)
        assert result.hi == pytest.approx(22.5)
        assert result.exists_fraction == 1.0
        assert result.is_stable
        assert result.cheaper_below == "knn"
        assert result.cheaper_above == "als"

    def test_noise_widens_the_interval_rather_than_moving_the_estimate(self):
        knn = self._sample("knn", 10.0, 5.0, spread=0.15, seed=1)
        als = self._sample("als", 100.0, 1.0, spread=0.15, seed=2)
        result = crossover_interval(knn, als, n_bootstrap=1000)

        assert result.lo < result.n_requests < result.hi
        # The estimate stays in the right neighbourhood; the width is what changed.
        assert 10 < result.n_requests < 45
        assert result.hi - result.lo > 1.0

    def test_near_identical_serving_costs_are_reported_as_unstable(self):
        """The case that motivated this whole class.

        ItemKNN and ALS measured 5.5e-5 and 6.6e-5 CPU-seconds per request on the
        synthetic catalogue -- 20 % apart, against run-to-run spread of a similar size.
        The crossover is a ratio whose denominator is that difference, so it can be
        enormous, tiny, or nonexistent depending on the resample. A point estimate here
        would be a number with no information in it, and it would look authoritative.
        """
        knn = self._sample("knn", 0.4, 5.5e-5, spread=0.30, n=10, seed=3)
        als = self._sample("als", 0.7, 6.6e-5, spread=0.30, n=10, seed=4)
        result = crossover_interval(knn, als, n_bootstrap=1000)

        assert not result.is_stable
        assert "UNSTABLE" in result.summary() or result.n_requests is None

    def test_domination_is_a_null_result_not_a_wide_interval(self):
        # Cheaper to train *and* cheaper to serve: there is nothing to cross.
        good = CostSample("good", [1.0] * 5, [1.0] * 5)
        bad = CostSample("bad", [10.0] * 5, [10.0] * 5)
        result = crossover_interval(good, bad, n_bootstrap=200)

        assert result.n_requests is None
        assert result.exists_fraction == 0.0
        assert not result.is_stable
        assert "no crossover" in result.summary()

    def test_costs_are_resampled_paired_by_repeat(self):
        """Breaking the pairing would understate the interval.

        A repeat's training and serving costs are correlated -- a moment of background
        load inflates both. Here the two are perfectly correlated across repeats, so
        every legitimate replicate must draw a matching pair and the crossover can only
        take the two values the data contains. Independent resampling would manufacture
        combinations that were never observed and report a narrower spread than reality.
        """
        sample = CostSample("x", [10.0, 20.0], [1.0, 2.0])
        rng = np.random.default_rng(0)
        for _ in range(50):
            line = sample.resample(rng)
            assert (line.once, line.per_request) in {(10.0, 1.0), (20.0, 2.0), (15.0, 1.5)}

    def test_median_is_used_rather_than_mean(self):
        # One contaminated repeat, four clean. The mean would be dragged to 2.8.
        sample = CostSample("x", [1.0, 1.0, 1.0, 1.0, 10.0], [1.0] * 5)
        assert sample.line().once == 1.0

    def test_mismatched_repeat_counts_are_refused(self):
        with pytest.raises(ValueError, match="paired by repeat"):
            CostSample("x", [1.0, 2.0], [1.0])


class TestRetraining:
    def test_training_recurs_on_the_interval(self):
        # 250 requests at an interval of 100 means training three times: at 0, 100, 200.
        line = CostLine("als", once=10.0, per_request=0.1).with_retraining(every=100)
        assert line.at(250) == pytest.approx(3 * 10.0 + 250 * 0.1)

    def test_before_the_first_interval_it_matches_the_plain_line(self):
        plain = CostLine("als", once=10.0, per_request=0.1)
        retrained = plain.with_retraining(every=100)
        assert retrained.at(50) == pytest.approx(plain.at(50))

    def test_frequent_retraining_can_reverse_the_verdict(self):
        """The finding that makes retraining worth modelling at all.

        A factor model amortises expensive training over many requests -- but only if it
        is allowed to. Retrain it often enough and the amortisation never happens, and
        the cheap-to-train neighbourhood model wins at a volume where the plain analysis
        says it loses.

        The interval matters and the first version of this test picked one that was too
        loose: at every=50 over 100 requests, ALS still wins 400 to 530, because its
        per-request saving (4 x 100) exceeds the extra training (2 x 90). Retraining
        every 10 requests flips it, 610 to 1200.
        """
        knn = CostLine("itemknn", once=10.0, per_request=5.0)
        als = CostLine("als", once=100.0, per_request=1.0)
        assert als.at(100) == pytest.approx(200.0)
        assert knn.at(100) == pytest.approx(510.0)

        # Eleven training events: one up front, ten more over 100 requests.
        knn_r = knn.with_retraining(every=10)
        als_r = als.with_retraining(every=10)
        assert knn_r.at(100) == pytest.approx(610.0)
        assert als_r.at(100) == pytest.approx(1200.0)
        assert knn_r.at(100) < als_r.at(100)

    def test_zero_interval_is_rejected(self):
        with pytest.raises(ValueError, match="positive"):
            CostLine("a", once=1.0, per_request=1.0).with_retraining(every=0)


class TestRetrainingTable:
    """The cadence axis, which a per-run energy figure cannot express at all."""

    @staticmethod
    def _lines():
        # Cheap to train, costly to serve -- against the opposite.
        return [
            CostLine("knn", once=1.0, per_request=1e-3),
            CostLine("als", once=100.0, per_request=1e-4),
        ]

    def test_the_verdict_reverses_as_retraining_gets_frequent(self):
        """The finding this table exists to show, with the arithmetic done by hand.

        The two lines cross at (100 - 1) / (1e-3 - 1e-4) = 110,000 requests, so the
        horizon has to be beyond that for ALS to be winning in the first place. At one
        million requests, trained once: knn pays 1 + 1,000 = 1,001, ALS pays
        100 + 100 = 200, so ALS wins.

        Retrained every 1,000 requests ALS pays its 100 a thousand times over --
        100,200 against knn's 2,001 -- and the verdict inverts without a single measured
        cost changing.

        (An earlier version of this test used a 100,000-request horizon and asserted ALS
        won there. It does not: 101 against 110. The code was right and the test was
        wrong, which is the usual way round.)
        """
        rows = retraining_table(self._lines(), [None, 1_000], n_requests=1_000_000)
        assert rows[0]["cheapest"] == "als"
        assert rows[0]["cost.als"] == pytest.approx(200.0)
        assert rows[1]["cheapest"] == "knn"
        assert rows[1]["cost.als"] == pytest.approx(100_200.0)

    def test_training_events_are_counted_not_smoothed(self):
        # Training happens in whole events. A smoothed average would understate cost
        # immediately after each retrain, which is when a deployment notices.
        rows = retraining_table(self._lines(), [10_000], n_requests=100_000)
        assert rows[0]["training_events"] == 11  # one up front, then ten more

    def test_never_retraining_matches_the_plain_line(self):
        lines = self._lines()
        rows = retraining_table(lines, [None], n_requests=5_000)
        assert rows[0]["training_events"] == 1
        for line in lines:
            assert rows[0][f"cost.{line.label}"] == pytest.approx(line.at(5_000))

    def test_every_line_appears_in_every_row(self):
        # A family silently missing from one row would look like it was not an option
        # at that cadence, rather than like it lost.
        rows = retraining_table(self._lines(), [None, 100, 10], n_requests=1_000)
        for row in rows:
            assert {"cost.knn", "cost.als"} <= set(row)

    def test_a_non_positive_interval_is_refused(self):
        with pytest.raises(ValueError, match="must be positive"):
            retraining_table(self._lines(), [0], n_requests=100)


class TestRegimes:
    def test_cheapest_family_changes_with_traffic(self):
        lines = [
            CostLine("popularity", once=0.1, per_request=0.01),
            CostLine("itemknn", once=1.0, per_request=5.0),
            CostLine("als", once=50.0, per_request=0.5),
        ]
        assert cheapest_at(lines, 1).label == "popularity"
        rows = regime_table(lines, [1, 10, 1000])
        assert [r["cheapest"] for r in rows] == ["popularity", "popularity", "popularity"]
        assert rows[0]["cost.itemknn"] == pytest.approx(6.0)

    def test_empty_input_is_an_error_not_a_silent_none(self):
        with pytest.raises(ValueError):
            cheapest_at([], 10)


# ------------------------------------------------------------------------- frontier


class TestFrontier:
    def test_dominated_option_is_excluded(self):
        good = Point("good", accuracy=0.5, cost=1.0)
        bad = Point("bad", accuracy=0.4, cost=2.0)
        assert dominates(good, bad)
        assert [p.label for p in frontier([good, bad])] == ["good"]
        assert [p.label for p in dominated([good, bad])] == ["bad"]

    def test_a_trade_off_keeps_both(self):
        # More accurate and more expensive is a genuine choice, not a dominated one.
        cheap = Point("cheap", accuracy=0.3, cost=1.0)
        accurate = Point("accurate", accuracy=0.6, cost=9.0)
        assert len(frontier([cheap, accurate])) == 2

    def test_equal_points_are_both_kept(self):
        """Two families landing in the same place is a result, not a duplicate.

        Dropping one would hide that a cheap family matched an expensive one exactly --
        which is the single most useful thing a green-computing study can report.
        """
        a = Point("a", accuracy=0.5, cost=1.0)
        b = Point("b", accuracy=0.5, cost=1.0)
        assert len(frontier([a, b])) == 2

    def test_frontier_is_ordered_by_cost(self):
        points = [
            Point("c", accuracy=0.9, cost=9.0),
            Point("a", accuracy=0.3, cost=1.0),
            Point("b", accuracy=0.6, cost=4.0),
        ]
        assert [p.label for p in frontier(points)] == ["a", "b", "c"]

    def test_zero_cost_efficiency_is_none_not_infinity(self):
        # A zero cost here means the stage fell below the clock quantum. Infinite
        # efficiency would be a measurement artefact dressed up as a result.
        assert accuracy_per_unit_cost(Point("x", accuracy=0.5, cost=0.0)) is None
        assert accuracy_per_unit_cost(Point("x", accuracy=0.5, cost=2.0)) == 0.25

    def test_membership_can_change_with_traffic(self):
        # The point where the two claims meet: which options are worth considering
        # depends on how many requests will be served.
        by_volume = {
            10.0: [Point("knn", 0.5, 1.0, 10), Point("als", 0.5, 5.0, 10)],
            10_000.0: [Point("knn", 0.5, 500.0, 10_000), Point("als", 0.5, 50.0, 10_000)],
        }
        result = frontier_at(by_volume)
        assert result[10.0] == ["knn"]
        assert result[10_000.0] == ["als"]


# ------------------------------------------------------------------------- validity


class TestAgreement:
    def test_a_perfectly_rescaled_clock_is_detected(self):
        """The claim-3 positive case: energy is exactly time times a constant."""
        seconds = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = agreement(seconds * 3.7, seconds)
        assert result.r_squared == pytest.approx(1.0)
        assert result.slope == pytest.approx(3.7)
        assert result.relative_spread == pytest.approx(0.0, abs=1e-9)
        assert result.is_rescaled_clock

    def test_an_independent_signal_is_not_flagged(self):
        seconds = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        energy = np.array([5.0, 1.0, 4.0, 2.0, 9.0])
        assert not agreement(energy, seconds).is_rescaled_clock

    def test_two_observations_are_refused(self):
        """Two points fit a line exactly, so R^2 is 1.0 whatever the data.

        Without this guard the project's headline negative result could be produced from
        no evidence at all -- the most embarrassing way to be wrong.
        """
        with pytest.raises(ValueError, match="at least three"):
            agreement(np.array([1.0, 2.0]), np.array([1.0, 2.0]))

    def test_rank_preservation_is_reported_separately_from_fit(self):
        # A badly-fitting estimate can still order families correctly, and for choosing
        # between them the ordering is what matters.
        reference = np.array([1.0, 2.0, 3.0, 4.0])
        estimate = reference**3
        result = agreement(estimate, reference)
        assert result.rank_preserved
        assert result.spearman == pytest.approx(1.0)
        assert result.r_squared < 1.0

    def test_shape_mismatch_is_an_error(self):
        with pytest.raises(ValueError, match="shape mismatch"):
            agreement(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0]))

    def test_constant_reference_explains_nothing(self):
        result = agreement(np.array([1.0, 2.0, 3.0]), np.array([2.0, 2.0, 2.0]))
        assert result.r_squared == 0.0


class TestEnergyAxisReport:
    def _reading(self, cpu, kwh=None):
        channels = {} if kwh is None else {"codecarbon.total_kwh": kwh}
        return Reading(
            stage="train", label="x", wall_seconds=cpu, cpu_seconds=cpu, channels=channels
        )

    def test_absent_backend_is_reported_not_faked(self):
        report = energy_axis_report([self._reading(1.0), self._reading(2.0)])
        assert report["available"] is False
        assert "energy backend" in report["reason"]

    def test_detects_a_rescaled_clock_over_readings(self):
        readings = [self._reading(c, kwh=c * 1e-5) for c in (1.0, 2.0, 3.0, 4.0)]
        report = energy_axis_report(readings)
        assert report["available"] is True
        assert report["vs_cpu_seconds"].is_rescaled_clock
        assert "no information beyond" in report["vs_cpu_seconds"].summary()
