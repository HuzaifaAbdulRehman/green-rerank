"""What one measured window records.

A :class:`Reading` is deliberately flat: a few always-present core fields plus an open
``channels`` mapping for whatever energy backends happened to be active. That shape is
what lets one run carry *several* cost estimates side by side -- CPU-seconds, a
codecarbon estimate, and RAPL counters if the machine exposes them -- which is exactly
what is needed to ask whether the cheap estimate agrees with the expensive one.

Nothing here computes a metric. Scoring must happen outside the measured window (it is
O(k^2) per user in Python and would otherwise dominate the cheap stages), so a Reading
never sees a recommendation list.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

#: Channel name for the conversion from CPU-seconds to joules. Kept as a constant so
#: that the one place the conversion happens is greppable: it is an assumption, not a
#: measurement, and every table that shows it has to say so.
JOULES_CHANNEL = "derived.joules"


@dataclass(frozen=True)
class Reading:
    """One measured window.

    Attributes:
        stage: pipeline stage this window covers (``train``, ``retrieve``, ...).
        label: what was being measured -- usually the model family's name.
        wall_seconds: elapsed wall-clock time.
        cpu_seconds: process CPU time, user + system, summed over all threads. This is
            the primary cost unit. Unlike an energy estimate it is reported by the
            kernel from counters it already maintains, so it needs no sampling, no
            hardware probe and no model of the machine.
        cpu_user_seconds: user-space component of ``cpu_seconds``.
        cpu_system_seconds: kernel component. Worth keeping separate: a stage that
            spends its time in the kernel is doing I/O, and I/O costs energy somewhere
            other than the CPU package.
        peak_rss_bytes: peak resident set size during the window, when measurable.
            Memory is a cost too, and the sparse-similarity work in the companion
            project turned on exactly this number.
        channels: readings contributed by optional energy backends, keyed
            ``<backend>.<quantity>`` (e.g. ``codecarbon.cpu_kwh``, ``rapl.package_j``).
        meta: run context that must travel with the number to keep it interpretable --
            power source, whether the machine was quiet, backend availability.
    """

    stage: str
    label: str
    wall_seconds: float
    cpu_seconds: float
    cpu_user_seconds: float = 0.0
    cpu_system_seconds: float = 0.0
    peak_rss_bytes: int | None = None
    repeats: int = 1
    channels: dict[str, float] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def cpu_seconds_each(self) -> float:
        """CPU-seconds for **one** execution of the measured work.

        Differs from :attr:`cpu_seconds` only when the work was repeated to clear the
        clock's quantum -- see :func:`green_rerank.measure.session.clock_quantum`. The
        raw total is kept as well, because a per-iteration figure derived from a window
        that was itself below the quantum would be a precise-looking division of noise.
        """
        return self.cpu_seconds / max(self.repeats, 1)

    @property
    def wall_seconds_each(self) -> float:
        return self.wall_seconds / max(self.repeats, 1)

    @property
    def cpu_utilisation(self) -> float:
        """CPU-seconds per wall-second: effective parallelism during the window.

        Above 1.0 means threads were genuinely running in parallel; near 0 means the
        window was mostly waiting. This is the number an energy estimator has to get
        right, which makes it the natural thing to check an estimator against.
        """
        if self.wall_seconds <= 0:
            return 0.0
        return self.cpu_seconds / self.wall_seconds

    def joules(self, watts_per_cpu_second: float) -> float:
        """Convert CPU-seconds to joules at a **stated** active-power figure.

        This is a conversion, not a measurement, and it is the only place the project
        turns work into energy. Callers must pass the figure explicitly -- there is no
        default -- so that no table can show joules without the assumption that
        produced them being visible in the code that made it.
        """
        if watts_per_cpu_second < 0:
            raise ValueError("watts_per_cpu_second must be non-negative")
        return self.cpu_seconds * watts_per_cpu_second

    def as_row(self) -> dict[str, Any]:
        """Flatten to a single CSV row, channels included."""
        row: dict[str, Any] = {
            "stage": self.stage,
            "label": self.label,
            "wall_seconds": self.wall_seconds,
            "cpu_seconds": self.cpu_seconds,
            "cpu_user_seconds": self.cpu_user_seconds,
            "cpu_system_seconds": self.cpu_system_seconds,
            "cpu_utilisation": self.cpu_utilisation,
            "peak_rss_bytes": self.peak_rss_bytes,
            "repeats": self.repeats,
            "cpu_seconds_each": self.cpu_seconds_each,
        }
        row.update(self.channels)
        row.update({f"meta.{k}": v for k, v in self.meta.items()})
        return row


def total(readings: list[Reading], attr: str = "cpu_seconds") -> float:
    """Sum one field across readings -- the pipeline total for a stage set.

    Exists so that "the cost of a pipeline" is computed one way everywhere, rather than
    being re-derived with a slightly different set of stages at each call site.
    """
    return float(sum(getattr(r, attr) for r in readings))
