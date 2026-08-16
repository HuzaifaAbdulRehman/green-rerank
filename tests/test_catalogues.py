"""Invariants for the catalogue registry.

The registry decides which files a measurement is taken on. Its failure modes are the
ones that produce a complete, plausible results table describing the wrong thing: a
catalogue silently loaded with different preprocessing than another it is compared
against, or a name resolving to a file nobody meant.

The cache is the sharpest of these. Loading the largest catalogue takes longer than the
measurements do, so it is cached -- and a cache keyed on the name alone would serve a
5-core dataset to a run that asked for 10-core, making two incomparable runs look
comparable with nothing in the output to show for it.
"""

from __future__ import annotations

import pytest

from green_rerank import catalogues
from green_rerank.catalogues import CATALOGUES, available, get, resolve


class TestRegistry:
    def test_every_entry_is_keyed_by_its_own_name(self):
        # A mismatch here means `load("software")` could return the appliances loader,
        # and every downstream label would still say "software".
        for key, catalogue in CATALOGUES.items():
            assert key == catalogue.name

    def test_every_entry_declares_a_known_kind(self):
        assert {c.kind for c in CATALOGUES.values()} <= {"movielens", "amazon"}

    def test_every_entry_states_its_grouping(self):
        """Exposure parity over genres and over popularity tiers are different claims.

        A results table that put both in one column without saying which is which would
        be comparing a curator-assigned partition against one derived from the very
        interaction counts being evaluated.
        """
        for catalogue in CATALOGUES.values():
            assert catalogue.grouping in {"curator genres", "popularity tiers"}
            assert catalogue.note

    def test_an_unknown_name_lists_the_known_ones(self):
        with pytest.raises(KeyError, match="unknown catalogue"):
            get("nonexistent")

    def test_the_error_names_the_alternatives(self):
        try:
            get("nonexistent")
        except KeyError as error:
            assert "ml100k" in str(error)


class TestResolution:
    def test_a_missing_catalogue_reports_every_path_it_tried(self, monkeypatch, tmp_path):
        """A bare "not found" is useless when three roots are searched.

        The usual cause is a checkout in an unexpected place, and the fix is to know
        which directories were considered.
        """
        monkeypatch.setattr(catalogues, "data_roots", lambda: [tmp_path])
        with pytest.raises(FileNotFoundError) as error:
            resolve("ml100k")
        assert str(tmp_path) in str(error.value)
        assert "GREEN_RERANK_DATA" in str(error.value)

    def test_the_local_data_directory_is_searched_before_the_companion(self, monkeypatch):
        """A copy in this repository must win over the companion's.

        Otherwise editing a local dataset to reproduce a bug would have no effect, and
        the run would silently keep using the sibling checkout's copy.
        """
        roots = catalogues.data_roots()
        assert roots[0] == catalogues.REPO_ROOT / "data"

    def test_an_env_override_is_searched_before_the_companion(self, monkeypatch, tmp_path):
        monkeypatch.setenv("GREEN_RERANK_DATA", str(tmp_path))
        roots = catalogues.data_roots()
        assert tmp_path in roots
        # After the repository's own data/, before any companion fallback.
        assert roots.index(tmp_path) == 1

    def test_available_reports_only_what_is_present(self, monkeypatch, tmp_path):
        monkeypatch.setattr(catalogues, "data_roots", lambda: [tmp_path])
        assert available() == []


class TestPreprocessingCache:
    def test_the_cache_is_keyed_on_the_preprocessing_arguments(self):
        """The failure this prevents makes incomparable runs look comparable.

        Loading the largest catalogue costs more than the measurements do, so results
        are cached. Keyed on the name alone, a run asking for 10-core filtering would be
        handed the 5-core dataset a previous run built -- a different set of users and
        items, reported under the same catalogue name, with nothing in the output
        showing the substitution.
        """
        import inspect

        signature = inspect.signature(catalogues._load_cached)
        assert list(signature.parameters) == [
            "name",
            "min_interactions",
            "n_groups",
            "max_sequence",
        ]

    @pytest.mark.needs_companion
    def test_two_filtering_settings_give_two_different_datasets(self):
        if "ml100k" not in available():
            pytest.skip("ml100k is not present on this machine")
        loose = catalogues.load("ml100k", min_interactions=5)
        strict = catalogues.load("ml100k", min_interactions=20)
        assert strict.n_users < loose.n_users
        # And the loose one is still itself: the cache returned the right object.
        assert catalogues.load("ml100k", min_interactions=5) is loose


@pytest.mark.needs_companion
class TestRealCatalogues:
    """Only runs where the data is actually present."""

    def test_each_present_catalogue_loads_with_aligned_shapes(self):
        names = available()
        if not names:
            pytest.skip("no catalogues present on this machine")
        for name in names:
            dataset = catalogues.load(name)
            assert dataset.groups.shape[0] == dataset.n_items
            assert len(dataset.item_ids) == dataset.n_items
            # Every held-out target must index a real column, or the metrics would be
            # scoring against an item that does not exist.
            assert all(0 <= item < dataset.n_items for item in dataset.held_out.values())

    def test_group_labels_are_aligned_with_the_matrix_columns(self):
        """`groups[i]` must describe `item_ids[i]`, and nothing downstream checks it.

        Every fairness number in this study -- exposure parity improving on 200 of 200
        users, the whole of claim 2's benefit side -- is computed by looking up
        `groups[candidate_column]`. Misalign that mapping and the metric still returns a
        number in the right range, still responds to reranking, and is measuring a
        permutation of the truth.

        Found by mutation testing: reversing the item order passed to the grouping
        function left the entire suite green.

        Checked on MovieLens because its groups come from curator genres, which are
        keyed by item id. The Amazon catalogues use popularity tiers derived from column
        sums, which cannot be misaligned this way.
        """
        import numpy as np

        if "ml100k" not in available():
            pytest.skip("ml100k is not present on this machine")

        from benchmarks.movielens import genre_groups, load_genres

        dataset = catalogues.load("ml100k")
        genres = load_genres(catalogues.resolve("ml100k"))
        expected = genre_groups(genres, list(dataset.item_ids), dataset.stats["n_groups"])

        assert np.array_equal(dataset.groups, expected)

    def test_popularity_tiers_put_the_most_popular_item_in_the_head_tier(self):
        """The Amazon grouping, checked against the data it claims to describe."""
        import numpy as np

        names = [n for n in available() if catalogues.get(n).grouping == "popularity tiers"]
        if not names:
            pytest.skip("no popularity-tiered catalogue present")

        dataset = catalogues.load(names[0])
        popularity = np.asarray(dataset.train.sum(axis=0)).ravel()
        busiest, quietest = int(popularity.argmax()), int(popularity.argmin())
        assert dataset.groups[busiest] != dataset.groups[quietest]

    def test_held_out_items_are_absent_from_training(self):
        names = available()
        if not names:
            pytest.skip("no catalogues present on this machine")
        dataset = catalogues.load(names[0])
        for row, target in list(dataset.held_out.items())[:200]:
            assert target not in set(dataset.train[row].indices.tolist())
