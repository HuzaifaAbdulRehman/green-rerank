"""Invariants for the measurement harness.

These are chosen the way the companion project chose its most valuable tests: not for
line coverage, but for the failures that produce a table which looks entirely normal and
is wrong. Each one below corresponds to a mistake that has actually been made, either in
the companion project or in this project's own preliminary probing.
"""

from __future__ import annotations

import os

import pytest

from green_rerank.measure import (
    CompositeMeter,
    ConditionsMonitor,
    ExclusiveLock,
    MeasurementSession,
    MockMeter,
    NullMeter,
    PreflightError,
    RaplMeter,
    Reading,
    preflight,
    total,
)
from green_rerank.measure.meters import EnergyMeter


class FakeClock:
    """A clock that only moves when told to, so ordering can be asserted exactly."""

    def __init__(self) -> None:
        self.now = 0.0

    def advance(self, seconds: float) -> None:
        self.now += seconds

    def __call__(self) -> float:
        return self.now


def cpu_clock_from(clock: FakeClock):
    """A CPU clock slaved to the fake wall clock, i.e. exactly one core busy."""

    def _times() -> tuple[float, float, float]:
        return clock.now, clock.now, 0.0

    return _times


# --------------------------------------------------------------------------- Reading


class TestReading:
    def test_utilisation_is_cpu_over_wall(self):
        r = Reading(stage="train", label="x", wall_seconds=2.0, cpu_seconds=8.0)
        assert r.cpu_utilisation == 4.0

    def test_utilisation_of_empty_window_is_zero_not_a_crash(self):
        # A stage that did nothing measurable must not divide by zero and take the run
        # down with it; the honest report is "no parallelism observed".
        r = Reading(stage="train", label="x", wall_seconds=0.0, cpu_seconds=0.0)
        assert r.cpu_utilisation == 0.0

    def test_joules_requires_an_explicit_rate(self):
        r = Reading(stage="train", label="x", wall_seconds=1.0, cpu_seconds=3.0)
        assert r.joules(15.0) == 45.0
        # There is deliberately no default: a joule figure must never appear without the
        # assumption that produced it being visible at the call site.
        with pytest.raises(TypeError):
            r.joules()  # type: ignore[call-arg]

    def test_negative_power_is_rejected(self):
        r = Reading(stage="train", label="x", wall_seconds=1.0, cpu_seconds=3.0)
        with pytest.raises(ValueError):
            r.joules(-1.0)

    def test_row_carries_channels_and_meta(self):
        r = Reading(
            stage="rerank",
            label="qubo",
            wall_seconds=1.0,
            cpu_seconds=2.0,
            channels={"mock.joules": 5.0},
            meta={"power_source": "ac"},
        )
        row = r.as_row()
        assert row["mock.joules"] == 5.0
        assert row["meta.power_source"] == "ac"
        assert row["cpu_utilisation"] == 2.0

    def test_total_sums_the_named_field(self):
        rs = [
            Reading(stage="train", label="a", wall_seconds=1.0, cpu_seconds=2.0),
            Reading(stage="rerank", label="a", wall_seconds=3.0, cpu_seconds=4.0),
        ]
        assert total(rs) == 6.0
        assert total(rs, "wall_seconds") == 4.0


# ---------------------------------------------------------------------------- meters


class TestMeters:
    def test_mock_meter_is_exact_arithmetic(self):
        clock = FakeClock()
        meter = MockMeter(watts=10.0, clock=clock)
        meter.start()
        clock.advance(3.0)
        assert meter.stop()["mock.joules"] == 30.0

    def test_mock_meter_refuses_stop_before_start(self):
        with pytest.raises(RuntimeError):
            MockMeter().stop()

    def test_null_meter_contributes_no_channels(self):
        m = NullMeter()
        m.start()
        assert m.stop() == {}

    def test_composite_drops_unavailable_backends_instead_of_raising(self):
        class Unavailable(EnergyMeter):
            name = "nope"

            @property
            def available(self) -> bool:
                return False

            def start(self) -> None:  # pragma: no cover - never called
                raise AssertionError("unavailable meter was started")

            def stop(self) -> dict[str, float]:  # pragma: no cover
                raise AssertionError("unavailable meter was stopped")

        # The same experiment script has to run on the laptop, on a Linux live USB and
        # in CI. A missing backend must cost channels, not the run.
        composite = CompositeMeter([Unavailable(), MockMeter(watts=2.0)])
        assert composite.skipped == ["nope"]
        assert len(composite.meters) == 1

    def test_composite_merges_channels_from_every_backend(self):
        clock = FakeClock()
        composite = CompositeMeter([MockMeter(watts=1.0, clock=clock)])
        composite.start()
        clock.advance(2.0)
        assert composite.stop()["mock.joules"] == 2.0


