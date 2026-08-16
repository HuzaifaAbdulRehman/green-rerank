"""Invariants for locating and importing from the companion project.

Both repositories have a top-level ``experiments`` directory. Resolving that collision
correctly is fiddly, and getting it wrong produces the worst kind of failure: code from
the wrong repository running under the right name, computing plausible numbers.

``companion_first`` temporarily rebinds the name. The danger is not that the rebinding
fails -- that raises immediately and is obvious -- but that it is never *undone*, so
every later import in the process silently comes from the other checkout. Found by
mutation testing: deleting the restoration left the whole suite passing.
"""

from __future__ import annotations

import sys

import pytest

from green_rerank import companion
from green_rerank.companion import CompanionNotFound, available, companion_first

needs_companion = pytest.mark.skipif(
    not available(), reason="needs the feasible-rerank checkout"
)


class TestResolution:
    def test_a_missing_companion_names_every_path_tried(self, monkeypatch):
        monkeypatch.setattr(companion, "candidate_paths", lambda: [])
        companion.companion_root.cache_clear()
        try:
            with pytest.raises(CompanionNotFound, match="feasible-rerank"):
                companion.companion_root()
        finally:
            companion.companion_root.cache_clear()

    def test_a_directory_of_the_right_name_is_not_enough(self, tmp_path, monkeypatch):
        """A half-cloned or renamed directory must fail here, not at first use.

        Checked against a module this project actually imports, so the error arrives
        with a useful message rather than as an AttributeError fifty frames deep.
        """
        (tmp_path / "qubo-rerank").mkdir()
        monkeypatch.setattr(companion, "candidate_paths", lambda: [tmp_path / "qubo-rerank"])
        companion.companion_root.cache_clear()
        try:
            with pytest.raises(CompanionNotFound):
                companion.companion_root()
        finally:
            companion.companion_root.cache_clear()


@needs_companion
class TestCompanionFirst:
    def test_the_companion_module_is_the_one_imported(self):
        with companion_first("experiments"):
            from experiments.paired import holm

        # A pure function over dicts; if this were our own module it would not exist.
        rows = [{"p_raw": 0.001}, {"p_raw": 0.5}]
        corrected = holm(rows)
        assert {"p_holm", "significant"} <= set(corrected[0])

    def test_the_original_module_objects_are_restored_not_merely_re_importable(self):
        """Identity, not just the path -- and the distinction is the whole point.

        Evicting the shim on exit is enough for a later ``import experiments.analyse``
        to resolve back to this project, so a test checking ``__file__`` passes even
        when the saved modules are never put back. But that import builds a *new* module
        object, and anything already holding the old one -- every ``from experiments.x
        import y`` executed earlier in the process -- keeps pointing at a separate copy
        with its own state.

        Mutation testing found this: deleting the restoration left a ``__file__`` check
        green, so the assertion is on ``is``.
        """
        import experiments.analyse as before

        with companion_first("experiments"):
            pass

        import experiments.analyse as after

        assert after is before
        assert sys.modules["experiments.analyse"] is before
        assert "rerank-green" in after.__file__

    def test_it_is_restored_even_when_the_body_raises(self):
        import experiments.analyse as before

        with pytest.raises(RuntimeError):
            with companion_first("experiments"):
                raise RuntimeError("boom")

        import experiments.analyse as after

        assert after.__file__ == before.__file__

    def test_submodules_loaded_inside_do_not_leak_out(self):
        with companion_first("experiments"):
            import experiments.paired  # noqa: F401

        # The companion's module must not remain registered under a name that now
        # resolves to this project's package.
        assert "experiments.paired" not in sys.modules

    def test_an_absent_directory_is_a_clear_error(self):
        with pytest.raises(CompanionNotFound, match="no nonexistent/ directory"):
            with companion_first("nonexistent"):
                pass

    def test_our_own_package_still_wins_outside_the_block(self):
        # ensure_importable appends rather than prepends precisely so that a stray
        # companion file can never shadow one of ours by accident.
        from experiments import analyse

        assert "rerank-green" in analyse.__file__
