"""Check the test suite by deliberately breaking the code.

Coverage says a line ran. It does not say that breaking that line would fail anything,
and in a project whose whole subject is defects that leave output looking normal, that
distinction is the one that matters. This script introduces a specific, plausible bug,
runs the tests that ought to notice, and reports whether they did.

Every mutation below is a mistake that could really be made -- a forgotten division, an
inverted comparison, a guard removed because it looked redundant -- rather than a random
token swap. A surviving mutation is not a failing test; it is a claim the suite does not
actually defend.

Four of these survived the first time it was run, and each was the project's
characteristic failure: a defect that changes results and leaves the table looking
entirely ordinary.

    python tests/mutations.py            # all of them
    python tests/mutations.py --filter rerank

Not named ``test_*`` on purpose: it rewrites source files, so pytest must never collect
it. Files are restored through ``git checkout``, so the working tree must be committed
before running -- the script refuses otherwise rather than risk discarding real edits.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


@dataclass(frozen=True)
class Mutation:
    """One deliberate bug, and the tests expected to object to it.

    Attributes:
        why: what a reader should understand about the invariant, in one line. This is
            the point of the entry -- a mutation nobody can explain is not evidence.
    """

    name: str
    path: str
    before: str
    after: str
    tests: str
    why: str


MUTATIONS: tuple[Mutation, ...] = (
    Mutation(
        "per_request_cost drops the division",
        "green_rerank/pipeline/runner.py",
        "return float(served / self.n_users)",
        "return float(served)",
        "tests/test_pipeline.py",
        "serving cost would scale with how many users the window happened to serve",
    ),
    Mutation(
        "cost uses the raw window, not the per-repeat figure",
        "green_rerank/pipeline/runner.py",
        'COST_ATTR = "cpu_seconds_each"',
        'COST_ATTR = "cpu_seconds"',
        "tests/test_pipeline.py",
        "a cheaper stage needs more repetitions, so it would report as more expensive",
    ),
    Mutation(
        "session leaks readings between runs",
        "green_rerank/pipeline/runner.py",
        "readings=list(session.readings[first_reading:]),",
        "readings=list(session.readings),",
        "tests/test_pipeline.py",
        "costs would climb monotonically through a sweep, each row still plausible",
    ),
    Mutation(
        "candidate cap removed",
        "green_rerank/pipeline/runner.py",
        "n_candidates = min(n_candidates, dataset.n_items, usable)",
        "n_candidates = min(n_candidates, dataset.n_items)",
        "tests/test_pipeline.py",
        "seen items re-enter the candidate set as -inf padding, then as NaN relevance",
    ),
    Mutation(
        "normalise propagates NaN instead of raising",
        "green_rerank/pipeline/runner.py",
        "if not np.isfinite(scores).all():",
        "if False:",
        "tests/test_pipeline.py",
        "the reranker would rank on NaN and could return an item the user has seen",
    ),
    Mutation(
        "reranked list not re-sorted by relevance",
        "green_rerank/pipeline/runner.py",
        "by_relevance = sorted(selection, key=lambda i: -scores[i])",
        "by_relevance = list(selection)",
        "tests/test_pipeline.py",
        "charges the reranker for an ordering it never claimed -- up to 0.09 NDCG",
    ),
    Mutation(
        "clock started before the energy probe",
        "green_rerank/measure/session.py",
        "self.meter.start()\n\n        cpu0, user0, sys0 = self._cpu_clock()",
        "cpu0, user0, sys0 = self._cpu_clock()\n        self.meter.start()",
        "tests/test_measure.py",
        "the probe's seconds get charged to the workload; a 0.008 s baseline read 5.4 s",
    ),
    Mutation(
        "below-quantum readings never flagged",
        "green_rerank/measure/session.py",
        'reading.meta["below_quantum"] = True',
        "pass",
        "tests/test_measure.py",
        "a tick count would be reported as a duration, indistinguishable from a real one",
    ),
    Mutation(
        "throttling never reported",
        "green_rerank/measure/guards.py",
        'result["throttled"] = drop > self.DROP_THRESHOLD',
        'result["throttled"] = False',
        "tests/test_measure.py",
        "a mid-sweep clock drop would pass unremarked; timings rise ~2.8x on battery",
    ),
    Mutation(
        "power-source changes ignored",
        "green_rerank/measure/guards.py",
        '"power_source_changed": len(self.power_sources) > 1,',
        '"power_source_changed": False,',
        "tests/test_measure.py",
        "the cable coming out mid-run is the failure the monitor exists for",
    ),
    Mutation(
        "exclusion mask writes through a shared array",
        "green_rerank/families/base.py",
        "scores = scores.copy()",
        "pass",
        "tests/test_families.py",
        "a family's cached scores get poisoned: first call right, everything after wrong",
    ),
    Mutation(
        "top-k skips boundary tie resolution",
        "green_rerank/families/base.py",
        "selected = strictly_better | (tied & (tie_position < remaining))",
        "selected = strictly_better | tied",
        "tests/test_families.py",
        "ties at the cut return the wrong number of items, non-deterministically",
    ),
    Mutation(
        "GRU4Rec has no reserved pad token",
        "green_rerank/families/neural.py",
        "nn.Embedding(n_items + 1, embedding, padding_idx=0)",
        "nn.Embedding(n_items + 1, embedding)",
        "tests/test_families.py",
        "the model learns that item 0 begins every short session",
    ),
    Mutation(
        "crossover numerator inverted",
        "green_rerank/analysis/breakeven.py",
        "once_gap = b.once - a.once",
        "once_gap = a.once - b.once",
        "tests/test_analysis.py",
        "every break-even lands on the wrong side, still a plausible request count",
    ),
    Mutation(
        "bootstrap breaks the pairing between costs",
        "green_rerank/analysis/breakeven.py",
        "once=float(np.median(np.asarray(self.once, dtype=float)[picked])),",
        "once=float(np.median(np.asarray(self.once, dtype=float)"
        "[rng.integers(0, self.n_repeats, size=self.n_repeats)])),",
        "tests/test_analysis.py",
        "manufactures cost combinations never observed and narrows the interval",
    ),
    Mutation(
        "a one-repeat bootstrap counts as stable",
        "green_rerank/analysis/breakeven.py",
        "and self.has_interval",
        "",
        "tests/test_analysis.py",
        "a zero-width interval reads as certainty and means the opposite",
    ),
    Mutation(
        "retraining smooths whole training events",
        "green_rerank/analysis/breakeven.py",
        "events = 1 + math.floor(n_requests / self.interval)",
        "events = 1 + n_requests / self.interval",
        "tests/test_analysis.py",
        "understates cost right after each retrain, when a deployment would notice",
    ),
    Mutation(
        "domination no longer needs a strict improvement",
        "green_rerank/analysis/frontier.py",
        "return at_least_as_good and strictly_better",
        "return at_least_as_good",
        "tests/test_analysis.py",
        "identical points would dominate each other and the frontier would empty",
    ),
    Mutation(
        "agreement accepts two observations",
        "green_rerank/analysis/validity.py",
        "if estimate.size < 3:",
        "if estimate.size < 2:",
        "tests/test_analysis.py",
        "two points fit a line exactly, so R^2 = 1.0 would 'prove' the claim on nothing",
    ),
    Mutation(
        "rerank reclassified as a once-cost",
        "green_rerank/pipeline/stages.py",
        'RERANK = ("rerank", Amortisation.PER_REQUEST)',
        'RERANK = ("rerank", Amortisation.ONCE)',
        "tests/test_pipeline.py",
        "the reranker's cost would vanish from every per-request figure",
    ),
    Mutation(
        "fairness groups misaligned with matrix columns",
        "green_rerank/data.py",
        "groups = groups_fn(matrix, item_ids, n_groups)",
        "groups = groups_fn(matrix, list(reversed(list(item_ids))), n_groups)",
        "tests/test_catalogues.py",
        "every exposure-parity number would measure a permutation of the truth",
    ),
    Mutation(
        "k-core filtering skipped",
        "green_rerank/data.py",
        "filtered = k_core(raw, min_interactions=min_interactions)",
        "filtered = raw",
        "tests/test_catalogues.py",
        "the two projects would no longer agree on which interactions survive",
    ),
    Mutation(
        "eval_users ignores its seed",
        "green_rerank/data.py",
        "rng = np.random.default_rng(seed)",
        "rng = np.random.default_rng(0)",
        "tests/test_pipeline.py",
        "repeats would resample nothing, so the uncertainty would be scheduler jitter",
    ),
    Mutation(
        "analysis accepts contaminated rows",
        "experiments/analyse.py",
        'if "trustworthy" in frame.columns and not allow_untrustworthy:',
        "if False:",
        "tests/test_experiments.py",
        "costs measured under CPU contention would enter the report unremarked",
    ),
    Mutation(
        "collapsed catalogues are never skipped",
        "experiments/sweep.py",
        "if dataset.n_users < min_users:",
        "if False:",
        "tests/test_experiments.py",
        "metrics over four items would sit beside real measurements",
    ),
    Mutation(
        "verdict ignores inverted energy channels",
        "experiments/validity.py",
        'responded = any(v["dynamic_range"] > 2.0 and not v["inverted"] '
        "for v in usable.values())",
        'responded = any(v["dynamic_range"] > 2.0 for v in usable.values())',
        "tests/test_validity_driver.py",
        "a backend reporting less energy under load would be judged to work",
    ),
    Mutation(
        "verdict divides rate channels by time",
        "experiments/validity.py",
        "rate = values / wall if cumulative else values",
        "rate = values / wall",
        "tests/test_validity_driver.py",
        "watts per second is not a quantity; it was printed in a results table once",
    ),
    Mutation(
        "lower-is-better metrics scored the wrong way",
        "experiments/compare.py",
        'LOWER_IS_BETTER = {"exposure_parity", "intra_list_similarity"}',
        "LOWER_IS_BETTER = set()",
        "tests/test_experiments.py",
        "inverts the fairness verdict while every number in the row stays correct",
    ),
    Mutation(
        "companion import bindings never restored",
        "green_rerank/companion.py",
        "sys.modules.update(saved)",
        "pass",
        "tests/test_companion.py",
        "later imports get fresh module objects with separate state",
    ),
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def apply(mutation: Mutation) -> bool:
    path = ROOT / mutation.path
    source = path.read_text(encoding="utf-8")
    if mutation.before not in source:
        return False
    path.write_text(source.replace(mutation.before, mutation.after, 1), encoding="utf-8")
    return True


def restore(mutation: Mutation) -> None:
    subprocess.run(["git", "checkout", "--", mutation.path], cwd=ROOT, check=True)


def caught(mutation: Mutation) -> bool:
    """Whether the named tests fail with the mutation applied."""
    result = subprocess.run(
        [PYTHON, "-m", "pytest", mutation.tests, "-q", "-x", "-m", "not timing"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode != 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--filter", default="", help="only mutations whose name matches")
    parser.add_argument("--list", action="store_true", help="list them without running")
    args = parser.parse_args()

    selected = [m for m in MUTATIONS if args.filter.lower() in m.name.lower()]
    if args.list:
        for mutation in selected:
            print(f"{mutation.name}\n    {mutation.why}")
        return 0

    # Restoration is `git checkout --`, which would discard uncommitted work.
    if _git("status", "--porcelain", "--", *{m.path for m in MUTATIONS}):
        print("refusing to run: the files this script mutates have uncommitted changes.")
        return 2

    survived, missing = [], []
    print(f"{len(selected)} mutations\n")
    for mutation in selected:
        if not apply(mutation):
            missing.append(mutation)
            print(f"  ?  not applied  {mutation.name}  (source has changed)")
            continue
        try:
            if caught(mutation):
                print(f"  .  caught       {mutation.name}")
            else:
                survived.append(mutation)
                print(f"  !  SURVIVED     {mutation.name}")
        finally:
            restore(mutation)

    print(f"\n{len(selected) - len(survived) - len(missing)} caught, "
          f"{len(survived)} survived, {len(missing)} not applied")
    for mutation in survived:
        print(f"\n  {mutation.name}\n    {mutation.why}\n    expected: {mutation.tests}")
    if missing:
        print("\nStale entries -- the code moved and the mutation no longer applies.")
        print("Update or delete them; an entry that cannot be applied tests nothing.")

    return 1 if survived or missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
