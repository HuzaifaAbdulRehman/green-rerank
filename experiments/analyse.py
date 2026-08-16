"""Turn a results directory into the three claims, as tables.

Separated from :mod:`experiments.sweep` because measurement and interpretation have
different failure modes and different costs. A sweep takes hours and must not be re-run
because a table needed reformatting; an analysis takes a second and will be re-run many
times. Keeping the raw readings on disk means every reported number can be traced back
to the window it came from, and a mistake in the derivation costs a second rather than
an afternoon.

The analysis refuses to run on rows the sweep marked untrustworthy. That refusal is the
point: an untrustworthy row is not a slightly worse row, it is a cost figure taken while
another process held the CPU, and it will look completely ordinary in a table.

Usage::

    python -m experiments.analyse --results results/main
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from green_rerank.analysis import (
    CostSample,
    Point,
    crossover_interval,
    dominated,
    frontier,
    regime_table,
    retraining_table,
)
from green_rerank.pipeline import PER_REQUEST_STAGES, Stage

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Traffic levels the regime table is reported at. Spread over decades because the whole
#: claim is that the answer changes with volume -- a table over a narrow range would show
#: one winner and imply the question was not worth asking.
VOLUMES = [1, 10, 100, 1_000, 10_000, 100_000, 1_000_000]

#: Retraining cadences, in requests between retrains. ``None`` is "trained once and
#: served forever" -- the assumption the plain break-even makes and no deployment
#: honours -- and is kept first as the baseline the rest is read against.
RETRAIN_INTERVALS = [None, 1_000_000, 100_000, 10_000, 1_000, 100]


def load_runs(directory: Path, allow_untrustworthy: bool = False) -> pd.DataFrame:
    """Read ``runs.csv``, dropping failures and refusing contaminated measurements."""
    frame = pd.read_csv(directory / "runs.csv")

    failed = frame[frame.get("status", "ok") == "failed"] if "status" in frame else frame.iloc[:0]
    frame = frame[frame.get("status", "ok") == "ok"] if "status" in frame else frame
    if len(failed):
        print(f"  {len(failed)} failed runs excluded")

    if "trustworthy" in frame.columns and not allow_untrustworthy:
        bad = frame[~frame["trustworthy"].astype(bool)]
        if len(bad):
            raise SystemExit(
                f"{len(bad)} of {len(frame)} rows were measured on a busy machine and "
                "are marked untrustworthy. Their cost column reflects CPU contention, "
                "not the families being compared.\nRe-run the sweep on an idle machine, "
                "or pass --allow-untrustworthy to inspect them anyway (the output is "
                "not a measurement)."
            )
    return frame


def label_of(family: str, reranker: str) -> str:
    return family if reranker in ("none", "", None) else f"{family}+{reranker}"


def cost_samples(frame: pd.DataFrame) -> list[CostSample]:
    """One :class:`CostSample` per configuration, gathering its repeats.

    Repeats are kept as observations rather than averaged here, because the crossover
    interval needs the spread and an average would silently discard it.
    """
    samples = []
    for (family, reranker), group in frame.groupby(["family", "reranker"], sort=False):
        group = group.sort_values("repeat")
        samples.append(
            CostSample(
                label=label_of(family, reranker),
                once=group["cpu_once"].astype(float).tolist(),
                per_request=group["cpu_per_request"].astype(float).tolist(),
            )
        )
    return samples


def cost_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Per-configuration costs and accuracy, with the spread across repeats.

    The spread column is not decoration. On this hardware repeated measurements of
    *identical* work differ by tens of percent, and a difference between two families
    smaller than that is not a difference.
    """
    rows = []
    for (family, reranker), group in frame.groupby(["family", "reranker"], sort=False):
        row: dict[str, Any] = {
            "family": family,
            "reranker": reranker,
            "repeats": len(group),
            "ndcg": group["ndcg"].median(),
            "recall": group["recall"].median(),
            "exposure_parity": group["exposure_parity"].median(),
            "cpu_once": group["cpu_once"].median(),
            "cpu_per_request": group["cpu_per_request"].median(),
        }
        for column, name in (("cpu_once", "once"), ("cpu_per_request", "per_request")):
            values = group[column].astype(float)
            median = values.median()
            row[f"spread_{name}"] = (
                float((values.max() - values.min()) / median) if median > 0 else float("nan")
            )
        for stage in Stage:
            row[f"cpu_{stage.label}"] = group[f"cpu_{stage.label}"].median()
        rows.append(row)
    return pd.DataFrame(rows).sort_values("cpu_per_request")


