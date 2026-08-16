"""Run a grid of measured pipelines and write a results directory.

Three properties matter more than the grid itself.

**Runs are sequential, always.** Not because parallelism is hard here -- it is trivial,
the cells are independent -- but because it would destroy the measurement. Two runs
sharing four cores charge each other's CPU time to whichever happens to hold the core,
and the resulting table looks entirely normal. The wall-clock cost of this decision is
real and it is the price of the numbers meaning anything.

**Every cell is repeated.** A single cost reading has no uncertainty attached, and
``break-even at N=13,736`` stated from one reading each is a false precision: the
crossover is a ratio of differences, so it amplifies whatever noise the two costs carry.
Repeats are what let :mod:`green_rerank.analysis.breakeven` put an interval on it.

**A failed cell is recorded, not fatal.** A sweep that dies three catalogues in because
one family exhausted memory has wasted the runs that succeeded. Failures land in the
results table with their error, so an absent row always means "not attempted" and never
"attempted and quietly dropped".

Usage::

    python -m experiments.sweep --config experiments/configs/main.yaml
"""

from __future__ import annotations

import argparse
import json
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from experiments import manifest
from green_rerank import catalogues
from green_rerank.data import Dataset
from green_rerank.families import build
from green_rerank.measure import (
    ConditionsMonitor,
    ExclusiveLock,
    MeasurementSession,
    default_meter,
    preflight,
)
from green_rerank.pipeline import run_pipeline

REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULTS: dict[str, Any] = {
    "name": "sweep",
    "catalogues": ["ml100k"],
    "families": ["popularity", "itemknn", "als"],
    # ``None`` means "no reranker", which is a condition under test rather than a
    # missing value: it is the baseline the rerank stage's cost is measured against.
    "rerankers": [None],
    "n_users": 200,
    "n_candidates": 200,
    "k": 10,
    "repeats": 5,
    "seed": 0,
    "lam": 0.3,
    "mu": 1.0,
    "require_mains": True,
    "max_busy_pct": 25.0,
    "energy": False,
    "min_users": 50,
    "min_items": 50,
    "family_kwargs": {},
    # ``family -> catalogues it may run on``. Families absent from this map run
    # everywhere. It exists because the neural families are scoped to MovieLens 100K:
    # GRU4Rec costs ~135 CPU-seconds per epoch there, and the largest catalogue has 17x
    # the users. Expressing the restriction here rather than in a second config keeps
    # every family that ran on a catalogue in one results directory, which is what the
    # efficiency frontier for that catalogue needs.
    "only_on": {},
    # Above this the run is still performed but every row is stamped
    # ``trustworthy=False``. Distinct from ``max_busy_pct``, which aborts: a plumbing
    # check on a busy machine is a legitimate thing to want, and a cost figure taken
    # during one is not.
    #
    # 15 % rather than 10 % because of what the number can resolve. On an 8-thread
    # machine a single fully busy core is 12.5 % of the total, so a threshold below
    # that cannot distinguish "quiet" from "one background process" -- it can only
    # distinguish "quiet" from "quiet plus measurement noise", and it fails on the
    # latter. This sits just above one core so it still rejects any real competitor.
    "trust_busy_pct": 15.0,
}


@dataclass(frozen=True)
class Cell:
    """One measured run: a family on a catalogue, with or without a reranker."""

    catalogue: str
    family: str
    reranker: str | None
    repeat: int

    @property
    def key(self) -> tuple[str, str, str, int]:
        return (self.catalogue, self.family, self.reranker or "none", self.repeat)

    def __str__(self) -> str:
        suffix = f"+{self.reranker}" if self.reranker else ""
        return f"{self.catalogue}/{self.family}{suffix} #{self.repeat}"


def load_config(path: str | Path) -> dict[str, Any]:
    """Read a config and fill defaults, rejecting keys that do nothing.

    An unknown key is an error rather than a warning because the usual way it arises is
    a typo in a name that matters -- ``repeat: 5`` instead of ``repeats: 5`` silently
    runs the whole sweep once and reports costs with no uncertainty at all.
    """
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    unknown = set(raw) - set(DEFAULTS)
    if unknown:
        raise SystemExit(
            f"unknown config keys: {sorted(unknown)}\nknown keys: {sorted(DEFAULTS)}"
        )
    config = dict(DEFAULTS)
    config.update(raw)
    return config


