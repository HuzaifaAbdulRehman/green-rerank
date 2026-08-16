"""The measured window itself.

One rule governs the whole module, and it is the rule the companion project got wrong
twice: **the clock starts after every probe, and stops before every teardown.**

``EmissionsTracker.start()`` takes seconds to interrogate the hardware. Timing from
before it charged that constant to whichever solver was being measured -- a baseline
that did 0.008 s of real work read 5.4 s. So the ordering here is not a matter of
taste:

    meter.start()      <- may be slow; costs nothing because the clock is not running
    clock.start()
        ... the workload, and nothing else ...
    clock.stop()
    meter.stop()       <- teardown, likewise uncharged

The second rule is that **scoring happens outside**. Metric computation is O(k^2) per
user in pure Python: noise for an expensive stage, and most of the measured time for a
cheap one. That is not a small error, it is an error concentrated exactly where the
comparison matters. :meth:`MeasurementSession.measure` therefore hands the workload's
output back to the caller and never scores it -- the API makes the mistake awkward
rather than trusting anyone to remember.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from contextlib import contextmanager
from functools import lru_cache
from typing import Any

from green_rerank.measure.guards import Preflight
from green_rerank.measure.meters import EnergyMeter, NullMeter
from green_rerank.measure.reading import Reading

try:  # pragma: no cover - import guard
    import psutil

    _HAS_PSUTIL = True
except ImportError:  # pragma: no cover
    psutil = None  # type: ignore[assignment]
    _HAS_PSUTIL = False


def _cpu_times() -> tuple[float, float, float]:
    """``(total, user, system)`` CPU seconds for this process, all threads included.

    ``time.process_time()`` is the authoritative total: the kernel maintains it, and it
    counts every thread, so a BLAS matmul spreading over four cores registers four
    CPU-seconds per wall-second. ``os.times()`` supplies the user/system split, which is
    worth keeping because a stage sitting in kernel time is doing I/O, and I/O spends
    energy somewhere other than the CPU package.
    """
    total = time.process_time()
    try:
        times = os.times()
        return total, float(times.user), float(times.system)
    except (OSError, AttributeError):  # pragma: no cover - platform fallback
        return total, total, 0.0


@lru_cache(maxsize=4)
def clock_quantum(samples: int = 200) -> float:
    """The smallest step ``process_time`` actually takes on this machine.

    ``time.get_clock_info("process_time")`` reports a resolution of 100 ns on Windows.
    That figure is wrong in the way that matters: the value is derived from the
    scheduler's accounting, which advances **once per tick**. Measured on the
    development machine, the smallest observable step is 15.625 ms -- five orders of
    magnitude coarser than advertised.

    The consequence is not noise, it is quantisation. A stage taking 3 ms reads either
    0 or 15.625 ms, so cheap stages report exact zeros and stages differing by 10x can
    report the same number. Any per-request cost derived from such a window is a
    precise-looking division of a tick count.

    :meth:`MeasurementSession.measure_repeated` uses this to decide how many repetitions
    are needed before a reading means anything.
    """
    steps = []
    for _ in range(samples):
        start = time.process_time()
        current = start
        # Spin until the counter moves. Cheap: at most one tick.
        while current == start:
            current = time.process_time()
        steps.append(current - start)
    return min(steps)


def _peak_rss() -> int | None:
    """Peak resident memory, if the platform will say.

    Peak rather than current: the sparse-similarity work in the companion project turned
    on a 1,016 MB allocation that existed only transiently, and a sample taken after the
    window would have missed it entirely.
    """
    if not _HAS_PSUTIL:
        return None
    try:
        info = psutil.Process().memory_info()
    except Exception:  # pragma: no cover - psutil is best-effort
        return None
    # Windows exposes a true high-water mark; elsewhere fall back to the current value
    # and let the caller know it is not a peak by way of the docstring.
    return int(getattr(info, "peak_wset", None) or info.rss)


class MeasurementSession:
    """Collects :class:`Reading` objects for one experiment run.

    Args:
        meter: optional energy backend. Defaults to none, which still measures
            wall-clock and CPU-seconds -- the primary cost unit needs no backend.
        label: default label for windows that do not give one (usually the model family).
        meta: run context stamped onto every reading, so that a results CSV carries the
            conditions it was taken under.
        preflight: result of :func:`green_rerank.measure.guards.preflight`, folded into
            that context.
    """

    def __init__(
        self,
        meter: EnergyMeter | None = None,
        label: str = "",
        meta: dict[str, Any] | None = None,
        preflight: Preflight | None = None,
        clock: Callable[[], float] = time.perf_counter,
        cpu_clock: Callable[[], tuple[float, float, float]] = _cpu_times,
    ) -> None:
        self.meter = meter or NullMeter()
        self.label = label
        self.readings: list[Reading] = []
        # Injected so that the ordering guarantee in this module's docstring -- that the
        # probe is not charged to the workload -- can be asserted exactly, rather than
        # inferred from sleeps on a machine that might stall.
        self._clock = clock
        self._cpu_clock = cpu_clock
        self._window_start_cpu = 0.0
        self.meta: dict[str, Any] = dict(meta or {})
        if preflight is not None:
            self.meta.update(preflight.as_meta())
        self.meta.setdefault("meter", self.meter.name)

    @contextmanager
    def window(
        self,
        stage: str,
        label: str | None = None,
        repeats: int | Callable[[], int] = 1,
    ):
        """Measure a block of work.

        Yields a one-element list that receives the :class:`Reading` on exit. The
        indirection exists because a context manager cannot yield a value it does not
        have yet, and the reading is not complete until the block is.

        Usage::

            with session.window("train", "itemknn") as out:
                model.fit(data)
            reading = out[0]
        """
        out: list[Reading] = []

        # Probe first: whatever this costs, it is not the workload's.
        self.meter.start()

        cpu0, user0, sys0 = self._cpu_clock()
        wall0 = self._clock()
        # Exposed so measure_repeated can watch the window grow from inside it.
        self._window_start_cpu = cpu0

        try:
            yield out
        finally:
            wall = self._clock() - wall0
            cpu1, user1, sys1 = self._cpu_clock()

            # Teardown after the clock has stopped, for the same reason as above.
            channels = self.meter.stop()

            # Resolved at close, so a caller that only learns the repetition count while
            # running -- which is how measure_repeated works -- can still report it.
            count = repeats() if callable(repeats) else repeats

            reading = Reading(
                stage=stage,
                label=label if label is not None else self.label,
                wall_seconds=wall,
                cpu_seconds=cpu1 - cpu0,
                cpu_user_seconds=user1 - user0,
                cpu_system_seconds=sys1 - sys0,
                peak_rss_bytes=_peak_rss(),
                repeats=max(int(count), 1),
                channels=channels,
                meta=dict(self.meta),
            )
            out.append(reading)
            self.readings.append(reading)

    def measure(
        self, stage: str, label: str, fn: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> tuple[Any, Reading]:
        """Measure one call and hand its result back **unscored**.

        Returning the payload rather than accepting a scorer is the whole design: the
        caller computes metrics after this returns, outside the window. Passing a
        ``score=`` callback here would put O(k^2) of Python inside the measurement and
        would corrupt precisely the cheap stages the comparison hinges on.
        """
        with self.window(stage, label) as out:
            result = fn(*args, **kwargs)
        return result, out[0]

    def measure_repeated(
        self,
        stage: str,
        label: str,
        fn: Callable[..., Any],
        *args: Any,
        min_quanta: float = 20.0,
        max_repeats: int = 10_000,
        max_seconds: float = 30.0,
        **kwargs: Any,
    ) -> tuple[Any, Reading]:
        """Repeat ``fn`` until the window is large enough to mean something.

        A stage cheaper than :func:`clock_quantum` cannot be measured once: the reading
        is a tick count, not a duration. Repeating until the total clears the quantum by
        ``min_quanta`` bounds the quantisation error at roughly ``1 / min_quanta`` --
        5 % at the default -- and :attr:`Reading.cpu_seconds_each` then reports the
        per-execution figure.

        Stopping is on **repetitions and elapsed work**, never on a target precision,
        so the number of repetitions does not depend on how fast the machine is in a way
        that would change the result. ``max_seconds`` is a safety valve for stages that
        turn out to be expensive; it is recorded when it fires rather than silently
        truncating.

        Args:
            min_quanta: how many clock quanta the total window must span.
            max_repeats: hard ceiling on repetitions.
            max_seconds: give up growing the window after this much wall-clock.

        Returns:
            ``(result_of_the_last_call, reading)``.
        """
        target = clock_quantum() * min_quanta
        counter = {"n": 0, "hit_time_limit": False}
        result: Any = None

        with self.window(stage, label, repeats=lambda: counter["n"]) as out:
            start = self._clock()
            while True:
                result = fn(*args, **kwargs)
                counter["n"] += 1

                cpu_used = self._cpu_clock()[0]
                elapsed_wall = self._clock() - start
                if counter["n"] >= max_repeats or elapsed_wall >= max_seconds:
                    counter["hit_time_limit"] = elapsed_wall >= max_seconds
                    break
                # Grow the window until the CPU clock has moved far enough that its
                # quantisation is a small fraction of the reading.
                if cpu_used >= self._window_start_cpu + target:
                    break

        reading = out[0]
        if reading.cpu_seconds < target:
            # Say so rather than let a below-quantum reading pass as a measurement. A
            # stage that is genuinely expensive clears the target on its first call and
            # is never flagged, so this marks only readings that could not be grown.
            reading.meta["below_quantum"] = True
            if counter["hit_time_limit"]:
                reading.meta["repeat_limit"] = "max_seconds"
        return result, reading

    def close(self) -> None:
        """Release the energy backend, if it holds anything."""
        closer = getattr(self.meter, "close", None)
        if closer is not None:
            closer()

    def __enter__(self) -> MeasurementSession:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ------------------------------------------------------------------ reporting

    def rows(self) -> list[dict[str, Any]]:
        return [r.as_row() for r in self.readings]

    def to_csv(self, path: str, append: bool = False) -> None:
        """Write the readings collected so far.

        Uses pandas rather than :mod:`csv` because channel sets differ between machines
        -- a run with RAPL has columns a run without it does not -- and a DataFrame
        reconciles that into a union with blanks instead of silently truncating to the
        first row's keys.
        """
        import pandas as pd

        frame = pd.DataFrame(self.rows())
        mode, header = ("a", False) if append and os.path.exists(path) else ("w", True)
        frame.to_csv(path, mode=mode, header=header, index=False)
