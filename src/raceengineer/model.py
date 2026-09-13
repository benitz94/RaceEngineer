"""Normalized samples; absent observations remain unavailable."""

from dataclasses import asdict, dataclass
import math


@dataclass(frozen=True)
class Sample:
    source_ts: float | None = None
    recv_ts: float | None = None
    source_id: str | None = None
    lap: int | None = None
    lap_time: float | None = None
    speed: float | None = None
    fuel: float | None = None
    valid: bool | None = None
    quality: str | None = None

    def __post_init__(self):
        for name in ("source_ts", "recv_ts", "lap_time", "speed", "fuel"):
            value = getattr(self, name)
            if value is not None and (
                type(value) not in (int, float) or not math.isfinite(value)
            ):
                raise ValueError(f"{name} must be a finite number or null")
        if self.lap is not None and type(self.lap) is not int:
            raise ValueError("lap must be an integer or null")
        if self.valid is not None and type(self.valid) is not bool:
            raise ValueError("valid must be a boolean or null")
        for name in ("source_id", "quality"):
            if getattr(self, name) is not None and not isinstance(getattr(self, name), str):
                raise ValueError(f"{name} must be a string or null")

    def to_dict(self):
        return asdict(self)
