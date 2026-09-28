#!/usr/bin/env python3
"""Evaluate RaceEngineer briefing and typed-decision model roles offline or with Ollama."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sys
import time
from typing import Iterable
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = (
    ROOT / "tests" / "model_eval" / "briefing_cases.jsonl",
    ROOT / "tests" / "model_eval" / "grounding_cases.jsonl",
    ROOT / "tests" / "model_eval" / "decision_cases.jsonl",
)

CATEGORIES = frozenset({"grounding", "hallucination", "style", "decision", "failure"})
TASK_LABELS = {
    "briefing": frozenset({"accept", "fallback"}),
    "canned_or_brief": frozenset({"canned", "brief", "fallback"}),
    "grounded_or_reject": frozenset({"grounded", "reject", "fallback"}),
}
REQUIRED_FIELDS = frozenset({"id", "category", "task", "input", "expected", "rationale", "fake"})
OPTIONAL_FIELDS = frozenset({"checks"})
CASE_ID = re.compile(r"^[a-z][a-z0-9_-]*$")
WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
NUMBER = re.compile(r"(?<![\w])\d+(?:[.,]\d+)?")
SENTENCE_END = re.compile(r"[.!?]+")
MAX_SENTENCES = 2
MAX_WORDS_PER_SENTENCE = 12
LOG_WORDS = frozenset({
    "alert", "format", "fuel_low", "message", "priority", "source", "timestamp",
    "type", "version", "json", "null", "true", "false",
})
CHATBOT_PHRASES = (
    "come assistente", "certamente", "ciao", "ecco la risposta",
    "posso aiutarti", "sure", "here is", "as an ai",
)
CSV_FIELDS = (
    "case_id", "category", "task", "expected", "actual", "pass", "latency_s",
    "error", "notes", "output", "backend", "model", "timestamp", "case_count",
)


class CorpusError(ValueError):
    """The evaluation corpus is malformed or internally inconsistent."""


@dataclass(frozen=True)
class ModelResult:
    """One backend response without scorer policy."""

    text: str = ""
    latency_s: float | None = None
    error: str = ""


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    category: str
    task: str
    expected: str
    actual: str
    passed: bool
    latency_s: float | None
    error: str
    notes: str
    output: str
    metrics: dict

    def to_dict(self) -> dict:
        result = asdict(self)
        result["pass"] = result.pop("passed")
        return result


class ModelBackend:
    """Minimal model adapter used by the evaluator."""

    name = "backend"
    model = ""

    def generate(self, case: dict) -> ModelResult:
        raise NotImplementedError


class FakeBackend(ModelBackend):
    """Return the deterministic result embedded in each fixture."""

    name = "fake"

    def generate(self, case: dict) -> ModelResult:
        fake = case["fake"]
        if "error" in fake:
            return ModelResult(latency_s=0.0, error=fake["error"])
        return ModelResult(text=fake["text"], latency_s=0.0)


class OllamaBackend(ModelBackend):
    """Small standard-library adapter for an already installed local Ollama model."""

    name = "ollama"

    def __init__(
        self,
        model: str,
        base_url: str = "http://127.0.0.1:11434",
        timeout: float = 15.0,
        opener=None,
    ):
        if not model.strip():
            raise ValueError("Ollama requires a model name")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and greater than zero")
        self.model = model.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.opener = opener or urllib.request.urlopen

    def generate(self, case: dict) -> ModelResult:
        payload = {
            "model": self.model,
            "messages": _messages(case),
            "stream": False,
            "options": {"temperature": 0},
        }
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        started = time.perf_counter()
        try:
            with self.opener(request, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as error:
            detail = _http_detail(error)
            return ModelResult(latency_s=time.perf_counter() - started, error=f"HTTP {error.code}: {detail}".rstrip())
        except (TimeoutError, OSError, urllib.error.URLError) as error:
            reason = getattr(error, "reason", error)
            prefix = "timeout" if isinstance(error, TimeoutError) or isinstance(reason, TimeoutError) else "unavailable"
            return ModelResult(latency_s=time.perf_counter() - started, error=f"{prefix}: {_one_line(reason)}".rstrip())
        latency = time.perf_counter() - started
        try:
            body = json.loads(raw.decode("utf-8"))
            message = body.get("message") if isinstance(body, dict) else None
            content = message.get("content") if isinstance(message, dict) else None
        except (UnicodeDecodeError, json.JSONDecodeError):
            content = None
        if not isinstance(content, str):
            return ModelResult(latency_s=latency, error="malformed Ollama response")
        return ModelResult(text=content.strip(), latency_s=latency)


def _one_line(value, limit: int = 240) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _http_detail(error: urllib.error.HTTPError) -> str:
    try:
        return _one_line(error.read().decode("utf-8", errors="replace"))
    except OSError:
        return ""


def _messages(case: dict) -> list[dict[str, str]]:
    task = case["task"]
    if task == "briefing":
        system = (
            "You are a pit-wall engineer. Return only a short Italian radio line of at most "
            "two sentences and at most twelve words per sentence. Use only the supplied current "
            "facts. Do not read JSON keys, timestamps, metadata, or digits aloud. Do not invent "
            "track places, rivals, gaps, weather, tyres, speed, or strategy."
        )
    elif task == "canned_or_brief":
        system = "Answer exactly canned or brief for the declared canned_or_brief question."
    else:
        system = (
            "Answer exactly grounded or reject. Reject a candidate that states anything not "
            "supported by the supplied facts, including metadata or historical values as current."
        )
    user = json.dumps(case["input"], sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def validate_case(case: object, location: str = "case") -> dict:
    if not isinstance(case, dict):
        raise CorpusError(f"{location}: case must be an object")
    missing = REQUIRED_FIELDS - case.keys()
    if missing:
        raise CorpusError(f"{location}: missing required fields: {', '.join(sorted(missing))}")
    unknown = case.keys() - REQUIRED_FIELDS - OPTIONAL_FIELDS
    if unknown:
        raise CorpusError(f"{location}: unknown fields: {', '.join(sorted(unknown))}")
    case_id = case["id"]
    if not isinstance(case_id, str) or not CASE_ID.fullmatch(case_id):
        raise CorpusError(f"{location}: invalid case id")
    if case["category"] not in CATEGORIES:
        raise CorpusError(f"{location}: unknown category: {case['category']}")
    task = case["task"]
    if task not in TASK_LABELS:
        raise CorpusError(f"{location}: unknown task: {task}")
    if case["expected"] not in TASK_LABELS[task]:
        raise CorpusError(f"{location}: illegal expected label for {task}: {case['expected']}")
    if not isinstance(case["input"], dict):
        raise CorpusError(f"{location}: input must be an object")
    if not isinstance(case["rationale"], str) or not case["rationale"].strip():
        raise CorpusError(f"{location}: rationale must be a nonempty string")
    fake = case["fake"]
    if not isinstance(fake, dict) or set(fake) not in ({"text"}, {"error"}):
        raise CorpusError(f"{location}: fake must contain exactly one of text or error")
    key = next(iter(fake))
    if not isinstance(fake[key], str) or (key == "error" and not fake[key].strip()):
        raise CorpusError(f"{location}: fake {key} must be a string")
    checks = case.get("checks", {})
    if not isinstance(checks, dict):
        raise CorpusError(f"{location}: checks must be an object")
    for key in ("required_terms", "required_any", "forbidden_terms", "allowed_numbers"):
        if key in checks and not isinstance(checks[key], list):
            raise CorpusError(f"{location}: checks.{key} must be a list")
    return case


def load_corpus(paths: Iterable[Path | str] | None = None) -> list[dict]:
    selected = tuple(Path(path) for path in (paths or DEFAULT_CORPUS))
    cases = []
    seen = {}
    for path in selected:
        try:
            handle = path.open(encoding="utf-8-sig")
        except OSError as error:
            raise CorpusError(f"{path}: {error}") from error
        with handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                location = f"{path}: line {line_number}"
                try:
                    parsed = json.loads(line)
                except json.JSONDecodeError as error:
                    raise CorpusError(f"{location}: invalid JSON: {error.msg}") from error
                case = validate_case(parsed, location)
                if case["id"] in seen:
                    raise CorpusError(f"{location}: duplicate case id {case['id']} (first at {seen[case['id']]})")
                seen[case["id"]] = location
                cases.append(case)
    if not cases:
        raise CorpusError("corpus contains no cases")
    return cases


def filter_cases(cases: Iterable[dict], categories: Iterable[str] | None = None) -> list[dict]:
    selected = set(categories or ())
    if not selected:
        return list(cases)
    unknown = selected - CATEGORIES
    if unknown:
        raise CorpusError(f"unknown categories: {', '.join(sorted(unknown))}")
    filtered = [case for case in cases if case["category"] in selected]
    if not filtered:
        raise CorpusError("category filter selected no cases")
    return filtered


def _normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def _term_present(normalized: str, term: object) -> bool:
    return _normalized(str(term)) in normalized


def assess_briefing(text: str, checks: dict | None = None) -> tuple[str, dict, list[str]]:
    """Apply only deterministic lexical, format, and fixture-specific checks."""
    checks = checks or {}
    cleaned = " ".join(text.split())
    words = WORD.findall(cleaned)
    sentences = [part.strip() for part in SENTENCE_END.split(cleaned) if part.strip()]
    normalized = _normalized(cleaned)
    tokens = {word.casefold() for word in words}
    format_violations = []
    style_violations = []
    forbidden_violations = []
    unsupported_claims = []
    malformed = not cleaned

    if any(char in cleaned for char in "{}[]\"`"):
        format_violations.append("JSON/log punctuation")
    if "```" in cleaned or re.search(r"(^|\s)(?:#{1,6}|[-*])\s", cleaned):
        format_violations.append("markdown")
    log_hits = sorted(tokens & LOG_WORDS)
    forbidden_violations.extend(log_hits)
    if len(sentences) > MAX_SENTENCES:
        style_violations.append(f"sentences>{MAX_SENTENCES}")
    if any(len(WORD.findall(sentence)) > MAX_WORDS_PER_SENTENCE for sentence in sentences):
        style_violations.append(f"words_per_sentence>{MAX_WORDS_PER_SENTENCE}")
    if any(phrase in normalized for phrase in CHATBOT_PHRASES):
        style_violations.append("chatbot framing")
    required_terms = checks.get("required_terms", [])
    for term in required_terms:
        if not _term_present(normalized, term):
            unsupported_claims.append(f"missing required claim: {term}")
    required_any = checks.get("required_any", [])
    if required_any and not any(_term_present(normalized, term) for term in required_any):
        unsupported_claims.append("missing required Italian/register marker")
    for term in checks.get("forbidden_terms", []):
        if _term_present(normalized, term):
            unsupported_claims.append(f"unsupported claim: {term}")

    allowed_numbers = {str(value).replace(",", ".") for value in checks.get("allowed_numbers", [])}
    numeric_claims = [match.group(0) for match in NUMBER.finditer(cleaned)]
    unsupported_numbers = [number for number in numeric_claims if number.replace(",", ".") not in allowed_numbers]
    if numeric_claims:
        style_violations.append("digits")
    if unsupported_numbers:
        unsupported_claims.extend(f"unsupported number: {number}" for number in unsupported_numbers)

    notes = []
    if malformed:
        notes.append("malformed: empty output")
    notes.extend(f"format: {item}" for item in format_violations)
    notes.extend(f"style: {item}" for item in style_violations)
    notes.extend(f"forbidden: {item}" for item in forbidden_violations)
    notes.extend(unsupported_claims)
    metrics = {
        "sentence_count": len(sentences),
        "word_count": len(words),
        "format_violations": format_violations,
        "style_violations": style_violations,
        "forbidden_token_violations": forbidden_violations,
        "unsupported_claim_violations": unsupported_claims,
        "unsupported_numeric_claims": unsupported_numbers,
        "malformed": malformed,
        "fallback_used": False,
    }
    return ("reject" if notes else "accept"), metrics, notes


def _fallback(case: dict, metrics: dict, notes: list[str]) -> str | None:
    rule_text = case["input"].get("rule_fallback")
    if isinstance(rule_text, str) and rule_text.strip():
        metrics["fallback_used"] = True
        notes.append("deterministic rule fallback available")
        return "fallback"
    return None


def score_case(case: dict, result: ModelResult) -> CaseResult:
    task = case["task"]
    notes = []
    metrics = {
        "sentence_count": 0,
        "word_count": 0,
        "format_violations": [],
        "style_violations": [],
        "forbidden_token_violations": [],
        "unsupported_claim_violations": [],
        "unsupported_numeric_claims": [],
        "malformed": False,
        "fallback_used": False,
    }
    if result.error:
        metrics["malformed"] = True
        notes.append(f"backend: {result.error}")
        actual = _fallback(case, metrics, notes) or "error"
    elif task == "briefing":
        assessment, metrics, notes = assess_briefing(result.text, case.get("checks"))
        actual = assessment
        if assessment == "reject":
            actual = _fallback(case, metrics, notes) or assessment
    else:
        actual = _normalized(result.text)
        legal = TASK_LABELS[task] - {"fallback"}
        if not actual or actual not in legal:
            metrics["malformed"] = True
            notes.append("malformed: expected exactly one legal label")
            actual = _fallback(case, metrics, notes) or "malformed"
    return CaseResult(
        case_id=case["id"], category=case["category"], task=task,
        expected=case["expected"], actual=actual, passed=actual == case["expected"],
        latency_s=result.latency_s, error=result.error, notes="; ".join(notes),
        output=result.text, metrics=metrics,
    )


def summarize(results: Iterable[CaseResult]) -> dict:
    rows = list(results)
    total = len(rows)
    passed = sum(row.passed for row in rows)
    failed = total - passed
    return {
        "cases_total": total,
        "passed": passed,
        "failed": failed,
        "accuracy": passed / total if total else 0.0,
        "false_grounded_acceptance": sum(
            row.expected == "reject" and row.actual == "grounded" for row in rows
        ),
        "false_rejection": sum(
            row.expected == "grounded" and row.actual == "reject" for row in rows
        ),
        "hallucination_failures": sum(
            not row.passed and row.category == "hallucination" for row in rows
        ),
        "style_failures": sum(
            not row.passed and (row.category == "style" or bool(row.metrics["style_violations"]))
            for row in rows
        ),
        "malformed_output_failures": sum(
            not row.passed and row.metrics["malformed"] for row in rows
        ),
    }


def evaluate(cases: Iterable[dict], backend: ModelBackend) -> tuple[list[CaseResult], dict]:
    results = [score_case(case, backend.generate(case)) for case in cases]
    return results, summarize(results)


def build_report(results: list[CaseResult], summary: dict, backend: ModelBackend) -> dict:
    timestamp = None
    if backend.name != "fake":
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "metadata": {
            "backend": backend.name,
            "model": backend.model or None,
            "timestamp": timestamp,
            "case_count": len(results),
        },
        "summary": summary,
        "cases": [result.to_dict() for result in results],
    }


def write_json(path: Path | str, report: dict) -> None:
    with Path(path).open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def write_csv(path: Path | str, report: dict) -> None:
    metadata = report["metadata"]
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        for case in report["cases"]:
            writer.writerow({
                "case_id": case["case_id"], "category": case["category"],
                "task": case["task"], "expected": case["expected"],
                "actual": case["actual"], "pass": str(case["pass"]).lower(),
                "latency_s": "" if case["latency_s"] is None else f"{case['latency_s']:.6f}",
                "error": case["error"], "notes": case["notes"], "output": case["output"],
                "backend": metadata["backend"], "model": metadata["model"] or "",
                "timestamp": metadata["timestamp"] or "", "case_count": metadata["case_count"],
            })


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", action="append", type=Path, help="JSONL corpus path; repeatable")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--list-cases", action="store_true")
    action.add_argument("--validate-corpus", action="store_true")
    parser.add_argument("--backend", choices=("fake", "ollama"), default="fake")
    parser.add_argument("--model", default="qwen3.5:4b", help="already installed Ollama model")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--category", action="append", choices=sorted(CATEGORIES))
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-csv", type=Path)
    return parser


def main(argv=None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        cases = load_corpus(args.corpus)
        cases = filter_cases(cases, args.category)
        if args.list_cases:
            for case in cases:
                print(f"{case['id']}\t{case['category']}\t{case['task']}\t{case['expected']}")
            return 0
        if args.validate_corpus:
            categories = ", ".join(sorted({case["category"] for case in cases}))
            print(f"Corpus valid: {len(cases)} cases; categories: {categories}")
            return 0
        backend: ModelBackend
        if args.backend == "fake":
            backend = FakeBackend()
        else:
            backend = OllamaBackend(args.model, args.ollama_url, args.timeout)
        results, summary = evaluate(cases, backend)
        report = build_report(results, summary, backend)
        if args.output_json:
            write_json(args.output_json, report)
        if args.output_csv:
            write_csv(args.output_csv, report)
        print(json.dumps({"metadata": report["metadata"], "summary": summary}, sort_keys=True, allow_nan=False))
        if args.backend == "ollama" and results and all(result.error for result in results):
            print("error: Ollama is unavailable or the requested local model could not answer; no model was downloaded", file=sys.stderr)
            return 2
        return 0
    except (CorpusError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
