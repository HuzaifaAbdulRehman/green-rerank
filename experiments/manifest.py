"""What a results directory has to say about itself.

A cost measurement is a claim about a machine at a moment, not a property of an
algorithm. Two runs of this project taken a week apart on the same laptop can differ by
a factor of three for reasons that have nothing to do with the code -- a cable, a
background updater, a thermal event. So a results directory that cannot say what it was
produced by and under what conditions is not a result, it is a number.

The manifest therefore records the **companion project's** revision as well as this
one's. Every metric this project reports is computed by companion code; a results table
whose provenance omits it is only half-provenanced, and the half it omits is the half
that decides the accuracy column.

Being explicit about a dirty working tree matters more than it looks. ``abc1234-dirty``
is not a version -- nobody can return to it. It is recorded so that a table produced
from uncommitted code is legible as such rather than appearing reproducible.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

from green_rerank.companion import CompanionNotFound, companion_root

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Packages whose version can change a measurement. NumPy and SciPy because the BLAS
#: they bind to sets how many cores a matmul spreads over, which is the difference
#: between one CPU-second and four; torch for the same reason, more so.
TRACKED_PACKAGES = (
    "numpy",
    "scipy",
    "pandas",
    "torch",
    "psutil",
    "codecarbon",
    "dimod",
    "dwave-neal",
    "dwave-samplers",
)


def _git(root: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):  # pragma: no cover - git may be absent
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip()


#: Paths whose modification does not make the *code* dirty. Results are the output of
#: the run being recorded, and they are written into the working tree while it runs --
#: so counting them would make every manifest say "dirty" and the flag would carry no
#: information at all, least of all about the thing it is for: whether the code that
#: produced these numbers is the code someone can check out.
NOT_CODE = ("results", "docs")


def git_state(root: Path) -> dict[str, Any]:
    """Revision, branch and cleanliness of a checkout.

    ``None`` for a directory that is not a repository at all, which is a legitimate
    state early in a project and must not be confused with a clean checkout.
    """
    revision = _git(root, "rev-parse", "HEAD")
    if revision is None:
        return {"revision": None, "branch": None, "dirty": None}

    status = _git(root, "status", "--porcelain")
    code_status = _git(
        root, "status", "--porcelain", "--", ".", *(f":(exclude){p}" for p in NOT_CODE)
    )
    return {
        "revision": revision,
        "branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        # Dirtiness of the code specifically. A run writes its own results into the
        # tree, so the unfiltered flag is true during every sweep by construction.
        "dirty": bool(code_status),
        # Kept so the distinction is visible rather than assumed away.
        "tree_dirty": bool(status),
    }


def package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in TRACKED_PACKAGES:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def machine() -> dict[str, Any]:
    """The hardware and OS, in enough detail to explain a threefold difference."""
    info: dict[str, Any] = {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": sys.version.split()[0],
    }
    try:
        import psutil

        info["cpu_logical"] = psutil.cpu_count(logical=True)
        info["cpu_physical"] = psutil.cpu_count(logical=False)
        frequency = psutil.cpu_freq()
        if frequency is not None:
            info["cpu_mhz_nominal"] = frequency.max or None
            info["cpu_mhz_at_start"] = frequency.current
        info["ram_bytes"] = psutil.virtual_memory().total
    except Exception:  # pragma: no cover - psutil is best-effort
        pass
    return info


def _plain(value: Any) -> Any:
    """Make a value JSON-safe without silently dropping anything.

    Dataclasses (the preflight record) and Paths appear in configs and results; a
    manifest that quietly omitted whichever fields did not serialise would be worse
    than one that failed, because it would still look complete.
    """
    if is_dataclass(value) and not isinstance(value, type):
        return _plain(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_plain(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def build(config: dict[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
    """Assemble the manifest for a results directory."""
    try:
        companion = git_state(companion_root())
        companion["path"] = str(companion_root())
    except CompanionNotFound:
        companion = {"revision": None, "branch": None, "dirty": None, "path": None}

    from green_rerank.measure.session import clock_quantum

    return _plain(
        {
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "green_rerank": git_state(REPO_ROOT),
            # Recorded because every accuracy metric in this project's results is
            # computed by companion code.
            "companion": companion,
            "packages": package_versions(),
            "machine": machine(),
            # Stamped because the repeat-until-measurable logic is calibrated against
            # it, so a machine with a different scheduler tick produces readings grown
            # to a different size.
            "clock_quantum_seconds": clock_quantum(),
            "config": config or {},
            **extra,
        }
    )


def write(directory: str | Path, config: dict[str, Any] | None = None, **extra: Any) -> Path:
    """Write ``manifest.json`` into a results directory and return its path."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "manifest.json"
    path.write_text(json.dumps(build(config, **extra), indent=2), encoding="utf-8")
    return path


def summary(manifest: dict[str, Any]) -> str:
    """One line naming the code version, for printing at the top of a run."""
    own = manifest.get("green_rerank", {})
    companion = manifest.get("companion", {})

    def label(state: dict[str, Any]) -> str:
        revision = state.get("revision")
        if not revision:
            return "uncommitted"
        return revision[:7] + ("-dirty" if state.get("dirty") else "")

    return f"green-rerank {label(own)}  companion {label(companion)}"
