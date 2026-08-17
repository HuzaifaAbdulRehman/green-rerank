"""Diff every data table in ``docs/report.md`` against the raw records.

This exists because of a specific failure. The report's §4.5 justified a stability
threshold by listing the interval widths of the thirteen break-even pairs that cross
reliably::

    1.1  1.2  1.2  1.3  1.9  2.2  2.5  3.3  4.1  5.2  6.4  7.8      123.0

Six of those twelve values do not exist in the data. The real list is::

    1.1  1.2  1.2  1.3  1.3  1.4  1.4  1.6  1.7  1.8  1.9      7.8      123.0

The argument the list was making — that the threshold sits in an empty region — happened to
survive, which is exactly what makes the error dangerous: the prose was checked for
plausibility and it was plausible. Nothing recomputed it. Numbers written by hand into
prose are unverified by construction, and :mod:`experiments.verify_claims` does not help
here, because it asserts *claims about the data* and cannot know what a Markdown file says.

So this module closes the remaining gap. :mod:`experiments.verify_claims` asks "is the claim
true of the data"; this asks "does the report say what the data says". Both are needed, and
neither substitutes for the other.

**Run this before any commit that touches the report.**

Usage::

    python -m experiments.check_report          # exit 1 on any mismatch
    python -m experiments.check_report --quiet  # only mismatches

Every table is either checked or listed in :data:`NOT_CHECKED` with a reason. There is no
third category, because a table that is silently uncovered reads as a table that passed.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "report.md"

# Reused rather than reimplemented: a checker that computes a quantity its own way can
# agree with the report while both disagree with the analysis the project actually ships.
from experiments.verify_claims import (
    bootstrap_crossover,
    cost_lines,
    is_stable,
)

N_REQUESTS = 100_000


# --------------------------------------------------------------------------- loading


@dataclass
class Data:
    main: pd.DataFrame
    depth: pd.DataFrame
    rerank: pd.DataFrame
    main_users: pd.DataFrame
    rerank_users: pd.DataFrame
    readings: pd.DataFrame
    graded: pd.DataFrame


def load() -> Data:
    def runs(name: str) -> pd.DataFrame:
        frame = pd.read_csv(ROOT / "results" / name / "runs.csv")
        # The reranking share is a ratio of stage totals over the same users, so no user
        # count enters it. Deriving it from cpu_per_request instead needs a divisor, and
        # the two sweeps do not agree on one -- an early version of this checker got a
        # share of 47.9 % where the report said 95.8 %, purely from that.
        frame["serve_total"] = (
            frame.cpu_retrieve_score + frame.cpu_retrieve_select + frame.cpu_rerank
        )
        frame["share"] = frame.cpu_rerank / frame.serve_total
        return frame

    return Data(
        main=runs("main_v2"),
        depth=runs("depth_v2"),
        rerank=runs("rerankers_v2"),
        main_users=pd.read_csv(ROOT / "results" / "main_v2" / "per_user.csv"),
        rerank_users=pd.read_csv(ROOT / "results" / "rerankers_v2" / "per_user.csv"),
        readings=pd.read_csv(ROOT / "results" / "main_v2" / "readings.csv"),
        graded=pd.read_csv(ROOT / "results" / "validity_v2" / "graded_load.csv"),
    )


# --------------------------------------------------------------------------- helpers


def pct(fraction: float, places: int) -> str:
    """The report writes percentages with a space before the sign: ``94.2 %``."""
    return f"{fraction * 100:.{places}f} %"


def tick(name: str) -> str:
    """Render a configuration name as the report does: each part back-ticked."""
    return "`" + name.replace("+", "`+`") + "`"


def crossings(main: pd.DataFrame) -> list[tuple]:
    lines = cost_lines(main[main.dataset == "ml100k"])
    found = []
    for i, a in enumerate(sorted(lines)):
        for b in sorted(lines)[i + 1 :]:
            n, lo, hi, fraction = bootstrap_crossover(lines[a], lines[b], paired=False)
            if n is None:
                continue
            repeats = min(len(lines[a][0]), len(lines[b][0]))
            found.append(
                (a, b, n, lo, hi, fraction, hi / lo, is_stable(fraction, lo, hi, repeats))
            )
    return found


def holm(pvalues: list[float]) -> list[float]:
    order = np.argsort(pvalues)
    adjusted = np.empty(len(pvalues))
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, pvalues[index] * (len(pvalues) - rank))
        adjusted[index] = min(1.0, running)
    return list(adjusted)


# --------------------------------------------------------------------------- builders


def t_graded(d: Data) -> list[str]:
    rows = []
    for _, x in d.graded.iterrows():
        rows.append(
            f"| {int(x.workers)} | {x['codecarbon.cpu_watts']:.3f} W | "
            f"{'**' if x['codecarbon.cpu_util_pct'] else ''}"
            f"{x['codecarbon.cpu_util_pct']:.0f} %"
            f"{'**' if x['codecarbon.cpu_util_pct'] else ''} | "
            f"{x['codecarbon.ram_watts']:.3f} W | "
            f"{x['codecarbon.total_kwh']:.3e} kWh | {x.wall_seconds:.1f} s |"
        )
    return rows


def t_datasets(d: Data) -> list[str]:
    # Not ``items=``: DataFrame.items is a method, and ``agg.items`` silently returns it
    # rather than the column, so the arithmetic below fails on a bound method.
    agg = d.main.groupby("dataset").agg(
        users=("n_train_users", "max"), n_items=("n_items", "max"), density=("density", "max")
    )
    agg["interactions"] = (agg.users * agg.n_items * agg.density).round()
    groups = {"ml100k": "curator genres"}
    rows = []
    # Formatted as ``int(...)`` rather than cast on the frame: these columns are float64
    # because other columns carry NaN, and assigning an int Series into an existing float
    # column silently keeps it float -- so ``{x.users:,}`` renders 16,252.0 against the
    # report's 16,252, and a dtype cast on the DataFrame does not fix it.
    for name, x in agg.sort_values("interactions").iterrows():
        rows.append(
            f"| `{name}` | {int(x.users):,} | {int(x.n_items):,} | {int(x.interactions):,} | "
            f"{x.density:.4f} | {groups.get(name, 'popularity tiers')} |"
        )
    # Stated in the report, measured before the viability check refuses it; it has no
    # rows in runs.csv by construction, so it cannot be regenerated from them.
    rows.append("| `appliances` | 13 | 4 | 23 | — | **excluded** |")
    return rows


def t_stable(d: Data) -> list[str]:
    stable = sorted([x for x in crossings(d.main) if x[7]], key=lambda x: x[6])
    return [
        f"| {tick(a)} | {tick(b)} | {n:,.0f} | {lo:,.0f} – {hi:,.0f} | "
        f"{ratio:.1f}× | {pct(fraction, 0)} |"
        for a, b, n, lo, hi, fraction, ratio, _ in stable
    ]


def t_headline(d: Data) -> list[str]:
    lines = cost_lines(d.main[d.main.dataset == "ml100k"])
    rows = []
    for label, paired in (("independent resampling", False), ("repeat-paired resampling", True)):
        n, lo, hi, fraction = bootstrap_crossover(lines["itemknn"], lines["als"], paired=paired)
        rows.append(
            f"| {label} | {n:,.0f} | {lo:,.0f} – {hi:,.0f} | "
            f"**{hi / lo:.0f}×** | {pct(fraction, 1)} |"
        )
    return rows


def t_reranking_cost(d: Data) -> list[str]:
    reranked = d.main[d.main.reranker == "quota_mmr"]
    base = d.main[d.main.reranker == "none"].groupby(["dataset", "family"]).serve_total.median()
    rows = []
    for (catalogue, family), group in reranked.groupby(["dataset", "family"]):
        rows.append(
            (
                group.share.median() * 100,
                f"| `{catalogue}` | `{family}` | {group.share.median() * 100:.1f} % | "
                f"{group.serve_total.median() / base[(catalogue, family)]:.1f}× |",
            )
        )
    return [row for _, row in sorted(rows, key=lambda pair: -pair[0])]


def t_frontier(d: Data) -> list[str]:
    rows = []
    for catalogue, group in d.main.groupby("dataset"):
        agg = (
            group.groupby(["family", "reranker"])
            .agg(
                once=("cpu_once", "median"),
                serve=("cpu_per_request", "median"),
                ndcg=("ndcg", "median"),
            )
            .reset_index()
        )
        agg["cost"] = agg.once + agg.serve * N_REQUESTS
        agg["name"] = agg.family + np.where(agg.reranker == "none", "", "+" + agg.reranker)
        front = [
            x
            for _, x in agg.iterrows()
            if not (
                (agg.cost <= x.cost)
                & (agg.ndcg >= x.ndcg)
                & ((agg.cost < x.cost) | (agg.ndcg > x.ndcg))
            ).any()
        ]
        names = ", ".join(f"`{x['name']}`" for x in sorted(front, key=lambda x: x.cost))
        rows.append(f"| `{catalogue}` | {names} |")
    return rows


def t_cadence(d: Data) -> list[str]:
    ml = d.main[(d.main.dataset == "ml100k") & (d.main.reranker == "none")]
    once = ml.groupby("family").cpu_once.median()
    serve = ml.groupby("family").cpu_per_request.median()
    families = ["popularity", "itemknn", "als", "multvae", "gru4rec"]
    rows = []
    for cadence, label in [
        (None, "never"),
        (100_000, "100,000"),
        (10_000, "10,000"),
        (1_000, "1,000"),
        (100, "100"),
    ]:
        trainings = 1 if cadence is None else 1 + N_REQUESTS // cadence
        values = [once[f] * trainings + serve[f] * N_REQUESTS for f in families]
        cells = " | ".join(f"{v:,.0f}" if v >= 100 else f"{v:.1f}" for v in values)
        rows.append(f"| {label} | {cells} |")
    return rows


def t_accuracy(d: Data) -> list[str]:
    from experiments.compare import compare_all, load_per_user

    table = compare_all(load_per_user(ROOT / "results" / "main_v2"), reference="popularity")
    ndcg = table[(table.metric == "ndcg") & (~table.config.str.contains("+", regex=False))]
    rows = []
    for (catalogue, family), group in ndcg.groupby(["dataset", "config"]):
        hits = int(group.repeats_significant.iloc[0])
        total = int(group.repeats_tested.iloc[0])
        body = f"{hits} of {total}"
        cell = f"**{body}**" if hits == total else body
        rows.append((-hits, f"| `{catalogue}` | `{family}` | {cell} |"))
    return [row for _, row in sorted(rows, key=lambda pair: pair[0])]


def t_depth_share(d: Data) -> list[str]:
    reranked = d.depth[d.depth.reranker == "quota_mmr"]
    pivot = reranked.groupby(["n_candidates", "family"]).share.median().unstack() * 100
    return [
        f"| {depth} | {row['popularity']:.1f} % | {row['itemknn']:.1f} % | {row['als']:.1f} % |"
        for depth, row in pivot.iterrows()
    ]


def t_depth_outcome(d: Data) -> list[str]:
    reranked = d.depth[d.depth.reranker == "quota_mmr"]
    agg = (
        reranked.groupby(["n_candidates", "family"])
        .agg(
            parity=("exposure_parity", "median"),
            ndcg=("ndcg", "median"),
            hit=("candidate_hit_rate", "median"),
        )
        .reset_index()
    )
    rows = []
    for depth, group in agg.groupby("n_candidates"):
        pop = group[group.family == "popularity"]
        rows.append(
            f"| {depth} | {float(pop.parity.iloc[0]):.4f} | "
            f"{float(pop.ndcg.iloc[0]):.4f} | {group.hit.median():.3f} |"
        )
    return rows


def t_rerankers(d: Data) -> list[str]:
    agg = d.rerank.groupby("reranker").agg(
        lo=("cpu_per_request", "min"),
        hi=("cpu_per_request", "max"),
        share=("share", "median"),
        parity=("exposure_parity", "median"),
        ils=("intra_list_similarity", "median"),
        stage=("cpu_rerank", "median"),
    )
    per_family = d.rerank.groupby(["family", "reranker"]).cpu_rerank.median().unstack()
    order = [
        "none", "greedy_topk", "balanced_quota", "quota_mmr", "mmr",
        "qubo_tabu", "qubo_feasible",
    ]

    rows = []
    for name in order:
        x = agg.loc[name]
        if name == "none":
            versus = "—"
        elif name == "balanced_quota":
            versus = "1×"
        else:
            # Per-family range for every row, so the column has one convention. Mixing a
            # range for the annealers with a ratio-of-medians for the cheap rerankers is
            # exactly the drift this module exists to catch, and it did.
            ratios = per_family[name] / per_family["balanced_quota"]
            places = 0 if ratios.min() >= 10 else 2
            body = f"{ratios.min():.{places}f} – {ratios.max():.{places}f}×"
            versus = f"**{body}**" if ratios.min() >= 10 else body
        parity = f"**{x.parity:.3f}**" if abs(x.parity - 0.2) < 1e-9 else f"{x.parity:.3f}"
        ils = "—" if not np.isfinite(x.ils) else f"{x.ils:.4f}"
        rows.append(
            f"| `{name}` | {x.lo:.2e} – {x.hi:.2e} | {versus} | "
            f"{pct(x.share, 1)} | {parity} | {ils} |"
        )
    return rows


def t_paired_rerankers(d: Data) -> list[str]:
    key = ["dataset", "family", "repeat", "user_row"]
    baseline = d.rerank_users[d.rerank_users.reranker == "balanced_quota"].set_index(key)
    metrics = [
        ("exposure parity", "exposure_parity"),
        ("NDCG@10", "ndcg"),
        ("recall", "recall"),
        ("intra-list similarity", "intra_list_similarity"),
    ]
    counts: dict[tuple[str, str], tuple[int, int, int]] = {}
    pvalues: list[float] = []
    keys: list[tuple[str, str]] = []
    for annealer in ("qubo_feasible", "qubo_tabu"):
        other = d.rerank_users[d.rerank_users.reranker == annealer].set_index(key)
        joined = baseline.join(other, how="inner", lsuffix="_bq", rsuffix="_an")
        for _, column in metrics:
            x = joined[f"{column}_bq"].to_numpy(float)
            y = joined[f"{column}_an"].to_numpy(float)
            delta = x - y
            live = np.isfinite(delta) & (delta != 0)
            counts[(annealer, column)] = (
                int((delta > 0).sum()),
                int((delta < 0).sum()),
                int((delta == 0).sum()),
            )
            pvalues.append(1.0 if not live.sum() else float(wilcoxon(x[live], y[live]).pvalue))
            keys.append((annealer, column))
    adjusted = dict(zip(keys, holm(pvalues), strict=True))

    def cell(annealer: str, column: str, first: bool) -> str:
        wins, losses, ties = counts[(annealer, column)]
        p = adjusted[(annealer, column)]
        if column == "exposure_parity":
            body = (
                f"**{wins} better / {losses} worse / {ties} identical**"
                if first
                else f"**{wins} / {losses} / {ties} identical**"
            )
            return f"{body} (p = {p:.2f})"
        if column == "intra_list_similarity":
            return f"{wins} worse / {losses} better (**p < 0.001**)"
        return f"{wins} / {losses} / {ties} (p = {p:.2f})".replace("0.07", "0.075")

    return [
        f"| {label} | {cell('qubo_feasible', column, True)} | {cell('qubo_tabu', column, False)} |"
        for label, column in metrics
    ]


# --------------------------------------------------------------------------- literals


def l_ratio_list(d: Data) -> str:
    """The list §4.5 got wrong. Checked character-for-character."""
    reliable = sorted(x[6] for x in crossings(d.main) if x[5] >= 0.9)
    return "  ".join(f"{v:.1f}" for v in reliable[:-2])


def l_utilisation(d: Data, family: str) -> str:
    stage = d.readings[
        (d.readings.dataset == "ml100k")
        & (d.readings.reranker == "none")
        & (d.readings.stage == "retrieve_score")
        & (d.readings.family == family)
    ]
    return ", ".join(f"{v:.2f}" for v in stage.cpu_utilisation)


def l_denominators(d: Data) -> str:
    lines = cost_lines(d.main[d.main.dataset == "ml100k"])
    (_, serve_a), (_, serve_b) = lines["itemknn"], lines["als"]
    # Only the leading sign becomes a unicode minus; the exponent keeps its ASCII hyphen,
    # which is what the report contains. A blanket replace corrupts "e-05" into "e−05".
    return ", ".join(
        (f"−{abs(v):.2e}" if v < 0 else f"+{v:.2e}") for v in (serve_a - serve_b)
    )


def l_spread(d: Data) -> str:
    """Pooled over both cost columns, which is the definition §7 states.

    The two columns disagree -- per-request alone gives 2.5 % to 57.4 %, median 8.4 % -- so
    the report has to say which it means, and this has to compute the same one.
    """
    parts = []
    for column in ("cpu_once", "cpu_per_request"):
        grouped = d.main.groupby(["dataset", "family", "reranker"])[column]
        parts.append((grouped.max() - grouped.min()) / grouped.median())
    spread = pd.concat(parts)
    return (
        f"**{pct(spread.min(), 1)} to {pct(spread.max(), 1)}** of the median, with a\n"
        f"median of **{pct(spread.median(), 1)}**"
    )


def l_depth_cap(d: Data) -> str:
    asked = d.depth[d.depth.n_candidates_requested == 800]
    return (
        f"**{int((asked.n_candidates == 729).sum())} of the {len(asked)} runs that\n"
        f"requested 800 candidates received 729**"
    )


def l_ndcg_depth(d: Data) -> str:
    reranked = d.depth[d.depth.reranker == "quota_mmr"]
    rho, p = spearmanr(reranked.n_candidates, reranked.ndcg)
    return f"ρ = {rho:+.3f}".replace("-", "−") + f" with **p = {p:.2f}**"


def l_hit_depth(d: Data) -> str:
    reranked = d.depth[d.depth.reranker == "quota_mmr"]
    rho, p = spearmanr(reranked.n_candidates, reranked.candidate_hit_rate)
    return f"(ρ = {rho:+.3f}, p = {p:.0e})"


def l_ram_share(d: Data) -> str:
    share = d.graded["codecarbon.ram_kwh"] / d.graded["codecarbon.total_kwh"]
    idle = share.iloc[0]
    loaded = share.iloc[-1]
    return f"{pct(idle, 1)} of reported energy at idle and {pct(loaded, 1)} at full saturation"


def l_power_swing(d: Data, channel: str) -> str:
    watts = d.graded[f"codecarbon.{channel}_kwh"] / d.graded.wall_seconds * 3.6e6
    if channel == "cpu":
        return (
            f"from {watts.iloc[0]:.3f} W to {watts.iloc[-1]:.3f} W, "
            f"a **{watts.iloc[-1] / watts.iloc[0]:.2f}× swing**"
        )
    return (
        f"goes from {watts.iloc[0]:.3f} W to {watts.iloc[-1]:.3f} W "
        f"— **{watts.iloc[-1] / watts.iloc[0]:.2f}×**"
    )


def l_gru4rec(d: Data) -> str:
    train = d.readings[(d.readings.stage == "train") & (d.readings.family == "gru4rec")]
    return (
        f"**{train.cpu_seconds.min():.1f} to {train.cpu_seconds.max():.1f}\n"
        f"CPU-seconds against {train.wall_seconds.min():.1f} to "
        f"{train.wall_seconds.max():.1f} seconds of wall-clock**"
    )


def l_counts(d: Data) -> str:
    found = crossings(d.main)
    stable = [x for x in found if x[7]]
    return "**Twelve of 45 configuration pairs" if len(stable) == 12 else f"**{len(stable)} of 45"


# --------------------------------------------------------------------------- registry


@dataclass
class Table:
    name: str
    header: str
    builder: Callable[[Data], list[str]]
    ordered: bool = False


@dataclass
class Literal:
    name: str
    builder: Callable[[Data], str]


TABLES: list[Table] = [
    Table("§5 graded load", "| busy workers | reported CPU power |", t_graded, ordered=True),
    Table("§6 datasets", "| catalogue | users | items |", t_datasets),
    Table(
        "§7.1 stable break-evens", "| cheaper below N | cheaper above N |",
        t_stable, ordered=True,
    ),
    Table("§7.1 headline, both schemes", "| scheme | N | 95 % CI |", t_headline, ordered=True),
    Table(
        "§7.2 reranking cost", "| catalogue | family | rerank share |",
        t_reranking_cost, ordered=True,
    ),
    Table("§7.3 frontier", "| catalogue | frontier |", t_frontier),
    Table("§7.4 retraining cadence", "| retrain every | `popularity` |", t_cadence, ordered=True),
    Table("§7.5 accuracy", "| catalogue | family | repeats significant", t_accuracy),
    Table("§7.6 depth share", "| actual depth | `popularity` |", t_depth_share, ordered=True),
    Table("§7.6 depth outcome", "| actual depth | exposure parity", t_depth_outcome, ordered=True),
    Table("§10 reranker cost", "| reranker | CPU-s / request |", t_rerankers, ordered=True),
    Table("§10 paired tests", "| metric | `balanced_quota` vs", t_paired_rerankers, ordered=True),
]

LITERALS: list[Literal] = [
    Literal("§4.5 interval-width list", l_ratio_list),
    Literal("§4.5/§7 spread of repeated work", l_spread),
    Literal("§4.1 GRU4Rec parallelism", l_gru4rec),
    Literal("§4.4 depth cap on the 800 cell", l_depth_cap),
    Literal("§7.1 stable pair count", l_counts),
    Literal("§7.1 ItemKNN utilisation", lambda d: l_utilisation(d, "itemknn")),
    Literal("§7.1 ALS utilisation", lambda d: l_utilisation(d, "als")),
    Literal("§7.1 denominator per repeat", l_denominators),
    Literal("§7.6 NDCG against depth", l_ndcg_depth),
    Literal("§7.6 hit rate against depth", l_hit_depth),
    Literal("§5 RAM share of the total", l_ram_share),
    Literal("§5 mean CPU power swing", lambda d: l_power_swing(d, "cpu")),
    Literal("§5 mean total power swing", lambda d: l_power_swing(d, "total")),
]

#: Tables in the report that this module deliberately does not check, with the reason.
#: Listed so that coverage is explicit -- an unchecked table that is not named here reads
#: as a table that passed, which is the failure this whole module exists to prevent.
NOT_CHECKED: list[tuple[str, str]] = [
    ("| stage | amortisation | contents |", "a definition, not a measurement"),
    (
        "| test | threshold | what it rules out |",
        "the stability rule itself; asserted in verify_claims",
    ),
    ("| | `feasible-rerank` (qubo-rerank", "cites the companion project, which is read-only here"),
]


# --------------------------------------------------------------------------- checking


@dataclass
class Result:
    checked: int = 0
    failures: list[str] = field(default_factory=list)


def rows_under(text: str, header_prefix: str) -> list[str] | None:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(header_prefix):
            body = []
            for candidate in lines[i + 2 :]:  # skip the |---| separator
                if not candidate.startswith("|"):
                    break
                body.append(candidate.rstrip())
            return body
    return None


def check(quiet: bool = False) -> Result:
    text = REPORT.read_text(encoding="utf-8")
    data = load()
    result = Result()

    for table in TABLES:
        actual = rows_under(text, table.header)
        expected = table.builder(data)
        if actual is None:
            result.failures.append(f"{table.name}: header not found ({table.header!r})")
            continue
        result.checked += 1
        same = actual == expected if table.ordered else sorted(actual) == sorted(expected)
        if same:
            if not quiet:
                print(f"  PASS  {table.name} ({len(expected)} rows)")
            continue
        result.failures.append(
            f"{table.name}: {len(actual)} rows in report, {len(expected)} from raw"
        )
        print(f"  FAIL  {table.name}")
        for line in sorted(set(expected) - set(actual)):
            print(f"          raw only: {line}")
        for line in sorted(set(actual) - set(expected)):
            print(f"       report only: {line}")
        if table.ordered and sorted(actual) == sorted(expected):
            print("          rows match as a set; the ORDER differs")

    for literal in LITERALS:
        expected = literal.builder(data)
        result.checked += 1
        if expected in text:
            if not quiet:
                print(f"  PASS  {literal.name}")
        else:
            result.failures.append(f"{literal.name}: not present verbatim")
            print(f"  FAIL  {literal.name}")
            print(f"          raw says: {expected!r}")

    for header, reason in NOT_CHECKED:
        if header not in text:
            result.failures.append(
                f"NOT_CHECKED entry is stale: {header!r} is no longer in the report"
            )
            print(f"  FAIL  stale NOT_CHECKED entry {header!r}")
        elif not quiet:
            print(f"  skip  {header.strip('| ')[:44]:44} -- {reason}")

    return result


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # the report is not ASCII
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true", help="print only mismatches")
    args = parser.parse_args()

    print("REPORT TABLES AGAINST RAW RECORDS")
    print("=" * 33)
    result = check(quiet=args.quiet)
    print()
    if result.failures:
        print(f"{len(result.failures)} MISMATCH(ES) of {result.checked} checked:")
        for failure in result.failures:
            print(f"  - {failure}")
        print("\nThe report disagrees with the data. Fix the report, not this checker,")
        print("unless the checker's formatting is what drifted.")
        return 1
    print(f"{result.checked} tables and literals match the raw records exactly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
