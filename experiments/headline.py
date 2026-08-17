"""Print every number the report quotes, straight from the results on disk.

**This is a reporter, not a verifier. It contains no assertions and cannot fail.**

The distinction matters and has been confused once already. This module's job is that a
human transcribing the report copies numbers rather than misremembering them; it makes no
claim about whether any of those numbers support a conclusion. Nothing here can go red, so
a green run is not evidence of anything.

Falsifiable checking lives in :mod:`experiments.verify_claims`, which recomputes each
claim from the raw records and fails when the data stops supporting it. If you find
yourself citing *this* file as coverage for a claim, that is the mistake.

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


def energy_axis(directory: Path) -> None:
    """Section 5 -- the graded load. Was claimed as covered and was not.

    This section is the reason the tool exists: its table drifted from the data once,
    and the drift was invisible because nothing regenerated it.
    """
    _rule("energy axis (section 5)")
    path = directory / "graded_load.csv"
    if not path.exists():
        print(f"  {path} absent -- run experiments.validity")
        return
    graded = pd.read_csv(path)
    columns = {
        "codecarbon.cpu_watts": "CPU power",
        "codecarbon.cpu_util_pct": "utilisation",
        "codecarbon.ram_watts": "RAM power",
        "codecarbon.total_kwh": "total energy",
    }
    print(f"  {'workers':>7}  " + "  ".join(f"{name:>13}" for name in columns.values()))
    for _, row in graded.iterrows():
        cells = []
        for column in columns:
            value = row.get(column)
            cells.append(f"{value:>13.3e}" if column.endswith("kwh") else f"{value:>13.3f}")
        print(f"  {int(row['workers']):>7}  " + "  ".join(cells))

    watts = graded["codecarbon.cpu_watts"]
    total = graded["codecarbon.total_kwh"]
    print(f"\nCPU power span      {watts.max() / watts.min():.2f}x")
    print(f"  utilisation values  {sorted(set(graded['codecarbon.cpu_util_pct']))}")
    print(f"  RAM power values    {sorted(set(graded['codecarbon.ram_watts']))} W")
    print(f"  loaded < idle       {total.iloc[-1] < total.iloc[0]} "
          f"({total.iloc[-1]:.3e} vs {total.iloc[0]:.3e} kWh)")


def depth_sensitivity_numbers(directory: Path) -> None:
    """Section 7.6 -- including the confound the original section omitted."""
    _rule("retrieval depth (section 7.6)")
    if not (directory / "runs.csv").exists():
        print(f"  {directory} absent")
        return
    runs = load_runs(directory)
    reranked = runs[runs.reranker != "none"].copy()
    labels = [s.label for s in PER_REQUEST_STAGES]
    reranked["share"] = reranked.cpu_rerank / reranked[[f"cpu_{x}" for x in labels]].sum(axis=1)

    table = reranked.groupby("n_candidates").agg(
        rerank=("cpu_rerank", "median"),
        share=("share", "median"),
        hit_rate=("candidate_hit_rate", "median"),
        parity=("exposure_parity", "median"),
        ndcg=("ndcg", "median"),
    )
    print(f"  {'depth':>6} {'rerank CPU-s':>13} {'share':>8} {'hit rate':>9} "
          f"{'parity':>8} {'NDCG':>8}")
    for depth_value, row in table.iterrows():
        print(f"  {int(depth_value):>6} {row.rerank:>13.4f} {row.share:>7.1%} "
              f"{row.hit_rate:>9.3f} {row.parity:>8.4f} {row.ndcg:>8.4f}")

    slope = np.polyfit(np.log(table.index), np.log(table.rerank), 1)[0]
    print(f"\ncost scaling        O(n^{slope:.2f})")
    print(f"  cost ratio          {table.rerank.iloc[-1] / table.rerank.iloc[0]:.1f}x")
    print(f"  parity spread       {table.parity.max() - table.parity.min():.4f}")
    print(f"  hit-rate confound   {table.hit_rate.iloc[0]:.3f} -> {table.hit_rate.iloc[-1]:.3f}"
          "   (depth and the recall ceiling are collinear)")

    capped = runs[runs.n_candidates != runs.n_candidates_requested]
    if len(capped):
        print(f"  capped rows         {len(capped)}, e.g. "
              f"{int(capped.n_candidates_requested.iloc[0])} -> "
              f"{int(capped.n_candidates.iloc[0])}")


def reranker_families(directory: Path) -> None:
    """Section 10 -- the annealers against the correct classical baseline."""
    _rule("rerankers, against balanced_quota (section 10)")
    if not (directory / "runs.csv").exists():
        print(f"  {directory} absent")
        return
    runs = load_runs(directory)
    table = runs.groupby(["family", "reranker"]).agg(
        cost=("cpu_per_request", "median"),
        parity=("exposure_parity", "median"),
        ndcg_mean=("ndcg", "mean"),
        ndcg_median=("ndcg", "median"),
    )
    print(f"  {'family':>11} {'reranker':>15} {'CPU-s/req':>11} {'parity':>8} "
          f"{'NDCG mean':>10} {'NDCG med':>9}")
    for (family, reranker), row in table.sort_index().iterrows():
        print(f"  {family:>11} {reranker:>15} {row.cost:>11.3e} {row.parity:>8.4f} "
              f"{row.ndcg_mean:>10.4f} {row.ndcg_median:>9.4f}")

    if "balanced_quota" in table.index.get_level_values("reranker"):
        baseline = table.xs("balanced_quota", level="reranker")
        for annealer in ("qubo_feasible", "qubo_tabu"):
            if annealer not in table.index.get_level_values("reranker"):
                continue
            got = table.xs(annealer, level="reranker")
            ratio = got.cost / baseline.cost
            print(f"\n{annealer} vs balanced_quota:")
            print(f"    cost      {', '.join(f'{f} {v:.0f}x' for f, v in ratio.items())}")
            print(f"    parity    identical: "
                  f"{bool((abs(got.parity - baseline.parity) < 1e-9).all())}")
            print(f"    NDCG mean worse on {int((got.ndcg_mean < baseline.ndcg_mean).sum())}"
                  f" of {len(got)} families")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=REPO_ROOT / "results" / "main_v2")
    parser.add_argument("--depth", type=Path, default=REPO_ROOT / "results" / "depth_v2")
    parser.add_argument(
        "--rerankers", type=Path, default=REPO_ROOT / "results" / "rerankers_v2"
    )
    parser.add_argument("--validity", type=Path, default=REPO_ROOT / "results" / "validity")
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
    depth_sensitivity_numbers(args.depth)
    reranker_families(args.rerankers)
    energy_axis(args.validity)
    print()


if __name__ == "__main__":
    main()