def breakeven_table(frame: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    """Every pair of configurations, with a bootstrapped crossover."""
    samples = cost_samples(frame)
    rows = []
    for i, a in enumerate(samples):
        for b in samples[i + 1 :]:
            result = crossover_interval(a, b, seed=seed)
            rows.append(
                {
                    "a": result.a,
                    "b": result.b,
                    "n_requests": result.n_requests,
                    "lo": result.lo,
                    "hi": result.hi,
                    "replicates_crossing": result.exists_fraction,
                    "repeats": result.n_repeats,
                    "stable": result.is_stable,
                    "cheaper_below": result.cheaper_below,
                    "cheaper_above": result.cheaper_above,
                }
            )
    return pd.DataFrame(rows)


def rerank_share(frame: pd.DataFrame) -> pd.DataFrame:
    """What fraction of serving cost the rerank stage accounts for -- claim 2.

    Prior energy studies decompose a pipeline into fit, predict and evaluate. None of
    them costs a fairness reranker, so the share reported here is, as far as we found,
    the first figure of its kind.
    """
    rows = []
    per_request_labels = [s.label for s in PER_REQUEST_STAGES]
    for (family, reranker), group in frame.groupby(["family", "reranker"], sort=False):
        if reranker in ("none", "", None):
            continue

        # The share is computed per run and then taken as a median -- not as a ratio of
        # two medians. The distinction is not pedantry: the two disagree by 2.7
        # percentage points for GRU4Rec, which is the endpoint of the range this study
        # quotes, and an earlier draft had the report's table using one statistic and
        # its summary sentence the other.
        #
        # Median of ratios is the right one. Each run is an observation *of the share*,
        # so the median of those observations estimates it directly; a ratio of medians
        # is a ratio of two separately-summarised quantities and has no such reading
        # when the numerator and denominator are distributed differently, which they
        # are whenever training or retrieval is much noisier than reranking.
        serving = group[[f"cpu_{label}" for label in per_request_labels]].sum(axis=1)
        rerank = group[f"cpu_{Stage.RERANK.label}"]
        share = (rerank / serving).median()
        multiplier = (serving / (serving - rerank)).median()

        rows.append(
            {
                "family": family,
                "reranker": reranker,
                "cpu_rerank": rerank.median(),
                "cpu_serving_total": serving.median(),
                "rerank_share_of_serving": share,
                "cpu_rerank_setup": group[f"cpu_{Stage.RERANK_SETUP.label}"].median(),
                # How much more expensive serving became. The honest framing of the
                # cost: a deployer is not choosing whether to pay for reranking in the
                # abstract, they are choosing to multiply their serving cost.
                "serving_multiplier": multiplier,
            }
        )
    return pd.DataFrame(rows)


def frontier_table(frame: pd.DataFrame, volumes: list[float] | None = None) -> pd.DataFrame:
    """Which configurations are worth deploying, at each traffic level.

    Evaluated at several volumes rather than one because cost depends on volume, so the
    frontier does too. A single-volume frontier is a claim about a traffic level the
    paper usually does not state.
    """
    volumes = volumes or VOLUMES
    samples = {s.label: s.line() for s in cost_samples(frame)}
    accuracy = {
        label_of(f, r): g["ndcg"].median()
        for (f, r), g in frame.groupby(["family", "reranker"], sort=False)
    }

    rows = []
    for volume in volumes:
        points = [
            Point(label=label, accuracy=accuracy[label], cost=line.at(volume), n_requests=volume)
            for label, line in samples.items()
        ]
        on = frontier(points)
        off = dominated(points)
        rows.append(
            {
                "n_requests": volume,
                "frontier": ", ".join(p.label for p in on),
                "dominated": ", ".join(p.label for p in off),
                "cheapest": min(points, key=lambda p: p.cost).label,
                "most_accurate": max(points, key=lambda p: p.accuracy).label,
            }
        )
    return pd.DataFrame(rows)


def regimes(frame: pd.DataFrame, volumes: list[float] | None = None) -> pd.DataFrame:
    lines = [s.line() for s in cost_samples(frame)]
    return pd.DataFrame(regime_table(lines, volumes or VOLUMES))


def retraining(frame: pd.DataFrame, n_requests: float = 100_000) -> pd.DataFrame:
    """How the verdict shifts as the model is retrained more often.

    Evaluated at one traffic level so the only thing varying is cadence. A family that
    wins by amortising expensive training over many requests pays that cost again on
    every retrain, and the winner can change part-way down this table -- which is the
    point, and is invisible in any figure reporting energy per run.
    """
    lines = [s.line() for s in cost_samples(frame)]
    return pd.DataFrame(retraining_table(lines, RETRAIN_INTERVALS, n_requests))


def _cell(column: str, value: Any) -> str:
    """Format one value for a report table.

    Written rather than delegated to ``DataFrame.to_markdown`` for two reasons: that
    path needs an extra dependency purely to draw pipes, and it applies one float format
    to every column. Here a cost spanning 1e-6 to 1e2 needs scientific notation while an
    NDCG needs four decimals, and a request count needs thousands separators to be
    readable at all -- ``13736`` and ``137360`` are hard to tell apart in a column.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "--"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if not isinstance(value, (int, float)):
        return str(value)
    if column in ("n_requests", "lo", "hi") or column.startswith("cost."):
        return f"{value:,.0f}" if abs(value) >= 1 else f"{value:.3g}"
    if column.startswith(("cpu_", "wall_")) or column == "cost":
        return f"{value:.3e}"
    if column.startswith(("spread_", "rerank_share", "replicates_")):
        return f"{value:.1%}"
    if isinstance(value, float):
        return f"{value:.4f}"
    return f"{value:,}"


def _markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_no rows_\n"
    columns = list(frame.columns)
    rows = [
        [_cell(c, v) for c, v in zip(columns, record, strict=True)]
        for record in frame.itertuples(index=False)
    ]
    widths = [
        max(len(str(column)), *(len(row[i]) for row in rows)) for i, column in enumerate(columns)
    ]

    def line(cells: list[str]) -> str:
        return "| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells)) + " |"

    return "\n".join(
        [line([str(c) for c in columns]), "|-" + "-|-".join("-" * w for w in widths) + "-|"]
        + [line(row) for row in rows]
    ) + "\n"


def analyse(directory: Path, allow_untrustworthy: bool = False) -> dict[str, pd.DataFrame]:
    """Produce every table for every catalogue in a results directory."""
    runs = load_runs(directory, allow_untrustworthy)
    out_dir = directory / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)

    produced: dict[str, pd.DataFrame] = {}
    sections: list[str] = []

    for catalogue, frame in runs.groupby("dataset", sort=False):
        n_items = int(frame["n_items"].iloc[0]) if "n_items" in frame else -1
        sections.append(f"\n## {catalogue}  ({n_items:,} items)\n")

        for name, table in (
            ("cost", cost_table(frame)),
            ("breakeven", breakeven_table(frame)),
            ("rerank_share", rerank_share(frame)),
            ("frontier", frontier_table(frame)),
            ("regimes", regimes(frame)),
            ("retraining", retraining(frame)),
        ):
            key = f"{catalogue}.{name}"
            produced[key] = table
            table.to_csv(out_dir / f"{catalogue}.{name}.csv", index=False)
            sections.append(f"\n### {name}\n\n{_markdown(table)}")

    (out_dir / "tables.md").write_text(
        f"# Results tables\n\nGenerated from `{directory}`.\n" + "".join(sections),
        encoding="utf-8",
    )
    return produced


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument(
        "--allow-untrustworthy",
        action="store_true",
        help="analyse rows measured on a busy machine; the output is not a measurement",
    )
    args = parser.parse_args()

    tables = analyse(args.results, args.allow_untrustworthy)
    for key, table in tables.items():
        print(f"\n=== {key} ===")
        print(table.to_string(index=False))
    print(f"\nwrote {args.results / 'tables'}")


if __name__ == "__main__":
    main()