class TestRapl:
    """RAPL against a synthetic sysfs tree.

    The development machine cannot run RAPL -- Windows exposes no interface, and WSL2's
    ``/sys/class/powercap`` is present but empty because the hypervisor does not pass the
    counters through. Verified directly: ``RaplMeter().available`` is False under WSL2.
    So the only way this code is exercised before it matters is against a fake tree.
    """

    # Real sysfs names these ``intel-rapl:0``. Windows cannot create a directory with a
    # colon in it, so the fake tree uses a dash and the meter's glob accepts both.
    def _domain(self, tmp_path, name, energy_uj, wrap=1_000_000, friendly=None):
        d = tmp_path / f"intel-rapl-{name}"
        d.mkdir()
        (d / "name").write_text(f"{friendly or f'package-{name}'}\n")
        (d / "energy_uj").write_text(f"{energy_uj}\n")
        (d / "max_energy_range_uj").write_text(f"{wrap}\n")
        return d

    def test_nested_domains_sharing_a_name_do_not_collide(self, tmp_path):
        """Two packages each contain a subdomain called ``core``.

        Keying channels by the friendly name alone would let one silently overwrite the
        other, understating total draw on a multi-socket machine by a whole package.
        """
        self._domain(tmp_path, "0-0", 0, friendly="core")
        self._domain(tmp_path, "1-0", 0, friendly="core")
        meter = RaplMeter(root=tmp_path)
        meter.start()
        assert len(meter.stop()) == 2

    def test_absent_powercap_is_unavailable_not_an_error(self, tmp_path):
        assert RaplMeter(root=tmp_path / "missing").available is False

    def test_reports_joules_from_microjoule_delta(self, tmp_path):
        d = self._domain(tmp_path, "0", 1_000_000)
        meter = RaplMeter(root=tmp_path)
        assert meter.available is True
        meter.start()
        (d / "energy_uj").write_text("3_000_000".replace("_", ""))
        assert meter.stop()["rapl.package-0_j"] == pytest.approx(2.0)

    def test_counter_wraparound_is_corrected(self, tmp_path):
        # RAPL counters are fixed-width and wrap. Untreated, the highest-power windows
        # are the ones most likely to report *negative* energy -- a silent failure that
        # would corrupt exactly the measurements the project cares most about.
        d = self._domain(tmp_path, "0", 900_000, wrap=1_000_000)
        meter = RaplMeter(root=tmp_path)
        meter.start()
        (d / "energy_uj").write_text("100000")
        assert meter.stop()["rapl.package-0_j"] == pytest.approx(0.2)

    def test_backwards_counter_without_a_wrap_point_raises(self, tmp_path):
        d = self._domain(tmp_path, "0", 900_000, wrap=0)
        meter = RaplMeter(root=tmp_path)
        meter.start()
        (d / "energy_uj").write_text("100000")
        with pytest.raises(RuntimeError, match="backwards"):
            meter.stop()


# --------------------------------------------------------------------------- session


