"""Wait for the machine to go quiet, then run a command.

This project and its companion share one laptop, and both of them measure. A sweep
started while the other is running produces rows the analysis refuses to read, so in
practice someone has to sit and watch for the machine to clear. That is a poor use of a
person and it is the reason several sweeps in this project's history were run twice.

So: queue the work instead. This polls until the machine has been genuinely quiet for a
few consecutive samples and then execs the command.

**The threshold is one core, not zero.** On eight logical cores a single fully busy
process is 12.5 % of the total, so a limit below that cannot distinguish "quiet" from
"one background job" -- and a limit at exactly zero never fires, because the poller,
the shell and the OS are themselves a percent or two. 10 % sits below one core and above
the floor.

**Consecutive samples, not one.** CPU load is spiky; a single quiet reading can land in
the gap between two phases of a job that is very much still running. Requiring several
in a row costs a couple of minutes and avoids starting a two-hour sweep into a lull.

    python -m experiments.when_idle -- python -m experiments.sweep --config x.yaml
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import time
from datetime import datetime, timedelta, timezone

try:
    import psutil
except ImportError:  # pragma: no cover - psutil is a declared dependency
    psutil = None  # type: ignore[assignment]

#: Percent of total machine capacity below which it counts as quiet. Below one core.
DEFAULT_IDLE_PCT = 10.0

#: How many consecutive quiet observations are required before starting.
DEFAULT_CONSECUTIVE = 3


def sample(seconds: float = 2.0, n: int = 5) -> float:
    """Median system-wide CPU over ``n`` samples.

    Median rather than mean so that one spike -- a browser repainting, an indexer
    waking -- does not by itself postpone the run indefinitely.
    """
    psutil.cpu_percent(interval=None)  # priming read; the first is meaningless
    return sorted(psutil.cpu_percent(interval=seconds) for _ in range(n))[n // 2]


def busiest() -> str:
    """The heaviest non-idle process, for saying *what* is holding the machine."""
    procs = list(psutil.process_iter(["name", "pid"]))
    for proc in procs:
        try:
            proc.cpu_percent(None)
        except psutil.Error:
            continue
    time.sleep(1.0)

    cores = psutil.cpu_count() or 1
    best, label = 0.0, ""
    for proc in procs:
        try:
            share = proc.cpu_percent(None) / cores
            if share > best and proc.info["name"] != "System Idle Process":
                best, label = share, f"{proc.info['name']} (pid {proc.info['pid']})"
        except psutil.Error:
            continue
    return f"{label} at {best:.0f}%" if label else "no single process dominant"


def wait(idle_pct: float, consecutive: int, poll: float, deadline: float | None) -> bool:
    """Block until the machine is quiet. Returns False if it timed out."""
    quiet = 0
    started = time.monotonic()

    while True:
        load = sample()
        if load <= idle_pct:
            quiet += 1
            print(f"  {datetime.now():%H:%M:%S}  {load:5.1f}%  quiet {quiet}/{consecutive}",
                  flush=True)
            if quiet >= consecutive:
                return True
        else:
            if quiet:
                print(f"  {datetime.now():%H:%M:%S}  {load:5.1f}%  -- not quiet after all,"
                      " restarting the count", flush=True)
            else:
                print(f"  {datetime.now():%H:%M:%S}  {load:5.1f}%  waiting -- {busiest()}",
                      flush=True)
            quiet = 0

        if deadline is not None and time.monotonic() - started > deadline:
            return False
        # Sampling already took ~10 s; sleep the remainder of the interval.
        time.sleep(max(0.0, poll - 10.0))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--idle-pct", type=float, default=DEFAULT_IDLE_PCT)
    parser.add_argument("--consecutive", type=int, default=DEFAULT_CONSECUTIVE)
    parser.add_argument("--poll", type=float, default=60.0, help="seconds between checks")
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="give up after this many seconds rather than waiting forever",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = [c for c in args.command if c != "--"]
    if not command:
        parser.error("no command given; put it after --")
    if psutil is None:
        parser.error("psutil is required to detect an idle machine")

    print(f"waiting for the machine to fall below {args.idle_pct:.0f} % "
          f"for {args.consecutive} consecutive checks")
    print(f"then running: {shlex.join(command)}\n", flush=True)

    if not wait(args.idle_pct, args.consecutive, args.poll, args.timeout):
        print(f"\ngave up after {timedelta(seconds=args.timeout)} -- machine never went quiet")
        return 2

    started = datetime.now(timezone.utc)
    print(f"\nmachine is quiet; starting at {started:%H:%M:%S} UTC\n", flush=True)
    result = subprocess.run(command)
    print(f"\ncommand exited {result.returncode} after "
          f"{datetime.now(timezone.utc) - started}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
