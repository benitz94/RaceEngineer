import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from raceengineer.demo import main
from raceengineer.model import Sample
from raceengineer.recording import encode
from raceengineer.rules import RulesEngine


class RulesTests(unittest.TestCase):
    def test_boundary_and_suppression(self):
        engine = RulesEngine()
        alert = engine.process(Sample(fuel=10.0, valid=True, source_ts=0, recv_ts=5, lap=2))
        self.assertEqual(json.loads(alert.encode()), {
            "format": "raceengineer.alert", "version": 1,
            "alert": {"type": "fuel_low", "priority": "high", "timestamp": 0,
                      "fuel": 10.0, "message": "Fuel low. Box this lap."},
        })
        self.assertIsNone(engine.process(Sample(fuel=9.9, valid=True)))
        self.assertEqual(engine.state.last_valid_fuel, 9.9)
        self.assertEqual(engine.state.lap, 2)
        self.assertTrue(engine.state.fuel_alert_fired)

    def test_missing_and_invalid_do_not_trigger_or_overwrite_state(self):
        engine = RulesEngine()
        engine.process(Sample(fuel=15, lap=2, valid=True))
        for sample in (Sample(fuel=None, valid=True), Sample(fuel=9, lap=3, valid=False), Sample(fuel=9)):
            self.assertIsNone(engine.process(sample))
        self.assertEqual(engine.state.last_valid_fuel, 15)
        self.assertEqual(engine.state.lap, 2)
        self.assertFalse(engine.state.fuel_alert_fired)

    def test_hysteresis_only_resets_above_twelve_with_valid_fuel(self):
        engine = RulesEngine()
        self.assertIsNotNone(engine.process(Sample(fuel=10, valid=True)))
        for sample in (Sample(fuel=12, valid=True), Sample(fuel=13, valid=False), Sample(fuel=None, valid=True)):
            self.assertIsNone(engine.process(sample))
            self.assertIsNone(engine.process(Sample(fuel=9, valid=True)))
        self.assertIsNone(engine.process(Sample(fuel=13, valid=True)))
        self.assertIsNotNone(engine.process(Sample(fuel=9, valid=True)))

    def test_restart_and_timestamp_fallback(self):
        engine = RulesEngine()
        self.assertEqual(engine.process(Sample(fuel=9, valid=True, recv_ts=5)).timestamp, 5)
        engine.restart()
        self.assertIsNone(engine.state.last_valid_fuel)
        self.assertIsNone(engine.state.lap)
        self.assertIsNone(engine.process(Sample(fuel=9, valid=True)).timestamp)

    def test_configurable_threshold(self):
        engine = RulesEngine(8)
        self.assertIsNone(engine.process(Sample(fuel=9, valid=True)))
        self.assertIsNotNone(engine.process(Sample(fuel=8, valid=True)))
        for threshold in (-1, 12, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                RulesEngine(threshold)

    def run_cli(self, arguments):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch("raceengineer.demo.paced", side_effect=lambda samples, rate: samples):
            self.assertEqual(main(arguments), 0)
        return [json.loads(line) for line in output.getvalue().splitlines()]

    def test_synthetic_cli_modes_are_repeatable(self):
        arguments = ["--source", "synthetic"]
        records = self.run_cli(arguments)
        self.assertEqual(records, self.run_cli(arguments))
        self.assertEqual(len(records), 21)
        alerts = [record for record in records if record["format"] == "raceengineer.alert"]
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["alert"]["fuel"], 10)
        self.assertEqual(self.run_cli(arguments + ["--alerts-only"]), alerts)
        self.assertEqual(len(self.run_cli(arguments + ["--samples-only"])), 20)

    def test_file_pipeline(self):
        samples = [Sample(fuel=fuel, valid=valid) for fuel, valid in
                   [(10, True), (9.9, True), (None, True), (13, False), (13, True), (9, True)]]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "samples.jsonl"
            path.write_text("\n".join(map(encode, samples)), encoding="utf-8")
            alerts = self.run_cli(["--source", "file", str(path), "--alerts-only"])
        self.assertEqual([record["alert"]["fuel"] for record in alerts], [10, 9])


if __name__ == "__main__":
    unittest.main()
