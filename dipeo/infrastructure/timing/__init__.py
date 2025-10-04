"""Timing infrastructure for DiPeO.

Provides zero-overhead timing collection with decorators and context managers.
"""

from dipeo.infrastructure.timing.collector import TimingCollector, timing_collector
from dipeo.infrastructure.timing.context import atime_phase, atimed, time_phase, timed

__all__ = [
    "TimingCollector",
    "atime_phase",
    "atimed",
    "time_phase",
    "timed",
    "timing_collector",
]
