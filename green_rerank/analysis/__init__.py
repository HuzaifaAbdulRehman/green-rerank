"""Turning stage-resolved costs into the three claims.

- :mod:`~green_rerank.analysis.breakeven` -- at what request volume families cross.
- :mod:`~green_rerank.analysis.frontier` -- which options are worth deploying at all.
- :mod:`~green_rerank.analysis.validity` -- whether the energy axis measures anything
  the clock does not already say.
"""

from green_rerank.analysis.breakeven import (
    CostLine,
    CostSample,
    Crossover,
    CrossoverInterval,
    RetrainedCostLine,
    cheapest_at,
    crossover,
    crossover_interval,
    regime_table,
    retraining_table,
)
from green_rerank.analysis.frontier import (
    Point,
    accuracy_per_unit_cost,
    dominated,
    dominates,
    frontier,
    frontier_at,
)
from green_rerank.analysis.validity import Agreement, agreement, energy_axis_report

__all__ = [
    "Agreement",
    "CostLine",
    "CostSample",
    "Crossover",
    "CrossoverInterval",
    "Point",
    "RetrainedCostLine",
    "accuracy_per_unit_cost",
    "agreement",
    "cheapest_at",
    "crossover",
    "crossover_interval",
    "dominated",
    "dominates",
    "energy_axis_report",
    "frontier",
    "frontier_at",
    "regime_table",
    "retraining_table",
]
