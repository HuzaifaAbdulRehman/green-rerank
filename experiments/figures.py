"""Figures for the report.

Two of the three claims are fundamentally geometric -- lines that cross, and a frontier
some options fall behind -- and a table states them far less clearly than a plot does.

The plotting choices are arguments, not decoration:

**Cost axes are logarithmic.** The costs here span roughly six orders of magnitude, from
a popularity lookup to a GRU4Rec training run. On a linear axis every family except the
most expensive one collapses onto the x-axis, which would hide precisely the differences
the study is about.

**The break-even plot draws the uncertainty band, not just the crossing.** A crossover is
a ratio of differences and can move by an order of magnitude under noise the eye cannot
see in the cost lines themselves. A bare vertical line at ``N`` would claim a precision
the measurement does not support.

**Nothing is plotted from untrustworthy rows.** The refusal lives in
:func:`experiments.analyse.load_runs`, which this module goes through.

Usage::

    python -m experiments.figures --results results/main
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

# Chosen before pyplot is imported: a sweep may run headless, and the interactive backend
# would either fail or silently block waiting for a window that nobody will close.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from experiments.analyse import cost_samples, label_of, load_runs
from green_rerank.analysis import Point, crossover_interval, frontier
from green_rerank.pipeline import PER_REQUEST_STAGES, Stage

#: One colour per family, held constant across every figure so a reader can follow a
#: family between plots without re-reading each legend.
COLOURS = {
    "popularity": "#8c8c8c",
    "itemknn": "#1f77b4",
    "als": "#d62728",
    "multvae": "#2ca02c",
    "gru4rec": "#9467bd",
}


def _colour(label: str) -> str:
    return COLOURS.get(label.split("+")[0], "#333333")


def _style(label: str) -> str:
    # Reranked variants share their family's colour and take a dashed line, so the cost
    # of reranking reads as a gap between two lines of one colour.
    return "--" if "+" in label else "-"


def cost_curves(runs, catalogue: str, out: Path) -> Path:
    """``C(N)`` for every configuration, with the crossings visible.

    This is the study's central figure: the whole argument is that these lines have
    different slopes and intercepts, so which one is lowest depends on where you look.
    """
    frame = runs[runs.dataset == catalogue]
    lines = [s.line() for s in cost_samples(frame)]
    volumes = np.logspace(0, 7, 200)

    figure, axis = plt.subplots(figsize=(8, 5.5))
    for line in sorted(lines, key=lambda ln: ln.once):
        axis.plot(
            volumes,
            [line.at(v) for v in volumes],
            label=line.label,
            color=_colour(line.label),
            linestyle=_style(line.label),
            linewidth=1.8,
        )

    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("requests served, N")
    axis.set_ylabel("total cost (CPU-seconds)")
    axis.set_title(f"Cost of serving N requests -- {catalogue}")
    axis.grid(True, which="both", alpha=0.15)
    axis.legend(fontsize=8, loc="upper left")

    path = out / f"{catalogue}.cost_curves.png"
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return path


def breakeven_band(runs, catalogue: str, a: str, b: str, out: Path) -> Path | None:
    """Two families' cost lines with the bootstrapped crossover drawn as a band.

    The band is the honest part. If it spans decades, the figure says so, and the reader
    can see that the crossing is not a number to act on.
    """
    frame = runs[runs.dataset == catalogue]
    samples = {s.label: s for s in cost_samples(frame)}
    if a not in samples or b not in samples:
        return None

    result = crossover_interval(samples[a], samples[b])
    volumes = np.logspace(0, 7, 200)

    figure, axis = plt.subplots(figsize=(8, 5))
    for label in (a, b):
        line = samples[label].line()
        axis.plot(
            volumes,
            [line.at(v) for v in volumes],
            label=label,
            color=_colour(label),
            linestyle=_style(label),
            linewidth=2.0,
        )
        # Every repeat as a faint line: the spread the bootstrap is drawn from, shown
        # rather than summarised, so the band's width is visibly earned.
        sample = samples[label]
        for once, per_request in zip(sample.once, sample.per_request, strict=True):
            axis.plot(
                volumes,
                once + volumes * per_request,
                color=_colour(label),
                alpha=0.18,
                linewidth=0.7,
            )

    if result.n_requests is not None:
        axis.axvline(result.n_requests, color="black", linewidth=1.0)
        if result.has_interval:
            axis.axvspan(result.lo, result.hi, color="black", alpha=0.10)
        # Anchored in axes coordinates on the y axis. Anchoring to `get_ylim()[0]`
        # placed the label using limits that autoscaling had not finished computing,
        # and on a log axis it landed off-canvas -- the annotation was silently absent
        # from the figure rather than misplaced within it.
        axis.annotate(
            f"N = {result.n_requests:,.0f}"
            + (f"\n[{result.lo:,.0f}, {result.hi:,.0f}]" if result.has_interval else "")
            + (f"\n{result.exists_fraction:.0%} of replicates cross"),
            xy=(result.n_requests, 0.04),
            xycoords=axis.get_xaxis_transform(),
            xytext=(8, 0),
            textcoords="offset points",
            fontsize=8,
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.8, "lw": 0},
        )
        subtitle = "" if result.is_stable else "  (unstable -- not reportable)"
    else:
        subtitle = "  (no crossover: one family dominates)"

    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("requests served, N")
    axis.set_ylabel("total cost (CPU-seconds)")
    axis.set_title(f"{a} vs {b} -- {catalogue}{subtitle}")
    axis.grid(True, which="both", alpha=0.15)
    axis.legend(fontsize=9, loc="upper left")

    path = out / f"{catalogue}.breakeven.{a}_vs_{b}.png".replace("+", "-")
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return path


def efficiency_frontier(runs, catalogue: str, out: Path, n_requests: float = 100_000) -> Path:
    """Accuracy against cost at a stated traffic level, with the frontier drawn.

    The traffic level is in the title because the frontier moves with it. A frontier
    plotted without one is a claim about a volume the reader cannot see.
    """
    frame = runs[runs.dataset == catalogue]
    lines = {s.label: s.line() for s in cost_samples(frame)}
    accuracy = {
        label_of(f, r): g["ndcg"].median()
        for (f, r), g in frame.groupby(["family", "reranker"], sort=False)
    }
    points = [
        Point(label, accuracy[label], line.at(n_requests), n_requests)
        for label, line in lines.items()
    ]
    on_frontier = {p.label for p in frontier(points)}

    figure, axis = plt.subplots(figsize=(8, 5.5))
    for point in points:
        best = point.label in on_frontier
        axis.scatter(
            point.cost,
            point.accuracy,
            s=130 if best else 60,
            color=_colour(point.label),
            marker="o" if "+" not in point.label else "^",
            edgecolor="black" if best else "none",
            linewidth=1.2,
            zorder=3 if best else 2,
            alpha=1.0 if best else 0.55,
        )
        axis.annotate(
            point.label,
            (point.cost, point.accuracy),
            textcoords="offset points",
            xytext=(7, 4),
            fontsize=8,
            alpha=1.0 if best else 0.6,
        )

    edge = sorted((p for p in points if p.label in on_frontier), key=lambda p: p.cost)
    if len(edge) > 1:
        axis.plot(
            [p.cost for p in edge],
            [p.accuracy for p in edge],
            color="black",
            linewidth=1.0,
            linestyle=":",
            zorder=1,
        )

    axis.set_xscale("log")
    axis.set_xlabel(f"cost of serving {n_requests:,.0f} requests (CPU-seconds)")
    axis.set_ylabel("NDCG@10 against the held-out item")
    axis.set_title(
        f"Efficiency frontier -- {catalogue}, N = {n_requests:,.0f}\n"
        "filled and outlined = non-dominated; triangles = with fairness reranker"
    )
    axis.grid(True, alpha=0.15)

    path = out / f"{catalogue}.frontier.png"
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return path


def stage_breakdown(runs, catalogue: str, out: Path) -> Path:
    """Where each family's per-request cost goes -- claim 2's figure.

    Two panels, because one axis cannot carry both questions honestly.

    The left panel is **share**, on a linear axis. A stacked bar on a *log* axis is a
    trap: ``log(a+b)`` is not ``log(a)+log(b)``, so a segment's visible width has no
    relationship to its contribution, and a figure whose entire claim is "the reranker
    is most of the cost" would be arguing that claim with meaningless widths.

    The right panel is **absolute** cost, on a log axis, because the totals genuinely
    span orders of magnitude. Kept separate so neither axis has to lie for the other.
    """
    frame = runs[runs.dataset == catalogue]
    labels, stacks = [], []
    stages = list(PER_REQUEST_STAGES)

    for (family, reranker), group in frame.groupby(["family", "reranker"], sort=False):
        labels.append(label_of(family, reranker))
        served = max(int(group["n_users"].median()), 1)
        stacks.append([group[f"cpu_{s.label}"].median() / served for s in stages])

    order = np.argsort([sum(s) for s in stacks])
    labels = [labels[i] for i in order]
    stacks = np.array([stacks[i] for i in order])
    totals = stacks.sum(axis=1)
    shares = stacks / np.where(totals[:, None] > 0, totals[:, None], 1.0)

    figure, (left_axis, right_axis) = plt.subplots(
        1, 2, figsize=(11, 0.5 * len(labels) + 2.8), gridspec_kw={"width_ratios": [2, 1]}
    )
    palette = {
        Stage.RETRIEVE_SCORE: "#4c78a8",
        Stage.RETRIEVE_SELECT: "#9ecae9",
        Stage.RERANK: "#e45756",
    }

    left = np.zeros(len(labels))
    for index, stage in enumerate(stages):
        left_axis.barh(
            labels,
            shares[:, index],
            left=left,
            label=stage.label,
            color=palette.get(stage, "#bbbbbb"),
        )
        left += shares[:, index]

    left_axis.set_xlim(0, 1)
    left_axis.set_xlabel("share of per-request cost")
    left_axis.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    left_axis.grid(True, axis="x", alpha=0.15)
    left_axis.legend(fontsize=8, loc="lower right")

    right_axis.barh(labels, totals, color=[_colour(x) for x in labels])
    right_axis.set_xscale("log")
    right_axis.set_xlabel("CPU-seconds per request")
    right_axis.set_yticklabels([])
    right_axis.grid(True, axis="x", alpha=0.15)

    figure.suptitle(f"Where per-request cost goes -- {catalogue}")

    path = out / f"{catalogue}.stages.png"
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return path


def retraining_curves(runs, catalogue: str, out: Path, n_requests: float = 1_000_000) -> Path:
    """Total cost against retraining cadence, at fixed traffic.

    The second axis the verdict turns on. The break-even figure varies traffic with the
    model trained once; this varies how often it is retrained with traffic held fixed,
    and the lines can reorder -- a family that wins by amortising an expensive training
    run stops winning once it pays for that run repeatedly.

    Traffic is fixed and stated in the title, because a cadence plot at an unstated
    volume is uninterpretable: the whole effect is a competition between a recurring
    once-cost and an accumulating per-request one.
    """
    frame = runs[runs.dataset == catalogue]
    lines = [s.line() for s in cost_samples(frame)]
    intervals = np.logspace(1, 6, 60)

    figure, axis = plt.subplots(figsize=(8, 5.5))
    for line in lines:
        axis.plot(
            intervals,
            [line.with_retraining(every).at(n_requests) for every in intervals],
            label=line.label,
            color=_colour(line.label),
            linestyle=_style(line.label),
            linewidth=1.8,
        )
        # The never-retrained floor, as a reference each staircase descends to.
        axis.axhline(line.at(n_requests), color=_colour(line.label), alpha=0.25, linewidth=0.7)

    axis.set_xscale("log")
    axis.set_yscale("log")
    # Frequent retraining on the left, because that is the expensive end and reading
    # left-to-right should mean "getting cheaper".
    axis.invert_xaxis()
    axis.set_xlabel("requests between retrains  (frequent <- -> rare)")
    axis.set_ylabel(f"total cost of {n_requests:,.0f} requests (CPU-seconds)")
    axis.set_title(
        f"Cost against retraining cadence -- {catalogue}, N = {n_requests:,.0f}\n"
        "faint horizontal lines are the never-retrained floor"
    )
    axis.grid(True, which="both", alpha=0.15)
    axis.legend(fontsize=8, loc="upper right")

    path = out / f"{catalogue}.retraining.png"
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return path


def all_figures(directory: Path, allow_untrustworthy: bool = False) -> list[Path]:
    runs = load_runs(directory, allow_untrustworthy)
    out = directory / "figures"
    out.mkdir(parents=True, exist_ok=True)

    made: list[Path] = []
    for catalogue in runs["dataset"].unique():
        made.append(cost_curves(runs, catalogue, out))
        made.append(stage_breakdown(runs, catalogue, out))
        made.append(efficiency_frontier(runs, catalogue, out))
        made.append(retraining_curves(runs, catalogue, out))

        # A panel per pair whose crossover is *stable*. Pairs where one family dominates
        # have nothing to show, and pairs whose crossing survives only a minority of
        # bootstrap replicates should not be given a figure at all: a plotted crossing
        # reads as a finding however the caption is worded, and drawing thirty of them
        # would bury the handful that are real.
        frame = runs[runs.dataset == catalogue]
        samples = cost_samples(frame)
        skipped = 0
        for i, a in enumerate(samples):
            for b in samples[i + 1 :]:
                result = crossover_interval(a, b, n_bootstrap=400)
                if not result.is_stable:
                    skipped += result.n_requests is not None
                    continue
                path = breakeven_band(runs, catalogue, a.label, b.label, out)
                if path is not None:
                    made.append(path)
        if skipped:
            # Stated rather than silent: a reader counting figures should know that
            # crossings were found and deliberately not drawn.
            print(f"  {catalogue}: {skipped} unstable crossover(s) not plotted")
    return made


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--allow-untrustworthy", action="store_true")
    args = parser.parse_args()

    made = all_figures(args.results, args.allow_untrustworthy)
    for path in made:
        print(path)
    print(f"\n{len(made)} figures in {args.results / 'figures'}")


if __name__ == "__main__":
    main()
