"""Deterministic fuel rule over normalized telemetry, without source logic."""

from dataclasses import asdict, dataclass
import json
import math

from .model import Sample

FUEL_LOW_THRESHOLD = 10.0
FUEL_RESET_THRESHOLD = 12.0
FUEL_LOW_MESSAGE = "Fuel low. Box this lap."
FUEL_LOW_RADIO_TEXT = "Benzina bassa. Boxa questo giro."


@dataclass
class SessionState:
    last_valid_fuel: float | None = None
    lap: int | None = None
    fuel_alert_fired: bool = False


@dataclass(frozen=True)
class Alert:
    type: str
    priority: str
    timestamp: float | None
    fuel: float
    message: str

    def encode(self) -> str:
        return json.dumps(
            {"format": "raceengineer.alert", "version": 1, "alert": asdict(self)},
            sort_keys=True, separators=(",", ":"), allow_nan=False,
        )


@dataclass(frozen=True)
class Radio:
    source: str
    type: str
    text: str
    timestamp: float | None

    def encode(self) -> str:
        return json.dumps(
            {"format": "raceengineer.radio", "version": 1, "radio": asdict(self)},
            sort_keys=True, separators=(",", ":"), allow_nan=False,
        )


def rule_radio(alert: Alert) -> Radio:
    """Driver-facing line for a fuel_low alert. The log message stays English."""
    return Radio("rule", alert.type, FUEL_LOW_RADIO_TEXT, alert.timestamp)


class RulesEngine:
    def __init__(self, fuel_low_threshold=FUEL_LOW_THRESHOLD):
        if not math.isfinite(fuel_low_threshold) or not 0 <= fuel_low_threshold < FUEL_RESET_THRESHOLD:
            raise ValueError("fuel low threshold must be finite and between 0 (inclusive) and 12 (exclusive)")
        self.fuel_low_threshold = fuel_low_threshold
        self.state = SessionState()

    def restart(self):
        """Call when the session source restarts; do not infer restarts from data."""
        self.state = SessionState()

    def process(self, sample: Sample) -> Alert | None:
        if sample.valid is not True:
            return None
        if sample.lap is not None:
            self.state.lap = sample.lap
        if sample.fuel is None:
            return None
        self.state.last_valid_fuel = sample.fuel
        if sample.fuel > FUEL_RESET_THRESHOLD:
            self.state.fuel_alert_fired = False
        if sample.fuel <= self.fuel_low_threshold and not self.state.fuel_alert_fired:
            self.state.fuel_alert_fired = True
            timestamp = sample.source_ts if sample.source_ts is not None else sample.recv_ts
            return Alert("fuel_low", "high", timestamp, sample.fuel, FUEL_LOW_MESSAGE)
        return None
