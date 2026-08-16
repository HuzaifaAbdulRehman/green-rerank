"""Does the energy backend measure anything the clock does not already say?

This is the study's third claim, and until now its evidence lived in a throwaway probe
script. That is not good enough: a negative result about a widely used tool has to be
reproducible by whoever doubts it, on their own machine, or it is an anecdote.

Two experiments, answering two different questions.

**The graded load** puts a known, controlled amount of work on the CPU -- 0, 1, 2, 4 and
8 busy workers -- and asks what the backend reports. This is the sharper test, because
the true answer is known in advance: eight saturated threads draw several times idle
power on any modern part. A backend that reports a flat line across that span is not
noisy, it is blind. Crucially the load is *known*, so the test does not depend on
trusting any other measurement.

**The agreement test** takes the readings from a real sweep and regresses reported energy
on elapsed time. An R^2 at or near 1.0 means the energy column is the timing column in
different units, and every "energy" conclusion drawn from it is a wall-clock conclusion.

The graded load runs busy work in *processes*, not threads. Python's global interpreter
lock would let a thread-based load saturate one core while the others idled, so a
thread-based version of this experiment would understate the true power swing and hand
the backend an easier test than the one it needs to pass.

Usage::

    python -m experiments.validity --out results/validity
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from experiments import manifest
from green_rerank.analysis.validity import agreement
from green_rerank.measure import MeasurementSession, default_meter
from green_rerank.measure.guards import power_source

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Worker counts. Zero is the idle floor; eight saturates the development machine's
#: logical cores. Powers of two so the span is wide with few points -- each one costs
#: `seconds` of wall-clock and the whole sweep must stay short enough to actually be run.
DEFAULT_LOADS = (0, 1, 2, 4, 8)


def _burn(seconds: float) -> None:
    """Occupy one core with arithmetic for a fixed duration.

    Deliberately trivial floating-point work in a tight loop. Anything touching memory
    or I/O would spend part of the window stalled, which is exactly the state a
    utilisation-based power estimate handles differently -- and the point here is to
    present the backend with an unambiguous, fully compute-bound load.
    """
    end = time.perf_counter() + seconds
    total = 0.0
    while time.perf_counter() < end:
        for i in range(10_000):
            total += i * 1.000001
    return None


def graded_load(
    loads: tuple[int, ...] = DEFAULT_LOADS,
    seconds: float = 20.0,
    meter=None,
) -> pd.DataFrame:
    """Measure a known, controlled load and record what the backend reports.

    Args:
        loads: number of busy worker processes per condition.
        seconds: duration of each condition.
        meter: energy backend; defaults to whatever this machine offers.

    Returns:
        One row per condition, carrying both what was *asked for* (workers, duration)
        and what was *reported* (every channel the meter emitted).
    """
    meter = meter if meter is not None else default_meter()
    session = MeasurementSession(meter=meter, label="graded_load")
    rows: list[dict[str, Any]] = []

    for workers in loads:
        with session.window("train", f"load_{workers}") as out:
            if workers == 0:
                time.sleep(seconds)
            else:
                processes = [
                    mp.Process(target=_burn, args=(seconds,)) for _ in range(workers)
                ]
                for process in processes:
                    process.start()
                for process in processes:
                    process.join()

        reading = out[0]
        row = {
            "workers": workers,
            "requested_seconds": seconds,
            "wall_seconds": reading.wall_seconds,
            # This process's own CPU time, which stays near zero because the work
            # happens in children. The system-wide load is the `workers` column, and
            # keeping them separate is the point: a backend that samples system CPU
            # should see the load regardless of which process performed it.
            "own_cpu_seconds": reading.cpu_seconds,
            "expected_core_seconds": workers * seconds,
        }
        row.update(reading.channels)
        rows.append(row)
        print(
            f"  {workers} worker(s): {reading.wall_seconds:5.1f}s wall, "
            + (
                ", ".join(f"{k}={v:.6g}" for k, v in reading.channels.items())
                or "no channels reported"
            )
        )

    session.close()
    return pd.DataFrame(rows)


#: Channel-name endings that denote a quantity accumulated over the window. Everything
#: else -- watts, percentages -- is already an instantaneous rate.
CUMULATIVE_SUFFIXES = ("_kwh", "_kg", "_joules", "_wh")


def _is_cumulative(channel: str) -> bool:
    return channel.endswith(CUMULATIVE_SUFFIXES)


def verdict(frame: pd.DataFrame) -> dict[str, Any]:
    """Judge whether the backend responded to the load at all.

    The test is deliberately generous: it asks only for a *monotone* response with some
    meaningful dynamic range, not for accuracy. A backend that cannot clear this bar is
    not imprecise, it is reporting something other than the load.
    """
    channels = [
        c
        for c in frame.columns
        if c
        not in {
            "workers",
            "requested_seconds",
            "wall_seconds",
            "own_cpu_seconds",
            "expected_core_seconds",
        }
    ]
    if not channels:
        return {
            "responded": False,
            "reason": "no energy backend reported any channel on this machine",
            # A dict, matching the populated case. Returning a list here made the two
            # branches differently shaped, and the caller iterating `.items()` only
            # broke on the path where there was nothing to report -- the path this
            # experiment most expects to take.
            "channels": {},
        }

    findings = {}
    wall = frame["wall_seconds"].to_numpy(dtype=float)
    for channel in channels:
        values = frame[channel].to_numpy(dtype=float)
        if not np.isfinite(values).all() or values.max() <= 0:
            findings[channel] = {"usable": False}
            continue

        # Only *cumulative* channels are divided by elapsed time. A longer window
        # accumulates more kWh whatever the load, so comparing kWh totals across windows
        # of unequal length would confound duration with power -- and these windows are
        # unequal, because starting more workers takes longer.
        #
        # Channels that are already rates must be left alone. Dividing watts by seconds
        # produces a quantity with no physical meaning, and it would have been reported
        # in the results table as though it were one.
        cumulative = _is_cumulative(channel)
        rate = values / wall if cumulative else values

        findings[channel] = {
            "usable": True,
            "cumulative": cumulative,
            "unit": "per second" if cumulative else "as reported",
            "idle": float(rate[0]),
            "loaded": float(rate[-1]),
            "dynamic_range": float(rate.max() / rate.min()) if rate.min() > 0 else float("inf"),
            "monotone": bool(np.all(np.diff(rate) >= -1e-12)),
            # A backend reporting *less* under full load than at idle has failed in a
            # way that no amount of averaging repairs.
            "inverted": bool(rate[-1] < rate[0]),
            # The sharpest evidence available, and it needs no threshold to interpret.
            # A channel that is bit-for-bit identical from idle to full saturation is
            # not a noisy measurement of the load; it is not a measurement of the load.
            # On this machine `ram_watts` is exactly 10.000 throughout and
            # `cpu_util_pct` exactly 0 -- a hardcoded constant and a broken probe, both
            # of which would pass unnoticed in any table reporting only totals.
            "constant": bool(np.ptp(values) == 0.0),
        }

    usable = {k: v for k, v in findings.items() if v.get("usable")}
    responded = any(v["dynamic_range"] > 2.0 and not v["inverted"] for v in usable.values())
    constants = sorted(k for k, v in usable.items() if v["constant"])
    return {
        "responded": responded,
        "channels": findings,
        # Reported separately from `responded` because it is a different and stronger
        # statement, and it survives whatever threshold anyone prefers for the former.
        "constant_channels": constants,
        "reason": (
            ""
            if responded
            else "no channel changed by more than 2x between idle and full load"
        ),
    }


def agreement_from_readings(path: Path, channel: str) -> dict[str, Any]:
    """Regress a sweep's reported energy on its timings.

    Separate from the graded load because it tests a weaker but more directly relevant
    thing: whether, on the actual workloads this study measures, the energy column adds
    anything to the timing column.
    """
    frame = pd.read_csv(path)
    if channel not in frame.columns:
        return {
            "available": False,
            "reason": f"{path.name} carries no {channel} column; the sweep ran without a meter",
        }
    usable = frame[np.isfinite(frame[channel])]
    if len(usable) < 3:
        return {"available": False, "reason": f"only {len(usable)} readings carry {channel}"}

    return {
        "available": True,
        "n": len(usable),
        "vs_cpu_seconds": agreement(usable[channel], usable["cpu_seconds"]).summary(),
        "vs_wall_seconds": agreement(usable[channel], usable["wall_seconds"]).summary(),
    }


def run(out_dir: Path, loads: tuple[int, ...], seconds: float, readings: Path | None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    meter = default_meter()
    print(f"backend: {meter.name}   power source: {power_source()}")
    if meter.name == "null":
        print(
            "  no energy backend on this machine. The graded load still runs and will\n"
            "  record that nothing was reported, which is itself the finding."
        )

    print(f"\ngraded load: {loads} workers, {seconds:.0f}s each")
    frame = graded_load(loads, seconds, meter)
    frame.to_csv(out_dir / "graded_load.csv", index=False)

    result = verdict(frame)
    report: dict[str, Any] = {"graded_load": result}
    if readings is not None and readings.exists():
        report["sweep_agreement"] = agreement_from_readings(readings, "codecarbon.total_kwh")

    book = manifest.build({"loads": list(loads), "seconds": seconds}, validity=report)
    (out_dir / "manifest.json").write_text(json.dumps(book, indent=2), encoding="utf-8")
    (out_dir / "verdict.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n" + "-" * 70)
    if not result["responded"]:
        print(
            "FINDING: the energy backend did not respond to the load.\n"
            f"  {result['reason']}\n"
            "  Energy reported by this backend on this machine is not a measurement of\n"
            "  the work done. CPU-seconds is the defensible cost unit here."
        )
    else:
        print("The backend responded to the graded load; energy may be reported directly.")
    for channel, finding in result.get("channels", {}).items():
        if finding.get("usable"):
            print(
                f"  {channel}: idle {finding['idle']:.4g} -> loaded "
                f"{finding['loaded']:.4g} {finding['unit']} "
                f"({finding['dynamic_range']:.2f}x"
                + (", INVERTED" if finding["inverted"] else "")
                + (", CONSTANT" if finding["constant"] else "")
                + ")"
            )
    if result.get("constant_channels"):
        print(
            "\n  Channels identical from idle to full saturation: "
            + ", ".join(result["constant_channels"])
            + "\n  These are not noisy measurements of the load. They are not "
            "measurements of the load."
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "results" / "validity")
    parser.add_argument("--seconds", type=float, default=20.0)
    parser.add_argument("--loads", type=int, nargs="+", default=list(DEFAULT_LOADS))
    parser.add_argument(
        "--readings",
        type=Path,
        default=None,
        help="a sweep's readings.csv, to also test agreement on real workloads",
    )
    args = parser.parse_args()
    run(Path(args.out), tuple(args.loads), args.seconds, args.readings)


if __name__ == "__main__":
    # Required on Windows: the graded load spawns processes, and without this guard the
    # child re-imports and re-runs this module, forking indefinitely.
    mp.freeze_support()
    main()
