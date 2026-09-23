"""Deterministic recorded-telemetry replay with an injectable timebase.

Playback speed controls only how quickly recorded time is presented.
Source timestamps on samples are never rewritten.

State transitions:

* STOPPED --start--> RUNNING
* RUNNING --pause--> PAUSED
* PAUSED --resume--> RUNNING
* RUNNING or PAUSED --EOF--> FINISHED
* any --stop--> STOPPED (idempotent)

Other transitions are no-ops. ``start`` from FINISHED or STOPPED begins
from the first sample. Reverse replay is not supported.
"""

from __future__ import annotations

from enum import Enum
import math

from .clock import Clock, MonotonicClock
from .model import Sample


class ReplayState(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"


MIN_SPEED = 1e-6
MAX_SPEED = 1e6


def validate_speed(multiplier: float) -> float:
    if type(multiplier) not in (int, float) or not math.isfinite(multiplier):
        raise ValueError("replay speed must be a finite positive number")
    if multiplier <= 0:
        raise ValueError("replay speed must be a finite positive number")
    if multiplier < MIN_SPEED or multiplier > MAX_SPEED:
        raise ValueError(f"replay speed must be between {MIN_SPEED} and {MAX_SPEED}")
    return float(multiplier)


def sample_time(sample: Sample) -> float | None:
    """Scheduling time from the recording; does not invent a clock value."""
    if sample.source_ts is not None:
        return sample.source_ts
    return sample.recv_ts


class ReplayController:
    def __init__(self, samples, speed: float = 1.0, clock: Clock | None = None) -> None:
        self._samples = list(samples)
        self._speed = validate_speed(speed)
        self._clock = clock if clock is not None else MonotonicClock()
        self._state = ReplayState.STOPPED
        self._index = 0
        self._last_source_time: float | None = None

    @property
    def state(self) -> ReplayState:
        return self._state

    @property
    def speed(self) -> float:
        return self._speed

    def start(self) -> None:
        if self._state == ReplayState.RUNNING:
            return
        if self._state == ReplayState.PAUSED:
            return
        self._index = 0
        self._last_source_time = None
        if not self._samples:
            self._state = ReplayState.FINISHED
            return
        self._state = ReplayState.RUNNING

    def pause(self) -> None:
        if self._state == ReplayState.RUNNING:
            self._state = ReplayState.PAUSED

    def resume(self) -> None:
        if self._state == ReplayState.PAUSED:
            self._state = ReplayState.RUNNING

    def stop(self) -> None:
        self._state = ReplayState.STOPPED
        self._index = 0
        self._last_source_time = None

    def set_speed(self, multiplier: float) -> None:
        self._speed = validate_speed(multiplier)

    def step(self) -> Sample | None:
        """Emit the next sample, sleeping for recorded deltas scaled by speed.

        Returns None when paused, stopped, finished, or before start.
        Paused replay does not skip or duplicate samples.
        """
        if self._state != ReplayState.RUNNING:
            return None
        if self._index >= len(self._samples):
            self._state = ReplayState.FINISHED
            return None
        sample = self._samples[self._index]
        source_time = sample_time(sample)
        if self._last_source_time is not None and source_time is not None:
            delta = source_time - self._last_source_time
            if delta > 0:
                self._clock.sleep(delta / self._speed)
        if self._state != ReplayState.RUNNING:
            return None
        self._index += 1
        if source_time is not None:
            self._last_source_time = source_time
        if self._index >= len(self._samples):
            self._state = ReplayState.FINISHED
        return sample

    def __iter__(self):
        if self._state == ReplayState.STOPPED:
            self.start()
        while self._state == ReplayState.RUNNING:
            sample = self.step()
            if sample is None:
                break
            yield sample
