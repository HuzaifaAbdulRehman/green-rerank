"""Shared fixtures and the companion-dependency marker.

This project imports its metrics, loaders and reranking solvers from
``feasible-rerank``, which is a **private** repository. Public CI therefore cannot check
it out, and tests that reach through to it cannot run there.

The honest handling is to skip them with a stated reason and to make the skipping
*visible*, rather than to weaken the tests until they pass everywhere. A test that has
been hollowed out to run without its dependency is worse than a skipped one: it reports
success while checking nothing, and nobody looks at it again.

Two things keep that skip from quietly becoming permanent:

- the reason is printed, so a CI log says what was not covered rather than showing a
  green tick over a smaller suite than anyone thinks;
- ``--strict-companion`` turns the skip into a failure, which is what the development
  machine and any runner with the checkout should use.
"""

from __future__ import annotations

import pytest

from green_rerank.companion import available as companion_available


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--strict-companion",
        action="store_true",
        default=False,
        help=(
            "fail, rather than skip, tests needing the companion checkout. Use wherever "
            "the checkout is expected to be present, so its absence is not silent."
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "needs_companion: requires the feasible-rerank checkout (private; absent in CI)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if companion_available():
        return

    if config.getoption("--strict-companion"):
        raise pytest.UsageError(
            "--strict-companion was given but the companion checkout could not be "
            "found. Set GREEN_RERANK_COMPANION, or drop the flag to skip those tests."
        )

    skip = pytest.mark.skip(
        reason=(
            "needs the feasible-rerank checkout, which is private and absent here. "
            "Set GREEN_RERANK_COMPANION to run it."
        )
    )
    for item in items:
        if "needs_companion" in item.keywords:
            item.add_marker(skip)
