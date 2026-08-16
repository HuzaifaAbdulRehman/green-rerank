"""Pipeline stages, and how each one's cost accumulates.

The second field is the point of this module. Prior work reports one energy figure per
run, which silently adds a cost paid *once* to a cost paid on *every request*. Those are
not the same kind of number and their sum is not interpretable: a model that trains for
an hour then serves free, and one that trains instantly then burns an hour answering
queries, can report identical totals and represent opposite deployment decisions.

Tagging each stage with how it amortises is what turns a table of costs into

    E_total(N) = E_once + N * E_per_request

and therefore into a break-even request volume -- the question a deployer actually has.
"""

from __future__ import annotations

from enum import Enum


class Amortisation(Enum):
    """How a stage's cost scales with the number of requests served."""

    #: Paid once, at deployment, no matter how many requests follow. Retraining
    #: cadence is a separate question -- see
    #: :func:`green_rerank.analysis.breakeven.with_retraining`.
    ONCE = "once"

    #: Paid on every request. The measured figure is divided by the number of users
    #: served in that window to get a per-request cost.
    PER_REQUEST = "per_request"


class Stage(Enum):
    """A costed step of the pipeline.

    ``SCORE`` is deliberately absent. Metric computation is O(k^2) per user in Python
    and must never enter a measured window -- it is noise for an expensive stage and
    most of the reading for a cheap one. Having no enum member for it means a stage
    cannot be measured by accident.
    """

    TRAIN = ("train", Amortisation.ONCE)

    #: Building whatever the reranker needs that does not depend on the request --
    #: for the fairness reranker, the item-item similarity matrix. Separated from
    #: ``RERANK`` because folding a one-off matrix build into a per-request cost is
    #: exactly the error this module exists to prevent.
    RERANK_SETUP = ("rerank_setup", Amortisation.ONCE)

    #: Scoring the catalogue for a user -- the family-specific half of retrieval. For a
    #: neighbourhood model this scales with catalogue size; for a factor model it is one
    #: thin product. That difference is the reason the families cross.
    RETRIEVE_SCORE = ("retrieve_score", Amortisation.PER_REQUEST)

    #: Selecting the top-n from those scores. Identical code for every family, and
    #: measured separately because it turned out to be the *majority* of retrieval cost
    #: -- 99.9 % of it for popularity. Folded into one ``retrieve`` figure it would make
    #: families look far more alike than their scoring actually is, and would credit or
    #: blame them for work none of them does differently.
    RETRIEVE_SELECT = ("retrieve_select", Amortisation.PER_REQUEST)

    #: Selecting k items from the candidate set. The stage no prior energy study has
    #: costed at all.
    RERANK = ("rerank", Amortisation.PER_REQUEST)

    def __init__(self, label: str, amortisation: Amortisation) -> None:
        self.label = label
        self.amortisation = amortisation

    def __str__(self) -> str:
        return self.label

    @classmethod
    def from_label(cls, label: str) -> Stage:
        for stage in cls:
            if stage.label == label:
                return stage
        raise KeyError(f"unknown stage {label!r}; known: {[s.label for s in cls]}")


#: Stages paid once at deployment.
ONCE_STAGES = tuple(s for s in Stage if s.amortisation is Amortisation.ONCE)

#: Stages paid on every request.
PER_REQUEST_STAGES = tuple(s for s in Stage if s.amortisation is Amortisation.PER_REQUEST)
