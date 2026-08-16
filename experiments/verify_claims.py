"""Re-derive every claim this project makes, from the results on disk.

Not a test. Tests assert that the code is right; this asserts that the *claims* are
right -- that each sentence in the README and report is still supported by the data in
`results/`. Those drift apart silently, and this project has already caught itself doing
it once.

Every check names the claim it verifies and prints the value it found, so a failure says
which sentence to change rather than only that something is wrong.

    python -m experiments.verify_claims
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PASSED: list[str] = []
FAILED: list[str] = []


def check(claim: str, condition: bool, found: str) -> None:
    (PASSED if condition else FAILED).append(claim)
    print(f"  {'PASS' if condition else 'FAIL'}  {claim}\n        found: {found}")


def section(title: str) -> None:
    print(f"\n{title}\n{'=' * len(title)}")


def main() -> int:
    main_dir = ROOT / "results" / "main"
    runs = pd.read_csv(main_dir / "runs.csv")
    ok = runs[(runs.status == "ok") & runs.trustworthy]

    # ---------------------------------------------------------------- provenance
    section("PROVENANCE")
    check("170 runs, zero failures", len(runs) == 170 and (runs.status == "failed").sum() == 0,
          f"{len(runs)} runs, {(runs.status == 'failed').sum()} failed")
    check("every row trustworthy", len(ok) == 170, f"{len(ok)} of {len(runs)}")
    check("five catalogues", runs.dataset.nunique() == 5, ", ".join(sorted(runs.dataset.unique())))
    check("five families", runs.family.nunique() == 5, ", ".join(sorted(runs.family.unique())))
    check("five repeats per cell", set(runs.repeat) == {0, 1, 2, 3, 4},
          str(sorted(set(runs.repeat))))
    below = runs.below_quantum.astype(str)
    check("no stage below the clock quantum",
          ((below == "") | (below == "nan")).all(),
          f"{(~((below == '') | (below == 'nan'))).sum()} rows flagged")

    conditions = json.loads((main_dir / "conditions.json").read_text(encoding="utf-8"))
    check("mains power throughout, no throttling",
          conditions["power_sources_seen"] == ["ac"] and not conditions["conditions_changed"],
          f"{conditions['power_sources_seen']}, drop {conditions['frequency_drop']:.1%}, "
          f"{conditions['samples']} samples")

    # ------------------------------------------------------------ claim 1: break-even
    section("CLAIM 1 -- BREAK-EVEN")
    be = pd.read_csv(main_dir / "tables" / "ml100k.breakeven.csv")
    row = be[(be.a == "itemknn") & (be.b == "als")].iloc[0]
    check("ItemKNN vs ALS crosses at N = 112,730",
          abs(row.n_requests - 112730) < 100, f"N = {row.n_requests:,.0f}")
    check("95 % CI [51,128 - 180,720]",
          abs(row.lo - 51128) < 200 and abs(row.hi - 180720) < 400,
          f"[{row.lo:,.0f}, {row.hi:,.0f}]")
    check("95 % of replicates cross", abs(row.replicates_crossing - 0.95) < 0.01,
          f"{row.replicates_crossing:.1%}")
    check("the crossover is marked stable", bool(row.stable), str(bool(row.stable)))

    stable = be[be.stable & be.n_requests.notna()]
    check("13 of 45 pairs cross stably on ml100k",
          len(stable) == 13 and len(be) == 45, f"{len(stable)} of {len(be)}")

    # The crossover must actually be where the two cost lines meet.
    cost = pd.read_csv(main_dir / "tables" / "ml100k.cost.csv")
    knn = cost[(cost.family == "itemknn") & (cost.reranker == "none")].iloc[0]
    als = cost[(cost.family == "als") & (cost.reranker == "none")].iloc[0]
    n = row.n_requests
    left = knn.cpu_once + n * knn.cpu_per_request
    right = als.cpu_once + n * als.cpu_per_request
    check("both families cost the same at the crossover",
          abs(left - right) / left < 0.02, f"{left:.2f} vs {right:.2f} CPU-seconds")
    check("ItemKNN is cheaper below and dearer above",
          (knn.cpu_once < als.cpu_once) and (knn.cpu_per_request > als.cpu_per_request),
          f"train {knn.cpu_once:.3f} vs {als.cpu_once:.3f}; "
          f"serve {knn.cpu_per_request:.2e} vs {als.cpu_per_request:.2e}")

    # ----------------------------------------------------------- claim 2: reranking
    section("CLAIM 2 -- RERANKING COST")
    rr = ok[ok.reranker != "none"].copy()
    rr["serving"] = rr[["cpu_retrieve_score", "cpu_retrieve_select", "cpu_rerank"]].sum(axis=1)
    rr["share"] = rr.cpu_rerank / rr.serving
    rr["mult"] = rr.serving / (rr.serving - rr.cpu_rerank)
    g = rr.groupby(["dataset", "family"]).agg(share=("share", "median"), mult=("mult", "median"))
    check("reranker is 81-98 % of per-request cost",
          0.80 <= g.share.min() and g.share.max() <= 0.99,
          f"{g.share.min():.1%} - {g.share.max():.1%} over {len(g)} configurations")
    check("serving multiplier 5.3x - 43.8x",
          abs(g.mult.min() - 5.3) < 0.2 and abs(g.mult.max() - 43.8) < 0.3,
          f"x{g.mult.min():.1f} - x{g.mult.max():.1f}")
    pop_ml = g.loc[("ml100k", "popularity")]
    check("popularity on ml100k pays 24x its serving cost",
          abs(pop_ml.mult - 24.0) < 0.5, f"x{pop_ml.mult:.1f}")
    check("the share falls as retrieval gets more expensive",
          g.loc[("ml100k", "gru4rec")].share < g.loc[("ml100k", "popularity")].share,
          f"gru4rec {g.loc[('ml100k', 'gru4rec')].share:.1%} < "
          f"popularity {g.loc[('ml100k', 'popularity')].share:.1%}")

    # Reranking must actually improve fairness, or the cost buys nothing.
    plain = ok[(ok.dataset == "ml100k") & (ok.reranker == "none")].exposure_parity.median()
    reranked = ok[(ok.dataset == "ml100k") & (ok.reranker != "none")].exposure_parity.median()
    check("reranking improves exposure parity (lower is better)",
          reranked < plain, f"{plain:.4f} -> {reranked:.4f}")

    # ------------------------------------------------------------- claim 3: validity
    section("CLAIM 3 -- ENERGY VALIDITY")
    graded = pd.read_csv(ROOT / "results" / "validity" / "graded_load.csv")
    check("utilisation reads 0.0 % at every load, including 8 workers",
          (graded["codecarbon.cpu_util_pct"] == 0).all(),
          f"{list(graded['codecarbon.cpu_util_pct'])}")
    check("RAM power is exactly 10.000 W at every load",
          (graded["codecarbon.ram_watts"] == 10.0).all(),
          f"{sorted(set(graded['codecarbon.ram_watts']))}")
    watts = graded["codecarbon.cpu_watts"]
    check("CPU power moves only 1.11x across the full span",
          abs(watts.max() / watts.min() - 1.11) < 0.02,
          f"{watts.min():.3f} W -> {watts.max():.3f} W = {watts.max() / watts.min():.2f}x")
    total = graded["codecarbon.total_kwh"]
    check("the fully loaded run reports less energy than idle",
          total.iloc[-1] < total.iloc[0],
          f"{total.iloc[-1]:.3e} < {total.iloc[0]:.3e} kWh")
    check("the load really was applied (8 workers x 20 s)",
          graded.expected_core_seconds.max() >= 160,
          f"{graded.expected_core_seconds.max():.0f} core-seconds requested")

    verdict = json.loads((ROOT / "results" / "validity" / "verdict.json").read_text("utf-8"))
    agreement = verdict["sweep_agreement"]
    check("the rescaled-clock hypothesis is refuted (R^2 near 0.55, not 1.0)",
          "0.55" in agreement["vs_cpu_seconds"], agreement["vs_cpu_seconds"])
    check("144 real readings behind the agreement test", agreement["n"] == 144,
          f"n = {agreement['n']}")

    # ------------------------------------------------------------ claim 4: accuracy
    section("CLAIM 4 -- ACCURACY, PAIRED")
    paired = pd.read_csv(main_dir / "tables" / "paired.csv")
    plain_ndcg = paired[(paired.metric == "ndcg") & (~paired.config.str.contains("+", regex=False))]
    winners = plain_ndcg[plain_ndcg.significant]
    beat_pop = set(winners.dataset)
    check("ItemKNN beats popularity on 4 of 5 catalogues",
          len(set(winners[winners.config == "itemknn"].dataset)) == 4,
          ", ".join(sorted(set(winners[winners.config == "itemknn"].dataset))))
    check("on ml100k only gru4rec beats popularity",
          set(winners[winners.dataset == "ml100k"].config) == {"gru4rec"},
          str(set(winners[winners.dataset == "ml100k"].config)))
    check("every catalogue has at least one significant winner", len(beat_pop) == 5,
          ", ".join(sorted(beat_pop)))
    check("the reference really is popularity", set(paired.reference) == {"popularity"},
          str(set(paired.reference)))

    gru = cost[(cost.family == "gru4rec") & (cost.reranker == "none")].iloc[0]
    pop = cost[(cost.family == "popularity") & (cost.reranker == "none")].iloc[0]
    check("gru4rec costs 2.7 million times popularity's training",
          abs(gru.cpu_train / pop.cpu_train / 1e6 - 2.7) < 0.2,
          f"{gru.cpu_train:.1f} / {pop.cpu_train:.6f} = {gru.cpu_train / pop.cpu_train:.2e}")

    # ItemKNN and MultVAE dominated on ml100k: costlier than popularity, less accurate.
    at = lambda r, n=100_000: r.cpu_once + n * r.cpu_per_request  # noqa: E731
    for family in ("itemknn", "multvae"):
        row_f = cost[(cost.family == family) & (cost.reranker == "none")].iloc[0]
        check(f"{family} is dominated by popularity on ml100k",
              at(row_f) > at(pop) and row_f.ndcg < pop.ndcg,
              f"cost {at(row_f):.2f} vs {at(pop):.2f}, ndcg {row_f.ndcg:.4f} vs {pop.ndcg:.4f}")

    # --------------------------------------------------------------- claim 5: depth
    section("CLAIM 5 -- RETRIEVAL DEPTH")
    depth = pd.read_csv(ROOT / "results" / "depth" / "runs.csv")
    depth = depth[(depth.status == "ok") & depth.trustworthy]
    dr = depth[depth.reranker != "none"].copy()
    dr["serving"] = dr[["cpu_retrieve_score", "cpu_retrieve_select", "cpu_rerank"]].sum(axis=1)
    dr["share"] = dr.cpu_rerank / dr.serving
    by = dr.groupby(["family", "n_candidates"])

    check("depth varies over a 16x range", dr.n_candidates.max() / dr.n_candidates.min() == 16,
          f"{sorted(dr.n_candidates.unique())}")
    shares = by.share.median()
    check("share climbs from ~76 % at depth 50 to ~99 % at depth 800",
          abs(shares.min() - 0.759) < 0.01 and abs(shares.max() - 0.991) < 0.01,
          f"{shares.min():.1%} -> {shares.max():.1%}")

    costs = by.cpu_rerank.median()
    ratio = costs[("itemknn", 800)] / costs[("itemknn", 50)]
    check("rerank cost rises ~35x over the range", 30 < ratio < 40, f"{ratio:.0f}x")
    for family in ("als", "itemknn", "popularity"):
        sub = costs[family]
        slope = np.polyfit(np.log(sub.index), np.log(sub.to_numpy()), 1)[0]
        check(f"{family} rerank cost scales O(n^1.2-1.3)", 1.15 < slope < 1.32,
              f"O(n^{slope:.2f})")

    parity = dr.groupby("n_candidates").exposure_parity.median()
    check("exposure parity is flat across depth (no fairness benefit)",
          parity.max() - parity.min() < 0.005,
          f"{parity.min():.4f} - {parity.max():.4f}, spread {parity.max() - parity.min():.4f}")
    ndcg = dr.groupby("n_candidates").ndcg.median()
    check("accuracy falls with depth", ndcg.iloc[-1] < ndcg.iloc[0],
          f"{ndcg.iloc[0]:.4f} at depth {ndcg.index[0]} -> "
          f"{ndcg.iloc[-1]:.4f} at depth {ndcg.index[-1]}")

    # ---------------------------------------------------------- claim 6: retraining
    section("CLAIM 6 -- RETRAINING CADENCE")
    retrain = pd.read_csv(main_dir / "tables" / "ml100k.retraining.csv")
    never = retrain[retrain.retrain_every == "never"].iloc[0]
    often = retrain[retrain.retrain_every == "100"].iloc[0]
    check("gru4rec total cost moves 791x with cadence alone",
          abs(often["cost.gru4rec"] / never["cost.gru4rec"] - 791) < 5,
          f"{never['cost.gru4rec']:.0f} -> {often['cost.gru4rec']:.0f} CPU-seconds "
          f"= {often['cost.gru4rec'] / never['cost.gru4rec']:.0f}x")
    order_never = never["cost.als"] < never["cost.multvae"]
    order_often = often["cost.als"] < often["cost.multvae"]
    check("ALS and MultVAE swap order as retraining gets frequent",
          order_never != order_often,
          f"never: als {'<' if order_never else '>'} multvae; "
          f"every 100: als {'<' if order_often else '>'} multvae")

    # -------------------------------------------------------------------- summary
    section("SUMMARY")
    print(f"  {len(PASSED)} claims verified, {len(FAILED)} failed")
    for claim in FAILED:
        print(f"    FAILED: {claim}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
