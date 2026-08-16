"""Invariants for the experiment that decides claim 3.

``verdict()`` is the function that concludes "the energy backend cannot see the load".
That is the project's most quotable negative result and it is asserted about a widely
used tool, so the logic behind it has to be right in both directions: it must not clear a
backend that is blind, and it must not condemn one that works.

The tests therefore include a **synthetic backend that behaves correctly**. Without one,
every test would confirm the conclusion the project already reached, and a bug that made
`verdict` always answer "did not respond" would look like success throughout.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from experiments.validity import _is_cumulative, graded_load, verdict
from green_rerank.measure.meters import MockMeter


def _frame(loads, **channels) -> pd.DataFrame:
    """A graded-load result with the given channels, one row per load."""
    rows = {
        "workers": list(loads),
        "requested_seconds": [20.0] * len(loads),
        "wall_seconds": [20.0] * len(loads),
        "own_cpu_seconds": [0.0] * len(loads),
        "expected_core_seconds": [20.0 * w for w in loads],
    }
    rows.update({name: list(values) for name, values in channels.items()})
    return pd.DataFrame(rows)


class TestChannelKind:
    def test_cumulative_channels_are_recognised(self):
        for name in ("codecarbon.total_kwh", "rapl.package_joules", "x.co2_kg", "y_wh"):
            assert _is_cumulative(name)

    def test_rate_channels_are_not(self):
        # Dividing watts by seconds yields a quantity with no physical meaning, and an
        # earlier version of the driver printed exactly that in the results table.
        for name in ("codecarbon.cpu_watts", "codecarbon.cpu_util_pct"):
            assert not _is_cumulative(name)


class TestVerdict:
    def test_a_working_backend_is_not_condemned(self):
        """The control case, without which every other test is confirmation bias.

        A backend whose reported power rises with load must clear the bar. If this
        fails, `verdict` is answering "blind" regardless of input and the project's
        headline negative result would be an artefact of its own analysis code.
        """
        frame = _frame(
            [0, 1, 2, 4, 8],
            **{
                "meter.cpu_watts": [2.0, 4.0, 7.0, 12.0, 20.0],
                "meter.total_kwh": [1.1e-5, 2.2e-5, 3.9e-5, 6.7e-5, 1.1e-4],
            },
        )
        result = verdict(frame)
        assert result["responded"]
        assert not result["constant_channels"]

    def test_a_flat_backend_is_reported_as_blind(self):
        frame = _frame(
            [0, 1, 2, 4, 8],
            **{"meter.cpu_watts": [1.500, 1.501, 1.503, 1.521, 1.660]},
        )
        result = verdict(frame)
        assert not result["responded"]
        assert "2x" in result["reason"]

    def test_a_constant_channel_is_flagged_without_a_threshold(self):
        """The sharpest evidence, and it needs no threshold to interpret.

        A channel bit-for-bit identical from idle to saturation is not a noisy
        measurement of the load. On the development machine `ram_watts` is exactly
        10.000 W throughout and dominates the reported total.
        """
        frame = _frame([0, 1, 2, 4, 8], **{"meter.ram_watts": [10.0] * 5})
        result = verdict(frame)
        assert result["constant_channels"] == ["meter.ram_watts"]
        assert result["channels"]["meter.ram_watts"]["constant"]

    def test_an_inverted_channel_cannot_count_as_responding(self):
        """Reporting *less* under load is a failure no dynamic range excuses.

        This channel swings by more than 2x, so a check that looked only at range
        would clear it -- while the backend was reporting that saturating eight cores
        used less energy than idling.
        """
        frame = _frame([0, 8], **{"meter.total_kwh": [1.0e-4, 3.0e-5]})
        result = verdict(frame)
        assert result["channels"]["meter.total_kwh"]["inverted"]
        assert not result["responded"]

    def test_cumulative_channels_are_normalised_by_time_and_rates_are_not(self):
        # Unequal windows: starting more workers takes longer, so comparing kWh totals
        # across them would confound duration with power.
        frame = _frame([0, 8], **{"meter.total_kwh": [1.0e-5, 2.0e-5], "meter.w": [5.0, 5.0]})
        frame.loc[1, "wall_seconds"] = 40.0
        result = verdict(frame)
        # 1e-5/20 == 2e-5/40, so the rate is unchanged despite the total doubling.
        assert result["channels"]["meter.total_kwh"]["dynamic_range"] == pytest.approx(1.0)
        assert result["channels"]["meter.w"]["idle"] == 5.0

    def test_no_backend_is_a_finding_with_the_right_shape(self):
        """The commonest case on the target hardware, and it used to crash the driver.

        `channels` was a list here and a dict everywhere else, so the caller iterating
        `.items()` broke on exactly the path this experiment most expects to take.
        """
        result = verdict(_frame([0, 1, 2]))
        assert not result["responded"]
        assert result["channels"] == {}
        assert isinstance(result["channels"], dict)

    def test_a_channel_that_is_all_zero_is_unusable_rather_than_constant(self):
        # A GPU channel on a machine with no discrete GPU reads zero throughout. That is
        # not evidence about the CPU probe and must not be counted as a blind channel.
        frame = _frame([0, 8], **{"meter.gpu_kwh": [0.0, 0.0]})
        assert not frame.empty
        result = verdict(frame)
        assert result["channels"]["meter.gpu_kwh"]["usable"] is False
        assert "meter.gpu_kwh" not in result["constant_channels"]


class TestGradedLoad:
    def test_it_records_the_load_asked_for_beside_what_was_reported(self):
        """Both halves are needed or the experiment proves nothing.

        The point is a comparison between a *known* applied load and a reported one, so
        a results file carrying only the reported side could not support any conclusion.
        """
        frame = graded_load(loads=(0, 1), seconds=0.2, meter=MockMeter(watts=15.0))
        assert list(frame["workers"]) == [0, 1]
        assert (frame["expected_core_seconds"] == [0.0, 0.2]).all()
        assert (frame["wall_seconds"] > 0).all()

    def test_a_mock_meter_that_tracks_time_is_seen_to_respond(self):
        # End-to-end through the real driver: a backend reporting energy proportional to
        # elapsed time, on windows of deliberately different length.
        frame = graded_load(loads=(0, 2), seconds=0.2, meter=MockMeter(watts=15.0))
        channels = [c for c in frame.columns if c.startswith("mock")]
        assert channels, "the mock meter reported nothing"
        assert np.isfinite(frame[channels].to_numpy(dtype=float)).all()
