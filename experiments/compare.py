"""Paired accuracy comparisons, so accuracy is held to the same standard as cost.

Cost in this project carries a bootstrap interval. Accuracy, until now, was a bare
mean -- two different standards of evidence inside one table. A reader comparing
NDCG 0.048 against 0.039 has no way to know whether that gap is a finding or noise, and
the cost column beside it is explicitly hedged.

The comparison is **paired on users**. Two families served the same sampled users, so
the question is not "is one mean bigger" but "does one win on more of the same users,
and by how much". Pairing removes between-user variance, which dominates: leave-one-out
NDCG is 0 for most users and ~1 for a few, so an unpaired test on those distributions
has almost no power regardless of how real the difference is.

Statistics are imported from the companion project (``experiments/paired.py``), not
rewritten. Two implementations of a Wilcoxon test that disagree is precisely the failure
this pair of projects exists to be above -- and a second implementation would be
plausible-looking either way.

**Effect size before p-value.** Every row reports the median paired difference and its
bootstrap interval first; the corrected p-value is reported alongside and never alone. A
significant difference of 0.0004 NDCG is a fact about sample size, not about
recommenders.

Usage::

    python -m experiments.compare --results results/main --reference itemknn
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.analyse import load_runs
from green_rerank.companion import companion_first

#: Metrics with a per-user value. Corpus-level measures (catalogue coverage, Gini) are
#: absent because there is no per-user quantity to pair -- they are properties of the
#: whole set of lists.
PAIRED_METRICS = ("ndcg", "recall", "exposure_parity", "intra_list_similarity")

#: Metrics where a *smaller* number is better, so that "better" counts the right way.
#: Getting this wrong inverts the verdict while leaving every number in the row correct.
LOWER_IS_BETTER = {"exposure_parity", "intra_list_similarity"}


def _companion_stats():
    """The companion's bootstrap interval and Holm correction.

    Wrapped because both repositories have a top-level ``experiments`` directory, so a
    plain ``from experiments.paired import holm`` finds *this* project's package. See
    :func:`green_rerank.companion.companion_first` for why neither reordering
    ``sys.path`` nor loading the file by path is sufficient.
    """
    with companion_first("experiments"):
        from experiments.paired import bootstrap_ci, holm
    return bootstrap_ci, holm


def load_per_user(directory: Path) -> pd.DataFrame:
    """Read the per-user metric table a sweep wrote."""
    path = directory / "per_user.csv"
    if not path.exists():
        raise SystemExit(
            f"{path} not found. It is written by experiments.sweep; a results directory "
            "produced before per-user metrics existed cannot be compared without "
            "re-running the sweep."
        )
    return pd.read_csv(path)


def compare_pair(
    a: pd.DataFrame, b: pd.DataFrame, metric: str, seed: int = 0
) -> dict | None:
    """One paired comparison of ``a`` against ``b`` on one metric.

    Returns ``None`` when the two runs did not serve the same users, rather than
    comparing them anyway. Mismatched pairing produces a difference distribution that
    looks completely normal and means nothing.
    """
    bootstrap_ci, _ = _companion_stats()
    from scipy import stats

    merged = a.merge(b, on="user_row", suffixes=("_a", "_b"))
    if merged.empty:
        return None

    left = merged[f"{metric}_a"].to_numpy(dtype=float)
    right = merged[f"{metric}_b"].to_numpy(dtype=float)

    # Intra-list similarity only exists for runs that built a similarity matrix, which
    # means runs with a reranker. Comparing a reranked run against a plain one on it
    # yields all-NaN, and reporting that as "no detectable difference" would state a
    # null result about a comparison that was never made.
    usable = np.isfinite(left) & np.isfinite(right)
    if usable.sum() < 3:
        return None
    left, right = left[usable], right[usable]
    difference = left - right

    better = difference < 0 if metric in LOWER_IS_BETTER else difference > 0
    worse = difference > 0 if metric in LOWER_IS_BETTER else difference < 0

    nonzero = difference[difference != 0.0]
    if nonzero.size == 0:
        # Identical on every user. A real outcome -- two families can return the same
        # lists -- and reporting p=1 is correct where running the test would raise.
        statistic, p_value = float("nan"), 1.0
    else:
        statistic, p_value = stats.wilcoxon(
            difference, alternative="two-sided", zero_method="wilcox"
        )

    low, high = bootstrap_ci(difference, seed=seed)
    return {
        "metric": metric,
        "n_users": int(difference.size),
        "median_diff": float(pd.Series(difference).median()),
        "ci_lo": float(low),
        "ci_hi": float(high),
        "better": int(better.sum()),
        "worse": int(worse.sum()),
        "tied": int((difference == 0.0).sum()),
        "statistic": float(statistic),
        "p_raw": float(p_value),
    }


def compare_all(
    per_user: pd.DataFrame, reference: str, seed: int = 0
) -> pd.DataFrame:
    """Compare every configuration against ``reference``, correcting once at the end.

    One correction across the whole reported family, not per metric. Correcting within
    each metric separately would let the family-wise error rate grow with the number of
    metrics reported -- which is a choice made after seeing the data.
    """
    _, holm = _companion_stats()

    per_user = per_user.copy()
    per_user["config"] = per_user.apply(
        lambda r: r["family"] if r["reranker"] in ("none", "", None)
        else f"{r['family']}+{r['reranker']}",
        axis=1,
    )
    available = sorted(per_user["config"].unique())
    if reference not in available:
        raise SystemExit(f"reference {reference!r} not among {available}")

    # Repeats resample users, so pooling them would put the same user in the table
    # several times with different neighbours and break the pairing. One repeat is
    # compared -- the first -- and the rest are what the *cost* interval is built from.
    first = per_user["repeat"].min()
    per_user = per_user[per_user["repeat"] == first]

    rows = []
    for catalogue, frame in per_user.groupby("dataset", sort=False):
        reference_rows = frame[frame["config"] == reference]
        if reference_rows.empty:
            continue
        for config in sorted(frame["config"].unique()):
            if config == reference:
                continue
            candidate = frame[frame["config"] == config]
            for metric in PAIRED_METRICS:
                if metric not in frame.columns or frame[metric].isna().all():
                    continue
                result = compare_pair(candidate, reference_rows, metric, seed)
                if result is None:
                    continue
                rows.append(
                    {"dataset": catalogue, "config": config, "reference": reference, **result}
                )

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(holm(rows))


def verdict(row) -> str:
    """Plain-language reading of one row, effect size first."""
    if not row["significant"]:
        return "no detectable difference"
    direction = "better" if row["better"] > row["worse"] else "worse"
    return f"{direction} on {row['better']}/{row['better'] + row['worse']} decided users"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument(
        "--reference",
        # The baseline every reported comparison in the study uses. It was `itemknn`
        # while the driver was being written, which meant re-running the analysis with
        # the documented command reproduced a different table from the report's.
        default="popularity",
        help=(
            "the configuration every other one is compared against "
            "(default: popularity, the baseline the report uses)"
        ),
    )
    parser.add_argument("--allow-untrustworthy", action="store_true")
    args = parser.parse_args()

    # Goes through load_runs purely for its refusal: per-user accuracy is unaffected by
    # CPU contention, but a directory whose costs are untrustworthy should not quietly
    # yield half a results table either.
    load_runs(args.results, args.allow_untrustworthy)

    table = compare_all(load_per_user(args.results), args.reference)
    if table.empty:
        print("no comparable pairs found")
        return

    table["verdict"] = table.apply(verdict, axis=1)
    table = table.sort_values(["dataset", "metric", "p_holm"])
    out = args.results / "tables" / "paired.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out, index=False)

    for (catalogue, metric), group in table.groupby(["dataset", "metric"], sort=False):
        print(f"\n=== {catalogue} -- {metric} (reference: {args.reference}) ===")
        for row in group.itertuples():
            print(
                f"  {row.config:<24} median diff {row.median_diff:+.4f} "
                f"[{row.ci_lo:+.4f}, {row.ci_hi:+.4f}]  "
                f"w/l/t {row.better}/{row.worse}/{row.tied}  "
                f"p={row.p_holm:.4f}  {row.verdict}"
            )
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
