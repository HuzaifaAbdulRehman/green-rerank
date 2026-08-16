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
    "mmr": ("greedy", "MMR", {"lam": 0.5}),
    "quota_mmr": ("greedy", "QuotaMMR", {"lam": 0.5}),
    "qubo_feasible": ("feasible", "FeasibleAnnealing", {}),
    "qubo_tabu": ("tabu", "TabuSearch", {}),
}

#: Rerankers whose stopping rule is wall-clock rather than work. Their cost figures are
#: roughly constant across machines while their *quality* is not, which inverts the
#: usual relationship and must be stated wherever they appear.
TIME_BOUNDED = frozenset({"qubo_tabu"})


def build_reranker(name: str, **kwargs: Any):
    """Construct a reranker by name from the companion project."""
    if name not in KNOWN:
        raise KeyError(f"unknown reranker {name!r}; known: {sorted(KNOWN)}")

    ensure_importable()
    module_name, class_name, defaults = KNOWN[name]

    import importlib

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

    return getattr(module, class_name)(**{**defaults, **kwargs})


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
