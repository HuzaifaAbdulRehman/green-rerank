"""Invariants for the experiment drivers.

The drivers are not analysis code, but every number in the report passes through them,
and their failure modes are the quiet kind: a sweep that silently ran once instead of
five times, a resume that re-ran everything, an analysis that averaged a contaminated
run in with clean ones. None of those raise, and all of them change the result.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from experiments import manifest
from experiments.analyse import breakeven_table, cost_table, label_of, load_runs, rerank_share
from experiments.sweep import DEFAULTS, Cell, cells, load_config, viability
from green_rerank.data import synthetic

# --------------------------------------------------------------------------- config


class TestConfig:
    def test_defaults_are_filled_in(self, tmp_path: Path):
        path = tmp_path / "c.yaml"
        path.write_text("name: x\ncatalogues: [ml100k]\n", encoding="utf-8")
        config = load_config(path)
        assert config["name"] == "x"
        assert config["repeats"] == DEFAULTS["repeats"]

    def test_an_unknown_key_is_an_error_not_a_warning(self, tmp_path: Path):
        """``repeat: 5`` instead of ``repeats: 5`` is the motivating typo.

        Ignored, it runs the whole sweep once and every cost is reported with no
        uncertainty at all -- which the analysis would then present as a crossover with
        a zero-width interval.
        """
        path = tmp_path / "c.yaml"
        path.write_text("name: x\nrepeat: 5\n", encoding="utf-8")
        with pytest.raises(SystemExit, match="unknown config keys"):
            load_config(path)

    def test_an_empty_config_is_all_defaults(self, tmp_path: Path):
        path = tmp_path / "c.yaml"
        path.write_text("", encoding="utf-8")
        assert load_config(path) == DEFAULTS


# ---------------------------------------------------------------------------- grid


class TestGrid:
    def test_repeat_is_the_outermost_loop(self):
        """So that an interrupted sweep is still a comparison.

        With repeat innermost, stopping halfway leaves five observations of the first
        family and none of the last -- not a weak result, but no result. Outermost, it
        leaves one clean observation of everything.
        """
        config = {**DEFAULTS, "catalogues": ["a", "b"], "families": ["f"], "repeats": 3}
        grid = cells(config)
        assert [c.repeat for c in grid] == [0, 0, 1, 1, 2, 2]

    def test_every_combination_appears_exactly_once(self):
        config = {
            **DEFAULTS,
            "catalogues": ["a", "b"],
            "families": ["f", "g"],
            "rerankers": [None, "mmr"],
            "repeats": 2,
        }
        grid = cells(config)
        assert len(grid) == 2 * 2 * 2 * 2
        assert len({c.key for c in grid}) == len(grid)

    def test_cell_key_normalises_the_absent_reranker(self):
        # `None` in the config and `"none"` in the CSV must resolve to one identity, or
        # resume would re-run every no-reranker cell forever.
        assert Cell("a", "f", None, 0).key == ("a", "f", "none", 0, 200)

    def test_retrieval_depth_is_part_of_a_cell_s_identity(self):
        """Two depths are two different measurements, not one repeated.

        The reranker's cost scales with its problem size, so a run at depth 50 and one
        at depth 800 are not interchangeable. If depth were left out of the key, resume
        would treat the second as already done and the sensitivity study would silently
        collapse to whichever depth ran first.
        """
        assert Cell("a", "f", None, 0, 50).key != Cell("a", "f", None, 0, 800).key

    def test_a_list_of_depths_becomes_a_grid_axis(self):
        config = {
            **DEFAULTS,
            "catalogues": ["a"],
            "families": ["f"],
            "rerankers": [None],
            "n_candidates": [50, 200],
            "repeats": 2,
        }
        grid = cells(config)
        assert len(grid) == 4
        assert {c.n_candidates for c in grid} == {50, 200}

    def test_a_scalar_depth_still_means_one_depth(self):
        # Every config written before the axis existed passes a scalar, and must keep
        # producing exactly the grid it produced then.
        config = {**DEFAULTS, "catalogues": ["a"], "families": ["f"], "repeats": 1}
        assert [c.n_candidates for c in cells(config)] == [DEFAULTS["n_candidates"]]


# ---------------------------------------------------------------------- viability


class TestViability:
    def test_a_usable_dataset_passes(self):
        assert viability(synthetic(n_users=60, n_items=40), 50, 30) is None

    def test_a_collapsed_catalogue_is_refused_with_a_reason(self):
        """Amazon ``Appliances`` reduces to 13 users and 4 items under 5-core.

        That is a property of the ratings-only export, not a loading bug. Running on it
        would produce a complete row of metrics computed over four items -- numbers that
        are not measurements, sitting in a table beside ones that are.
        """
        tiny = synthetic(n_users=13, n_items=4, blocks=2, per_user=2)
        reason = viability(tiny, 50, 50)
        assert reason is not None and "13 users" in reason

    def test_too_few_items_is_reported_separately_from_too_few_users(self):
        reason = viability(synthetic(n_users=60, n_items=40), 50, 100)
        assert reason is not None and "items" in reason


# ------------------------------------------------------------------------ manifest


class TestManifest:
    def test_records_both_repositories(self):
        """Half-provenance is the failure worth guarding.

        Every accuracy metric this project reports is computed by companion code, so a
        manifest naming only this repository cannot identify what produced the numbers.
        """
        book = manifest.build({"name": "t"})
        assert "green_rerank" in book and "companion" in book
        assert set(book["green_rerank"]) >= {"revision", "branch", "dirty"}

    def test_is_json_safe_with_a_dataclass_inside(self):
        import json

        from green_rerank.measure.guards import Preflight

        book = manifest.build({"n": 1}, preflight=Preflight(power_source="ac"))
        json.dumps(book)  # must not raise
        assert book["preflight"]["power_source"] == "ac"

    def test_a_dirty_tree_is_visible_in_the_summary(self):
        book = {
            "green_rerank": {"revision": "a" * 40, "dirty": True},
            "companion": {"revision": "b" * 40, "dirty": False},
        }
        text = manifest.summary(book)
        assert "aaaaaaa-dirty" in text and "bbbbbbb" in text and "bbbbbbb-dirty" not in text

    def test_an_uncommitted_checkout_is_not_reported_as_clean(self):
        assert "uncommitted" in manifest.summary({"green_rerank": {}, "companion": {}})

    def test_results_being_written_do_not_count_as_dirty_code(self, tmp_path: Path):
        """Otherwise the dirty flag is true in every manifest and means nothing.

        A sweep writes its results into the working tree, so an unfiltered
        ``git status`` is non-empty for the entire duration of every run. The flag is
        there to answer one question -- is the code that produced these numbers the code
        someone can check out -- and results churn drowns it out completely.
        """
        import subprocess

        def git(*args):
            subprocess.run(["git", *args], cwd=tmp_path, capture_output=True, check=False)

        git("init")
        git("config", "user.email", "t@example.com")
        git("config", "user.name", "t")
        (tmp_path / "code.py").write_text("x = 1\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-m", "initial")

        assert manifest.git_state(tmp_path)["dirty"] is False

        # Results appear: the tree is dirty, the code is not.
        (tmp_path / "results").mkdir()
        (tmp_path / "results" / "runs.csv").write_text("a,b\n1,2\n", encoding="utf-8")
        state = manifest.git_state(tmp_path)
        assert state["dirty"] is False
        assert state["tree_dirty"] is True

        # A real source change is still caught.
        (tmp_path / "code.py").write_text("x = 2\n", encoding="utf-8")
        assert manifest.git_state(tmp_path)["dirty"] is True


# ------------------------------------------------------------------------ analysis


def _runs(tmp_path: Path, trustworthy: bool = True, repeats: int = 4) -> Path:
    """A minimal results file with two families of opposite cost shape."""
    rng = np.random.default_rng(0)
    served = 200
    rows = []
    for repeat in range(repeats):
        for family, once, per_request, ndcg in (
            ("itemknn", 0.4, 5.0e-4, 0.14),
            ("als", 0.7, 1.0e-4, 0.09),
        ):
            for reranker in ("none", "quota_mmr"):
                extra = 1.0e-3 if reranker != "none" else 0.0
                rows.append(
                    {
                        "dataset": "d",
                        "family": family,
                        "reranker": reranker,
                        "repeat": repeat,
                        "status": "ok",
                        "trustworthy": trustworthy,
                        "n_items": 1349,
                        "ndcg": ndcg,
                        "recall": ndcg,
                        "exposure_parity": 0.3,
                        # Per-request stage columns hold the cost of serving *all*
                        # the users in the window, exactly as the runner writes them;
                        # only `cpu_per_request` is divided. A fixture that stored them
                        # already divided would let a missing division pass unnoticed.
                        "n_users": served,
                        "cpu_once": once * (1 + 0.05 * rng.standard_normal()),
                        "cpu_per_request": (per_request + extra),
                        "cpu_train": once,
                        "cpu_rerank_setup": 0.001 if reranker != "none" else 0.0,
                        "cpu_retrieve_score": per_request * 0.6 * served,
                        "cpu_retrieve_select": per_request * 0.4 * served,
                        "cpu_rerank": extra * served,
                    }
                )
    path = tmp_path / "runs.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return tmp_path


class TestAnalysis:
    def test_untrustworthy_results_stop_the_analysis(self, tmp_path: Path):
        # A cost measured while another process held the CPU is not a worse measurement,
        # it is a measurement of something else, and it looks entirely normal in a table.
        directory = _runs(tmp_path, trustworthy=False)
        with pytest.raises(SystemExit, match="untrustworthy"):
            load_runs(directory)
        assert len(load_runs(directory, allow_untrustworthy=True)) > 0

    def test_failed_runs_are_dropped_but_the_rest_survive(self, tmp_path: Path):
        directory = _runs(tmp_path)
        frame = pd.read_csv(directory / "runs.csv")
        frame.loc[0, "status"] = "failed"
        frame.to_csv(directory / "runs.csv", index=False)
        assert len(load_runs(directory)) == len(frame) - 1

    def test_repeats_are_gathered_not_averaged_away(self, tmp_path: Path):
        table = cost_table(load_runs(_runs(tmp_path, repeats=4)))
        assert set(table["repeats"]) == {4}
        # The spread column is what makes a difference between families readable.
        assert (table["spread_once"] > 0).all()

    def test_the_breakeven_table_covers_every_pair_once(self, tmp_path: Path):
        table = breakeven_table(load_runs(_runs(tmp_path)))
        # Four configurations -> six unordered pairs.
        assert len(table) == 6
        assert len({frozenset((r.a, r.b)) for r in table.itertuples()}) == 6

    def test_the_expected_crossover_is_found_and_marked_stable(self, tmp_path: Path):
        table = breakeven_table(load_runs(_runs(tmp_path, repeats=6)))
        row = table[(table.a == "itemknn") & (table.b == "als")].iloc[0]
        # (0.7-0.4)/(5e-4 - 1e-4) = 750 requests.
        assert row["stable"]
        assert 400 < row["n_requests"] < 1400
        assert row["cheaper_below"] == "itemknn"
        assert row["cheaper_above"] == "als"

    def test_rerank_share_covers_only_reranked_rows(self, tmp_path: Path):
        table = rerank_share(load_runs(_runs(tmp_path)))
        assert set(table["reranker"]) == {"quota_mmr"}
        assert (table["rerank_share_of_serving"] > 0.5).all()
        # Serving cost more than doubled, which is the deployer-facing framing.
        assert (table["serving_multiplier"] > 2).all()

    def test_labels_distinguish_a_reranked_family_from_a_plain_one(self):
        assert label_of("als", "none") == "als"
        assert label_of("als", "quota_mmr") == "als+quota_mmr"


def _per_user(tmp_path: Path, n_users: int = 200, repeats: int = 2) -> Path:
    """Per-user metrics where itemknn genuinely beats popularity on most users.

    200 users, matching the sweep's own setting, and the number is not decorative. At
    40 users a hit-rate difference of 0.45 against 0.15 leaves only ~15 users decided
    and reaches p = 0.07 -- an effect that is unambiguously real in the generator and
    still not detectable in the sample. That is the whole reason accuracy needs a paired
    test rather than a comparison of means, and the reason the sweep serves 200.
    """
    rng = np.random.default_rng(1)
    rows = []
    for repeat in range(repeats):
        users = rng.choice(500, size=n_users, replace=False)
        for family, hit_rate in (("itemknn", 0.45), ("popularity", 0.15)):
            hits = rng.random(n_users) < hit_rate
            for user, hit in zip(users, hits, strict=True):
                rows.append(
                    {
                        "user_row": int(user),
                        "dataset": "d",
                        "family": family,
                        "reranker": "none",
                        "repeat": repeat,
                        "ndcg": float(hit),
                        "recall": float(hit),
                        "exposure_parity": 0.5 if family == "itemknn" else 0.9,
                        "intra_list_similarity": np.nan,
                    }
                )
    path = tmp_path / "per_user.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


class TestPairedComparison:
    """Accuracy has to be held to the same standard of evidence as cost."""

    def test_a_real_difference_is_detected_with_its_effect_size(self, tmp_path: Path):
        from experiments.compare import compare_all

        table = compare_all(pd.read_csv(_per_user(tmp_path)), reference="itemknn")
        row = table[(table.config == "popularity") & (table.metric == "ndcg")].iloc[0]
        assert row["worse"] > row["better"]
        assert row["significant"]
        # Effect size is reported, not only the verdict.
        assert row["ci_lo"] <= row["median_diff"] <= row["ci_hi"]

    def test_repeats_are_not_pooled(self, tmp_path: Path):
        """Pooling repeats would compare a user against a different user.

        Each repeat resamples the served users, so concatenating them puts the same
        `user_row` in the table more than once with different partners. The merge would
        then pair rows across repeats and produce a difference distribution that looks
        entirely ordinary and means nothing.
        """
        from experiments.compare import compare_all

        table = compare_all(
            pd.read_csv(_per_user(tmp_path, n_users=200, repeats=3)), reference="itemknn"
        )
        assert (table["n_users"] <= 200).all()

    def test_a_metric_only_one_side_computed_is_skipped(self, tmp_path: Path):
        """Intra-list similarity exists only for runs that built a similarity matrix.

        Comparing a reranked run against a plain one on it yields all-NaN. Reporting
        that as "no detectable difference" would state a null result about a comparison
        that never happened.
        """
        from experiments.compare import compare_all

        table = compare_all(pd.read_csv(_per_user(tmp_path)), reference="itemknn")
        assert "intra_list_similarity" not in set(table["metric"])

    def test_lower_is_better_metrics_count_the_right_way(self, tmp_path: Path):
        """Getting this backwards inverts the verdict while every number stays correct.

        itemknn has the lower exposure-parity score here, and lower is better for that
        metric, so popularity must be recorded as *worse* despite its larger value.
        """
        from experiments.compare import compare_all

        table = compare_all(pd.read_csv(_per_user(tmp_path)), reference="itemknn")
        row = table[table.metric == "exposure_parity"].iloc[0]
        assert row["worse"] > row["better"]

    def test_an_unknown_reference_lists_the_available_ones(self, tmp_path: Path):
        from experiments.compare import compare_all

        with pytest.raises(SystemExit, match="not among"):
            compare_all(pd.read_csv(_per_user(tmp_path)), reference="nope")


class TestFigures:
    """Smoke tests only.

    A figure's *content* is not worth asserting -- pixel comparisons break on every
    matplotlib release and tell you nothing about whether the plot is right. What is
    worth asserting is that the code path runs on real result shapes, because these
    functions index columns by name and a renamed column would break them silently at
    report time, which is the worst moment to discover it.
    """

    def test_every_figure_is_produced(self, tmp_path: Path):
        from experiments.figures import all_figures

        made = all_figures(_runs(tmp_path, repeats=4))
        assert len(made) >= 3
        assert all(p.exists() and p.stat().st_size > 0 for p in made)

    def test_figures_also_refuse_untrustworthy_rows(self, tmp_path: Path):
        # The refusal lives in load_runs, and this asserts the figure path goes through
        # it rather than reading the CSV itself.
        from experiments.figures import all_figures

        with pytest.raises(SystemExit, match="untrustworthy"):
            all_figures(_runs(tmp_path, trustworthy=False))
