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


def available() -> bool:
    """Whether the companion can be imported, for skipping tests that need real data."""
    try:
        ensure_importable()
    except CompanionNotFound:
        return False
    return True
