import contextlib
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

from raceengineer.briefing import SYSTEM_PROMPT as ENGINEER_PROMPT
from tools.eval_models import (
    CSV_FIELDS,
    CaseResult,
    CorpusError,
    FakeBackend,
    ModelResult,
    OllamaBackend,
    assess_briefing,
    build_report,
    evaluate,
    filter_cases,
    load_corpus,
    main,
    score_case,
    summarize,
    validate_case,
    validate_ollama_url,
    write_csv,
    write_json,
)


GOOD_BRIEF = "Benzina a dieci litri. Box questo giro."


def _case(**changes):
    case = {
        "id": "test-case",
        "category": "grounding",
        "task": "engineer_line",
        "input": {"facts": {"fuel": 10.0}},
        "expected": "accept",
        "rationale": "Test fixture.",
        "fake": {"text": GOOD_BRIEF},
        "checks": {"required_terms": ["dieci litri"], "required_any": ["benzina", "box"]},
    }
    case.update(changes)
    return case


def _write_cases(path, cases):
    path.write_text("\n".join(json.dumps(case) for case in cases) + "\n", encoding="utf-8")


def _summary_metrics():
    return {"style_violations": [], "malformed": False}


class _Response:
    def __init__(self, body):
        self.body = json.dumps(body).encode("utf-8")

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class ModelEvaluationCorpusTests(unittest.TestCase):
    def test_default_corpus_is_valid_and_unique(self):
        cases = load_corpus()
        self.assertEqual(len(cases), 65)
        self.assertEqual(len({case["id"] for case in cases}), 65)
        self.assertEqual({case["task"] for case in cases}, {"engineer_line", "urgency", "grounded_or_reject"})
        self.assertEqual({case["category"] for case in cases}, {
            "grounding", "hallucination", "style", "decision", "failure",
        })

    def test_duplicate_case_ids_are_rejected_across_files(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            first = Path(directory) / "first.jsonl"
            second = Path(directory) / "second.jsonl"
            _write_cases(first, [_case()])
            _write_cases(second, [_case()])
            with self.assertRaisesRegex(CorpusError, "duplicate case id"):
                load_corpus([first, second])

    def test_missing_required_field_is_rejected(self):
        case = _case()
        del case["rationale"]
        with self.assertRaisesRegex(CorpusError, "missing required fields: rationale"):
            validate_case(case)

    def test_unknown_category_is_rejected(self):
        with self.assertRaisesRegex(CorpusError, "unknown category"):
            validate_case(_case(category="weather"))

    def test_unknown_task_and_illegal_label_are_rejected(self):
        with self.assertRaisesRegex(CorpusError, "unknown task"):
            validate_case(_case(task="speak_or_hold"))
        with self.assertRaisesRegex(CorpusError, "illegal expected label"):
            validate_case(_case(expected="maybe"))

    def test_retired_fallback_and_brief_inputs_are_rejected(self):
        for field, value in (("rule_fallback", "Box, box. Questo giro."), ("brief", True)):
            with self.subTest(field=field), self.assertRaisesRegex(CorpusError, "retired input fields"):
                validate_case(_case(input={"facts": {"fuel": 10.0}, field: value}))

    def test_old_tasks_and_fallback_label_are_rejected(self):
        for task in ("briefing", "canned_or_brief"):
            with self.subTest(task=task), self.assertRaisesRegex(CorpusError, "unknown task"):
                validate_case(_case(task=task))
        with self.assertRaisesRegex(CorpusError, "illegal expected label"):
            validate_case(_case(expected="fallback"))

    def test_invalid_json_has_a_line_diagnostic(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "broken.jsonl"
            path.write_text("{\n", encoding="utf-8")
            with self.assertRaisesRegex(CorpusError, r"line 1: invalid JSON"):
                load_corpus([path])

    def test_category_filter_selects_only_requested_cases(self):
        cases = filter_cases(load_corpus(), ["failure", "style"])
        self.assertTrue(cases)
        self.assertEqual({case["category"] for case in cases}, {"failure", "style"})


class ModelEvaluationBackendTests(unittest.TestCase):
    def test_fake_backend_returns_fixture_text_without_network(self):
        with patch("tools.eval_models.urllib.request.urlopen") as urlopen:
            result = FakeBackend().generate(_case())
        self.assertEqual(result, ModelResult(text=GOOD_BRIEF, latency_s=0.0))
        urlopen.assert_not_called()

    def test_fake_backend_error_leaves_the_radio_silent(self):
        case = _case(expected="silent", fake={"error": "unavailable"})
        result = score_case(case, FakeBackend().generate(case))
        self.assertTrue(result.passed)
        self.assertEqual(result.actual, "silent")
        self.assertIn("radio silent", result.notes)
        self.assertIn("unavailable", result.error)

    def test_ollama_backend_parses_a_local_response(self):
        requests = []

        def opener(request, timeout):
            requests.append((request, timeout))
            return _Response({"message": {"content": GOOD_BRIEF}})

        backend = OllamaBackend("local-model", timeout=3, opener=opener)
        result = backend.generate(_case())
        self.assertEqual(result.text, GOOD_BRIEF)
        self.assertEqual(result.error, "")
        self.assertGreaterEqual(result.latency_s, 0)
        payload = json.loads(requests[0][0].data)
        self.assertEqual(payload["model"], "local-model")
        self.assertEqual(payload["options"], {"temperature": 0})
        self.assertEqual(payload["messages"][0]["content"], ENGINEER_PROMPT)
        self.assertNotIn("format", payload)
        self.assertEqual(requests[0][1], 3)

    def test_chat_decision_uses_the_decision_model_and_a_label_schema(self):
        requests = []

        def opener(request, timeout):
            requests.append(request)
            return _Response({"message": {"content": '{"label": "now"}'}})

        backend = OllamaBackend("voice-model", opener=opener, decision_model="istinto-model")
        case = _case(category="decision", task="urgency", expected="now", input={"facts": {"priority": "high"}}, checks={})
        result = score_case(case, backend.generate(case))
        self.assertTrue(result.passed, result.notes)
        payload = json.loads(requests[0].data)
        self.assertTrue(requests[0].full_url.endswith("/api/chat"))
        self.assertEqual(payload["model"], "istinto-model")
        self.assertEqual(payload["format"]["properties"]["label"]["enum"], ["calm", "normal", "now"])

    def test_systemone_decision_reads_choice_and_confidence(self):
        requests = []

        def opener(request, timeout):
            requests.append(request)
            return _Response({"model": "tev1:0.8b", "answers": {"grounded_or_reject": {
                "type": "choice", "choice": "reject",
                "probabilities": {"grounded": 0.1, "reject": 0.9}, "confidence": 0.8,
            }}})

        backend = OllamaBackend("voice-model", opener=opener, decision_model="tev1:0.8b", decision_api="systemone")
        case = _case(
            category="hallucination", task="grounded_or_reject", expected="reject",
            input={"facts": {"fuel": 10.0}, "candidate": "Box alla curva tre."}, checks={},
        )
        result = score_case(case, backend.generate(case))
        self.assertTrue(result.passed, result.notes)
        self.assertEqual(result.metrics["confidence"], 0.8)
        payload = json.loads(requests[0].data)
        self.assertTrue(requests[0].full_url.endswith("/v1/systemone"))
        self.assertEqual(payload["model"], "tev1:0.8b")
        self.assertEqual(payload["state"], case["input"])
        question = payload["questions"]["grounded_or_reject"]
        self.assertEqual(question["type"], "choice")
        self.assertEqual(set(question["criteria"]), {"grounded", "reject"})

    def test_systemone_malformed_answer_leaves_the_radio_silent(self):
        backend = OllamaBackend(
            "voice-model", decision_api="systemone",
            opener=lambda request, timeout: _Response({"answers": {}}),
        )
        case = _case(category="failure", task="urgency", expected="silent", input={"facts": {}}, checks={})
        result = score_case(case, backend.generate(case))
        self.assertTrue(result.passed)
        self.assertIn("malformed decision response", result.error)

    def test_engineer_lines_never_use_systemone(self):
        requests = []

        def opener(request, timeout):
            requests.append(request)
            return _Response({"message": {"content": GOOD_BRIEF}})

        OllamaBackend("voice-model", opener=opener, decision_api="systemone").generate(_case())
        self.assertTrue(requests[0].full_url.endswith("/api/chat"))

    def test_unavailable_ollama_returns_a_clear_diagnostic(self):
        backend = OllamaBackend(
            "missing-model", opener=lambda request, timeout: (_ for _ in ()).throw(urllib.error.URLError("refused")),
        )
        result = backend.generate(_case())
        self.assertEqual(result.text, "")
        self.assertIn("unavailable", result.error)
        self.assertIn("refused", result.error)

    def test_ollama_url_accepts_only_http_loopback_origins(self):
        accepted = (
            "http://127.0.0.1:11434",
            "http://localhost:11434",
            "http://[::1]:11434",
        )
        for url in accepted:
            with self.subTest(url=url):
                self.assertEqual(validate_ollama_url(url), url)

    def test_ollama_url_rejects_public_malformed_and_credentialed_urls(self):
        rejected = (
            "https://example.com",
            "http://8.8.8.8:11434",
            "not-a-url",
            "http://user:password@localhost:11434",
        )
        with patch("tools.eval_models.urllib.request.urlopen") as urlopen:
            for url in rejected:
                with self.subTest(url=url), self.assertRaisesRegex(ValueError, "Ollama URL"):
                    OllamaBackend("local-model", base_url=url)
        urlopen.assert_not_called()

    def test_ollama_cli_unavailable_is_nonzero_and_downloads_nothing(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            corpus = Path(directory) / "one.jsonl"
            _write_cases(corpus, [_case()])
            output = io.StringIO()
            error = io.StringIO()
            with patch("tools.eval_models.urllib.request.urlopen", side_effect=urllib.error.URLError("offline")), \
                 contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                status = main(["--corpus", str(corpus), "--backend", "ollama", "--model", "not-installed"])
        self.assertEqual(status, 2)
        self.assertIn("no model was downloaded", error.getvalue())
        self.assertIn('"backend": "ollama"', output.getvalue())


class ModelEvaluationScoringTests(unittest.TestCase):
    def test_briefing_metrics_count_words_and_sentences(self):
        actual, metrics, notes = assess_briefing(
            GOOD_BRIEF, {"required_terms": ["dieci litri"], "required_any": ["benzina"]},
        )
        self.assertEqual(actual, "accept")
        self.assertEqual(metrics["sentence_count"], 2)
        self.assertEqual(metrics["word_count"], 7)
        self.assertEqual(notes, [])

    def test_briefing_scorer_finds_log_style_and_unsupported_claims(self):
        actual, metrics, notes = assess_briefing(
            "Ecco la risposta: {\"timestamp\":1.5, \"corner\":3}",
            {"required_any": ["benzina", "box"], "forbidden_terms": ["corner"]},
        )
        self.assertEqual(actual, "reject")
        self.assertTrue(metrics["format_violations"])
        self.assertIn("timestamp", metrics["forbidden_token_violations"])
        self.assertEqual(metrics["unsupported_numeric_claims"], ["1.5", "3"])
        self.assertTrue(any("chatbot framing" in note for note in notes))
        self.assertTrue(any("unsupported claim: corner" in note for note in notes))

    def test_false_grounded_acceptance_is_counted(self):
        case = _case(
            category="hallucination", task="grounded_or_reject", expected="reject",
            input={"facts": {}, "candidate": "Curva tre."}, fake={"text": "grounded"}, checks={},
        )
        results, summary = evaluate([case], FakeBackend())
        self.assertFalse(results[0].passed)
        self.assertEqual(summary["false_grounded_acceptance"], 1)
        self.assertEqual(summary["hallucination_failures"], 1)

    def test_false_rejection_is_counted(self):
        case = _case(
            task="grounded_or_reject", expected="grounded",
            input={"facts": {"fuel": 10}, "candidate": GOOD_BRIEF}, fake={"text": "reject"}, checks={},
        )
        _results, summary = evaluate([case], FakeBackend())
        self.assertEqual(summary["false_rejection"], 1)

    def test_malformed_decision_output_is_counted(self):
        case = _case(
            task="grounded_or_reject", expected="grounded",
            input={"facts": {"fuel": 10}, "candidate": GOOD_BRIEF}, fake={"text": "maybe"}, checks={},
        )
        results, summary = evaluate([case], FakeBackend())
        self.assertEqual(results[0].actual, "silent")
        self.assertEqual(summary["malformed_output_failures"], 1)

    def test_false_decision_rates_use_expected_label_denominators(self):
        rows = [
            CaseResult("r1", "grounding", "grounded_or_reject", "reject", "grounded", False, 0, "", "", "", _summary_metrics()),
            CaseResult("r2", "grounding", "grounded_or_reject", "reject", "reject", True, 0, "", "", "", _summary_metrics()),
            CaseResult("g1", "grounding", "grounded_or_reject", "grounded", "reject", False, 0, "", "", "", _summary_metrics()),
            CaseResult("g2", "grounding", "grounded_or_reject", "grounded", "grounded", True, 0, "", "", "", _summary_metrics()),
        ]
        summary = summarize(rows)
        self.assertEqual(summary["false_grounded_acceptance"], 1)
        self.assertEqual(summary["false_grounded_acceptance_rate"], 0.5)
        self.assertEqual(summary["false_rejection"], 1)
        self.assertEqual(summary["false_rejection_rate"], 0.5)

    def test_false_decision_rates_are_zero_without_relevant_expected_labels(self):
        rows = [
            CaseResult("u1", "decision", "urgency", "now", "normal", False, 0, "", "", "", _summary_metrics()),
        ]
        summary = summarize(rows)
        self.assertEqual(summary["false_grounded_acceptance_rate"], 0.0)
        self.assertEqual(summary["false_rejection_rate"], 0.0)

    def test_false_decision_rates_handle_mixed_results(self):
        rows = [
            CaseResult("r1", "grounding", "grounded_or_reject", "reject", "grounded", False, 0, "", "", "", _summary_metrics()),
            CaseResult("r2", "grounding", "grounded_or_reject", "reject", "reject", True, 0, "", "", "", _summary_metrics()),
            CaseResult("r3", "failure", "grounded_or_reject", "reject", "silent", False, 0, "", "", "", _summary_metrics()),
            CaseResult("g1", "grounding", "grounded_or_reject", "grounded", "grounded", True, 0, "", "", "", _summary_metrics()),
            CaseResult("g2", "grounding", "grounded_or_reject", "grounded", "reject", False, 0, "", "", "", _summary_metrics()),
            CaseResult("u1", "decision", "urgency", "now", "calm", False, 0, "", "", "", _summary_metrics()),
        ]
        summary = summarize(rows)
        self.assertEqual(summary["false_grounded_acceptance"], 1)
        self.assertAlmostEqual(summary["false_grounded_acceptance_rate"], 1 / 3)
        self.assertEqual(summary["false_rejection"], 1)
        self.assertEqual(summary["false_rejection_rate"], 0.5)

    def test_empty_line_is_malformed_and_leaves_the_radio_silent(self):
        case = _case(expected="silent", category="failure", fake={"text": ""})
        result = score_case(case, FakeBackend().generate(case))
        self.assertTrue(result.passed)
        self.assertTrue(result.metrics["malformed"])
        self.assertEqual(result.actual, "silent")

    def test_latency_summary_reports_percentiles(self):
        rows = [
            CaseResult(f"l{index}", "decision", "urgency", "now", "now", True, latency, "", "", "", _summary_metrics())
            for index, latency in enumerate((0.1, 0.2, 0.3, 0.4, None))
        ]
        summary = summarize(rows)
        self.assertEqual(summary["latency_p50_s"], 0.2)
        self.assertEqual(summary["latency_p95_s"], 0.4)
        self.assertEqual(summary["latency_max_s"], 0.4)
        self.assertIsNone(summarize([])["latency_p50_s"])

    def test_fake_corpus_evaluation_is_deterministic(self):
        cases = load_corpus()
        first_results, first_summary = evaluate(cases, FakeBackend())
        second_results, second_summary = evaluate(cases, FakeBackend())
        self.assertEqual(first_results, second_results)
        self.assertEqual(first_summary, second_summary)
        self.assertEqual(first_summary["passed"], 65)
        self.assertEqual(first_summary["failed"], 0)


class ModelEvaluationReportingTests(unittest.TestCase):
    def setUp(self):
        self.results, self.summary = evaluate([_case()], FakeBackend())
        self.report = build_report(self.results, self.summary, FakeBackend())

    def test_json_report_contains_metadata_summary_and_case_metrics(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "report.json"
            write_json(path, self.report)
            loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(loaded["metadata"], {
            "backend": "fake", "case_count": 1, "decision_api": None, "decision_model": None,
            "model": None, "timestamp": None,
        })
        self.assertEqual(loaded["summary"]["accuracy"], 1.0)
        self.assertEqual(loaded["cases"][0]["case_id"], "test-case")
        self.assertEqual(loaded["cases"][0]["metrics"]["sentence_count"], 2)

    def test_csv_report_has_one_row_per_case_and_stable_columns(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "report.csv"
            write_csv(path, self.report)
            with path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(tuple(rows[0]), CSV_FIELDS)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["case_id"], "test-case")
        self.assertEqual(rows[0]["pass"], "true")
        self.assertEqual(rows[0]["backend"], "fake")

    def test_cli_writes_json_and_csv_for_filtered_cases(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            json_path = Path(directory) / "report.json"
            csv_path = Path(directory) / "report.csv"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main([
                    "--backend", "fake", "--category", "decision",
                    "--output-json", str(json_path), "--output-csv", str(csv_path),
                ])
            report = json.loads(json_path.read_text(encoding="utf-8"))
            with csv_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(status, 0)
        self.assertGreater(report["metadata"]["case_count"], 0)
        self.assertEqual(len(rows), report["metadata"]["case_count"])
        self.assertTrue(all(row["category"] == "decision" for row in rows))
        self.assertIn('"failed": 0', output.getvalue())

    def test_validate_corpus_cli_does_not_instantiate_a_backend(self):
        output = io.StringIO()
        with patch("tools.eval_models.FakeBackend.generate", side_effect=AssertionError("called")), \
             contextlib.redirect_stdout(output):
            status = main(["--validate-corpus"])
        self.assertEqual(status, 0)
        self.assertIn("Corpus valid: 65 cases", output.getvalue())


if __name__ == "__main__":
    unittest.main()
