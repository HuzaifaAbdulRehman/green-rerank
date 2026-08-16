"""Optional energy backends.

The core cost unit -- wall-clock and CPU-seconds -- is collected by
:class:`green_rerank.measure.session.MeasurementSession` itself and always available.
Everything in this module is an *extra* channel layered on top, and every one of them
is allowed to be missing. That is not defensive habit: the project's third claim is
about whether these backends can be believed, so the harness has to keep working, and
keep being tested, on machines where they cannot run at all.

**Why CPU-seconds is primary, and codecarbon is not.** On the development machine
(i5-8350U, Windows, no RAPL) codecarbon cannot see CPU load. Measured with a graded
load of 0/1/2/4/8 busy workers, 20 s each:

===========  ===========  ==================  =============
busy workers  CPU power    reported CPU util   total kWh
===========  ===========  ==================  =============
0 (idle)      1.501 W      3.0 %               7.371e-05
1             1.506 W      0.0 %               6.400e-05
2             1.517 W      0.0 %               6.418e-05
4             1.558 W      0.0 %               6.516e-05
8 (saturated) 1.815 W      0.0 %               7.290e-05
===========  ===========  ==================  =============

Three separate disqualifications: a 1.21x dynamic range where the part's true range is
roughly 10x; 0 % utilisation reported while all eight threads were pegged; and the
fully loaded window reporting *less* total energy than the idle one, because RAM is
billed at a hardcoded constant 10.000 W that swamps the CPU term.

So codecarbon is still collected here -- the disagreement between it and measured CPU
time is a result the project reports -- but it is never the number a conclusion rests
on. See :meth:`green_rerank.measure.reading.Reading.joules` for how work becomes energy
instead.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path

# --------------------------------------------------------------------------- base


class EnergyMeter(ABC):
    """A backend that can report energy consumed between :meth:`start` and :meth:`stop`.

    Implementations return a mapping of ``<backend>.<quantity>`` to value rather than a
    fixed schema, because the backends genuinely measure different things: RAPL reports
    joules per power domain, codecarbon reports estimated kWh per component. Forcing
    them into one shape would mean inventing numbers for whichever fields a backend does
    not have.
    """

    name: str = "base"

    @property
    def available(self) -> bool:
        """Whether this backend can run here. Checked before use, never assumed."""
        return True

    @abstractmethod
    def start(self) -> None:
        """Begin a window. Any expensive hardware probe belongs here, before the
        session's clock starts, so that its cost is not charged to the workload."""

    @abstractmethod
    def stop(self) -> dict[str, float]:
        """End the window and return its channels."""


class NullMeter(EnergyMeter):
    """No energy backend. Wall-clock and CPU-seconds still work.

    This is the default, and CI runs on it. A harness whose measurement path is only
    exercised on the one machine that has a working backend is a harness whose
    measurement path is untested.
    """

    name = "null"

    def start(self) -> None:
        return None

    def stop(self) -> dict[str, float]:
        return {}


class MockMeter(EnergyMeter):
    """Deterministic fake energy, for tests.

    Reports ``watts * elapsed`` so that tests can assert on exact arithmetic without a
    real backend, a real workload, or a quiet machine.
    """

    name = "mock"

    def __init__(self, watts: float = 10.0, clock=None) -> None:
        import time

        self.watts = watts
        self._clock = clock or time.perf_counter
        self._t0: float | None = None

    def start(self) -> None:
        self._t0 = self._clock()

    def stop(self) -> dict[str, float]:
        if self._t0 is None:
            raise RuntimeError("MockMeter.stop() called before start()")
        elapsed = self._clock() - self._t0
        self._t0 = None
        return {"mock.joules": self.watts * elapsed, "mock.watts": self.watts}


# --------------------------------------------------------------------- codecarbon


