"""Re-derive every claim from the rawest artifact that can support it.

Not a test. Tests assert the code is right; this asserts the *claims* are right.

**Rebuilt after an external audit found the previous version substantially
tautological.** It read `tables/*.csv` -- the output of `analyse.py` -- and asserted
those files said what the report said. "analyse.py wrote 112,730; the verifier confirms
analyse.py wrote 112,730" is not verification: a bug in the derivation is invisible to a
check that consumes the derivation.

So nothing here reads `tables/`. Every figure is recomputed from `runs.csv`,
`readings.csv`, `per_user.csv`, `graded_load.csv` or the manifests, with the arithmetic
written out locally even where that duplicates `analyse.py`. The duplication is the
point: two independent implementations that disagree is a signal, and one implementation
checking itself is not.

Each check declares its evidence class:

* ``RAW``   -- recomputed from measurement records, independent of the analysis code.
* ``ARITH`` -- deterministic arithmetic on RAW values (a cost model, a ratio).

A claim that can only be supported by a table the analysis wrote has no place here; if
one appears, it is a finding rather than a check.

    python -m experiments.verify_claims
    python -m experiments.verify_claims --results results/main_v2
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PASSED: list[str] = []
FAILED: list[str] = []


def check(claim: str, condition: bool, found: str, evidence: str = "RAW") -> None:
    (PASSED if condition else FAILED).append(claim)
    print(f"  [{evidence:5}] {'PASS' if condition else 'FAIL'}  {claim}\n           found: {found}")


def section(title: str) -> None:
    print(f"\n{title}\n{'=' * len(title)}")


def load(directory: Path) -> pd.DataFrame:
    frame = pd.read_csv(directory / "runs.csv")
    return frame[(frame.get("status", "ok") == "ok") & frame.get("trustworthy", True)]


# ------------------------------------------------------------------ recomputation


def cost_lines(frame: pd.DataFrame) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """``label -> (once[], per_request[])`` straight from the run rows."""
    out = {}
    for (family, reranker), group in frame.groupby(["family", "reranker"], sort=False):
        group = group.sort_values("repeat")
        label = family if reranker == "none" else f"{family}+{reranker}"
        out[label] = (
            group.cpu_once.to_numpy(dtype=float),
            group.cpu_per_request.to_numpy(dtype=float),
        )
    return out


def crossover_of(once_a, serve_a, once_b, serve_b):
    """``N`` where the two cost lines meet, or None. Written out, not imported.

    The sign test is on ``n``, not on the denominator. An earlier version of this
    function required ``serve_a > serve_b`` and so silently dropped every crossing where
    the roles are reversed -- both gaps negative, quotient still positive, a perfectly
    real crossing. It reported 2 stable pairs where there are 12, which is the kind of
    error a verifier that merely re-read the analysis could never have exposed.

    **A near-zero denominator is deliberately not clamped, and this is not an oversight.**
    A serving-cost gap of +3.8e-07 yields N = 14.6 million, and +1e-12 yields 5.6 trillion.
    Those values are mathematically correct -- near-parallel cost lines really do cross
    very far out -- and suppressing them here would hide the pathology inside a function
    that has no way to report it. It is caught by :func:`is_stable`, whose interval-width
    bound exists for exactly this case. Do not add a magnitude cutoff.
    """
    denominator = serve_a - serve_b
    if denominator == 0:
        return None
    n = (once_b - once_a) / denominator
    return float(n) if n > 0 else None


def bootstrap_crossover(a, b, paired: bool, n_boot: int = 2000, seed: int = 0):
    """Percentile bootstrap over repeats, under either resampling scheme.

    ``paired`` draws one index vector and applies it to both families; independent
    draws two. The two disagree exactly when a run's conditions affect both families
    together, which is the case a shared machine creates.
    """
    rng = np.random.default_rng(seed)
    (once_a, serve_a), (once_b, serve_b) = a, b
    n = min(len(once_a), len(once_b))
    crossings = []
    for _ in range(n_boot):
        ia = rng.integers(0, n, size=n)
        ib = ia if paired else rng.integers(0, n, size=n)
        value = crossover_of(
            float(np.median(once_a[ia])), float(np.median(serve_a[ia])),
            float(np.median(once_b[ib])), float(np.median(serve_b[ib])),
        )
        if value is not None:
            crossings.append(value)
    fraction = len(crossings) / n_boot
    if not crossings:
        return None, None, None, fraction
    v = np.asarray(crossings)
    return (
        float(np.median(v)),
        float(np.quantile(v, 0.025)),
        float(np.quantile(v, 0.975)),
        fraction,
    )


#: Stability, replacing the crossing-fraction-only rule the audit showed was inadequate.
#:
#: The old rule passed ItemKNN-vs-ALS at 94 % crossing while its interval spanned 123x.
#: A test that admits a two-order-of-magnitude interval is not a stability test.
#:
#: The width bound is 10x, and it is not tuned to the result: across the twelve other
#: stable pairs the CI ratio runs 1.1x to 7.8x, then jumps to 123x. The threshold sits in
#: an empty region of the observed distribution.
MIN_CROSSING = 0.9
MAX_CI_RATIO = 10.0
MIN_REPEATS = 3


def is_stable(fraction: float, lo: float | None, hi: float | None, repeats: int) -> bool:
    if lo is None or hi is None or lo <= 0:
        return False
    return fraction >= MIN_CROSSING and (hi / lo) < MAX_CI_RATIO and repeats >= MIN_REPEATS


# ------------------------------------------------------------------------ sections


def provenance(directory: Path, runs: pd.DataFrame) -> None:
    section(f"PROVENANCE -- {directory.name}")
    book = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    conditions = json.loads((directory / "conditions.json").read_text(encoding="utf-8"))

    check("zero failed runs",
          (pd.read_csv(directory / "runs.csv").status == "failed").sum() == 0,
          f"{len(runs)} usable rows")
    check("every row trustworthy", len(runs) == len(pd.read_csv(directory / "runs.csv")),
          f"{len(runs)} of {len(pd.read_csv(directory / 'runs.csv'))}")
    check("both repositories clean at measurement time",
          book["green_rerank"]["dirty"] is False and book["companion"]["dirty"] is False,
          f"green {book['green_rerank']['revision'][:7]} "
          f"dirty={book['green_rerank']['dirty']}, "
          f"companion {book['companion']['revision'][:7]} "
          f"dirty={book['companion']['dirty']}")
    check("mains power throughout, no condition change",
          conditions["power_sources_seen"] == ["ac"] and not conditions["conditions_changed"],
          f"{conditions['power_sources_seen']}, conditions_changed="
          f"{conditions['conditions_changed']}, {conditions['samples']} samples")

    below = runs.below_quantum.astype(str)
    check("no stage below the clock quantum",
          ((below == "") | (below == "nan")).all(),
          f"{(~((below == '') | (below == 'nan'))).sum()} rows flagged")


def breakeven(runs: pd.DataFrame) -> None:
    section("BREAK-EVEN -- method, and the headline pair separately")
    lines = cost_lines(runs[runs.dataset == "ml100k"])

    results = []
    labels = sorted(lines)
    for i, a in enumerate(labels):
        for b in labels[i + 1 :]:
            n, lo, hi, frac = bootstrap_crossover(lines[a], lines[b], paired=False)
            if n is None:
                continue
            repeats = min(len(lines[a][0]), len(lines[b][0]))
            results.append((a, b, n, lo, hi, frac, hi / lo if lo else np.inf,
                            is_stable(frac, lo, hi, repeats)))

    stable = [r for r in results if r[7]]
    check("the break-even method yields tight intervals on most pairs",
          len(stable) >= 10 and max(r[6] for r in stable) < MAX_CI_RATIO,
          f"{len(stable)} pairs stable under crossing>=90% and CI ratio<10x; "
          f"widest surviving interval {max(r[6] for r in stable):.1f}x")

    headline = [r for r in results if {r[0], r[1]} == {"itemknn", "als"}]
    if headline:
        a, b, n, lo, hi, frac, ratio, ok = headline[0]
        check("the ItemKNN-vs-ALS headline is NOT stably reportable",
              not ok, f"N={n:,.0f} CI[{lo:,.0f}, {hi:,.0f}] = {ratio:.0f}x span, "
                      f"{frac:.1%} crossing -> stable={ok}")

        # The mechanism, from the per-repeat costs rather than from the bootstrap.
        (oa, sa), (ob, sb) = lines["itemknn"], lines["als"]
        denominators = sa - sb
        check("the denominator changes sign across repeats",
              (denominators > 0).any() and (denominators <= 0).any(),
              f"serve difference per repeat: {[f'{d:+.2e}' for d in denominators]}")
        check("the numerator is stable while the denominator is not",
              float(np.ptp(ob - oa) / np.median(ob - oa)) < 0.15,
              f"numerator spread {float(np.ptp(ob - oa) / np.median(ob - oa)):.1%}, "
              f"denominator spans {denominators.min():+.2e} to {denominators.max():+.2e}")


def blas_confound(directory: Path) -> None:
    section("COST-UNIT CONFOUND -- BLAS thread count")
    readings = pd.read_csv(directory / "readings.csv")
    r = readings[
        (readings.dataset == "ml100k")
        & (readings.reranker == "none")
        & (readings.stage == "retrieve_score")
    ]
    util = {fam: g.cpu_utilisation.to_numpy(float) for fam, g in r.groupby("family")}

    check("ALS serving utilisation varies across repeats of identical work",
          "als" in util and float(np.ptp(util["als"])) > 0.5,
          f"als utilisation {[f'{v:.2f}' for v in util.get('als', [])]}")
    check("ItemKNN serving utilisation does not",
          "itemknn" in util and float(np.ptp(util["itemknn"])) < 0.2,
          f"itemknn utilisation {[f'{v:.2f}' for v in util.get('itemknn', [])]}")
    check("so CPU-seconds charges the same work differently between families",
          "als" in util and float(util["als"].max() / util["als"].min()) > 1.5,
          f"als utilisation ratio {float(util['als'].max() / util['als'].min()):.2f}x",
          evidence="ARITH")


def reranking(runs: pd.DataFrame) -> None:
    section("RERANKING COST AND WHAT IT BUYS")
    stages = ["cpu_retrieve_score", "cpu_retrieve_select", "cpu_rerank"]
    r = runs[runs.reranker != "none"].copy()
    r["share"] = r.cpu_rerank / r[stages].sum(axis=1)
    shares = r.groupby(["dataset", "family"]).share.median()
    check("the reranker is 80-98 % of per-request cost",
          0.80 <= shares.min() and shares.max() <= 0.98,
          f"{shares.min():.1%} - {shares.max():.1%} over {len(shares)} configurations")

    # What it bought, per configuration, from the run rows.
    bought = {}
    for (cat, fam), g in runs.groupby(["dataset", "family"]):
        before = g[g.reranker == "none"].exposure_parity.median()
        after = g[g.reranker != "none"].exposure_parity.median()
        if pd.notna(before) and pd.notna(after):
            bought[(cat, fam)] = (before, after)
    nothing = [k for k, (b, a) in bought.items() if a >= b]
    check("reranking does not improve parity on every configuration",
          len(nothing) > 0,
          f"{len(nothing)} of {len(bought)} bought nothing: {nothing}")


def parity_degeneracy(directory: Path) -> None:
    section("PARITY -- the corrected metric, per user")
    per_user = pd.read_csv(directory / "per_user.csv")
    for catalogue in ("luxury_beauty", "digital_music"):
        before = per_user[
            (per_user.dataset == catalogue)
            & (per_user.family == "popularity")
            & (per_user.reranker == "none")
            & (per_user.repeat == 0)
        ]
        after = per_user[
            (per_user.dataset == catalogue)
            & (per_user.family == "popularity")
            & (per_user.reranker != "none")
            & (per_user.repeat == 0)
        ]
        if before.empty or after.empty:
            continue
        merged = before.merge(after, on="user_row", suffixes=("_a", "_b"))
        changed = int((merged.exposure_parity_b != merged.exposure_parity_a).sum())
        check(f"{catalogue}/popularity: reranking changed parity for no user",
              changed == 0,
              f"{changed} of {len(merged)} users changed; "
              f"{merged.exposure_parity_a.iloc[0]:.4f} -> {merged.exposure_parity_b.iloc[0]:.4f}")


def depth(directory: Path) -> None:
    section("RETRIEVAL DEPTH")
    if not (directory / "runs.csv").exists():
        print("  absent")
        return
    from scipy import stats

    runs = load(directory)
    r = runs[runs.reranker != "none"].copy()
    stages = ["cpu_retrieve_score", "cpu_retrieve_select", "cpu_rerank"]
    r["share"] = r.cpu_rerank / r[stages].sum(axis=1)

    per_depth = r.groupby("n_candidates").agg(
        rerank=("cpu_rerank", "median"), share=("share", "median"),
        hit=("candidate_hit_rate", "median"), parity=("exposure_parity", "median"),
    )
    slope = float(np.polyfit(np.log(per_depth.index), np.log(per_depth.rerank), 1)[0])
    check("rerank cost scales superlinearly in depth",
          1.15 < slope < 1.35, f"O(n^{slope:.2f})")
    check("cost rises 28-35x over the depth range",
          28 <= per_depth.rerank.iloc[-1] / per_depth.rerank.iloc[0] <= 35,
          f"{per_depth.rerank.iloc[-1] / per_depth.rerank.iloc[0]:.1f}x", evidence="ARITH")
    check("exposure parity is flat across depth",
          float(per_depth.parity.max() - per_depth.parity.min()) < 0.01,
          f"{per_depth.parity.min():.4f} - {per_depth.parity.max():.4f}")

    rho, p = stats.spearmanr(r.n_candidates, r.ndcg)
    check("accuracy does NOT decline monotonically with depth (claim retracted)",
          p > 0.05, f"Spearman rho={rho:+.3f} p={p:.2f}")
    check("depth is confounded with the recall ceiling",
          float(per_depth.hit.iloc[-1] - per_depth.hit.iloc[0]) > 0.5,
          f"candidate_hit_rate {per_depth.hit.iloc[0]:.3f} -> {per_depth.hit.iloc[-1]:.3f}")

    capped = runs[runs.n_candidates != runs.n_candidates_requested]
    check("capped runs record the depth they actually ran at",
          len(capped) == 0 or (capped.n_candidates < capped.n_candidates_requested).all(),
          f"{len(capped)} capped rows"
          + (f", e.g. {int(capped.n_candidates_requested.iloc[0])} -> "
             f"{int(capped.n_candidates.iloc[0])}" if len(capped) else ""))


def rerankers(directory: Path) -> None:
    section("QUANTUM-INSPIRED RERANKERS vs THE CORRECT CLASSICAL BASELINE")
    if not (directory / "runs.csv").exists():
        print("  absent")
        return
    runs = load(directory)

    per_family = runs.groupby(["family", "reranker"]).agg(
        cost=("cpu_per_request", "median"), parity=("exposure_parity", "median"),
        ndcg_mean=("ndcg", "mean"), ndcg_median=("ndcg", "median"),
    )
    floor = per_family.xs("balanced_quota", level="reranker").parity
    check("balanced_quota reaches the parity floor on every family",
          bool((np.abs(floor - 0.2) < 1e-9).all()),
          f"{[round(v, 4) for v in floor]}")
    for annealer in ("qubo_feasible", "qubo_tabu"):
        got = per_family.xs(annealer, level="reranker").parity
        check(f"{annealer} reaches the same floor and no better",
              bool((np.abs(got - floor) < 1e-9).all()),
              f"{[round(v, 4) for v in got]}")

    cost_ratio = (
        per_family.xs("qubo_feasible", level="reranker").cost
        / per_family.xs("balanced_quota", level="reranker").cost
    )
    check("qubo_feasible costs ~290x balanced_quota for that identical floor",
          bool(((cost_ratio > 200) & (cost_ratio < 400)).all()),
          f"{[round(v) for v in cost_ratio]}x by family", evidence="ARITH")

    # Dominance is scoped to balanced_quota, and checked under both summaries because
    # the two disagree when pooled across families.
    qf = per_family.xs("qubo_feasible", level="reranker")
    bq = per_family.xs("balanced_quota", level="reranker")
    check("qubo_feasible is worse than balanced_quota on accuracy, both statistics",
          bool((qf.ndcg_mean < bq.ndcg_mean).all() and (qf.ndcg_median < bq.ndcg_median).all()),
          f"mean {[round(v, 4) for v in qf.ndcg_mean]} vs {[round(v, 4) for v in bq.ndcg_mean]}")

    # And explicitly NOT dominated by no-reranking -- the claim that would overreach.
    none = per_family.xs("none", level="reranker")
    worse = (qf.ndcg_mean < none.ndcg_mean)
    check("qubo_feasible is NOT strictly dominated by no-reranking",
          not bool(worse.all()),
          f"worse than no-reranking on {int(worse.sum())} of {len(worse)} families "
          f"({list(worse[worse].index)}), better on {list(worse[~worse].index)}")


def energy(directory: Path) -> None:
    """Checks on the graded-load result reported in §5.

    Two checks that used to live here have been **removed rather than relaxed**, because
    re-running the graded load at a clean revision refuted both. They asserted that
    utilisation "reads 0.0 % at every load" and that "the fully loaded run reports less
    energy than idle"; on ``results/validity_v2`` utilisation reads 5 % at two workers and
    the loaded run reports *more* energy than idle. They were passing against
    ``results/validity``, a superseded directory taken with dirty code -- so a stale
    default here was quietly certifying two claims the report has withdrawn. The default
    now points at the current directory, which is the only way this file can be trusted.

    What replaces them is the claim §5 actually rests on: the axis does not move enough to
    rank anything, because the channel that dominates the total is a compile-time constant.
    """
    section("ENERGY-AXIS VALIDITY")
    graded = pd.read_csv(directory / "graded_load.csv")

    check("RAM power is a constant",
          float(np.ptp(graded["codecarbon.ram_watts"])) == 0.0,
          f"{sorted(set(graded['codecarbon.ram_watts']))} W")

    ram_share = graded["codecarbon.ram_kwh"] / graded["codecarbon.total_kwh"]
    check("the constant RAM channel dominates the reported total",
          bool((ram_share > 0.75).all()),
          f"{ram_share.min():.1%} to {ram_share.max():.1%} of total energy")

    util = graded["codecarbon.cpu_util_pct"]
    check("utilisation reads zero under the heaviest load",
          float(util.iloc[-1]) == 0.0,
          f"{list(util)} % across {list(graded.workers)} workers")

    # Mean power over each window, not the single instantaneous value codecarbon reports
    # last: cpu_watts is a final sample and understates the swing.
    mean_cpu = graded["codecarbon.cpu_kwh"] / graded.wall_seconds * 3.6e6
    cpu_swing = float(mean_cpu.iloc[-1] / mean_cpu.iloc[0])
    check("the CPU channel responds, but far less than the true dynamic range",
          1.2 < cpu_swing < 3.0,
          f"{mean_cpu.iloc[0]:.3f} -> {mean_cpu.iloc[-1]:.3f} W = {cpu_swing:.2f}x "
          f"(a 15 W part swings ~10x)")

    mean_total = graded["codecarbon.total_kwh"] / graded.wall_seconds * 3.6e6
    total_swing = float(mean_total.iloc[-1] / mean_total.iloc[0])
    check("the reported energy axis barely moves from idle to saturated",
          total_swing < 1.15,
          f"{mean_total.iloc[0]:.3f} -> {mean_total.iloc[-1]:.3f} W = {total_swing:.2f}x, "
          f"against workloads spanning six orders of magnitude")

    check("the load was really applied",
          float(graded.expected_core_seconds.max()) >= 100,
          f"{graded.expected_core_seconds.max():.0f} core-seconds requested")


def retraining(runs: pd.DataFrame) -> None:
    section("RETRAINING CADENCE")
    ml = runs[(runs.dataset == "ml100k") & (runs.reranker == "none")]
    per_family = ml.groupby("family").agg(once=("cpu_once", "median"),
                                          serve=("cpu_per_request", "median"))
    n_requests, interval = 100_000, 100
    events = 1 + n_requests // interval
    for family in per_family.index:
        never = per_family.once[family] + n_requests * per_family.serve[family]
        often = events * per_family.once[family] + n_requests * per_family.serve[family]
        if family == "gru4rec":
            check("gru4rec total cost moves ~800x with cadence alone",
                  750 < often / never < 850,
                  f"{never:,.0f} -> {often:,.0f} CPU-s = {often / never:.0f}x",
                  evidence="ARITH")
    def multiplier(family: str) -> float:
        once, serve = per_family.once[family], per_family.serve[family]
        return (events * once + n_requests * serve) / (once + n_requests * serve)

    spread = [multiplier(f) for f in per_family.index]
    check("the cadence effect is not uniform across families",
          max(spread) / min(spread) > 100,
          ", ".join(f"{f} {multiplier(f):.0f}x" for f in per_family.index),
          evidence="ARITH")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "results" / "main_v2")
    parser.add_argument("--depth", type=Path, default=ROOT / "results" / "depth_v2")
    parser.add_argument("--rerankers", type=Path, default=ROOT / "results" / "rerankers_v2")
    # results/validity is superseded (dirty code, older companion). Defaulting to it made
    # this verifier certify two claims the report has since withdrawn -- see energy().
    parser.add_argument("--validity", type=Path, default=ROOT / "results" / "validity_v2")
    args = parser.parse_args()

    runs = load(args.results)
    provenance(args.results, runs)
    breakeven(runs)
    blas_confound(args.results)
    reranking(runs)
    parity_degeneracy(args.results)
    retraining(runs)
    depth(args.depth)
    rerankers(args.rerankers)
    energy(args.validity)

    section("SUMMARY")
    print(f"  {len(PASSED)} claims verified, {len(FAILED)} failed")
    print("  every check recomputed from runs.csv / readings.csv / per_user.csv /")
    print("  graded_load.csv -- no check reads a table written by analyse.py")
    for claim in FAILED:
        print(f"    FAILED: {claim}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
