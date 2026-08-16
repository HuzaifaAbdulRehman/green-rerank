"""Model families under comparison.

Families are grouped by how their cost behaves, not by accuracy. The point of the
comparison is that training cost and serving cost trade against each other, so the
cheapest family is a function of expected request volume rather than a fixed answer.
"""

from green_rerank.families.base import Family, Recommendations
from green_rerank.families.classical import ImplicitALS, ItemKNN, Popularity

#: Families that need no optional dependency. The neural family lives in
#: :mod:`green_rerank.families.neural` and is imported lazily by :func:`build`, because
#: torch is ~2.5 GB and most of this project must stay usable without it.
CLASSICAL: dict[str, type[Family]] = {
    Popularity.name: Popularity,
    ItemKNN.name: ItemKNN,
    ImplicitALS.name: ImplicitALS,
}


def build(name: str, **kwargs) -> Family:
    """Construct a family by name.

    Experiment configs name families as strings, so the mapping from string to class
    belongs in one place rather than in each driver script.
    """
    if name in CLASSICAL:
        return CLASSICAL[name](**kwargs)

    # Deferred: importing this raises a clear message if torch is absent, which is a
    # better failure than an ImportError at the top of an unrelated module.
    from green_rerank.families.neural import NEURAL

    if name in NEURAL:
        return NEURAL[name](**kwargs)

    known = sorted(set(CLASSICAL) | set(NEURAL))
    raise KeyError(f"unknown family {name!r}; known families: {known}")


__all__ = [
    "CLASSICAL",
    "Family",
    "ImplicitALS",
    "ItemKNN",
    "Popularity",
    "Recommendations",
    "build",
]