def viability(dataset: Dataset, min_users: int, min_items: int) -> str | None:
    """Why this catalogue cannot be measured on, or ``None`` if it can.

    Not every registered catalogue survives its own preprocessing. The Amazon
    ``Appliances`` ratings export collapses to 13 users and 4 items under 5-core
    filtering -- a real property of that export, not a loading bug. Running on it would
    produce a full row of metrics computed over four items, which is a number and not a
    measurement. Excluding it here means the exclusion is stated in the results
    directory rather than being a gap someone has to notice.
    """
    if dataset.n_users < min_users:
        return f"only {dataset.n_users} users survive filtering (need {min_users})"
    if dataset.n_items < min_items:
        return f"only {dataset.n_items} items survive filtering (need {min_items})"
    if not dataset.held_out:
        return "no user has a held-out item"
    return None


def cells(config: dict[str, Any]) -> list[Cell]:
    """The grid, ordered so that a partial sweep is still a usable table.

    Repeat is the outermost loop on purpose. If the sweep is interrupted, an outer
    repeat loop leaves one complete observation of every cell rather than five
    observations of the first family and none of the rest -- the first is a result with
    weak error bars, the second is not a comparison at all.
    """
    only_on = config.get("only_on") or {}
    unknown = set(only_on) - set(config["families"])
    if unknown:
        # A restriction naming a family that is not in the sweep silently does nothing,
        # and the usual cause is a rename -- so the neural families would quietly run on
        # every catalogue, which is hours of work nobody asked for.
        raise SystemExit(
            f"only_on names families not in this sweep: {sorted(unknown)}; "
            f"families are {sorted(config['families'])}"
        )

    out = []
    for repeat in range(config["repeats"]):
        for catalogue in config["catalogues"]:
            for family in config["families"]:
                if family in only_on and catalogue not in only_on[family]:
                    continue
                for reranker in config["rerankers"]:
                    out.append(Cell(catalogue, family, reranker, repeat))
    return out


def _completed(path: Path) -> set[tuple[str, str, str, int]]:
    """Cells already in a results file, so an interrupted sweep can resume."""
    if not path.exists():
        return set()
    frame = pd.read_csv(path)
    needed = {"dataset", "family", "reranker", "repeat"}
    if not needed <= set(frame.columns):
        return set()
    return {
        (str(r.dataset), str(r.family), str(r.reranker), int(r.repeat))
        for r in frame.itertuples()
    }


