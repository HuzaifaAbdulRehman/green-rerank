"""The catalogues this project measures on, and where to find them.

Two things are deliberate here.

**The registry is data, not code.** Every experiment names a catalogue by string; nothing
downstream knows what a MovieLens directory looks like. Adding a catalogue is one entry,
and the report's dataset table is generated from the same entries the runs used, so the
two cannot drift.

**Files are located, never copied.** The companion project already holds these downloads,
and duplicating 130 MB into this repository would create two copies that can silently
diverge -- the same failure mode as two implementations of one metric. Resolution walks
this repository's ``data/``, then ``$GREEN_RERANK_DATA``, then the companion's ``data/``,
and reports every path it tried when it finds nothing.

Catalogue *size* is the reason more than one is here. A break-even between a
neighbourhood model and a factor model is a statement about how serving cost scales with
catalogue size, so demonstrating it on a single 1,349-item catalogue would be an anecdote.
These range over roughly two orders of magnitude.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from green_rerank.companion import CompanionNotFound, companion_root
from green_rerank.data import Dataset, load_amazon, load_movielens

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Catalogue:
    """A named dataset: how to find it, how to load it, and what it is for.

    Attributes:
        name: the string experiments refer to it by.
        kind: which loader handles it -- ``movielens`` or ``amazon``.
        relative: path under whichever data root contains it.
        grouping: what the fairness groups mean, carried into the report because
            "exposure parity" over curator genres and over popularity tiers are
            different claims and must not share a column without explanation.
        note: one line on why this catalogue earns its place in the study.
        kwargs: loader overrides.
    """

    name: str
    kind: str
    relative: str
    grouping: str
    note: str
    kwargs: dict = field(default_factory=dict)


#: Registered catalogues, smallest first.
#:
#: The Amazon entries are the McAuley ratings-only exports, which carry no product
#: metadata -- hence popularity tiers rather than genres for their groups.
CATALOGUES: dict[str, Catalogue] = {
    c.name: c
    for c in (
        Catalogue(
            name="ml100k",
            kind="movielens",
            relative="ml100k/ml-100k",
            grouping="curator genres",
            note=(
                "The standard reference point. Small enough that every family, "
                "including the neural ones, can be trained repeatedly on a laptop."
            ),
        ),
        Catalogue(
            name="gift_cards",
            kind="amazon",
            relative="amazon_Gift_Cards/Gift_Cards.csv",
            grouping="popularity tiers",
            note="Smallest Amazon catalogue; sparse enough to stress retrieval quality.",
        ),
        Catalogue(
            name="software",
            kind="amazon",
            relative="amazon_Software/Software.csv",
            grouping="popularity tiers",
            note="Mid-sized catalogue with a pronounced short head.",
        ),
        Catalogue(
            name="luxury_beauty",
            kind="amazon",
            relative="amazon_lb/Luxury_Beauty.csv",
            grouping="popularity tiers",
            note="Dense repeat-purchase behaviour, unlike the media catalogues.",
        ),
        Catalogue(
            name="appliances",
            kind="amazon",
            relative="amazon_Appliances/Appliances.csv",
            grouping="popularity tiers",
            note="Long-tail heavy; few users have enough history to survive k-core.",
        ),
        Catalogue(
            name="digital_music",
            kind="amazon",
            relative="amazon_Digital_Music/Digital_Music.csv",
            grouping="popularity tiers",
            note=(
                "Largest catalogue here. Carries the break-even argument: a "
                "neighbourhood model's serving cost scales with catalogue size and a "
                "factor model's does not, which a small catalogue cannot show."
            ),
        ),
    )
}


def data_roots() -> list[Path]:
    """Directories that might hold the raw downloads, most local first."""
    roots = [REPO_ROOT / "data"]
    override = os.environ.get("GREEN_RERANK_DATA")
    if override:
        roots.append(Path(override).expanduser())
    try:
        roots.append(companion_root() / "data")
    except CompanionNotFound:
        pass
    return roots


def resolve(name: str) -> Path:
    """Locate a registered catalogue's files, or raise saying where it looked."""
    catalogue = get(name)
    tried = []
    for root in data_roots():
        candidate = root / catalogue.relative
        tried.append(candidate)
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"catalogue {name!r} not found.\nTried:\n  "
        + "\n  ".join(str(p) for p in tried)
        + "\nSet GREEN_RERANK_DATA to a directory holding the downloads."
    )


def get(name: str) -> Catalogue:
    try:
        return CATALOGUES[name]
    except KeyError:
        raise KeyError(
            f"unknown catalogue {name!r}; known: {sorted(CATALOGUES)}"
        ) from None


def available() -> list[str]:
    """Registered catalogues whose files are actually present."""
    present = []
    for name in CATALOGUES:
        try:
            resolve(name)
        except FileNotFoundError:
            continue
        present.append(name)
    return present


@lru_cache(maxsize=8)
def _load_cached(name: str, min_interactions: int, n_groups: int, max_sequence: int):
    catalogue = get(name)
    path = resolve(name)
    shared = dict(
        min_interactions=min_interactions,
        n_groups=n_groups,
        max_sequence=max_sequence,
        **catalogue.kwargs,
    )
    if catalogue.kind == "movielens":
        return load_movielens(path, **shared)
    if catalogue.kind == "amazon":
        return load_amazon(path, name=catalogue.name, **shared)
    raise ValueError(f"catalogue {name!r} has unknown kind {catalogue.kind!r}")


def load(
    name: str,
    min_interactions: int = 5,
    n_groups: int = 4,
    max_sequence: int = 200,
) -> Dataset:
    """Load a registered catalogue.

    Cached because a sweep runs many families over one catalogue and reloading the
    largest of them costs more than the measurements do. The cache is keyed on the
    preprocessing arguments, so two runs that filtered differently can never be served
    the same object -- which would make their results look comparable when they are not.
    """
    return _load_cached(name, min_interactions, n_groups, max_sequence)
