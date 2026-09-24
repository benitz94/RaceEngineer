import contextlib
import io
import json
import unittest
from unittest.mock import patch

from raceengineer.decision import answer
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
    def test_canned_unless_brief_is_true(self):
        self.assertEqual(answer("canned_or_brief", {}), "canned")
        self.assertEqual(answer("canned_or_brief", {"brief": False}), "canned")
        self.assertEqual(answer("canned_or_brief", {"brief": True}), "brief")

    def test_grounded_or_reject_labels(self):
        self.assertEqual(answer("grounded_or_reject", {"text": CLEAN}), "grounded")
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

    def test_undeclared_question_fails(self):
        with self.assertRaises(ValueError):
            answer("speak_or_hold", {})

    def run_cli(self, arguments):
        output = io.StringIO()
        error = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error), \
             patch("raceengineer.demo.paced", side_effect=lambda samples, rate: samples):
            status = main(arguments)
        self.assertEqual(status, 0, error.getvalue())
        radios = [json.loads(line) for line in output.getvalue().splitlines()]
        return radios, error.getvalue()

    def test_no_brief_emits_one_rule_radio_and_skips_ollama(self):
        questions = []

        def spy(question_id, payload):
            questions.append(question_id)
            return answer(question_id, payload)

        with patch("socket.create_connection", side_effect=OSError("blocked")), \
             patch("urllib.request.urlopen", side_effect=OSError("blocked")) as urlopen, \
             patch("raceengineer.demo.answer", side_effect=spy):
            radios, stderr = self.run_cli(["--source", "synthetic", "--radio-only"])
        self.assertEqual(stderr, "")
        self.assertEqual(len(radios), 1)
        self.assertEqual(radios[0]["radio"]["source"], "rule")
        self.assertEqual(radios[0]["radio"]["text"], "Box, box. Questo giro.")
        self.assertEqual(questions, ["canned_or_brief"])
        urlopen.assert_not_called()

    def test_brief_with_clean_stub_emits_rule_and_llm(self):
        def opener(request, timeout):
            return _Response(CLEAN)

        with patch("socket.create_connection", side_effect=OSError("blocked")), \
             patch("urllib.request.urlopen", side_effect=opener):
            radios, stderr = self.run_cli(["--source", "synthetic", "--radio-only", "--brief"])
        self.assertEqual(stderr, "")
        self.assertEqual([radio["radio"]["source"] for radio in radios], ["rule", "llm"])
        self.assertEqual(radios[0]["radio"]["text"], "Box, box. Questo giro.")
        self.assertEqual(radios[1]["radio"]["text"], CLEAN)
        self.assertEqual(radios[1]["radio"]["timestamp"], radios[0]["radio"]["timestamp"])

    def test_brief_with_log_like_stub_keeps_the_rule_radio(self):
        def opener(request, timeout):
            return _Response(LOG)

        with patch("socket.create_connection", side_effect=OSError("blocked")), \
             patch("urllib.request.urlopen", side_effect=opener):
            radios, stderr = self.run_cli(["--source", "synthetic", "--radio-only", "--brief"])
        self.assertEqual(len(radios), 1)
        self.assertEqual(radios[0]["radio"]["source"], "rule")
        self.assertEqual(radios[0]["radio"]["text"], "Box, box. Questo giro.")
        self.assertEqual(stderr.splitlines(), ["error: brief rejected"])


if __name__ == "__main__":
    unittest.main()