class CodeCarbonMeter(EnergyMeter):
    """codecarbon, driven through its per-task API.

    ``EmissionsTracker.start()`` probes the hardware and costs seconds, so one tracker
    is created and reused across every window rather than one per measurement. The
    per-task API (``start_task``/``stop_task``) is what makes that possible, and it is
    also what keeps stage windows from double-counting each other.

    Collected for comparison only. See the module docstring for what it does to load on
    the machine this was written on.
    """

    name = "codecarbon"

    def __init__(self, measure_power_secs: int = 1) -> None:
        self._tracker = None
        self._task = 0
        self._measure_power_secs = measure_power_secs
        self._started = False

    @property
    def available(self) -> bool:
        try:
            import codecarbon  # noqa: F401
        except ImportError:
            return False
        return True

    def _ensure_tracker(self):
        if self._tracker is None:
            from codecarbon import EmissionsTracker

            # log_level="error" keeps codecarbon's very chatty INFO output out of
            # experiment logs; save_to_file=False avoids littering an emissions.csv
            # next to every run.
            self._tracker = EmissionsTracker(
                log_level="error",
                save_to_file=False,
                measure_power_secs=self._measure_power_secs,
            )
            self._tracker.start()
            self._started = True
        return self._tracker

    def start(self) -> None:
        tracker = self._ensure_tracker()
        self._task += 1
        tracker.start_task(f"window{self._task}")

    def stop(self) -> dict[str, float]:
        if self._tracker is None:
            raise RuntimeError("CodeCarbonMeter.stop() called before start()")
        data = self._tracker.stop_task(f"window{self._task}")

        # Components are kept apart deliberately. The RAM term is a constant on this
        # platform, so a total that folds it in hides the only part that moves.
        out: dict[str, float] = {}
        for field, channel in (
            ("cpu_energy", "codecarbon.cpu_kwh"),
            ("ram_energy", "codecarbon.ram_kwh"),
            ("gpu_energy", "codecarbon.gpu_kwh"),
            ("energy_consumed", "codecarbon.total_kwh"),
            ("cpu_power", "codecarbon.cpu_watts"),
            ("ram_power", "codecarbon.ram_watts"),
            ("emissions", "codecarbon.co2_kg"),
            ("cpu_utilization_percent", "codecarbon.cpu_util_pct"),
        ):
            value = getattr(data, field, None)
            if value is not None:
                out[channel] = float(value)
        return out

    def close(self) -> None:
        """Shut the shared tracker down. Safe to call more than once."""
        if self._tracker is not None and self._started:
            try:
                self._tracker.stop()
            except Exception:  # pragma: no cover - codecarbon teardown is best-effort
                pass
            self._started = False
            self._tracker = None


# --------------------------------------------------------------------------- RAPL


