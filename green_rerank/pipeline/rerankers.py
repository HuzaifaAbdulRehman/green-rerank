"""Rerankers, imported from the companion project.

Not reimplemented, and not wrapped in anything that could change their behaviour. The
companion project's whole contribution is that these solvers were measured carefully --
including the finding that the textbook QUBO recipe fails silently -- and a
reimplementation here would put that result at arm's length from the code that produced
it.

What this module adds is the cost question the companion could not ask: it measures the
*reranker* against a fixed candidate set, so it can say which reranker is better but not
what reranking costs relative to training the model that produced the candidates. That
ratio is what a deployer weighs, and no published energy study reports it.
"""

from __future__ import annotations

from typing import Any

from green_rerank.companion import ensure_importable

#: Reranker name -> (companion module, class name, default keyword arguments).
#:
#: An earlier version of this module named the submodule rather than the ``solvers``
#: package, intending to let the three pure-numpy rerankers run without the D-Wave
#: stack. That does not work and the test suite caught it: importing
#: ``qubo_rerank.solvers.greedy`` executes the package's ``__init__``, which imports
#: ``neal`` unconditionally. The dependency is therefore required for **any** reranking,
#: not just the QUBO ones, and it is listed as such rather than papered over.
#:
#: The submodule is still named, because it keeps the mapping explicit about where each
#: class comes from.
#:
#: ``qubo_tabu`` is included but flagged: it stops on a wall-clock timeout, so its
#: *quality* is hardware-dependent -- the companion measured it scoring better on a
#: faster CPU at identical settings. In a project about cost that is a trap, because a
#: slower machine would make it look cheap and bad at the same time.
KNOWN: dict[str, tuple[str, str, dict[str, Any]]] = {
    "greedy_topk": ("greedy", "GreedyTopK", {}),
    "mmr": ("greedy", "MMR", {}),
    "quota_mmr": ("greedy", "QuotaMMR", {}),
    # Largest-remainder apportionment. **The classical baseline that decides whether the
    # QUBO's fairness advantage is real.**
    #
    # QuotaMMR caps each group at ceil(k/|C|) as an upper bound with no lower bound and
    # no remainder rule, so it can finish 3/3/3/1 over four groups and never recover --
    # parity 0.30 against an arithmetic floor of 0.20. An audit of the companion project
    # showed that is a defect of that one heuristic rather than a property of classical
    # reranking, and the companion retracted its feasibility headline accordingly
    # (qubo-rerank 8a72831). BalancedQuota attains the floor deterministically.
    #
    # Omitting it is what let this project claim the annealers reach a fairness optimum
    # "the classical rerankers do not get there at any setting tested". Any comparison
    # against the QUBO that leaves it out is measuring a broken baseline.
    "balanced_quota": ("greedy", "BalancedQuota", {}),
    "qubo_feasible": ("feasible", "FeasibleAnnealing", {}),
    "qubo_tabu": ("tabu", "TabuSearch", {}),
}

#: Rerankers whose stopping rule is wall-clock rather than work. Their cost figures are
#: roughly constant across machines while their *quality* is not, which inverts the
#: usual relationship and must be stated wherever they appear.
TIME_BOUNDED = frozenset({"qubo_tabu"})

#: Rerankers with a stochastic search. They must be seeded or two runs of one
#: configuration differ for reasons the results table cannot show: the committed
#: rerankers sweep has als/qubo_feasible NDCG of 0.0587, 0.0523 and 0.0149 across three
#: repeats of identical settings, which is the solver's randomness being reported as
#: run-to-run variance.
STOCHASTIC = frozenset({"qubo_feasible", "qubo_tabu"})

#: Default seed for the stochastic solvers. A fixed value rather than ``None``, because
#: ``None`` is what produced the spread above.
SOLVER_SEED = 0


def build_reranker(name: str, lam: float | None = None, seed: int | None = None, **kwargs: Any):
    """Construct a reranker by name from the companion project.

    Args:
        name: registry key.
        lam: diversity weight. Applied to every solver whose constructor accepts it, so
            the classical and QUBO rerankers optimise the *same* objective. Previously
            ``mmr`` and ``quota_mmr`` were pinned at ``lam=0.5`` in this registry while
            the annealers read ``problem.lam`` (0.3 from the config), so the two
            families were solving different problems and the comparison between them
            was not a comparison of methods.
        seed: seed for the stochastic solvers. Defaults to :data:`SOLVER_SEED`.
        **kwargs: further constructor overrides, applied last.
    """
    if name not in KNOWN:
        raise KeyError(f"unknown reranker {name!r}; known: {sorted(KNOWN)}")

    ensure_importable()
    module_name, class_name, defaults = KNOWN[name]

    import importlib
    import inspect

    try:
        module = importlib.import_module(f"qubo_rerank.solvers.{module_name}")
    except ImportError as exc:  # pragma: no cover - depends on what is installed
        raise ImportError(
            f"reranker {name!r} could not be imported. Every reranker needs the D-Wave "
            f"stack, because the companion project's solvers package imports neal at "
            f"package-import time even for the pure-numpy rerankers. Install it with:\n"
            f"    pip install -e .[rerank]\n"
            f"Original error: {exc}"
        ) from exc

    cls = getattr(module, class_name)
    accepted = inspect.signature(cls.__init__).parameters
    settings: dict[str, Any] = dict(defaults)

    # Applied only where the constructor takes them, so adding a solver that ignores
    # diversity or is deterministic needs no special case here.
    if lam is not None and "lam" in accepted:
        settings["lam"] = lam
    if "seed" in accepted:
        settings["seed"] = SOLVER_SEED if seed is None else seed

    settings.update(kwargs)
    return cls(**settings)


def rerankers_available() -> bool:
    """Whether reranking can run here, for skipping tests that need it."""
    try:
        build_reranker("greedy_topk")
    except Exception:
        return False
    return True


def is_time_bounded(name: str) -> bool:
    """Whether this reranker's stopping rule makes its quality hardware-dependent."""
    return name in TIME_BOUNDED
