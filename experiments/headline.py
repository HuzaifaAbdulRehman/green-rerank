"""Print every number the report quotes, straight from the results on disk.

This exists because of a mistake. The energy table in section 5 was transcribed from a
validity run that a later run then superseded, so the report quoted 1.12x and 7.459e-05
while the committed CSV said 1.11x and 7.371e-05. Nobody would have noticed: both sets
of numbers are plausible, both support the same conclusion, and the prose around them
did not change.

That is the project's own thesis pointed at its write-up. A results directory can be
perfectly reproducible and the *document describing it* can still drift, because the
document is written by hand and nothing checks it.

So: one command that regenerates every headline figure from the results. Updating the
report means copying from this output rather than from memory, and re-running it after
any new sweep says immediately whether the prose still matches the data.

It deliberately hardcodes no expected values. An audit that asserted "the crossover is
112,730" would need editing whenever the measurement legitimately changed, and would
eventually be edited to match rather than the other way round.

Usage::

    python -m experiments.headline --results results/main
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.analyse import load_runs
from green_rerank.pipeline import PER_REQUEST_STAGES

REPO_ROOT = Path(__file__).resolve().parents[1]


def _rule(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


def provenance(directory: Path, runs: pd.DataFrame) -> None:
    _rule("provenance")
    print(f"  runs                 {len(runs)}")
    print(f"  failures             {(runs.get('status', 'ok') == 'failed').sum()}")
    if "trustworthy" in runs:
        print(f"  trustworthy          {int(runs.trustworthy.sum())} / {len(runs)}")
    if "busy_pct_at_start" in runs:
        print(f"  machine busy at start {runs.busy_pct_at_start.iloc[0]:.1f} %")
    below = runs.get("below_quantum")
    if below is not None:
        n = int((below.notna() & (below.astype(str) != "") & (below.astype(str) != "nan")).sum())
        print(f"  rows with a below-quantum stage  {n}")
    print(f"  catalogues           {', '.join(sorted(runs.dataset.unique()))}")
    print(f"  families             {', '.join(sorted(runs.family.unique()))}")

    conditions = directory / "conditions.json"
    if conditions.exists():
        import json

        c = json.loads(conditions.read_text(encoding="utf-8"))
        print(f"  power sources seen   {c.get('power_sources_seen')}")
        print(f"  frequency drop       {c.get('frequency_drop', 0):.1%}  "
              f"over {c.get('samples')} samples")


def spread(runs: pd.DataFrame) -> None:
    """Run-to-run spread on identical work -- the noise floor every claim must clear."""
    _rule("run-to-run spread (max-min over median, across repeats)")
    rows = []
    for _, g in runs.groupby(["dataset", "family", "reranker"], sort=False):
        for column in ("cpu_once", "cpu_per_request"):
            values = g[column].astype(float)
            if values.median() > 0 and len(values) > 1:
                rows.append((values.max() - values.min()) / values.median())
    if rows:
        print(f"  min {min(rows):.1%}   median {np.median(rows):.1%}   max {max(rows):.1%}")


def breakeven(directory: Path) -> None:
    _rule("stable crossovers (claim 1)")
    total = stable = 0
    for path in sorted((directory / "tables").glob("*.breakeven.csv")):
        catalogue = path.name.split(".")[0]
        table = pd.read_csv(path)
        total += len(table)
        good = table[table.stable & table.n_requests.notna()].sort_values("n_requests")
        stable += len(good)
        for row in good.itertuples():
            print(
                f"  {catalogue:<14} {row.a:<20} vs {row.b:<20} "
                f"N={row.n_requests:>10,.0f}  [{row.lo:>9,.0f}, {row.hi:>9,.0f}]  "
                f"{row.replicates_crossing:.0%} cross"
            )
    print(f"\n  {stable} of {total} configuration pairs cross stably enough to report")


def reranking(runs: pd.DataFrame) -> None:
    _rule("reranker share of per-request cost (claim 2)")
    reranked = runs[runs.reranker != "none"].copy()
    if reranked.empty:
        print("  no reranked runs in this directory")
        return
    labels = [s.label for s in PER_REQUEST_STAGES]
    reranked["serving"] = reranked[[f"cpu_{x}" for x in labels]].sum(axis=1)
    reranked["share"] = reranked.cpu_rerank / reranked.serving
    reranked["multiplier"] = reranked.serving / (reranked.serving - reranked.cpu_rerank)

    # Retrieval depth became a recorded axis after the first sweeps, and the share
    # depends on it -- so it is printed when present rather than assumed, and a results
    # directory written before the axis existed still reports its shares.
    aggregations = {"share": ("share", "median"), "multiplier": ("multiplier", "median")}
    if "n_candidates" in reranked.columns:
        aggregations["depth"] = ("n_candidates", "median")

    grouped = reranked.groupby(["dataset", "family"]).agg(**aggregations)
    for (catalogue, family), row in grouped.iterrows():
        depth = f"  (depth {row.depth:.0f})" if "depth" in grouped.columns else ""
        print(f"  {catalogue:<14} {family:<11} {row.share:6.1%}  x{row.multiplier:5.1f}{depth}")
    print(f"\n  range: {grouped.share.min():.1%} - {grouped.share.max():.1%}, "
          f"multiplier x{grouped.multiplier.min():.1f} - x{grouped.multiplier.max():.1f}")


def frontier(directory: Path) -> None:
    _rule("efficiency frontier at N = 100,000 (claim: what to deploy)")
    for path in sorted((directory / "tables").glob("*.frontier.csv")):
        catalogue = path.name.split(".")[0]
        table = pd.read_csv(path)
        row = table[table.n_requests == 100_000]
        if row.empty:
            continue
        row = row.iloc[0]
        print(f"  {catalogue:<14} on:  {row['frontier']}")
        if isinstance(row["dominated"], str) and row["dominated"]:
            print(f"  {'':<14} off: {row['dominated']}")


def retraining(directory: Path) -> None:
    _rule("retraining cadence")
    for path in sorted((directory / "tables").glob("*.retraining.csv")):
        catalogue = path.name.split(".")[0]
        table = pd.read_csv(path)
        costs = [c for c in table.columns if c.startswith("cost.") and "+" not in c]
        if not costs:
            continue
        never, often = table.iloc[0], table.iloc[-1]
        worst = max(costs, key=lambda c: often[c] / never[c] if never[c] else 0)
        print(
            f"  {catalogue:<14} {worst.replace('cost.', ''):<11} "
            f"{often[worst] / never[worst]:>8,.0f}x  between never retraining and "
            f"every {table.retrain_every.iloc[-1]} requests"
        )
        # iterrows, not itertuples: the cost columns contain dots, which itertuples
        # renames to positional fields, so the labels cannot be looked up by name.
        for _, row in table.iterrows():
            order = sorted(costs, key=lambda c, r=row: r[c])
            print(f"    every {row['retrain_every']!s:<10} "
                  + " < ".join(c.replace("cost.", "") for c in order))
        break  # one catalogue is enough to show the mechanism; the CSVs hold the rest


def accuracy(directory: Path) -> None:
    _rule("paired accuracy (significant rows only)")
    path = directory / "tables" / "paired.csv"
    if not path.exists():
        print("  no paired.csv -- run experiments.compare")
        return
    table = pd.read_csv(path)
    good = table[table.significant]
    if good.empty:
        print(f"  nothing significant among {len(table)} comparisons")
        return
    for row in good.sort_values(["dataset", "metric"]).itertuples():
        print(
            f"  {row.dataset:<14} {row.config:<22} {row.metric:<16} "
            f"w/l/t {row.better}/{row.worse}/{row.tied}  p={row.p_holm:.4f}"
        )
    print(f"\n  {len(good)} of {len(table)} comparisons reach significance")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=REPO_ROOT / "results" / "main")
    parser.add_argument("--allow-untrustworthy", action="store_true")
    args = parser.parse_args()

    runs = load_runs(args.results, args.allow_untrustworthy)
    print(f"headline figures from {args.results}")
    provenance(args.results, runs)
    spread(runs)
    breakeven(args.results)
    reranking(runs)
    frontier(args.results)
    retraining(args.results)
    accuracy(args.results)
    print()


if __name__ == "__main__":
    main()
