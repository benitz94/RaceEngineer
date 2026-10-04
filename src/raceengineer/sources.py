"""Telemetry sources share the normalized Sample representation."""

import math
import time
import threading
from .model import Sample
from .recording import read_samples


def validate_rate(rate):
    if not math.isfinite(rate) or rate <= 0:
        raise ValueError("rate must be finite and greater than zero")


def synthetic(count=20, rate=10.0):
    """A fixed scenario with logical seconds and explicit unavailable data."""
    validate_rate(rate)
    if count < 0:
        raise ValueError("count must be nonnegative")
    for index in range(count):
        timestamp = index / rate
        yield Sample(
            source_ts=timestamp, recv_ts=timestamp, source_id="synthetic",
            lap=1 + index // 10, lap_time=(index % 10) / rate,
            speed=None if index % 7 == 6 else float(20 + index % 10),
            fuel=round(max(0.0, 11.5 - index * 0.1), 6),
            valid=index % 11 != 10,
            quality="invalid" if index % 11 == 10 else "synthetic",
        )


def paced(samples, rate, *, clock=time.monotonic, sleep=time.sleep):
    """Deliver at a controlled rate without replacing sample timestamps."""
    validate_rate(rate)
    start = clock()
    for index, sample in enumerate(samples):
        delay = start + index / rate - clock()
        if delay > 0:
            sleep(delay)
        yield sample


def replay(path):
    """Preserve file order, missing values, duplicates, and timestamps."""
    return read_samples(path)


class ReplaySession:
    """Paced recorded replay with programmatic pause and resume controls.

    One consumer advances the session. Control methods may be called from
    another thread; a condition makes each delivery decision atomic with
    respect to pause. A sample already returned to the consumer cannot be
    recalled or interrupt downstream processing already in progress.
    """

    def __init__(self, path, rate, *, clock=time.monotonic, wait=None):
        validate_rate(rate)
        self._samples = iter(read_samples(path))
        self._rate = rate
        self._clock = clock
        self._wait_hook = wait
        self._condition = threading.Condition()
        self._state = "running"
        self._started = False
        self._start = None
        self._emitted = 0
        self._schedule_shift = 0.0
        self._deadline = None
        self._remaining = None
        self._paused_at = None

    @property
    def state(self):
        """Return ``running``, ``paused``, or terminal ``exhausted``."""
        with self._condition:
            return self._state

    def pause(self):
        """Pause delivery, freezing any outstanding pacing interval."""
        with self._condition:
            if self._state != "running":
                return
            now = self._clock()
            self._paused_at = now
            if self._deadline is not None:
                self._remaining = max(0.0, self._deadline - now)
            self._state = "paused"
            self._condition.notify_all()

    def resume(self):
        """Resume delivery; this is a no-op unless currently paused."""
        with self._condition:
            if self._state != "paused":
                return
            now = self._clock()
            if self._started:
                self._schedule_shift += now - self._paused_at
                if self._deadline is not None:
                    self._deadline = now + self._remaining
            self._remaining = None
            self._paused_at = None
            self._state = "running"
            self._condition.notify_all()

    def __iter__(self):
        return self

    def _wait(self, timeout):
        if self._wait_hook is None:
            self._condition.wait(timeout)
        else:
            self._wait_hook(self._condition, timeout)

    def __next__(self):
        with self._condition:
            while self._state == "paused":
                self._wait(None)
            if self._state == "exhausted":
                raise StopIteration

            try:
                sample = next(self._samples)
            except StopIteration:
                self._state = "exhausted"
                self._condition.notify_all()
                raise

            if not self._started:
                self._started = True
                self._start = self._clock()
            else:
                self._deadline = (
                    self._start + self._emitted / self._rate + self._schedule_shift
                )
                while True:
                    if self._state == "paused":
                        self._wait(None)
                        continue
                    remaining = self._deadline - self._clock()
                    if remaining <= 0:
                        break
                    self._wait(remaining)

            self._emitted += 1
            self._deadline = (
                self._start + self._emitted / self._rate + self._schedule_shift
            )
            return sample
