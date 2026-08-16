"""Cost measurement for pipeline stages.

The primary unit is CPU-seconds, measured by the kernel. Energy backends are optional
extras layered on top, because on the hardware this was developed for the available
backend could not see CPU load at all -- see :mod:`green_rerank.measure.meters`.
"""

from green_rerank.measure.guards import (
    ConditionsMonitor,
    ExclusiveLock,
    Preflight,
    PreflightError,
    machine_busy_pct,
    power_source,
    preflight,
)
from green_rerank.measure.meters import (
    CodeCarbonMeter,
    CompositeMeter,
    EnergyMeter,
    MockMeter,
    NullMeter,
    RaplMeter,
    default_meter,
)
from green_rerank.measure.reading import JOULES_CHANNEL, Reading, total
from green_rerank.measure.session import MeasurementSession

__all__ = [
    "JOULES_CHANNEL",
    "CodeCarbonMeter",
    "CompositeMeter",
    "ConditionsMonitor",
    "EnergyMeter",
    "ExclusiveLock",
    "MeasurementSession",
    "MockMeter",
    "NullMeter",
    "Preflight",
    "PreflightError",
    "RaplMeter",
    "Reading",
    "default_meter",
    "machine_busy_pct",
    "power_source",
    "preflight",
    "total",
]
