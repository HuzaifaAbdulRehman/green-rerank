"""Preflight checks that refuse to produce a number rather than produce a bad one.

Every check here exists because the companion project was bitten by the thing it
guards. The failure mode they share is the dangerous one: the run completes, the table
looks entirely normal, and only the cost column is wrong.

The worst of them, in the companion project's own words: mid-session the laptop was
unplugged, the CPU dropped from ~3.6 GHz turbo to a pinned 1.297 GHz, every timing rose
~2.8x, and *every quality metric stayed byte-identical*. Nothing looked wrong. A cost
column that moves by a factor of three because a cable came out is worth aborting for.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

try:  # pragma: no cover - import guard
    import psutil

    _HAS_PSUTIL = True
except ImportError:  # pragma: no cover
    psutil = None  # type: ignore[assignment]
    _HAS_PSUTIL = False


class PreflightError(RuntimeError):
    """A precondition for trustworthy measurement is not met."""


@dataclass
class Preflight:
    """Result of the preflight checks, recorded into every :class:`Reading`.

    Kept as data rather than a bare pass/fail so that the conditions a number was taken
    under travel with the number. A results CSV that cannot say whether it was taken on
    mains power is a results CSV that cannot be compared to another one.
    """

    power_source: str = "unknown"
    machine_busy_pct: float | None = None
    exclusive: bool = False
    warnings: list[str] = field(default_factory=list)

    def as_meta(self) -> dict[str, object]:
        return {
            "power_source": self.power_source,
            "machine_busy_pct": self.machine_busy_pct,
            "exclusive": self.exclusive,
            "warnings": ";".join(self.warnings) if self.warnings else "",
        }


def power_source() -> str:
    """``"ac"``, ``"battery"``, or ``"unknown"``.

    ``unknown`` is returned for desktops (no battery to report) and for machines where
    psutil is absent. It is deliberately distinct from ``"ac"``: a check that cannot run
    must not be recorded as a check that passed.
    """
    if not _HAS_PSUTIL:
        return "unknown"
    battery = psutil.sensors_battery()
    if battery is None:
        # No battery at all -- a desktop, which is mains-powered by construction.
        return "ac"
    return "ac" if battery.power_plugged else "battery"


def machine_busy_pct(sample_seconds: float = 0.5, samples: int = 3) -> float | None:
    """System-wide CPU utilisation before the run starts, as a median of samples.

    Measurement pitfall three: never run two jobs at once, because CPU contention is
    charged to whichever method happens to be running. This cannot detect a job that
    starts *during* the window -- :class:`ConditionsMonitor` covers that -- but it
    catches the common case of a forgotten run in another terminal.

    The median of several samples rather than one reading. A single sample is taken
    moments after the interpreter has finished importing numpy, scipy, pandas and
    possibly torch, and that startup burst is still draining: it reports the process's
    own arrival as though it were someone else's load. Observed doing exactly that --
    a genuinely idle machine read 10.4 %, which was enough to mark an entire 170-run
    sweep untrustworthy before the first measurement was taken.
    """
    if not _HAS_PSUTIL:
        return None
    psutil.cpu_percent(interval=None)  # priming call; the first read is meaningless
    readings = sorted(float(psutil.cpu_percent(interval=sample_seconds)) for _ in range(samples))
    return readings[len(readings) // 2]


class ExclusiveLock:
    """A lockfile asserting this is the only measuring process on the machine.

    Advisory, and only against this project's own runs -- it cannot see a training job
    someone started by hand. It exists because the easiest way to ruin a batch of
    measurements is to start the next one before the last has finished.
    """

    def __init__(self, path: str | Path = "results/.measure.lock") -> None:
        self.path = Path(path)
        self.acquired = False

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # O_EXCL makes creation atomic, so two processes racing cannot both win.
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if self._stale():
                self.path.unlink(missing_ok=True)
                return self.acquire()
            return False
        with os.fdopen(fd, "w") as handle:
            handle.write(f"{os.getpid()}\n{time.time()}\n")
        self.acquired = True
        return True

    def _stale(self) -> bool:
        """Whether the lock belongs to a process that no longer exists.

        A crashed run must not block the machine forever, but a *running* one must not
        be stepped on -- so staleness is decided by asking the OS about the pid rather
        than by a timeout, which would eventually evict a long training job.
        """
        try:
            pid = int(self.path.read_text().splitlines()[0])
        except (OSError, ValueError, IndexError):
            return True
        if not _HAS_PSUTIL:
            return False
        return not psutil.pid_exists(pid)

    def release(self) -> None:
        if self.acquired:
            self.path.unlink(missing_ok=True)
            self.acquired = False

    def __enter__(self) -> ExclusiveLock:
        if not self.acquire():
            raise PreflightError(
                f"another measurement run holds {self.path}. Runs must be sequential: "
                "CPU contention is charged to whichever method happens to be running."
            )
        return self

    def __exit__(self, *exc: object) -> None:
        self.release()


class ConditionsMonitor:
    """Watch power source and CPU frequency *while* a sweep runs.

    :func:`preflight` can only assert that conditions were acceptable at the start, and
    a sweep over six catalogues runs for a long time. The failure this catches is the
    one described in this module's docstring happening in the middle: the cable comes
    out at run seven of twenty, the remaining runs are clocked ~2.8x slower, and because
    quality metrics do not move at all the results table looks completely ordinary. The
    cheap families would appear to have got expensive.

    A sampling thread, not a check, because the event is instantaneous and the evidence
    is gone by the time the sweep ends. Sampling is deliberately slow (once a second)
    and does almost nothing: the monitor must not become load of its own.

    ``frequency_drop`` is the number that matters. Turbo clocks vary by a few percent
    under normal thermal behaviour, which is not a defect; a drop to a third is a
    different machine.
    """

    #: Fractional frequency drop from the observed maximum that counts as a change of
    #: regime rather than ordinary turbo variation.
    DROP_THRESHOLD = 0.25

    def __init__(self, interval: float = 1.0) -> None:
        self.interval = interval
        self.frequencies: list[float] = []
        self.power_sources: set[str] = set()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _sample(self) -> None:
        while not self._stop.wait(self.interval):
            self.power_sources.add(power_source())
            if not _HAS_PSUTIL:
                continue
            try:
                current = psutil.cpu_freq()
            except Exception:  # pragma: no cover - not all platforms report frequency
                continue
            if current is not None:
                self.frequencies.append(float(current.current))

    def start(self) -> ConditionsMonitor:
        self.power_sources.add(power_source())
        self._thread = threading.Thread(target=self._sample, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> dict[str, object]:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self.interval * 2)
        return self.report()

    def report(self) -> dict[str, object]:
        """What the conditions did, and whether they invalidate the run."""
        result: dict[str, object] = {
            "power_sources_seen": sorted(self.power_sources),
            "power_source_changed": len(self.power_sources) > 1,
            "samples": len(self.frequencies),
        }
        if self.frequencies:
            top = max(self.frequencies)
            low = min(self.frequencies)
            result.update(
                {
                    "cpu_mhz_max": top,
                    "cpu_mhz_min": low,
                    "cpu_mhz_mean": sum(self.frequencies) / len(self.frequencies),
                    "frequency_drop": (top - low) / top if top else 0.0,
                }
            )
        drop = float(result.get("frequency_drop", 0.0) or 0.0)
        result["throttled"] = drop > self.DROP_THRESHOLD
        # One flag the caller can act on without knowing which check produced it. Any
        # run carrying this is not comparable to one that does not, on the cost axis.
        result["conditions_changed"] = bool(
            result["power_source_changed"] or result["throttled"]
        )
        return result

    def __enter__(self) -> ConditionsMonitor:
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.stop()


def preflight(
    require_mains: bool = True,
    max_busy_pct: float | None = 25.0,
    lock: ExclusiveLock | None = None,
    power_source_fn=power_source,
    busy_fn=machine_busy_pct,
) -> Preflight:
    """Check the machine is fit to measure on, or raise.

    Args:
        require_mains: abort on battery. The default is on because the alternative is a
            cost column that silently changes by ~3x.
        max_busy_pct: abort if the machine is already this busy. ``None`` disables.
        lock: an already-acquired exclusivity lock, recorded into the result.
        power_source_fn: injected for tests -- the whole point of this function is the
            behaviour when a check *fails*, which cannot be triggered on demand on real
            hardware.
        busy_fn: injected for tests, for the same reason.

    Raises:
        PreflightError: if a required condition is not met.
    """
    result = Preflight(exclusive=bool(lock and lock.acquired))

    result.power_source = power_source_fn()
    if result.power_source == "battery" and require_mains:
        raise PreflightError(
            "on battery power. This machine drops from ~3.6 GHz turbo to a pinned "
            "1.297 GHz on battery and every timing rises ~2.8x, while every quality "
            "metric stays byte-identical -- so nothing would look wrong. Plug in, or "
            "pass require_mains=False and expect the cost column to be uncomparable."
        )
    if result.power_source == "unknown":
        result.warnings.append("power source could not be determined")

    if max_busy_pct is not None:
        result.machine_busy_pct = busy_fn()
        if result.machine_busy_pct is None:
            result.warnings.append("machine load could not be sampled")
        elif result.machine_busy_pct > max_busy_pct:
            raise PreflightError(
                f"machine is already {result.machine_busy_pct:.0f}% busy "
                f"(limit {max_busy_pct:.0f}%). Another job's CPU time would be charged "
                "to whatever this run measures."
            )

    if not result.exclusive:
        result.warnings.append("no exclusivity lock held")

    return result