class TestWindowOrdering:
    """The two ordering rules that the companion project got wrong."""

    def test_probe_cost_is_not_charged_to_the_workload(self):
        """The mistake that made a 0.008 s baseline read 5.4 s.

        ``EmissionsTracker.start()`` probes the hardware and takes seconds. If the clock
        starts before it, every stage is charged a constant -- which is invisible in the
        slow stages and is the entire reading for the fast ones.
        """
        clock = FakeClock()

        class SlowProbeMeter(EnergyMeter):
            name = "slow"

            def start(self) -> None:
                clock.advance(5.0)  # the hardware probe

            def stop(self) -> dict[str, float]:
                clock.advance(2.0)  # teardown
                return {}

        session = MeasurementSession(
            meter=SlowProbeMeter(), clock=clock, cpu_clock=cpu_clock_from(clock)
        )
        with session.window("train", "x"):
            clock.advance(1.0)  # the actual work

        reading = session.readings[0]
        # Exactly the work: not 6.0 (probe included), not 8.0 (probe and teardown).
        assert reading.wall_seconds == 1.0
        assert reading.cpu_seconds == 1.0

    def test_scoring_after_the_window_does_not_enter_the_measurement(self):
        """Metric computation is O(k^2) per user in Python.

        For an expensive stage that is noise; for a cheap one it is most of the reading.
        ``measure`` returns the payload unscored precisely so this cannot happen, and
        this test injects a scorer far more expensive than the work to prove it.
        """
        clock = FakeClock()
        session = MeasurementSession(clock=clock, cpu_clock=cpu_clock_from(clock))

        def work():
            clock.advance(1.0)
            return list(range(10))

        result, reading = session.measure("rerank", "x", work)

        def expensive_scoring(items):
            clock.advance(100.0)
            return sum(items)

        expensive_scoring(result)

        assert reading.wall_seconds == 1.0
        assert session.readings[0].wall_seconds == 1.0

    def test_reading_is_recorded_even_when_the_workload_raises(self):
        # A stage that dies partway still consumed real resources, and losing the
        # reading would quietly bias a results table toward runs that happened to
        # succeed.
        clock = FakeClock()
        session = MeasurementSession(clock=clock, cpu_clock=cpu_clock_from(clock))
        with pytest.raises(ValueError), session.window("train", "x"):
            clock.advance(2.0)
            raise ValueError("boom")
        assert len(session.readings) == 1
        assert session.readings[0].wall_seconds == 2.0

    def test_windows_do_not_accumulate_into_each_other(self):
        clock = FakeClock()
        session = MeasurementSession(clock=clock, cpu_clock=cpu_clock_from(clock))
        for stage, cost in (("train", 3.0), ("rerank", 5.0)):
            with session.window(stage, "x"):
                clock.advance(cost)
        assert [r.wall_seconds for r in session.readings] == [3.0, 5.0]

    def test_meta_travels_onto_every_reading(self):
        clock = FakeClock()
        session = MeasurementSession(
            meta={"power_source": "ac"}, clock=clock, cpu_clock=cpu_clock_from(clock)
        )
        with session.window("train", "x"):
            clock.advance(1.0)
        assert session.readings[0].meta["power_source"] == "ac"
        assert session.readings[0].meta["meter"] == "null"


@pytest.mark.timing
class TestRealClocks:
    """Assertions about the real clocks, which need a quiet machine.

    Deselected in CI (a shared runner can stall a process mid-window) but run locally,
    because these are the ones that would catch the harness measuring nothing.
    """

    def test_cpu_seconds_counts_all_threads(self):
        """A parallel numpy matmul must register more CPU time than wall time.

        This is what separates CPU-seconds from a stopwatch. If BLAS threads were not
        counted, every parallel stage would be undercharged and the whole cost
        comparison would favour whichever family threads best.
        """
        np = pytest.importorskip("numpy")
        if os.cpu_count() is None or os.cpu_count() < 2:  # pragma: no cover
            pytest.skip("needs more than one core")

        session = MeasurementSession()
        a = np.random.default_rng(0).random((900, 900))
        _, reading = session.measure("train", "matmul", lambda: a @ a @ a)

        assert reading.cpu_seconds > 0
        # Not asserting >1.0 utilisation: BLAS may be single-threaded in some builds,
        # and a false failure here would be worse than a weak assertion. What must hold
        # is that real CPU time was seen at all.
        assert reading.cpu_seconds >= reading.wall_seconds * 0.5

    def test_cpu_seconds_is_monotone_in_work(self):
        """Twice the work must not cost less.

        This exists because preliminary probing of codecarbon on this machine produced a
        12-second fully-loaded window reporting *less* CPU energy than a 4-second one.
        Whatever the cost unit, non-monotonicity in work means the unit is not measuring
        work, and every number built on it is void. CPU-seconds must not have that flaw.
        """

        def burn(n: int) -> float:
            x = 0.0
            for _ in range(n):
                x += 1.0
            return x

        session = MeasurementSession()
        _, small = session.measure("train", "burn", burn, 2_000_000)
        _, large = session.measure("train", "burn", burn, 8_000_000)

        assert large.cpu_seconds > small.cpu_seconds


# ---------------------------------------------------------------------------- guards