def run(config: dict[str, Any], out_dir: Path, resume: bool = True) -> pd.DataFrame:
    """Execute the grid and write ``runs.csv``, ``readings.csv`` and ``manifest.json``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    runs_path = out_dir / "runs.csv"
    readings_path = out_dir / "readings.csv"

    done = _completed(runs_path) if resume else set()
    if not resume and runs_path.exists():
        runs_path.unlink()
        readings_path.unlink(missing_ok=True)

    with ExclusiveLock(out_dir / ".measure.lock") as lock:
        checks = preflight(
            require_mains=config["require_mains"],
            max_busy_pct=config["max_busy_pct"],
            lock=lock,
        )
        book = manifest.build(config, preflight=checks)
        print(manifest.summary(book))
        print(f"  meter: {default_meter().name}   quantum: "
              f"{book['clock_quantum_seconds'] * 1000:.3f} ms")

        # Decided once, up front, and carried on every row. A busy machine does not make
        # the pipeline wrong -- the recommendations are identical -- it makes the cost
        # column wrong, and only the cost column. That is precisely the kind of damage
        # that survives review, so it is recorded as data rather than left to a note.
        busy = checks.machine_busy_pct
        trustworthy = busy is not None and busy <= config["trust_busy_pct"]
        book["trustworthy"] = trustworthy
        if not trustworthy:
            observed = "not sampled" if busy is None else f"{busy:.0f}% busy"
            print(
                f"  !! machine {observed} (trust threshold "
                f"{config['trust_busy_pct']:.0f}%): rows will be marked untrustworthy "
                "and must not be reported as measurements"
            )

        skipped = _resolve_catalogues(config)
        planned = [c for c in cells(config) if c.catalogue not in skipped]
        todo = [c for c in planned if c.key not in done]
        print(f"  {len(todo)} runs to do ({len(planned) - len(todo)} already present)\n")

        monitor = ConditionsMonitor().start()
        rows: list[dict[str, Any]] = []
        try:
            for index, cell in enumerate(todo, start=1):
                print(f"[{index}/{len(todo)}] {cell}", flush=True)
                row = _run_cell(cell, config, out_dir, readings_path)
                row["trustworthy"] = trustworthy
                row["busy_pct_at_start"] = busy
                rows.append(row)
                # Written after every cell rather than at the end: a sweep over the
                # larger catalogues runs for hours, and results that exist only in
                # memory are results that a power cut deletes.
                _append(runs_path, row)
        finally:
            conditions = monitor.stop()
            (out_dir / "conditions.json").write_text(
                json.dumps(conditions, indent=2), encoding="utf-8"
            )

        book["conditions"] = conditions
        book["skipped_catalogues"] = skipped
        (out_dir / "manifest.json").write_text(json.dumps(book, indent=2), encoding="utf-8")

        if conditions.get("conditions_changed"):
            # Loud, because the run completed and the table looks perfectly normal.
            print(
                "\n!! machine conditions changed during the sweep "
                f"(power={conditions['power_sources_seen']}, "
                f"frequency drop={conditions.get('frequency_drop', 0):.0%}). "
                "Cost figures across this run are not comparable to each other."
            )

    return pd.read_csv(runs_path) if runs_path.exists() else pd.DataFrame(rows)


def _resolve_catalogues(config: dict[str, Any]) -> dict[str, str]:
    """Load each catalogue once up front, returning those that must be skipped.

    Front-loaded so that a catalogue which is missing or too small is reported before
    any measurement begins, rather than after an hour of runs on the others.
    """
    skipped: dict[str, str] = {}
    for name in config["catalogues"]:
        try:
            dataset = catalogues.load(name)
        except FileNotFoundError as error:
            skipped[name] = f"not found: {error}"
            continue
        reason = viability(dataset, config["min_users"], config["min_items"])
        if reason:
            skipped[name] = reason
    for name, reason in skipped.items():
        print(f"  skipping {name}: {reason}")
    return skipped


def _run_cell(
    cell: Cell, config: dict[str, Any], out_dir: Path, readings_path: Path
) -> dict[str, Any]:
    """One measured run, with failures captured rather than raised."""
    base = {
        "dataset": cell.catalogue,
        "family": cell.family,
        "reranker": cell.reranker or "none",
        "repeat": cell.repeat,
    }
    try:
        dataset = catalogues.load(cell.catalogue)
        family = build(cell.family, **config["family_kwargs"].get(cell.family, {}))
        session = MeasurementSession(
            meter=default_meter() if config["energy"] else None,
            label=cell.family,
            meta={"catalogue": cell.catalogue, "repeat": cell.repeat},
        )
        result = run_pipeline(
            dataset,
            family,
            reranker=cell.reranker,
            n_candidates=config["n_candidates"],
            k=config["k"],
            n_users=config["n_users"],
            # Varied with the repeat so that repeats resample the users. Holding the
            # sample fixed would measure the same arithmetic five times and report its
            # scheduler jitter as the uncertainty on the result, which understates the
            # real spread and would make the break-even interval far too narrow.
            seed=config["seed"] + cell.repeat,
            session=session,
            lam=config["lam"],
            mu=config["mu"],
        )
        row = {**base, **result.as_row(), "status": "ok", "error": ""}
        row["below_quantum"] = ";".join(result.below_quantum_stages())
        row["n_items"] = dataset.n_items
        row["n_train_users"] = dataset.n_users
        row["density"] = dataset.stats.get("density")
        _append_readings(readings_path, result, cell)
        _append_per_user(out_dir / "per_user.csv", result, cell)
        print(
            f"      ndcg={result.metrics['ndcg']:.4f}  "
            f"once={result.once_cost():.4f}s  "
            f"per_request={result.per_request_cost():.3e}s"
        )
        return row
    # Broad on purpose: a failed cell must not end the sweep. Anything a family or
    # reranker can raise -- memory, linear algebra, a missing optional dependency --
    # becomes a recorded row rather than losing the runs that already succeeded.
    except Exception as error:
        print(f"      FAILED: {type(error).__name__}: {error}")
        return {
            **base,
            "status": "failed",
            "error": f"{type(error).__name__}: {error}",
            "traceback": traceback.format_exc(limit=5),
        }


def _append_readings(path: Path, result, cell: Cell) -> None:
    """Persist the raw per-stage readings beside the summary row.

    Kept because ``runs.csv`` holds derived costs. If the derivation is ever found to be
    wrong -- and one of them already was -- the readings can be reprocessed instead of
    the whole sweep being run again.
    """
    rows = []
    for reading in result.readings:
        row = reading.as_row()
        row.update(
            {
                "dataset": cell.catalogue,
                "family": cell.family,
                "reranker": cell.reranker or "none",
                "repeat": cell.repeat,
            }
        )
        rows.append(row)
    _append(path, rows)


def _append_per_user(path: Path, result, cell: Cell) -> None:
    """Persist one row per served user, for paired accuracy comparisons.

    Written with the user's row index rather than its position in the sample. Two runs
    of the same cell draw the same users but the *positions* mean nothing across runs,
    so pairing on position would silently compare different people -- producing a
    difference distribution that looks entirely normal.
    """
    if not result.per_user or result.user_rows is None:
        return
    frame = pd.DataFrame({name: values for name, values in result.per_user.items()})
    frame.insert(0, "user_row", [int(r) for r in result.user_rows])
    for key, value in (
        ("dataset", cell.catalogue),
        ("family", cell.family),
        ("reranker", cell.reranker or "none"),
        ("repeat", cell.repeat),
    ):
        frame[key] = value
    _append(path, frame.to_dict("records"))


def _append(path: Path, rows: dict[str, Any] | list[dict[str, Any]]) -> None:
    """Append rows, reconciling columns that differ between runs.

    Pandas rather than :mod:`csv`: a failed cell has a ``traceback`` column that a
    successful one does not, and an energy-enabled run has channel columns. Writing with
    :mod:`csv` would silently truncate later rows to the first row's fields.
    """
    frame = pd.DataFrame(rows if isinstance(rows, list) else [rows])
    if not path.exists():
        frame.to_csv(path, index=False)
        return
    existing = pd.read_csv(path)
    combined = pd.concat([existing, frame], ignore_index=True)
    combined.to_csv(path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument(
        "--out", type=Path, default=None, help="results directory (default results/<name>)"
    )
    parser.add_argument(
        "--fresh", action="store_true", help="discard existing results instead of resuming"
    )
    parser.add_argument("--repeats", type=int, default=None)
    parser.add_argument("--n-users", type=int, default=None)
    parser.add_argument(
        "--allow-battery",
        action="store_true",
        help="measure on battery anyway; the cost column will not be comparable",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    if args.repeats is not None:
        config["repeats"] = args.repeats
    if args.n_users is not None:
        config["n_users"] = args.n_users
    if args.allow_battery:
        config["require_mains"] = False

    out_dir = args.out or (REPO_ROOT / "results" / config["name"])
    frame = run(config, Path(out_dir), resume=not args.fresh)

    failures = frame[frame["status"] == "failed"] if "status" in frame else frame.iloc[:0]
    print(f"\nwrote {out_dir}  ({len(frame)} rows, {len(failures)} failed)")
    for row in failures.itertuples():
        print(f"  {row.dataset}/{row.family}: {row.error}")


if __name__ == "__main__":
    main()
