"""Telemetry sources share the normalized Sample representation."""

import math
import time
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