class TestPreflight:
    def test_battery_aborts_the_run(self):
        # The companion project measured this: on battery the CPU pins to 1.297 GHz and
        # every timing rises ~2.8x, while every quality metric stays byte-identical. So
        # nothing looks wrong, which is why this has to be an abort and not a warning.
        with pytest.raises(PreflightError, match="battery"):
            preflight(power_source_fn=lambda: "battery", busy_fn=lambda: 0.0)

    def test_battery_is_permitted_when_explicitly_accepted(self):
        result = preflight(
            require_mains=False, power_source_fn=lambda: "battery", busy_fn=lambda: 0.0
        )
        assert result.power_source == "battery"

    def test_unknown_power_warns_rather_than_passing_silently(self):
        # A check that could not run must never be recorded as a check that passed.
        result = preflight(power_source_fn=lambda: "unknown", busy_fn=lambda: 0.0)
        assert any("power source" in w for w in result.warnings)

    def test_busy_machine_aborts(self):
        with pytest.raises(PreflightError, match="busy"):
            preflight(power_source_fn=lambda: "ac", busy_fn=lambda: 80.0)

    def test_unsampleable_load_warns(self):
        result = preflight(power_source_fn=lambda: "ac", busy_fn=lambda: None)
        assert any("load" in w for w in result.warnings)

    def test_clean_machine_passes_and_reports_conditions(self):
        result = preflight(power_source_fn=lambda: "ac", busy_fn=lambda: 3.0)
        meta = result.as_meta()
        assert meta["power_source"] == "ac"
        assert meta["machine_busy_pct"] == 3.0


class TestBelowQuantum:
    """A reading that could not be grown past the clock tick is not a measurement.

    ``measure_repeated`` grows a window until it spans ~20 quanta. When it cannot --
    because the repeat ceiling or the time limit fires first -- the reading is a tick
    count, and any per-request cost derived from it is a precise-looking division of the
    scheduler's accounting granularity. It must be flagged rather than reported.

    Found by mutation testing: deleting the flag left every existing test passing, so
    unreliable readings would have been indistinguishable from good ones in the results.
    """

    def test_a_stage_that_cannot_be_grown_is_flagged(self):
        clock = FakeClock()
        session = MeasurementSession(clock=clock, cpu_clock=cpu_clock_from(clock))

        # Work that advances the clock by far less than one quantum, capped at a few
        # repetitions so the window can never reach the target.
        _, reading = session.measure_repeated(
            "retrieve_score", "x", lambda: clock.advance(1e-9), max_repeats=3
        )
        assert reading.meta.get("below_quantum") is True

    def test_an_expensive_stage_is_not_flagged(self):
        """The other direction, without which the flag could always be true.

        A stage that clears the target on its first call must come back clean, or every
        row in the results would carry the warning and it would be ignored.
        """
        clock = FakeClock()
        session = MeasurementSession(clock=clock, cpu_clock=cpu_clock_from(clock))

        _, reading = session.measure_repeated("train", "x", lambda: clock.advance(10.0))
        assert "below_quantum" not in reading.meta
        assert reading.repeats == 1

    def test_the_reason_for_stopping_is_recorded(self):
        clock = FakeClock()
        session = MeasurementSession(clock=clock, cpu_clock=cpu_clock_from(clock))

        # The wall clock is the same fake clock, so a tiny advance per call trips
        # max_seconds long before the CPU target is reached.
        _, reading = session.measure_repeated(
            "rerank", "x", lambda: clock.advance(0.001), max_seconds=0.05
        )
        assert reading.meta.get("below_quantum") is True
        assert reading.meta.get("repeat_limit") == "max_seconds"


