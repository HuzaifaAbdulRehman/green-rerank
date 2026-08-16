"""Is the energy axis measuring anything the clock does not already say?

This is the project's third claim, and it exists because of what happened when the
measurement backend was checked rather than trusted.

A great deal of green-computing work reports energy from ``codecarbon``. On hardware with
Intel RAPL counters that is a real measurement. On hardware without them -- Windows, most
laptops, any VM, and WSL2, all verified here -- codecarbon estimates CPU power from the
processor's rated TDP and a utilisation sample. If that estimate tracks utilisation
poorly, the reported energy degenerates into

    kWh ~ constant * seconds

and every "energy" result obtained that way is a wall-clock result in different units.
That is a testable statement, and this module tests it.

The test is a regression of reported energy on elapsed time. An R^2 at or near 1.0 means
the energy column carries no information the timing column did not already have. It is a
negative result if it holds, and the most transferable thing in the project: it does not
depend on recommender systems at all.

Measured on the development machine before any of this was built, with a graded load of
0/1/2/4/8 busy workers for 20 s each, codecarbon reported CPU power moving from 1.501 W
to 1.815 W -- a 1.21x range across the full span from idle to saturation -- while
reporting 0 % CPU utilisation throughout, and billing RAM a constant 10.000 W that
dominated the total. The fully loaded window reported *less* total energy than the idle
one. That is what motivated CPU-seconds as the primary unit.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Agreement:
    """How closely one cost measure tracks another.

    Attributes:
        n: number of paired observations.
        r_squared: fraction of variance in ``estimate`` explained by a straight line in
            ``reference``. Near 1.0 means the estimate is a rescaled copy.
        slope: fitted conversion factor.
        spearman: rank correlation. Separated from ``r_squared`` on purpose -- an
            estimate can be a poor *linear* fit while still ranking methods correctly,
            and for choosing between families the ranking is what matters.
        rank_preserved: whether the estimate orders the observations exactly as the
            reference does.
        relative_spread: spread of the estimate-to-reference ratio, as a fraction of its
            median. Zero means a perfectly constant conversion.
    """

    n: int
    r_squared: float
    slope: float
    spearman: float
    rank_preserved: bool
    relative_spread: float

    @property
    def is_rescaled_clock(self) -> bool:
        """Whether the estimate is, to a good approximation, the reference rescaled.

        The threshold is deliberately strict. The claim being tested is strong -- "this
        column carries no independent information" -- so it should require a fit that
        leaves almost nothing unexplained.
        """
        return self.r_squared >= 0.99 and self.relative_spread <= 0.05

    def summary(self) -> str:
        verdict = (
            "carries no information beyond the reference"
            if self.is_rescaled_clock
            else "carries some information beyond the reference"
        )
        return (
            f"n={self.n}  R^2={self.r_squared:.4f}  slope={self.slope:.4g}  "
            f"spearman={self.spearman:.4f}  ratio spread={self.relative_spread:.3f}  "
            f"-> {verdict}"
        )


def agreement(estimate: np.ndarray, reference: np.ndarray) -> Agreement:
    """Compare an estimated cost against a directly measured one.

    Args:
        estimate: the column under suspicion -- typically codecarbon kWh.
        reference: the column believed to be sound -- typically CPU-seconds.

    Raises:
        ValueError: if fewer than three paired observations are supplied. Two points
            define a line exactly, so an R^2 computed from them is 1.0 by construction
            and would "prove" the claim on no evidence.
    """
    estimate = np.asarray(estimate, dtype=float).ravel()
    reference = np.asarray(reference, dtype=float).ravel()

    if estimate.shape != reference.shape:
        raise ValueError(f"shape mismatch: {estimate.shape} against {reference.shape}")

    finite = np.isfinite(estimate) & np.isfinite(reference)
    estimate, reference = estimate[finite], reference[finite]
    if estimate.size < 3:
        raise ValueError(
            "need at least three paired observations; two points fit a line exactly and "
            "would report R^2 = 1.0 regardless of the data"
        )

    # A reference that never varies cannot explain anything, and asking polyfit to fit a
    # line through it is numerically ill-posed -- it warns and returns an arbitrary
    # slope. Answering the question directly is both correct and quieter.
    if float(np.ptp(reference)) == 0.0:
        slope, r_squared = 0.0, 0.0
    else:
        slope, intercept = np.polyfit(reference, estimate, 1)
        predicted = slope * reference + intercept
        residual = float(np.sum((estimate - predicted) ** 2))
        total = float(np.sum((estimate - estimate.mean()) ** 2))
        r_squared = 1.0 - residual / total if total > 0 else 0.0

    spearman = _spearman(estimate, reference)
    rank_preserved = bool(
        np.array_equal(np.argsort(np.argsort(estimate)), np.argsort(np.argsort(reference)))
    )

    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(reference > 0, estimate / reference, np.nan)
    ratio = ratio[np.isfinite(ratio)]
    if ratio.size and np.median(ratio) != 0:
        spread = float((ratio.max() - ratio.min()) / abs(np.median(ratio)))
    else:
        spread = float("inf")

    return Agreement(
        n=int(estimate.size),
        r_squared=float(r_squared),
        slope=float(slope),
        spearman=spearman,
        rank_preserved=rank_preserved,
        relative_spread=spread,
    )


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Rank correlation, computed directly to avoid a scipy.stats import here.

    Ties are averaged, which is what makes this agree with the textbook definition on
    data containing repeated values -- and repeated values are common when a cost column
    is quantised by the scheduler tick.
    """
    ranked_a, ranked_b = _rank(a), _rank(b)
    if ranked_a.std() == 0 or ranked_b.std() == 0:
        return 0.0
    return float(np.corrcoef(ranked_a, ranked_b)[0, 1])


def _rank(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="stable")
    ranks = np.empty(values.size, dtype=float)
    ranks[order] = np.arange(values.size, dtype=float)

    # Average the ranks of tied values.
    _, inverse, counts = np.unique(values, return_inverse=True, return_counts=True)
    for index in np.flatnonzero(counts > 1):
        tied = inverse == index
        ranks[tied] = ranks[tied].mean()
    return ranks


def energy_axis_report(readings, energy_channel: str = "codecarbon.total_kwh") -> dict:
    """Test the energy column against CPU-seconds and wall-clock, over real readings.

    Returns a mapping with one :class:`Agreement` per reference. Both references are
    reported because they fail differently: agreeing with wall-clock means the estimate
    is a stopwatch, while agreeing with CPU-seconds means it at least tracks work.
    """
    energy = np.array([r.channels.get(energy_channel, np.nan) for r in readings], dtype=float)
    cpu = np.array([r.cpu_seconds for r in readings], dtype=float)
    wall = np.array([r.wall_seconds for r in readings], dtype=float)

    usable = np.isfinite(energy)
    if usable.sum() < 3:
        return {
            "available": False,
            "reason": (
                f"only {int(usable.sum())} readings carry {energy_channel}; "
                "the energy backend was absent or reported nothing"
            ),
        }

    return {
        "available": True,
        "channel": energy_channel,
        "vs_cpu_seconds": agreement(energy[usable], cpu[usable]),
        "vs_wall_seconds": agreement(energy[usable], wall[usable]),
    }
