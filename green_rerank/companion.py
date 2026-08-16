"""Locate the companion project (``feasible-rerank``) and import from it.

The brief for this project is explicit, and it is the right call: reuse, do not
reimplement. Two implementations of "the same" metric that disagree is the exact failure
this pair of projects is supposed to be above -- and the companion's NDCG, exposure
parity, DPFR port, Amazon/MovieLens loaders and ItemKNN are already tested there.

So this module resolves the companion checkout once and puts it on ``sys.path``, rather
than each experiment script growing its own three lines of path surgery that drift apart.

Resolution order:

1. ``$GREEN_RERANK_COMPANION``, for anyone whose checkout is elsewhere.
2. ``../qubo-rerank`` relative to this repository, which is how it sits on the machine
   this was developed on.

Missing companion is a clear error at the point of use, not an ``ImportError`` fifty
frames deep -- the two repositories are separate on purpose, and someone reading only
this one deserves to be told why an import failed.
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

#: Sibling checkout name. The GitHub repository is ``feasible-rerank``; the directory on
#: disk is ``qubo-rerank``, from before the project was renamed.
DEFAULT_DIRNAME = "qubo-rerank"

REPO_ROOT = Path(__file__).resolve().parents[1]


class CompanionNotFound(RuntimeError):
    """The companion checkout could not be located."""


def candidate_paths() -> list[Path]:
    """Where the companion might be, most explicit first."""
    found: list[Path] = []
    override = os.environ.get("GREEN_RERANK_COMPANION")
    if override:
        found.append(Path(override).expanduser())
    found.append(REPO_ROOT.parent / DEFAULT_DIRNAME)
    return found


def _looks_like_companion(path: Path) -> bool:
    """Whether ``path`` is the companion rather than merely a directory of that name.

    Checked against the package *and* a module this project actually imports, so that a
    half-cloned or renamed directory fails here with a useful message instead of at the
    first attribute access.
    """
    return (path / "qubo_rerank" / "metrics" / "relevance.py").exists()


@lru_cache(maxsize=1)
def companion_root() -> Path:
    """The companion checkout, or raise with the paths that were tried."""
    tried = candidate_paths()
    for path in tried:
        if _looks_like_companion(path):
            return path
    raise CompanionNotFound(
        "could not find the companion project (feasible-rerank). It supplies the "
        "metrics, loaders and evaluation protocol this project reuses rather than "
        "reimplements.\nTried:\n  "
        + "\n  ".join(str(p) for p in tried)
        + "\nSet GREEN_RERANK_COMPANION to the checkout to override."
    )


@lru_cache(maxsize=1)
def ensure_importable() -> Path:
    """Put the companion on ``sys.path`` and return its root. Idempotent."""
    root = companion_root()
    if str(root) not in sys.path:
        # Appended rather than prepended: this project's own modules must win any name
        # collision, or a stray file in the companion could shadow ours silently.
        sys.path.append(str(root))
    return root


@contextmanager
def companion_first(name: str):
    """Temporarily bind a top-level package name to the companion's copy of it.

    Both repositories have a top-level ``experiments`` directory, and this is harder to
    resolve than it looks.

    Reordering ``sys.path`` does not work. The companion's ``experiments/`` has no
    ``__init__.py``, so it is a *namespace* portion; this project's has one, so it is a
    regular package. During a path scan a regular package wins the moment it is found
    and a namespace portion only accumulates -- so ours is imported no matter which
    directory comes first.

    Loading the file by path does not work either: the companion's ``paired.py`` does
    ``from experiments.run_experiment import ...``, and that absolute name resolves
    through the normal machinery straight back into this project.

    What does work is binding the name itself. A ``sys.modules`` entry is consulted
    before any path search, so installing a package object whose ``__path__`` points at
    the companion's directory makes every ``experiments.*`` import inside the block --
    including the ones nested in the companion's own modules -- resolve there.

    Everything is restored on exit, including on an exception. A permanently rebound
    ``experiments`` would mean later imports in the same process silently came from the
    other repository, which is the failure that yields correct-looking results computed
    by the wrong code.

    Usage::

        with companion_first("experiments"):
            from experiments.paired import bootstrap_ci, holm
    """
    import types

    root = ensure_importable()
    directory = root / name
    if not directory.is_dir():
        raise CompanionNotFound(f"companion has no {name}/ directory (looked in {directory})")

    def bound() -> list[str]:
        return [m for m in list(sys.modules) if m == name or m.startswith(f"{name}.")]

    saved = {m: sys.modules[m] for m in bound()}
    for module in bound():
        del sys.modules[module]

    shim = types.ModuleType(name)
    shim.__path__ = [str(directory)]  # type: ignore[attr-defined]
    sys.modules[name] = shim
    try:
        yield shim
    finally:
        for module in bound():
            del sys.modules[module]
        sys.modules.update(saved)


def available() -> bool:
    """Whether the companion can be imported, for skipping tests that need real data."""
    try:
        ensure_importable()
    except CompanionNotFound:
        return False
    return True