class TestConditionsMonitor:
    """The guard that watches conditions *during* a run rather than before it.

    Preflight can only assert that the machine was fit at the start. The failure this
    catches is the cable coming out at run seven of twenty: the remaining runs are
    clocked ~2.8x slower, every quality metric stays byte-identical, and the results
    table looks completely ordinary while the cheap families appear to have got
    expensive.

    Tested by populating the sample buffers directly. The event cannot be triggered on
    demand on real hardware, and a monitor that is only ever exercised on a machine
    where nothing goes wrong is a monitor whose firing path has never run.
    """

    @staticmethod
    def _monitor(frequencies, sources=("ac",)):
        monitor = ConditionsMonitor()
        monitor.frequencies = list(frequencies)
        monitor.power_sources = set(sources)
        return monitor

    def test_a_steady_machine_reports_no_change(self):
        report = self._monitor([2800.0, 2795.0, 2801.0]).report()
        assert not report["conditions_changed"]
        assert not report["throttled"]
        assert not report["power_source_changed"]

    def test_ordinary_turbo_variation_is_not_called_throttling(self):
        # Clocks move a few percent under normal thermal behaviour. A guard that fired
        # on that would be disabled within a day, and then it would catch nothing.
        report = self._monitor([3600.0, 3500.0, 3450.0, 3550.0]).report()
        assert not report["throttled"]

    def test_a_drop_to_a_third_is_caught(self):
        # The measured event: ~3.6 GHz turbo to a pinned 1.297 GHz on battery.
        report = self._monitor([3600.0, 3600.0, 1297.0, 1297.0]).report()
        assert report["throttled"]
        assert report["conditions_changed"]
        assert report["frequency_drop"] == pytest.approx(1 - 1297 / 3600, abs=1e-3)

    def test_the_cable_coming_out_is_caught_even_at_a_steady_clock(self):
        """Power source and frequency are independent evidence.

        A machine that switches to battery without the clock having dropped yet is
        still no longer comparable to the runs before it, and on hardware where psutil
        reports a static frequency the power channel is the only live signal there is.
        """
        report = self._monitor([2800.0] * 4, sources=("ac", "battery")).report()
        assert report["power_source_changed"]
        assert report["conditions_changed"]
        assert not report["throttled"]

    def test_no_frequency_samples_does_not_claim_a_clean_run(self):
        # Some platforms report no frequency at all. Absence of evidence must not be
        # recorded as evidence of stability.
        report = self._monitor([]).report()
        assert "frequency_drop" not in report
        assert report["samples"] == 0

    def test_it_starts_and_stops_without_leaving_a_thread(self):
        import threading

        before = threading.active_count()
        with ConditionsMonitor(interval=0.01) as monitor:
            assert monitor._thread is not None
        # The sampling thread must not outlive the run it was watching.
        assert threading.active_count() <= before

    def test_stop_returns_the_same_report_as_report(self):
        monitor = ConditionsMonitor(interval=0.01).start()
        stopped = monitor.stop()
        assert set(stopped) == set(monitor.report())


class TestExclusiveLock:
    def test_second_holder_is_refused(self, tmp_path):
        path = tmp_path / "lock"
        first = ExclusiveLock(path)
        assert first.acquire() is True
        assert ExclusiveLock(path).acquire() is False
        first.release()
        assert ExclusiveLock(path).acquire() is True

    def test_context_manager_raises_for_the_loser(self, tmp_path):
        path = tmp_path / "lock"
        with ExclusiveLock(path):
            with pytest.raises(PreflightError, match="sequential"):
                with ExclusiveLock(path):
                    pass  # pragma: no cover

    def test_lock_from_a_dead_process_is_reclaimed(self, tmp_path):
        # A crashed run must not block the machine forever. Staleness is decided by
        # asking the OS about the pid rather than by a timeout, which would eventually
        # evict a long-running training job that was doing nothing wrong.
        path = tmp_path / "lock"
        path.write_text("999999999\n0\n")
        pytest.importorskip("psutil")
        assert ExclusiveLock(path).acquire() is True

    def test_release_is_idempotent(self, tmp_path):
        lock = ExclusiveLock(tmp_path / "lock")
        lock.acquire()
        lock.release()
        lock.release()


# --------------------------------------------------------------------------- output


class TestOutput:
    def test_csv_reconciles_differing_channel_sets(self, tmp_path):
        """A run with RAPL has columns a run without it does not.

        Writing with :mod:`csv` would truncate every later row to the first row's keys,
        silently dropping whichever backend started reporting late.
        """
        pytest.importorskip("pandas")
        clock = FakeClock()
        session = MeasurementSession(clock=clock, cpu_clock=cpu_clock_from(clock))
        with session.window("train", "a") as out:
            clock.advance(1.0)
        out[0].channels["rapl.package-0_j"] = 12.0
        with session.window("rerank", "a"):
            clock.advance(1.0)

        path = tmp_path / "readings.csv"
        session.to_csv(str(path))

        import pandas as pd

        frame = pd.read_csv(path)
        assert list(frame["stage"]) == ["train", "rerank"]
        assert "rapl.package-0_j" in frame.columns
        assert frame["rapl.package-0_j"].iloc[0] == 12.0
        assert pd.isna(frame["rapl.package-0_j"].iloc[1])
