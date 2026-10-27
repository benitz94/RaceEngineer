import contextlib
import io
import json
import unittest
from unittest.mock import patch

from raceengineer.decision import URGENCY_SECONDS, answer
from raceengineer.demo import main


CLEAN = "Benzina a dieci litri. Box questo giro."
LOG = "alert type fuel_low timestamp 1.5. Conferma il segnale sul sector 3."


class _Response:
    def __init__(self, content):
        self.raw = json.dumps({"message": {"content": content}}).encode("utf-8")

    def read(self):
        return self.raw

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class DecisionTests(unittest.TestCase):
    def test_urgency_labels(self):
        self.assertEqual(answer("urgency", {"priority": "high"}), "now")
        self.assertEqual(answer("urgency", {"priority": "low"}), "normal")
        self.assertEqual(answer("urgency", {}), "normal")
        self.assertEqual(URGENCY_SECONDS, {"now": 1.0, "normal": 3.0, "calm": 6.0})

    def test_canned_or_brief_is_gone(self):
        with self.assertRaises(ValueError):
            answer("canned_or_brief", {"brief": True})

    def test_grounded_or_reject_labels(self):
        self.assertEqual(answer("grounded_or_reject", {"text": CLEAN, "fuel": 10}), "grounded")
        self.assertEqual(answer("grounded_or_reject", {"text": "Box, box. Questo giro."}), "grounded")
        for text in (
            LOG,
            "type fuel_low",
            "timestamp 1.5",
            "format version source",
            "usa `questo`",
            "il token fuel_low resta",
        ):
            with self.subTest(text=text):
                self.assertEqual(answer("grounded_or_reject", {"text": text}), "reject")

    def test_tangente_sud_is_rejected(self):
        self.assertEqual(answer("grounded_or_reject", {"text": "tangente sud", "fuel": 10}), "reject")

    def test_ordinary_italian_fuel_sentence_is_grounded(self):
        text = "Ho dieci litri di benzina nel serbatoio, box."
        self.assertEqual(answer("grounded_or_reject", {"text": text, "fuel": 10}), "grounded")

    def test_undeclared_question_fails(self):
        with self.assertRaises(ValueError):
            answer("speak_or_hold", {})

    def run_cli(self, arguments, expected_status=0):
        output = io.StringIO()
        error = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error), \
             patch("raceengineer.demo.paced", side_effect=lambda samples, rate: samples):
            status = main(arguments)
        self.assertEqual(status, expected_status, error.getvalue())
        radios = [json.loads(line) for line in output.getvalue().splitlines()]
        return radios, error.getvalue()

    def test_engineer_asks_urgency_then_grounding(self):
        questions = []

        def spy(question_id, payload):
            questions.append(question_id)
            return answer(question_id, payload)

        with patch("socket.create_connection", side_effect=OSError("blocked")), \
             patch("urllib.request.urlopen", side_effect=lambda request, timeout: _Response(CLEAN)), \
             patch("raceengineer.demo.answer", side_effect=spy):
            radios, stderr = self.run_cli(["--source", "synthetic", "--radio-only", "--engineer"])
        self.assertEqual(stderr, "")
        self.assertEqual(questions, ["urgency", "grounded_or_reject"])
        self.assertEqual([(radio["radio"]["source"], radio["radio"]["text"]) for radio in radios], [("llm", CLEAN)])

    def test_without_engineer_no_question_is_asked(self):
        with patch("urllib.request.urlopen", side_effect=OSError("blocked")) as urlopen, \
             patch("raceengineer.demo.answer") as asked:
            records, stderr = self.run_cli(["--source", "synthetic", "--alerts-only"])
        self.assertEqual(stderr, "")
        self.assertEqual([record["format"] for record in records], ["raceengineer.alert"])
        asked.assert_not_called()
        urlopen.assert_not_called()

    def test_log_like_line_leaves_the_radio_silent(self):
        with patch("socket.create_connection", side_effect=OSError("blocked")), \
             patch("urllib.request.urlopen", side_effect=lambda request, timeout: _Response(LOG)):
            radios, stderr = self.run_cli(["--source", "synthetic", "--radio-only", "--engineer"], 1)
        self.assertEqual(radios, [])
        self.assertEqual(stderr.splitlines(), ["error: engineer silent: line rejected"])


if __name__ == "__main__":
    unittest.main()
