"""The efficiency frontier: what a unit of accuracy costs.

Reporting accuracy and cost in separate columns leaves the reader to do the trade-off in
their head, and they will do it badly -- a model 1 % more accurate for 60x the energy
reads as "slightly better" in a table sorted by accuracy. The frontier makes dominated
options visible: a family is *dominated* if some other family is at least as accurate and
no more expensive, and a dominated family should never be deployed at any traffic level.

Two things this module deliberately refuses to do.

It does not collapse accuracy and cost into a single score. Any such score embeds an
exchange rate between them that belongs to the deployer, not to us, and hiding that rate
inside a metric is how "efficiency" numbers become unfalsifiable.

It does not report accuracy-per-joule as a ratio by default. Ratios of small numbers are
unstable and invite comparisons between models whose accuracies differ by less than their
own measurement noise. The frontier answers "which options are worth considering"; the
ratio is available for a chosen operating point.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    """One configuration's position on the accuracy/cost plane.

    Attributes:
        label: family, or family plus reranker.
        accuracy: higher is better. Must be a ground-truth measure -- an accuracy graded
            against the retrieval model's own scores is 1.0 by construction and would
            put every family on the same horizontal line.
        cost: lower is better, in whatever unit the study reports.
        n_requests: traffic level this cost was evaluated at, since cost depends on it.
    """

    label: str
    accuracy: float
    cost: float
    n_requests: float = 0.0
    unit: str = "cpu_seconds"


def dominates(a: Point, b: Point) -> bool:
    """Whether ``a`` is at least as good as ``b`` on both axes, and better on one."""
    at_least_as_good = a.accuracy >= b.accuracy and a.cost <= b.cost
    strictly_better = a.accuracy > b.accuracy or a.cost < b.cost
    return at_least_as_good and strictly_better


def frontier(points: list[Point]) -> list[Point]:
    """The non-dominated points, cheapest first.

    Ties -- identical accuracy and identical cost -- are all kept. Dropping one
    arbitrarily would hide that two genuinely different families landed in the same
    place, which is itself a result worth seeing.
    """
    keep = [p for p in points if not any(dominates(other, p) for other in points)]
    return sorted(keep, key=lambda p: (p.cost, -p.accuracy))


def dominated(points: list[Point]) -> list[Point]:
    """The points some other option beats outright, worst first.

    Reported explicitly because "this family should never be deployed" is a stronger and
    more useful statement than "this family scored slightly lower".
    """
    on_frontier = {id(p) for p in frontier(points)}
    return sorted(
        (p for p in points if id(p) not in on_frontier),
        key=lambda p: (-p.cost, p.accuracy),
    )


def accuracy_per_unit_cost(point: Point) -> float | None:
    """Accuracy bought per unit of cost, or ``None`` when cost is zero.

    ``None`` rather than infinity: a zero-cost reading on this hardware usually means the
    stage fell below the clock quantum, so an infinite efficiency would be an artefact of
    measurement resolution presented as a result.
    """
    if point.cost <= 0:
        return None
    return point.accuracy / point.cost


def frontier_at(points_by_volume: dict[float, list[Point]]) -> dict[float, list[str]]:
    """Which families are on the frontier at each traffic level.

    The frontier is not fixed: cost depends on request volume, so a family can enter or
    leave it as traffic grows. Showing that movement is the point where this project's
    two claims meet -- the break-even analysis says *when* the ordering changes, and this
    says what the change does to the set of options worth considering.
    """
    return {
        volume: [p.label for p in frontier(points)]
        for volume, points in sorted(points_by_volume.items())
    }
