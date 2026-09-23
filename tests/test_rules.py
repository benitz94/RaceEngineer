import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from raceengineer.demo import main, speak
from raceengineer.model import Sample
from raceengineer.recording import encode
from raceengineer.rules import RulesEngine, rule_radio


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

    def test_fuel_low_radio_text_is_italian(self):
        engine = RulesEngine()
        alert = engine.process(Sample(fuel=10.0, valid=True, source_ts=0, recv_ts=5, lap=2))
        self.assertEqual(alert.message, "Fuel low. Box this lap.")
        self.assertEqual(json.loads(rule_radio(alert).encode()), {
            "format": "raceengineer.radio", "version": 1,
            "radio": {"source": "rule", "type": "fuel_low",
                      "text": "Benzina bassa. Boxa questo giro.", "timestamp": 0},
        })
        self.assertIsNone(engine.process(Sample(fuel=9.9, valid=True, source_ts=1)))

    def test_missing_and_invalid_fuel_produce_no_radio(self):
        samples = [Sample(fuel=None, valid=True), Sample(fuel=9, lap=3, valid=False), Sample(fuel=9)]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "samples.jsonl"
            path.write_text("\n".join(map(encode, samples)), encoding="utf-8")
            records = self.run_cli(["--source", "file", str(path)])
            alerts = self.run_cli(["--source", "file", str(path), "--alerts-only"])
            radios = self.run_cli(["--source", "file", str(path), "--radio-only"])
        self.assertEqual(alerts, [])
        self.assertEqual(radios, [])
        self.assertTrue(all(record["format"] == "raceengineer.sample" for record in records))

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
        self.assertEqual(len(records), 22)
        alerts = [record for record in records if record["format"] == "raceengineer.alert"]
        radios = [record for record in records if record["format"] == "raceengineer.radio"]
        self.assertEqual(len(alerts), 1)
        self.assertEqual(len(radios), 1)
        self.assertEqual(alerts[0]["alert"]["fuel"], 10)
        self.assertEqual(radios[0]["radio"]["source"], "rule")
        self.assertEqual(radios[0]["radio"]["text"], "Benzina bassa. Boxa questo giro.")
        self.assertEqual(alerts[0]["alert"]["message"], "Fuel low. Box this lap.")
        self.assertEqual(radios[0]["radio"]["timestamp"], alerts[0]["alert"]["timestamp"])
        alert_at = next(index for index, record in enumerate(records) if record["format"] == "raceengineer.alert")
        self.assertEqual(records[alert_at + 1]["format"], "raceengineer.radio")
        self.assertEqual(self.run_cli(arguments + ["--alerts-only"]), alerts)
        self.assertEqual(self.run_cli(arguments + ["--radio-only"]), radios)
        self.assertEqual(len(self.run_cli(arguments + ["--samples-only"])), 20)

    def test_file_pipeline(self):
        samples = [Sample(fuel=fuel, valid=valid) for fuel, valid in
                   [(10, True), (9.9, True), (None, True), (13, False), (13, True), (9, True)]]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "samples.jsonl"
            path.write_text("\n".join(map(encode, samples)), encoding="utf-8")
            alerts = self.run_cli(["--source", "file", str(path), "--alerts-only"])
        self.assertEqual([record["alert"]["fuel"] for record in alerts], [10, 9])

    def test_speak_uses_italian_radio_text_without_audio(self):
        spoken = []

        def record(text):
            spoken.append((text, sys.stdout.getvalue()))

        with patch("raceengineer.demo.speak", side_effect=record):
            radios = self.run_cli(["--source", "synthetic", "--radio-only", "--speak"])
        self.assertEqual([radio["radio"]["text"] for radio in radios], ["Benzina bassa. Boxa questo giro."])
        self.assertEqual(spoken[0][0], "Benzina bassa. Boxa questo giro.")
        self.assertIn("Benzina bassa. Boxa questo giro.", spoken[0][1])

    def test_speak_without_radio_is_a_no_op(self):
        samples = [Sample(fuel=None, valid=True), Sample(fuel=9, valid=False), Sample(fuel=9)]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "samples.jsonl"
            path.write_text("\n".join(map(encode, samples)), encoding="utf-8")
            with patch("raceengineer.demo.speak") as speak_text:
                records = self.run_cli(["--source", "file", str(path), "--speak"])
        self.assertTrue(records)
        self.assertTrue(all(record["format"] == "raceengineer.sample" for record in records))
        speak_text.assert_not_called()

    def test_speak_failure_still_emits_radio(self):
        output = io.StringIO()
        error = io.StringIO()
        with patch("raceengineer.demo.speak", side_effect=RuntimeError("sapi down")), \
             contextlib.redirect_stdout(output), contextlib.redirect_stderr(error), \
             patch("raceengineer.demo.paced", side_effect=lambda samples, rate: samples):
            status = main(["--source", "synthetic", "--radio-only", "--speak"])
        self.assertEqual(status, 1)
        radio = json.loads(output.getvalue())
        self.assertEqual(radio["radio"]["text"], "Benzina bassa. Boxa questo giro.")
        self.assertIn("error: speech failed: sapi down", error.getvalue())

    def test_speak_invokes_windows_sapi_without_starting_it(self):
        with patch("raceengineer.demo.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
            speak("Benzina bassa. Boxa questo giro.")
        command = run.call_args.args[0]
        self.assertEqual(command[0], "powershell.exe")
        self.assertIn("System.Speech", command[-1])
        self.assertEqual(run.call_args.kwargs["env"]["RACEENGINEER_RADIO_TEXT"], "Benzina bassa. Boxa questo giro.")


if __name__ == "__main__":
    unittest.main()
