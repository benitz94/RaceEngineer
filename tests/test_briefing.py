import contextlib
import io
import json
import os
import unittest
from unittest.mock import patch

from raceengineer.demo import main
from raceengineer.llm.backend import LLMUnavailable, complete
from raceengineer.llm.briefing import (
    LLM_DOWN_WARNING, allowed_numbers, build_prompt, sanitize_briefing, speak,
)
from raceengineer.rules import RulesEngine
from raceengineer.sources import synthetic


RADIO = "Fuel is at the box window. Last samples hit 10. Box this lap."


def session_dicts():
    engine = RulesEngine()
    samples = [sample.to_dict() for sample in synthetic()]
    alerts = []
    for sample in synthetic():
        alert = engine.process(sample)
        if alert is not None:
            alerts.append(json.loads(alert.encode())["alert"])
    return samples, alerts


class FakeBackendTests(unittest.TestCase):
    def test_synthetic_session_includes_fuel_low(self):
        samples, alerts = session_dicts()
        self.assertEqual(len(samples), 20)
        self.assertEqual([alert["type"] for alert in alerts], ["fuel_low"])
        self.assertEqual(alerts[0]["fuel"], 10)

    def test_fake_backend_returns_speakable_radio(self):
        samples, alerts = session_dicts()
        text = speak(samples, alerts, complete=lambda prompt: RADIO)
        self.assertEqual(text, RADIO)
        self.assertEqual(len(text.split()), 13)
        self.assertLessEqual(len(text.split()), 80)
        self.assertNotRegex(text, r"[*#`\[\]]")

    def test_prompt_includes_data_and_language(self):
        samples, alerts = session_dicts()
        english = build_prompt(samples, alerts, "en")
        italian = build_prompt(samples, alerts, "it")
        self.assertIn("English", english)
        self.assertIn("Italiano", italian)
        self.assertIn('"type":"fuel_low"', english)
        self.assertIn('"fuel":10.0', english)
        with self.assertRaises(ValueError):
            build_prompt(samples, alerts, "fr")

    def test_sanitize_strips_markdown_emoji_and_invented_numbers(self):
        samples, alerts = session_dicts()
        text = sanitize_briefing(
            "Sure, **Fuel** is at the box window. Last samples hit 10. "
            "Box this lap. Invented fuel is 3.5. Ignore this \U0001F525 line.",
            samples, alerts,
        )
        self.assertEqual(text, RADIO)
        long_radio = " ".join(["Fuel stays at 10 and extra unused words pad this sentence out."] * 8)
        capped = sanitize_briefing(long_radio, samples, alerts)
        self.assertIsNotNone(capped)
        self.assertLessEqual(len(capped.split()), 80)
        self.assertLessEqual(capped.count("."), 5)

    def test_empty_or_failed_backend_yields_none(self):
        samples, alerts = session_dicts()
        self.assertIsNone(speak(samples, alerts, complete=lambda prompt: ""))
        self.assertIsNone(speak(samples, alerts, complete=lambda prompt: "Fuel is 99 litres."))

        def boom(_prompt):
            raise LLMUnavailable("down")

        self.assertIsNone(speak(samples, alerts, complete=boom))
        allowed = allowed_numbers(*session_dicts())
        self.assertIn("10", allowed)
        self.assertIn("10.0", allowed)
        self.assertNotIn("99", allowed)

    def test_dead_openai_env_is_unavailable_without_gpu(self):
        env = {
            "RACEENGINEER_LLM_BACKEND": "openai",
            "RACEENGINEER_LLM_URL": "http://127.0.0.1:1",
            "RACEENGINEER_LLM_TIMEOUT": "0.2",
            "RACEENGINEER_LLM_API_KEY": "not-a-real-key",
        }
        with patch.dict(os.environ, env, clear=False):
            with self.assertRaises(LLMUnavailable):
                complete("hello")

    def run_cli(self, arguments, speak_impl):
        output = io.StringIO()
        error = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error), \
                patch("raceengineer.demo.paced", side_effect=lambda samples, rate: samples), \
                patch("raceengineer.demo.speak", side_effect=speak_impl):
            code = main(arguments)
        return code, output.getvalue(), error.getvalue()

    def test_cli_brief_success_and_llm_down(self):
        langs = []

        def ok(samples, alerts, lang="en"):
            langs.append(lang)
            self.assertTrue(any(sample["fuel"] == 10.0 and sample["valid"] for sample in samples))
            self.assertEqual(alerts[0]["type"], "fuel_low")
            return RADIO

        code, out, err = self.run_cli(
            ["--source", "synthetic", "--brief", "--lang", "it", "--alerts-only"], ok,
        )
        self.assertEqual(code, 0)
        self.assertEqual(langs, ["it"])
        self.assertIn("fuel_low", out)
        self.assertTrue(out.strip().endswith(RADIO))
        self.assertEqual(err, "")
        code, out, err = self.run_cli(
            ["--source", "synthetic", "--brief", "--alerts-only"],
            lambda samples, alerts, lang="en": None,
        )
        self.assertEqual(code, 0)
        self.assertIn("fuel_low", out)
        self.assertNotIn("Fuel is at the box window", out)
        self.assertEqual(err.strip(), LLM_DOWN_WARNING)
        self.assertEqual(err.count("warning:"), 1)

    def test_cli_without_brief_is_unchanged(self):
        called = []
        code, out, err = self.run_cli(
            ["--source", "synthetic"],
            lambda *args, **kwargs: called.append(True),
        )
        self.assertEqual(code, 0)
        self.assertEqual(called, [])
        self.assertEqual(err, "")
        records = [json.loads(line) for line in out.splitlines()]
        self.assertEqual(len(records), 21)
        alerts = [record for record in records if record["format"] == "raceengineer.alert"]
        self.assertEqual(alerts[0]["alert"]["type"], "fuel_low")

    def test_brief_rejected_for_samples_only_and_udp(self):
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            with self.assertRaises(SystemExit):
                main(["--source", "synthetic", "--brief", "--samples-only"])
            with self.assertRaises(SystemExit):
                main(["--source", "udp", "--brief"])


if __name__ == "__main__":
    unittest.main()
