import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

from raceengineer.briefing import SYSTEM_PROMPT, TIMEOUT_SECONDS, BriefingUnavailable, brief_alert
from raceengineer.demo import main
from raceengineer.model import Sample
from raceengineer.recording import encode
from raceengineer.rules import Alert


SENTENCE = "Benzina a dieci litri. Box questo giro."


class _Response:
    def __init__(self, payload):
        self.raw = json.dumps(payload).encode("utf-8")

    def read(self):
        return self.raw

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _alert(timestamp=1.5, fuel=10.0):
    return Alert("fuel_low", "high", timestamp, fuel, "Fuel low. Box this lap.")


def _http_error(status, detail, reason="Bad Request"):
    body = json.dumps({"error": detail}).encode("utf-8")
    return urllib.error.HTTPError(
        "http://127.0.0.1:11434/api/chat", status, reason, None, io.BytesIO(body),
    )


class BriefingTests(unittest.TestCase):
    def run_cli(self, arguments):
        output = io.StringIO()
        error = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error), \
             patch("raceengineer.demo.paced", side_effect=lambda samples, rate: samples):
            status = main(arguments)
        self.assertEqual(status, 0, error.getvalue())
        records = [json.loads(line) for line in output.getvalue().splitlines()]
        return records, error.getvalue()

    def test_prompt_limits_the_model_to_passed_alert_fields(self):
        self.assertIn("pit-wall engineer", SYSTEM_PROMPT)
        self.assertIn("Speak Italian. At most two short sentences.", SYSTEM_PROMPT)
        self.assertIn("docs/RADIO_PHRASES.md is register training, not a script and not a whitelist.", SYSTEM_PROMPT)
        self.assertIn("dieci litri", SYSTEM_PROMPT)
        self.assertIn("Never say the JSON key names type, timestamp, source, format, or version.", SYSTEM_PROMPT)
        self.assertIn("Never say a raw timestamp such as 1.5.", SYSTEM_PROMPT)
        self.assertIn("Do not speak English except the standard call Box, box.", SYSTEM_PROMPT)
        self.assertIn("Do not say alert, procedura, or conferma il segnale.", SYSTEM_PROMPT)
        self.assertIn("Do not invent corners, sectors, or rivals.", SYSTEM_PROMPT)
        captured = {}

        def opener(request, timeout):
            captured["payload"] = json.loads(request.data.decode())
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            self.assertEqual(request.get_method(), "POST")
            return _Response({"message": {"content": SENTENCE, "thinking": "sector 3"}})

        self.assertEqual(brief_alert(_alert(), opener=opener), SENTENCE)
        payload = captured["payload"]
        self.assertEqual(captured["url"], "http://127.0.0.1:11434/api/chat")
        self.assertEqual(captured["timeout"], TIMEOUT_SECONDS)
        self.assertEqual(payload["model"], "qwen3.5:4b")
        self.assertIs(payload["stream"], False)
        self.assertIs(payload["think"], False)
        self.assertEqual(payload["options"], {"temperature": 0})
        self.assertEqual(payload["messages"][0], {"role": "system", "content": SYSTEM_PROMPT})
        examples = [item["content"] for item in payload["messages"] if item["role"] == "assistant"]
        self.assertEqual(examples, [
            "Ho dieci litri di benzina nel serbatoio, box.",
            "Rientra. Benzina a dieci litri.",
        ])
        for line in examples:
            for place in ("curva", "settore", "tangente", "sud", "rettilineo", "scarica"):
                self.assertNotIn(place, line.lower())
        last_user = [item["content"] for item in payload["messages"] if item["role"] == "user"][-1]
        self.assertEqual(json.loads(last_user), {
            "fuel": 10.0, "timestamp": 1.5, "type": "fuel_low",
        })

    def test_null_timestamp_is_passed_through(self):
        captured = {}

        def opener(request, timeout):
            messages = json.loads(request.data.decode())["messages"]
            captured["user"] = [item["content"] for item in messages if item["role"] == "user"][-1]
            return _Response({"message": {"content": "Benzina bassa. Entra ora."}})

        brief_alert(_alert(timestamp=None, fuel=9), opener=opener)
        self.assertEqual(json.loads(captured["user"])["timestamp"], None)

    def test_empty_content_is_not_replaced_by_thinking(self):
        def opener(request, timeout):
            return _Response({"message": {"content": "  \n", "thinking": "Turn 3, rival ahead"}})

        with self.assertRaisesRegex(BriefingUnavailable, "empty response"):
            brief_alert(_alert(), opener=opener)

    def test_rejected_think_field_is_retried_once_without_it(self):
        calls = []

        def opener(request, timeout):
            payload = json.loads(request.data.decode())
            calls.append(payload)
            if "think" in payload:
                raise _http_error(400, 'json: unknown field "think"')
            return _Response({"message": {"content": "  Entra ai box. Benzina bassa.  "}})

        self.assertEqual(brief_alert(_alert(), opener=opener), "Entra ai box. Benzina bassa.")
        self.assertEqual(len(calls), 2)
        self.assertIs(calls[0]["think"], False)
        self.assertNotIn("think", calls[1])
        self.assertEqual(calls[0]["messages"], calls[1]["messages"])

    def test_other_http_errors_do_not_retry(self):
        calls = []

        def opener(request, timeout):
            calls.append(1)
            raise _http_error(404, "model not found", "Not Found")

        with self.assertRaisesRegex(BriefingUnavailable, "HTTP 404"):
            brief_alert(_alert(), opener=opener)
        self.assertEqual(calls, [1])

    def test_timeout_and_invalid_json_do_not_retry(self):
        for failure in (TimeoutError("timed out"), urllib.error.URLError(TimeoutError("timed out")), b"not-json"):
            calls = []

            def opener(request, timeout, failure=failure):
                calls.append(1)
                if isinstance(failure, bytes):
                    response = _Response({})
                    response.raw = failure
                    return response
                raise failure

            with self.assertRaises(BriefingUnavailable):
                brief_alert(_alert(), opener=opener)
            self.assertEqual(calls, [1])

    def test_paths_without_a_briefing_do_not_use_the_network(self):
        with patch("socket.create_connection", side_effect=OSError("blocked")) as connect, \
             patch("urllib.request.urlopen", side_effect=OSError("blocked")) as urlopen:
            records, stderr = self.run_cli(["--source", "synthetic"])
            radios, radio_stderr = self.run_cli(["--source", "synthetic", "--radio-only"])
            samples, samples_stderr = self.run_cli(["--source", "synthetic", "--samples-only", "--brief"])
            alerts, alerts_stderr = self.run_cli(["--source", "synthetic", "--alerts-only", "--brief"])
        self.assertEqual(stderr, "")
        self.assertEqual(radio_stderr, "")
        self.assertEqual(samples_stderr, "")
        self.assertEqual(alerts_stderr, "")
        self.assertEqual(len(records), 22)
        self.assertEqual([record["radio"]["source"] for record in records if "radio" in record], ["rule"])
        self.assertEqual(radios[0]["radio"]["text"], "Box, box. Questo giro.")
        self.assertEqual(len(samples), 20)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["format"], "raceengineer.alert")
        connect.assert_not_called()
        urlopen.assert_not_called()

    def test_radio_only_brief_appends_the_model_sentence(self):
        captured = {}

        def opener(request, timeout):
            captured["payload"] = json.loads(request.data.decode())
            captured["timeout"] = timeout
            return _Response({"message": {"content": f"  {SENTENCE}\n", "thinking": "sector 2"}})

        with patch("socket.create_connection", side_effect=OSError("blocked")), \
             patch("urllib.request.urlopen", side_effect=opener):
            radios, stderr = self.run_cli(["--source", "synthetic", "--radio-only", "--brief"])
        self.assertEqual(stderr, "")
        self.assertEqual(captured["timeout"], 15)
        self.assertEqual([radio["format"] for radio in radios], ["raceengineer.radio", "raceengineer.radio"])
        self.assertEqual([radio["version"] for radio in radios], [1, 1])
        rule, briefing = (radio["radio"] for radio in radios)
        self.assertEqual(rule, {
            "source": "rule", "type": "fuel_low",
            "text": "Box, box. Questo giro.", "timestamp": 1.5,
        })
        self.assertEqual(briefing, {
            "source": "llm", "type": "fuel_low", "text": SENTENCE, "timestamp": 1.5,
        })
        self.assertNotIn("sector", briefing["text"])
        users = [item["content"] for item in captured["payload"]["messages"] if item["role"] == "user"]
        user = json.loads(users[-1])
        self.assertEqual(user, {"fuel": 10.0, "timestamp": 1.5, "type": "fuel_low"})

    def test_ollama_failures_keep_the_rule_radio_and_exit_zero(self):
        failures = {
            "down": urllib.error.URLError("down\nstill down"),
            "timeout": TimeoutError("timed out"),
            "empty": _Response({"message": {"content": "   "}}),
            "invalid": _Response({}),
        }
        failures["invalid"].raw = b"not-json"

        for name, failure in failures.items():
            with self.subTest(name=name):
                def opener(request, timeout, failure=failure):
                    if isinstance(failure, BaseException):
                        raise failure
                    return failure

                output = io.StringIO()
                error = io.StringIO()
                with patch("urllib.request.urlopen", side_effect=opener), \
                     patch("socket.create_connection", side_effect=OSError("blocked")), \
                     contextlib.redirect_stdout(output), contextlib.redirect_stderr(error), \
                     patch("raceengineer.demo.paced", side_effect=lambda samples, rate: samples):
                    status = main(["--source", "synthetic", "--radio-only", "--brief"])
                self.assertEqual(status, 0)
                radios = [json.loads(line) for line in output.getvalue().splitlines()]
                self.assertEqual(len(radios), 1)
                self.assertEqual(radios[0]["radio"]["source"], "rule")
                self.assertEqual(radios[0]["radio"]["text"], "Box, box. Questo giro.")
                lines = error.getvalue().splitlines()
                self.assertEqual(len(lines), 1)
                self.assertTrue(lines[0].startswith("error: briefing unavailable:"))
                if name == "timeout":
                    self.assertIn("timed out", lines[0])
                if name == "down":
                    self.assertIn("down still down", lines[0])
                if name == "empty":
                    self.assertIn("empty response", lines[0])

    def test_missing_fuel_with_brief_does_not_call_ollama(self):
        samples = [Sample(fuel=None, valid=True), Sample(fuel=9, valid=False), Sample(fuel=9)]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "samples.jsonl"
            path.write_text("\n".join(map(encode, samples)), encoding="utf-8")
            with patch("urllib.request.urlopen", side_effect=OSError("blocked")) as urlopen:
                records, stderr = self.run_cli(["--source", "file", str(path), "--brief"])
        self.assertEqual(stderr, "")
        self.assertTrue(records)
        self.assertTrue(all(record["format"] == "raceengineer.sample" for record in records))
        urlopen.assert_not_called()

    def test_each_reset_fuel_alert_gets_its_own_briefing(self):
        samples = [
            Sample(fuel=10, valid=True, source_ts=1),
            Sample(fuel=9, valid=True, source_ts=2),
            Sample(fuel=13, valid=True, source_ts=3),
            Sample(fuel=9, valid=True, source_ts=4),
        ]
        calls = []

        def opener(request, timeout):
            messages = json.loads(request.data.decode())["messages"]
            calls.append(json.loads([item["content"] for item in messages if item["role"] == "user"][-1]))
            return _Response({"message": {"content": "Benzina. Box questo giro."}})

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "samples.jsonl"
            path.write_text("\n".join(map(encode, samples)), encoding="utf-8")
            with patch("urllib.request.urlopen", side_effect=opener):
                radios, stderr = self.run_cli(["--source", "file", str(path), "--radio-only", "--brief"])
        self.assertEqual(stderr, "")
        self.assertEqual([radio["radio"]["source"] for radio in radios], ["rule", "llm", "rule", "llm"])
        self.assertEqual(radios[0]["radio"]["text"], "Box, box. Questo giro.")
        self.assertEqual(radios[2]["radio"]["text"], "Box, box. Questo giro.")
        self.assertEqual(radios[1]["radio"]["timestamp"], 1)
        self.assertEqual(radios[3]["radio"]["timestamp"], 4)
        self.assertEqual(calls, [
            {"fuel": 10, "timestamp": 1, "type": "fuel_low"},
            {"fuel": 9, "timestamp": 4, "type": "fuel_low"},
        ])

    def test_speak_with_brief_speaks_rule_then_llm(self):
        spoken = []

        def record(text, voice="paola"):
            spoken.append((text, sys.stdout.getvalue()))

        def opener(request, timeout):
            return _Response({"message": {"content": SENTENCE}})

        with patch("raceengineer.demo.speak", side_effect=record), \
             patch("urllib.request.urlopen", side_effect=opener), \
             patch("socket.create_connection", side_effect=OSError("blocked")):
            radios, stderr = self.run_cli(["--source", "synthetic", "--radio-only", "--speak", "--brief"])
        self.assertEqual(stderr, "")
        self.assertEqual([text for text, _stdout in spoken], ["Box, box. Questo giro.", SENTENCE])
        self.assertIn("Box, box. Questo giro.", spoken[0][1])
        self.assertNotIn(SENTENCE, spoken[0][1])
        self.assertIn(SENTENCE, spoken[1][1])
        self.assertEqual([radio["radio"]["source"] for radio in radios], ["rule", "llm"])

    def test_speech_failure_still_returns_one_when_a_briefing_is_printed(self):
        def opener(request, timeout):
            return _Response({"message": {"content": SENTENCE}})

        output = io.StringIO()
        error = io.StringIO()
        with patch("raceengineer.demo.speak", side_effect=RuntimeError("sapi down")), \
             patch("urllib.request.urlopen", side_effect=opener), \
             contextlib.redirect_stdout(output), contextlib.redirect_stderr(error), \
             patch("raceengineer.demo.paced", side_effect=lambda samples, rate: samples):
            status = main(["--source", "synthetic", "--radio-only", "--speak", "--brief"])
        self.assertEqual(status, 1)
        radios = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual([radio["radio"]["source"] for radio in radios], ["rule", "llm"])
        self.assertEqual(radios[0]["radio"]["text"], "Box, box. Questo giro.")
        self.assertEqual(radios[1]["radio"]["text"], SENTENCE)
        self.assertEqual(error.getvalue().splitlines(), [
            "error: speech failed: sapi down",
            "error: speech failed: sapi down",
        ])
        self.assertNotIn("briefing unavailable", error.getvalue())

    def test_rejected_brief_is_retried_once_then_aired(self):
        replies = iter(["tangente sud", "Ho dieci litri di benzina nel serbatoio, box."])
        calls = []

        def opener(request, timeout):
            body = json.loads(request.data.decode())
            calls.append(body["options"]["temperature"])
            return _Response({"message": {"content": next(replies)}})

        with patch("urllib.request.urlopen", side_effect=opener), \
             patch("socket.create_connection", side_effect=OSError("blocked")):
            radios, stderr = self.run_cli(["--source", "synthetic", "--radio-only", "--brief"])
        self.assertEqual(stderr, "")
        self.assertEqual(calls, [0, 0])
        self.assertEqual([radio["radio"]["text"] for radio in radios], [
            "Box, box. Questo giro.",
            "Ho dieci litri di benzina nel serbatoio, box.",
        ])

    def test_second_reject_keeps_the_rule_radio(self):
        calls = []

        def opener(request, timeout):
            calls.append(1)
            return _Response({"message": {"content": "tangente sud"}})

        with patch("urllib.request.urlopen", side_effect=opener), \
             patch("socket.create_connection", side_effect=OSError("blocked")):
            radios, stderr = self.run_cli(["--source", "synthetic", "--radio-only", "--brief"])
        self.assertEqual(calls, [1, 1])
        self.assertEqual(len(radios), 1)
        self.assertEqual(radios[0]["radio"]["text"], "Box, box. Questo giro.")
        self.assertEqual(stderr.splitlines(), ["error: brief rejected"])

    def test_speak_does_not_say_a_rejected_brief(self):
        spoken = []

        def opener(request, timeout):
            return _Response({"message": {"content": "alert type fuel_low timestamp 1.5"}})

        with patch("raceengineer.demo.speak", side_effect=lambda text, voice="paola": spoken.append(text)), \
             patch("urllib.request.urlopen", side_effect=opener), \
             patch("socket.create_connection", side_effect=OSError("blocked")):
            radios, stderr = self.run_cli(["--source", "synthetic", "--radio-only", "--speak", "--brief"])
        self.assertEqual(spoken, ["Box, box. Questo giro."])
        self.assertEqual([radio["radio"]["source"] for radio in radios], ["rule"])
        self.assertIn("brief rejected", stderr)

    def test_log_like_brief_is_rejected_and_rule_radio_stays(self):
        def opener(request, timeout):
            return _Response({
                "message": {
                    "content": "alert type fuel_low timestamp 1.5. Conferma il segnale sul sector 3.",
                },
            })

        output = io.StringIO()
        error = io.StringIO()
        with patch("urllib.request.urlopen", side_effect=opener), \
             patch("socket.create_connection", side_effect=OSError("blocked")), \
             contextlib.redirect_stdout(output), contextlib.redirect_stderr(error), \
             patch("raceengineer.demo.paced", side_effect=lambda samples, rate: samples):
            status = main(["--source", "synthetic", "--radio-only", "--brief"])
        self.assertEqual(status, 0)
        radios = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(len(radios), 1)
        self.assertEqual(radios[0]["radio"]["source"], "rule")
        self.assertEqual(radios[0]["radio"]["text"], "Box, box. Questo giro.")
        self.assertEqual(error.getvalue().splitlines(), ["error: brief rejected"])


if __name__ == "__main__":
    unittest.main()
