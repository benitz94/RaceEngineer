"""Injectable clocks for production timing and instant replay tests."""

from __future__ import annotations

from typing import Protocol
import time


class Clock(Protocol):
    def now(self) -> float:
        """Return the current timebase value in seconds."""

    def sleep(self, seconds: float) -> None:
        """Advance this timebase by at least ``seconds``."""


class MonotonicClock:
    """Wall-independent production clock."""

    def now(self) -> float:
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)


class VirtualClock:
    """Logical clock that advances immediately on sleep."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def now(self) -> float:
        return self._now

    def sleep(self, seconds: float) -> None:
        if seconds > 0:
            self._now += seconds
