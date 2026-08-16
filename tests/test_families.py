"""Invariants every model family must satisfy.

The most valuable test here is the leakage one. A family that forgets to exclude items
the user already interacted with posts *better* accuracy for a reason that has nothing to
do with being a better model, and nothing in the output looks wrong -- the lists are the
right length and full of plausible items. That is the same failure shape as the
companion project's penalty barrier, and it is why the exclusion lives in the base class
and is asserted for every family rather than trusted to each one.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import sparse

from green_rerank.families import CLASSICAL, ImplicitALS, Popularity, build
from green_rerank.families.base import Family, Recommendations, Sequences
from green_rerank.families.neural import GRU4Rec, MultVAE, torch_available


def block_matrix(n_users=60, n_items=40, blocks=4, seed=0):
    """Users in ``blocks`` groups, each preferring its own contiguous item block.

    Structure a latent-factor model should recover and a neighbourhood model should see
    in co-occurrence. Having a *known* answer is what makes it possible to assert a
    family is optimising rather than merely running -- the same role the companion
    project's "at lam=0 the optimum is greedy top-k, and it returns exactly that" check
    plays.
    """
    rng = np.random.default_rng(seed)
    rows, cols = [], []
    per_block = n_items // blocks
    for user in range(n_users):
        block = user % blocks
        lo, hi = block * per_block, (block + 1) * per_block
        chosen = rng.choice(np.arange(lo, hi), size=max(2, per_block // 2), replace=False)
        rows.extend([user] * len(chosen))
        cols.extend(chosen.tolist())
    data = np.ones(len(rows))
    return sparse.csr_matrix((data, (rows, cols)), shape=(n_users, n_items))


def user_block(row: int, n_items=40, blocks=4) -> range:
    per_block = n_items // blocks
    block = row % blocks
    return range(block * per_block, (block + 1) * per_block)


needs_torch = pytest.mark.skipif(not torch_available(), reason="torch is an optional extra")

ALL_FAMILIES = [
    pytest.param(Popularity, {}, id="popularity"),
    pytest.param(ImplicitALS, {"factors": 8, "epochs": 5}, id="als"),
    # MultVAE joins the shared contract because it needs no interaction order. The
    # epoch and width settings are the smallest that still train; the contract tests
    # assert structure -- shapes, leakage, determinism -- not accuracy.
    pytest.param(
        MultVAE,
        {"epochs": 1, "latent": 4, "hidden": 8, "batch_size": 16},
        id="multvae",
        marks=needs_torch,
    ),
]


# ------------------------------------------------------------------- the contract


@pytest.mark.parametrize("cls,kwargs", ALL_FAMILIES)
class TestFamilyContract:
    def test_serving_before_training_is_refused(self, cls, kwargs):
        with pytest.raises(RuntimeError, match="fitted"):
            cls(**kwargs).recommend(block_matrix(), np.array([0]), n=5)

    def test_shapes_line_up(self, cls, kwargs):
        matrix = block_matrix()
        rows = np.array([0, 1, 2])
        recs = cls(**kwargs).fit(matrix).recommend(matrix, rows, n=7)
        assert recs.items.shape == (3, 7)
        assert recs.scores.shape == (3, 7)
        assert np.array_equal(recs.user_rows, rows)

    def test_never_recommends_an_item_the_user_already_has(self, cls, kwargs):
        """The leakage rule. Invisible in the output if broken."""
        matrix = block_matrix()
        rows = np.arange(matrix.shape[0])
        recs = cls(**kwargs).fit(matrix).recommend(matrix, rows, n=10)
        for position, row in enumerate(rows):
            seen = set(matrix[row].indices.tolist())
            assert not seen & set(recs.items[position].tolist())

    def test_scores_are_descending(self, cls, kwargs):
        matrix = block_matrix()
        recs = cls(**kwargs).fit(matrix).recommend(matrix, np.array([0, 5]), n=8)
        for row in recs.scores:
            assert np.all(np.diff(row) <= 1e-12)

    def test_items_are_distinct(self, cls, kwargs):
        matrix = block_matrix()
        recs = cls(**kwargs).fit(matrix).recommend(matrix, np.array([0, 3]), n=9)
        for row in recs.items:
            assert len(set(row.tolist())) == len(row)

    def test_asking_for_more_than_the_catalogue_is_an_error(self, cls, kwargs):
        matrix = block_matrix()
        model = cls(**kwargs).fit(matrix)
        with pytest.raises(ValueError, match="exceeds the catalogue"):
            model.recommend(matrix, np.array([0]), n=matrix.shape[1] + 1)

    def test_repeated_serving_is_deterministic(self, cls, kwargs):
        # Cost comparisons are run repeatedly and differenced. A family that returned a
        # different list each call would put noise into every downstream metric while
        # still looking entirely reasonable in any single run.
        matrix = block_matrix()
        model = cls(**kwargs).fit(matrix)
        first = model.recommend(matrix, np.array([0, 1]), n=6)
        second = model.recommend(matrix, np.array([0, 1]), n=6)
        assert np.array_equal(first.items, second.items)

    def test_model_bytes_is_reported(self, cls, kwargs):
        matrix = block_matrix()
        model = cls(**kwargs).fit(matrix)
        assert model.model_bytes > 0


# ------------------------------------------------------------------- tie-breaking


class TestTieBreaking:
    def test_fast_path_matches_the_reference_lexsort_exactly(self):
        """The optimised top-k must be the same function, not merely a similar one.

        ``_top_n`` was rewritten because the original per-user ``lexsort`` loop was 99.8 %
        of popularity's measured serving cost -- the harness was drowning out the
        families it was meant to compare. A faster implementation that broke ties
        differently would silently change which items every family returns, so this
        asserts equality against the reference rule element-for-element, including on
        data engineered to be almost entirely ties.

        This is the same shape of test as the companion project's "sparse and dense
        similarity agree exactly", which caught a real bug there.
        """
        rng = np.random.default_rng(0)
        for scores in (
            rng.random((7, 50)),
            # Heavy ties: rounding to one decimal guarantees large equal blocks.
            np.round(rng.random((7, 50)), 1),
            # Every score identical -- tie-breaking is the only thing being tested.
            np.zeros((4, 20)),
            # Excluded items, which must sort last rather than first.
            np.where(rng.random((5, 30)) < 0.3, -np.inf, rng.random((5, 30))),
        ):
            columns = np.arange(scores.shape[1])
            expected = np.stack(
                [np.lexsort((columns, -row))[:10] for row in scores]
            )
            items, ordered = Family._top_n(scores, 10)
            assert np.array_equal(items, expected)
            assert np.array_equal(ordered, np.take_along_axis(scores, expected, axis=1))

    def test_ties_break_by_index_not_memory_order(self):
        """Ties are common and ``argpartition`` breaks them by memory order.

        That makes the result depend on how the matrix happened to be built. Popularity
        on a uniform catalogue is the extreme case: every score is identical, so without
        a rule the output is arbitrary.
        """
        scores = np.array([[5.0, 5.0, 5.0, 1.0]])
        items, ordered = Family._top_n(scores, 3)
        assert items[0].tolist() == [0, 1, 2]
        assert ordered[0].tolist() == [5.0, 5.0, 5.0]

    def test_negative_scores_still_rank_below_excluded_items(self):
        """Exclusion uses -inf, not 0.

        A factor model produces genuinely negative scores. Masking seen items with zero
        would leave them ranked *above* legitimate negative-scoring candidates, quietly
        reintroducing the leakage the mask exists to prevent.
        """
        matrix = sparse.csr_matrix(np.array([[1.0, 0.0, 0.0]]))

        class Negative(Family):
            name = "negative"

            def fit(self, m):
                self._n_items = m.shape[1]
                self._fitted = True
                return self

            def _scores(self, m, rows):
                return np.array([[10.0, -5.0, -7.0]])

        recs = Negative().fit(matrix).recommend(matrix, np.array([0]), n=2)
        assert recs.items[0].tolist() == [1, 2]


# --------------------------------------------------------------------- popularity


class TestPopularity:
    def test_every_user_gets_the_same_ranking_modulo_exclusions(self):
        matrix = block_matrix()
        model = Popularity().fit(matrix)
        recs = model.recommend(matrix, np.array([0, 1]), n=5, exclude_seen=False)
        assert recs.items[0].tolist() == recs.items[1].tolist()

    def test_ranks_by_interaction_count(self):
        matrix = sparse.csr_matrix(np.array([[1.0, 1.0, 0.0], [0.0, 1.0, 0.0]]))
        recs = Popularity().fit(matrix).recommend(matrix, np.array([0]), n=3, exclude_seen=False)
        assert recs.items[0][0] == 1  # column 1 has two interactions


# ---------------------------------------------------------------------------- ALS


class TestImplicitALS:
    def test_recovers_block_structure(self):
        """The check that ALS is optimising rather than merely running.

        A model that fitted nothing would rank items arbitrarily. On data where users
        split into blocks, a trained factor model must prefer unseen items from the
        user's *own* block. Without an assertion like this a silently broken solver
        still produces full, plausible-looking recommendation lists.
        """
        matrix = block_matrix(n_users=80, n_items=40, blocks=4)
        model = ImplicitALS(factors=16, epochs=20, seed=0).fit(matrix)

        rows = np.arange(0, 40)
        recs = model.recommend(matrix, rows, n=5)

        hits = sum(
            1
            for position, row in enumerate(rows)
            for item in recs.items[position]
            if item in user_block(row)
        )
        # Chance is 1 in 4 (four equal blocks). Demanding well above chance keeps the
        # test meaningful without making it brittle to the random init.
        assert hits / (len(rows) * 5) > 0.6

    def test_training_is_work_bounded_not_time_bounded(self):
        # More epochs must do strictly more work and change the model. A family whose
        # stopping rule were wall-clock would make its own quality depend on machine
        # speed -- the flaw that made the companion project's tabu results non-portable.
        matrix = block_matrix()
        short = ImplicitALS(factors=8, epochs=1, seed=0).fit(matrix)
        long = ImplicitALS(factors=8, epochs=10, seed=0).fit(matrix)
        assert not np.allclose(short._item_factors, long._item_factors)

    def test_same_seed_reproduces_exactly(self):
        matrix = block_matrix()
        a = ImplicitALS(factors=8, epochs=3, seed=7).fit(matrix)
        b = ImplicitALS(factors=8, epochs=3, seed=7).fit(matrix)
        assert np.allclose(a._user_factors, b._user_factors)

    def test_users_with_no_interactions_do_not_break_the_solve(self):
        # A cold user contributes no rows to the least-squares system, which is singular
        # rather than merely ill-conditioned. Zeroing is the defined answer; crashing
        # halfway through an experiment batch is not.
        dense = np.zeros((5, 6))
        dense[0, :3] = 1.0
        matrix = sparse.csr_matrix(dense)
        model = ImplicitALS(factors=4, epochs=3).fit(matrix)
        assert np.allclose(model._user_factors[4], 0.0)

    def test_model_size_grows_with_factors(self):
        matrix = block_matrix()
        small = ImplicitALS(factors=4, epochs=1).fit(matrix)
        large = ImplicitALS(factors=32, epochs=1).fit(matrix)
        assert large.model_bytes > small.model_bytes


# -------------------------------------------------------------------------- build


@needs_torch
class TestNeural:
    """The sequential family, which cannot join the shared contract.

    ``GRU4Rec`` needs interaction *order*, so every contract test that calls
    ``fit(matrix)`` would raise for it. Testing it separately is the cost of that, and
    it is worth paying: these families went their whole first draft without being
    executed once, and the first run found a constructor that accepted
    ``learning_rate`` and never stored it -- a crash on the first line of ``fit`` that
    no amount of reading had surfaced.
    """

    @staticmethod
    def _sequences(matrix) -> Sequences:
        return Sequences(
            by_user={row: matrix[row].indices.tolist() for row in range(matrix.shape[0])},
            max_length=20,
        )

    @staticmethod
    def _model(**kwargs) -> GRU4Rec:
        defaults = {"epochs": 1, "hidden": 8, "embedding": 8, "batch_size": 16, "max_length": 20}
        return GRU4Rec(**{**defaults, **kwargs})

    def test_every_constructor_argument_survives_into_fit(self):
        """Directly against the bug the first execution found.

        A constructor argument that is accepted and dropped is invisible until the
        attribute is read, which happened inside ``fit`` -- so the family imported,
        constructed, and appeared in the registry while being impossible to train.
        """
        model = self._model(learning_rate=5e-4)
        assert model.learning_rate == 5e-4
        matrix = block_matrix()
        model.fit(matrix, self._sequences(matrix))
        assert model._fitted

    def test_trains_and_serves(self):
        matrix = block_matrix()
        model = self._model().fit(matrix, self._sequences(matrix))
        recs = model.recommend(matrix, np.array([0, 1, 2]), n=5)
        assert recs.items.shape == (3, 5)
        assert np.all(np.diff(recs.scores, axis=1) <= 1e-12)

    def test_training_without_sequences_is_refused(self):
        # Silently training on the interaction matrix alone would produce a model that
        # looks trained and has learned no order at all -- the entire point of the family.
        with pytest.raises((ValueError, TypeError), match="sequence"):
            self._model().fit(block_matrix(), None)

    def test_never_recommends_a_seen_item(self):
        matrix = block_matrix()
        model = self._model().fit(matrix, self._sequences(matrix))
        rows = np.arange(matrix.shape[0])
        recs = model.recommend(matrix, rows, n=6)
        for position, row in enumerate(rows):
            assert not set(matrix[row].indices.tolist()) & set(recs.items[position].tolist())

    def test_padding_index_is_reserved(self):
        """The classic sequence-model bug, asserted structurally.

        Without a reserved pad token the network learns that item 0 begins every short
        session. The model still trains, still scores, and is quietly wrong about one
        real catalogue item -- so this is checked on the embedding table rather than
        through behaviour, where it would be invisible.
        """
        matrix = block_matrix()
        model = self._model().fit(matrix, self._sequences(matrix))
        embedding = model._net.embed
        assert embedding.num_embeddings == matrix.shape[1] + 1
        assert embedding.padding_idx == 0
        # Read through numpy rather than torch: torch is an optional extra and must not
        # be imported at this module's scope, or collecting the suite would fail on a
        # machine without it.
        assert not embedding.weight[0].detach().numpy().any()

    def test_repeated_serving_is_deterministic(self):
        # The VAE samples its latent during training and must not at serving time.
        matrix = block_matrix()
        model = self._model().fit(matrix, self._sequences(matrix))
        first = model.recommend(matrix, np.array([0, 4]), n=5)
        second = model.recommend(matrix, np.array([0, 4]), n=5)
        assert np.array_equal(first.items, second.items)

    def test_multvae_does_not_sample_at_serving_time(self):
        """Two identical calls must return identical lists.

        The VAE draws ``z = mu + std * eps`` while training. If ``eval()`` were not set,
        or the sampling branch not guarded on ``self.training``, recommendations would
        differ between calls -- and the cost study repeats every measurement, so that
        noise would land in every downstream metric while each run looked reasonable.
        """
        matrix = block_matrix()
        model = MultVAE(epochs=1, latent=4, hidden=8, batch_size=16).fit(matrix)
        first = model.recommend(matrix, np.array([0, 3]), n=5)
        second = model.recommend(matrix, np.array([0, 3]), n=5)
        assert np.array_equal(first.items, second.items)
        assert np.allclose(first.scores, second.scores)

    def test_model_bytes_is_reported(self):
        # Memory is one of the costs the study reports, and a family that returns zero
        # would silently look free on that axis.
        matrix = block_matrix()
        model = self._model().fit(matrix, self._sequences(matrix))
        assert model.model_bytes > 0


class TestBuild:
    def test_builds_every_classical_family_by_name(self):
        for name in CLASSICAL:
            assert build(name).name == name

    def test_unknown_family_lists_the_known_ones(self):
        with pytest.raises(KeyError, match="unknown family"):
            build("does-not-exist")

    def test_kwargs_reach_the_constructor(self):
        assert build("als", factors=17).factors == 17


# ----------------------------------------------------------------- recommendations


class TestRecommendations:
    def test_mismatched_shapes_are_rejected_at_construction(self):
        with pytest.raises(ValueError, match="disagree"):
            Recommendations(
                items=np.zeros((2, 3), dtype=np.int64),
                scores=np.zeros((2, 4)),
                user_rows=np.arange(2),
            )

    def test_one_row_per_user_is_required(self):
        with pytest.raises(ValueError, match="per user"):
            Recommendations(
                items=np.zeros((2, 3), dtype=np.int64),
                scores=np.zeros((2, 3)),
                user_rows=np.arange(3),
            )
