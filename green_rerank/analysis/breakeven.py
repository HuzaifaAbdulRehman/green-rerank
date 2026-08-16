"""Break-even analysis: at what request volume does one family overtake another?

This is the project's first claim, and it is a claim the existing literature cannot
make. Published energy studies report a figure per experimental run, which adds a cost
paid once to a cost paid per request. That sum answers no question a deployer has: a
model that trains for an hour then serves free, and one that trains instantly then burns
an hour serving, can report the same total and imply opposite decisions.

Modelling cost as a line instead

    C(N) = C_once + N * C_per_request

makes the comparison between two families a comparison between two lines, and two lines
with different slopes **cross**. The crossing point is a number a deployer can act on --
"below ~50,000 requests use the neighbourhood model, above it use the factor model" --
and it is not in any paper we found.

The units are deliberately left open. Everything here is linear, so a crossover computed
in CPU-seconds is the *same request count* as one computed in joules, provided the
conversion between them is a constant. That is what makes the analysis survive the fact
that energy could not be measured directly on the development hardware.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CostLine:
    """One family's cost as a function of requests served.

    Attributes:
        label: family name, for tables and figures.
        once: cost paid at deployment, whatever the traffic.
        per_request: cost of serving one request.
        unit: what the numbers are in. Carried so a figure cannot silently mix
            CPU-seconds with joules.
    """

    label: str
    once: float
    per_request: float
    unit: str = "cpu_seconds"

    def at(self, n_requests: float) -> float:
        """Total cost after serving ``n_requests``."""
        if n_requests < 0:
            raise ValueError("n_requests must be non-negative")
        return self.once + n_requests * self.per_request

    def with_retraining(self, every: float) -> RetrainedCostLine:
        """This model retrained every ``every`` requests.

        The plain line assumes a model is trained once and serves forever, which no
        deployment does. Under periodic retraining the one-off cost recurs, and a family
        whose training is expensive loses its amortisation advantage in proportion to
        how often it is retrained -- which can reverse the verdict entirely.
        """
        if every <= 0:
            raise ValueError("retraining interval must be positive")
        return RetrainedCostLine(self.label, self.once, self.per_request, every, self.unit)

    @classmethod
    def from_result(cls, result, unit: str = "cpu_seconds") -> CostLine:
        """Build from a :class:`~green_rerank.pipeline.runner.PipelineResult`."""
        label = result.family
        if result.reranker is not None:
            label = f"{result.family}+{result.reranker}"
        return cls(
            label=label,
            once=result.once_cost(),
            per_request=result.per_request_cost(),
            unit=unit,
        )


@dataclass(frozen=True)
class RetrainedCostLine:
    """A cost model that pays its training cost again every ``interval`` requests.

    No longer a straight line: it is a staircase, because training happens in whole
    events. Reporting it as a smoothed line would understate cost immediately after each
    retrain, which is exactly when a deployment is most likely to notice.
    """

    label: str
    once: float
    per_request: float
    interval: float
    unit: str = "cpu_seconds"

    def at(self, n_requests: float) -> float:
        if n_requests < 0:
            raise ValueError("n_requests must be non-negative")
        # One training event up front, then one more per completed interval.
        events = 1 + math.floor(n_requests / self.interval)
        return events * self.once + n_requests * self.per_request


@dataclass(frozen=True)
class Crossover:
    """Where two cost lines meet, if they meet at a request count that can occur.

    Attributes:
        cheaper_below: label of the family that is cheaper before the crossing.
        cheaper_above: label of the family that is cheaper after it.
        n_requests: the crossing point, or ``None`` when one family is cheaper
            everywhere.
        reason: why there is no crossing, when there is none.
    """

    a: str
    b: str
    n_requests: float | None
    cheaper_below: str | None = None
    cheaper_above: str | None = None
    reason: str = ""

    @property
    def exists(self) -> bool:
        return self.n_requests is not None


def crossover(a: CostLine, b: CostLine) -> Crossover:
    """The request count at which ``a`` and ``b`` cost the same.

    Solves ``a.once + N*a.per_request == b.once + N*b.per_request``.

    Returns a :class:`Crossover` whose ``n_requests`` is ``None`` when the lines do not
    cross at any non-negative request count. That case is reported rather than returned
    as a negative number, because a negative crossover is not a small crossover -- it
    means one family simply dominates, which is a different finding.
    """
    if a.unit != b.unit:
        raise ValueError(f"cannot compare {a.unit} against {b.unit}")

    slope_gap = a.per_request - b.per_request
    once_gap = b.once - a.once

    if math.isclose(slope_gap, 0.0, abs_tol=1e-15):
        # Parallel lines: whichever starts lower stays lower forever.
        if math.isclose(once_gap, 0.0, abs_tol=1e-15):
            return Crossover(a.label, b.label, None, reason="identical cost models")
        winner = a.label if a.once < b.once else b.label
        return Crossover(
            a.label,
            b.label,
            None,
            cheaper_below=winner,
            cheaper_above=winner,
            reason="equal per-request cost, so the lines never cross",
        )

    n = once_gap / slope_gap
    if n <= 0:
        winner = a.label if a.at(1.0) < b.at(1.0) else b.label
        return Crossover(
            a.label,
            b.label,
            None,
            cheaper_below=winner,
            cheaper_above=winner,
            reason="one family is cheaper at every non-negative request count",
        )

    # Below the crossing, the family with the smaller intercept leads.
    below = a.label if a.once < b.once else b.label
    above = b.label if below == a.label else a.label
    return Crossover(a.label, b.label, float(n), cheaper_below=below, cheaper_above=above)


# ---------------------------------------------------------------- with uncertainty


@dataclass(frozen=True)
class CostSample:
    """A family's cost as *repeated observations*, not a single figure.

    The crossover is a ratio of two differences, so it amplifies the noise in both. Two
    families whose per-request costs are 5.5e-5 and 6.6e-5 differ by 20 %, and if either
    figure carries 15 % run-to-run spread -- which measured repeats of identical work on
    this hardware do -- then the denominator can approach zero and the crossover can move
    by an order of magnitude, or cease to exist. Quoting a single ``N`` from one reading
    each would be false precision of the worst kind: precise, reproducible in form, and
    unsupported.

    Attributes:
        once: one deployment cost per repeat.
        per_request: one serving cost per repeat, aligned with ``once`` by repeat.
    """

    label: str
    once: Sequence[float]
    per_request: Sequence[float]
    unit: str = "cpu_seconds"

    def __post_init__(self) -> None:
        if len(self.once) != len(self.per_request):
            raise ValueError(
                f"{self.label}: {len(self.once)} once-costs against "
                f"{len(self.per_request)} per-request costs; they are paired by repeat"
            )
        if not self.once:
            raise ValueError(f"{self.label}: no observations")

    @property
    def n_repeats(self) -> int:
        return len(self.once)

    def line(self) -> CostLine:
        """The central estimate: medians, not means.

        Median because the noise here is one-sided. A background process can only make a
        run slower, never faster, so the distribution has a tail on the expensive side
        and a mean would track that tail rather than the machine's actual behaviour.
        """
        return CostLine(
            label=self.label,
            once=float(np.median(self.once)),
            per_request=float(np.median(self.per_request)),
            unit=self.unit,
        )

    def resample(self, rng: np.random.Generator) -> CostLine:
        """One bootstrap replicate.

        Repeat indices are drawn once and used for **both** costs, because they came
        from the same run. Resampling them independently would break the correlation
        between a run's training cost and its serving cost -- a moment of background
        load inflates both -- and would report an interval narrower than the truth.
        """
        picked = rng.integers(0, self.n_repeats, size=self.n_repeats)
        return CostLine(
            label=self.label,
            once=float(np.median(np.asarray(self.once, dtype=float)[picked])),
            per_request=float(np.median(np.asarray(self.per_request, dtype=float)[picked])),
            unit=self.unit,
        )


@dataclass(frozen=True)
class CrossoverInterval:
    """A crossover with the uncertainty that makes it reportable.

    Attributes:
        n_requests: median crossover across bootstrap replicates.
        lo, hi: percentile interval.
        exists_fraction: share of replicates in which the lines cross at all. This is
            the number that decides whether the finding may be stated. An interval
            computed from the 40 % of replicates that happened to cross is a selection
            effect, not a result, so a low fraction is a null result and is reported as
            one rather than as a wide interval.
        point: the crossover of the median lines, for comparison with the median of
            crossovers. A large gap between them means the estimate is unstable.
    """

    a: str
    b: str
    n_requests: float | None
    lo: float | None
    hi: float | None
    exists_fraction: float
    n_bootstrap: int
    cheaper_below: str | None = None
    cheaper_above: str | None = None
    point: float | None = None
    unit: str = "cpu_seconds"
    n_repeats: int = 0

    #: Below this share of replicates crossing, the crossover is not claimed.
    STABLE_FRACTION = 0.9

    #: Fewest repeats from which an interval may be quoted. A bootstrap over one
    #: observation returns that observation every time, so ``lo == hi`` -- which reads
    #: as perfect precision on the page and means the exact opposite. Three is the
    #: smallest number at which resampling can produce a spread at all.
    MIN_REPEATS = 3

    @property
    def has_interval(self) -> bool:
        return self.n_repeats >= self.MIN_REPEATS

    @property
    def is_stable(self) -> bool:
        return (
            self.n_requests is not None
            and self.exists_fraction >= self.STABLE_FRACTION
            and self.has_interval
        )

    def summary(self) -> str:
        if self.n_requests is None:
            return f"{self.a} vs {self.b}: no crossover ({self.exists_fraction:.0%} of replicates)"
        band = (
            f"[{self.lo:,.0f}, {self.hi:,.0f}]"
            if self.has_interval
            else f"(no interval: {self.n_repeats} repeat(s))"
        )
        verdict = "" if self.is_stable else "  UNSTABLE -- do not report as a crossover"
        return (
            f"{self.a} vs {self.b}: cross at N={self.n_requests:,.0f} {band}; "
            f"{self.cheaper_below} cheaper below, {self.cheaper_above} above "
            f"({self.exists_fraction:.0%} of replicates cross){verdict}"
        )


def crossover_interval(
    a: CostSample,
    b: CostSample,
    n_bootstrap: int = 2000,
    alpha: float = 0.05,
    seed: int = 0,
) -> CrossoverInterval:
    """Bootstrap the request volume at which two families cross.

    Percentile bootstrap over repeats. It is used rather than propagating variances
    analytically because the crossover is a ratio whose denominator can be near zero:
    its sampling distribution is heavy-tailed and sometimes has no finite value at all,
    which no closed-form interval handles honestly.

    Replicates in which the lines do not cross are **counted, not discarded**. Their
    share is ``exists_fraction``, and a low one is the finding.
    """
    if a.unit != b.unit:
        raise ValueError(f"cannot compare {a.unit} against {b.unit}")

    rng = np.random.default_rng(seed)
    crossings: list[float] = []
    below: list[str] = []
    above: list[str] = []

    for _ in range(n_bootstrap):
        result = crossover(a.resample(rng), b.resample(rng))
        if result.exists:
            crossings.append(float(result.n_requests))
            below.append(result.cheaper_below or "")
            above.append(result.cheaper_above or "")

    fraction = len(crossings) / n_bootstrap
    point = crossover(a.line(), b.line())

    if not crossings:
        return CrossoverInterval(
            a=a.label,
            b=b.label,
            n_requests=None,
            lo=None,
            hi=None,
            exists_fraction=0.0,
            n_bootstrap=n_bootstrap,
            n_repeats=min(a.n_repeats, b.n_repeats),
            cheaper_below=point.cheaper_below,
            cheaper_above=point.cheaper_above,
            point=point.n_requests,
            unit=a.unit,
        )

    values = np.asarray(crossings, dtype=float)
    return CrossoverInterval(
        a=a.label,
        b=b.label,
        n_requests=float(np.median(values)),
        lo=float(np.quantile(values, alpha / 2)),
        hi=float(np.quantile(values, 1 - alpha / 2)),
        exists_fraction=fraction,
        n_bootstrap=n_bootstrap,
        n_repeats=min(a.n_repeats, b.n_repeats),
        # Taken from the replicates rather than the point estimate: which family leads
        # below the crossing is itself an outcome of the resampling when the lines are
        # close, and the majority verdict is the honest one to report.
        cheaper_below=max(set(below), key=below.count) if below else None,
        cheaper_above=max(set(above), key=above.count) if above else None,
        point=point.n_requests,
        unit=a.unit,
    )


def retraining_table(
    lines: list[CostLine], intervals: list[float], n_requests: float
) -> list[dict]:
    """Which family is cheapest at a fixed traffic level, as retraining gets frequent.

    The plain break-even assumes a model is trained once and serves forever. No
    deployment does that: catalogues change, users arrive, and a stale model is
    retrained on a cadence. Under retraining the once-cost recurs, so a family that won
    purely by amortising an expensive training run over many requests loses that
    advantage in proportion to how often it pays again.

    ``intervals`` is in requests between retrains, and ``None`` in the list means "never
    retrained" -- the baseline the rest is read against. The verdict can reverse across
    this table, which is the finding: the cheapest family is a function not only of
    traffic volume but of how fast the data goes stale, and neither appears in a
    per-run energy figure.
    """
    rows = []
    for interval in intervals:
        if interval is None:
            costs = {line.label: line.at(n_requests) for line in lines}
            label = "never"
        else:
            costs = {line.label: line.with_retraining(interval).at(n_requests) for line in lines}
            label = f"{interval:,.0f}"
        cheapest = min(costs, key=lambda k: costs[k])
        rows.append(
            {
                "retrain_every": label,
                "n_requests": n_requests,
                "cheapest": cheapest,
                # How many training events were actually paid. Reported because the
                # staircase's height is the whole mechanism, and a reader checking the
                # arithmetic cannot recover it from the totals.
                "training_events": (
                    1 if interval is None else 1 + math.floor(n_requests / interval)
                ),
                **{f"cost.{label_}": value for label_, value in costs.items()},
            }
        )
    return rows


def cheapest_at(lines: list[CostLine], n_requests: float) -> CostLine:
    """Which family costs least at a given traffic level."""
    if not lines:
        raise ValueError("no cost lines given")
    return min(lines, key=lambda line: line.at(n_requests))


def regime_table(lines: list[CostLine], volumes: list[float]) -> list[dict]:
    """Cheapest family at each of several traffic levels.

    The presentation the claim deserves. A single crossover between two families is a
    fact; a table showing which family wins across the range a deployer might actually
    operate in is a recommendation, and it also exposes families that never win at all --
    which is worth knowing and invisible in a per-run energy table.
    """
    rows = []
    for volume in volumes:
        winner = cheapest_at(lines, volume)
        rows.append(
            {
                "n_requests": volume,
                "cheapest": winner.label,
                "cost": winner.at(volume),
                "unit": winner.unit,
                **{f"cost.{line.label}": line.at(volume) for line in lines},
            }
        )
    return rows