class RaplMeter(EnergyMeter):
    """Intel RAPL on-chip energy counters, read from ``/sys/class/powercap``.

    This is real measurement rather than estimation: the CPU maintains the counters
    itself. It is Linux-only and normally root-only (reads were restricted after the
    PLATYPUS side-channel), which is why the development machine cannot use it despite
    having a CPU that supports it -- Windows exposes no interface to these counters.

    Kept in the codebase, and tested against a synthetic sysfs tree, so that booting the
    same laptop from a Linux live USB upgrades the project's numbers from estimates to
    measurements without any change to the harness.
    """

    name = "rapl"
    ROOT = Path("/sys/class/powercap")

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root is not None else self.ROOT
        self._domains: list[tuple[str, Path, int]] = []
        self._start: dict[str, int] = {}

    def _discover(self) -> list[tuple[str, Path, int]]:
        """Find readable RAPL domains and their counter wrap points.

        The glob is ``intel-rapl*`` rather than ``intel-rapl:*`` so that the synthetic
        sysfs tree the tests build is reachable on Windows, which cannot create a
        directory containing a colon. Real sysfs entries match either way.

        Domains nest: ``intel-rapl:0`` is a whole package and ``intel-rapl:0:0`` is the
        core subdomain *inside* it. They are reported as separate channels and must
        never be summed -- adding package to core double-counts the core. Names are
        disambiguated below because two packages each contain a domain called ``core``.
        """
        found: list[tuple[str, Path, int]] = []
        if not self.root.exists():
            return found

        seen: dict[str, int] = {}
        for entry in sorted(self.root.glob("intel-rapl*")):
            energy = entry / "energy_uj"
            if not energy.exists():
                continue
            try:
                energy.read_text()
            except OSError:
                # Present but unreadable -- almost always "not running as root".
                continue

            name = (entry / "name").read_text().strip() if (entry / "name").exists() else entry.name
            seen[name] = seen.get(name, 0) + 1
            if seen[name] > 1:
                # Collision: qualify with the sysfs entry, which is unique by
                # construction. Silently overwriting one domain's reading with
                # another's would understate total draw on a multi-socket machine.
                name = f"{name}@{entry.name.replace(':', '_')}"

            try:
                wrap = int((entry / "max_energy_range_uj").read_text().strip())
            except (OSError, ValueError):
                wrap = 0
            found.append((name, energy, wrap))
        return found

    @property
    def available(self) -> bool:
        return bool(self._discover())

    def start(self) -> None:
        self._domains = self._discover()
        if not self._domains:
            raise RuntimeError("no readable RAPL domains; needs Linux and usually root")
        self._start = {name: int(path.read_text().strip()) for name, path, _ in self._domains}

    def stop(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for name, path, wrap in self._domains:
            end = int(path.read_text().strip())
            begin = self._start[name]
            delta = end - begin
            if delta < 0:
                # The counter is a fixed-width register that wraps. Without this the
                # highest-power windows are the ones most likely to silently report a
                # negative energy -- exactly the wrong failure mode.
                if wrap <= 0:
                    raise RuntimeError(
                        f"RAPL domain {name} went backwards and reports no wrap point"
                    )
                delta += wrap
            out[f"rapl.{name}_j"] = delta / 1e6
        self._start = {}
        return out


# ---------------------------------------------------------------------- composite


class CompositeMeter(EnergyMeter):
    """Run several backends over the same window.

    Load-bearing for the project's third claim: asking whether a cheap estimate agrees
    with a real measurement requires both to be taken over *the same* work, not over two
    runs that were meant to be identical.

    Unavailable backends are dropped at construction with a note in
    :attr:`skipped`, rather than raising, so the same experiment script runs on the
    laptop, on a Linux live USB and in CI and simply reports fewer channels.
    """

    name = "composite"

    def __init__(self, meters: list[EnergyMeter]) -> None:
        self.meters: list[EnergyMeter] = []
        self.skipped: list[str] = []
        for meter in meters:
            if meter.available:
                self.meters.append(meter)
            else:
                self.skipped.append(meter.name)

    def start(self) -> None:
        for meter in self.meters:
            meter.start()

    def stop(self) -> dict[str, float]:
        out: dict[str, float] = {}
        # Reversed so the window closes in the opposite order to opening, keeping each
        # backend's window nested rather than staggered.
        for meter in reversed(self.meters):
            out.update(meter.stop())
        return out

    def close(self) -> None:
        for meter in self.meters:
            closer = getattr(meter, "close", None)
            if closer is not None:
                closer()


def default_meter(prefer_codecarbon: bool = True) -> EnergyMeter:
    """The best set of backends this machine can actually run.

    Deliberately never raises. A missing backend costs channels, not the run: the
    primary cost unit does not depend on any of them.
    """
    candidates: list[EnergyMeter] = [RaplMeter()]
    if prefer_codecarbon and os.environ.get("GREEN_RERANK_NO_CODECARBON") != "1":
        candidates.append(CodeCarbonMeter())

    composite = CompositeMeter(candidates)
    if not composite.meters:
        return NullMeter()
    return composite
