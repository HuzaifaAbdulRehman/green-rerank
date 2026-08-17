"""Tests for the report/data diff.

The point of :mod:`experiments.check_report` is to fail when the report disagrees with the
data. A checker that has quietly stopped comparing anything passes silently and reads
exactly like a checker that found nothing wrong -- which is the same failure mode as the
frequency sensor in §8 and codecarbon's utilisation channel in §5. So the thing worth
testing is not that it passes on the real report; it is that it **fails** when it should.
"""

from __future__ import annotations

import shutil

import pytest

from experiments import check_report

pytestmark = pytest.mark.needs_companion


@pytest.fixture()
def report_copy(tmp_path, monkeypatch):
    """A writable copy of the real report, with the module pointed at it."""
    if not check_report.REPORT.exists():  # pragma: no cover - defensive
        pytest.skip("docs/report.md is absent")
    target = tmp_path / "report.md"
    shutil.copy(check_report.REPORT, target)
    monkeypatch.setattr(check_report, "REPORT", target)
    return target


class TestRowsUnder:
    def test_it_takes_the_rows_after_the_separator(self):
        text = "\n".join(
            [
                "prose",
                "| a | b |",
                "|---|---|",
                "| 1 | 2 |",
                "| 3 | 4 |",
                "",
                "more prose",
            ]
        )
        assert check_report.rows_under(text, "| a | b |") == ["| 1 | 2 |", "| 3 | 4 |"]

    def test_a_missing_header_is_none_rather_than_empty(self):
        # Empty would be indistinguishable from a table that legitimately has no rows,
        # and would let a deleted table pass as an unchanged one.
        assert check_report.rows_under("| a |\n|---|\n", "| nope |") is None


class TestItFailsOnDisagreement:
    def test_the_real_report_agrees_with_the_real_data(self, report_copy):
        result = check_report.check(quiet=True)
        assert result.failures == []
        assert result.checked > 20, "far fewer checks than expected -- registry lost entries?"

    def test_a_changed_table_cell_is_caught(self, report_copy):
        text = report_copy.read_text(encoding="utf-8")
        original = "| `ml100k` | `popularity` | 95.9 % | 24.9× |"
        assert original in text
        report_copy.write_text(text.replace(original, original.replace("24.9", "24.0")), "utf-8")

        result = check_report.check(quiet=True)
        assert any("§7.2" in failure for failure in result.failures)

    def test_the_fabricated_interval_list_is_caught(self, report_copy):
        """The exact error this module was written for.

        §4.5 listed twelve interval widths, six of which were not in the data. The
        conclusion it supported happened to be correct, so nothing about the surrounding
        prose looked wrong.
        """
        text = report_copy.read_text(encoding="utf-8")
        real = "1.1  1.2  1.2  1.3  1.3  1.4  1.4  1.6  1.7  1.8  1.9"
        fabricated = "1.1  1.2  1.2  1.3  1.9  2.2  2.5  3.3  4.1  5.2  6.4"
        assert real in text
        report_copy.write_text(text.replace(real, fabricated), "utf-8")

        result = check_report.check(quiet=True)
        assert any("interval-width" in failure for failure in result.failures)

    def test_a_deleted_table_is_caught(self, report_copy):
        text = report_copy.read_text(encoding="utf-8")
        header = "| retrain every | `popularity` |"
        assert header in text
        report_copy.write_text(text.replace(header, "| retrain every | REMOVED |"), "utf-8")

        result = check_report.check(quiet=True)
        assert any("header not found" in failure for failure in result.failures)

    def test_a_stale_not_checked_entry_is_caught(self, report_copy):
        """An uncovered table must not be able to hide behind an exemption that no longer
        matches anything in the report."""
        text = report_copy.read_text(encoding="utf-8")
        header = "| stage | amortisation | contents |"
        assert header in text
        report_copy.write_text(text.replace(header, "| stage | amortisation | notes |"), "utf-8")

        result = check_report.check(quiet=True)
        assert any("stale" in failure for failure in result.failures)


class TestCoverageIsExplicit:
    def test_every_pipe_table_is_either_checked_or_exempted(self, report_copy):
        """No third category.

        A table that is neither checked nor named in ``NOT_CHECKED`` reads as a table that
        passed, so this test is what stops the registry silently falling behind the report.
        """
        text = report_copy.read_text(encoding="utf-8")
        lines = text.splitlines()
        headers = [
            line
            for i, line in enumerate(lines)
            if line.startswith("|")
            and i + 1 < len(lines)
            and set(lines[i + 1].replace("|", "").replace(" ", "")) == {"-"}
        ]
        known = [t.header for t in check_report.TABLES] + [h for h, _ in check_report.NOT_CHECKED]
        uncovered = [h for h in headers if not any(h.startswith(k) for k in known)]
        assert uncovered == [], f"tables neither checked nor exempted: {uncovered}"
