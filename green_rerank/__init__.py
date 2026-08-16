"""green-rerank: stage-resolved cost accounting for recommender pipelines.

The companion project (``feasible-rerank``) measures the *reranker*. This measures the
*pipeline*: train, retrieve, rerank and score, each costed separately, so that the
question "what does a unit of accuracy cost" can be answered per stage rather than per
run.

The primary cost unit is **CPU-seconds**, not kWh. That is a measured decision, not a
stylistic one -- see :mod:`green_rerank.measure.meters` for why the energy estimate
available on commodity hardware could not be trusted.
"""

__version__ = "0.1.0"
