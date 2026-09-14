#!/usr/bin/env python3
"""Bench local Ollama models on one fixed synthetic fuel_low session."""

import argparse
import csv
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from raceengineer.llm.backend import LLMUnavailable, complete_detailed  # noqa: E402
from raceengineer.llm.briefing import build_prompt, speak  # noqa: E402
from raceengineer.rules import RulesEngine  # noqa: E402
from raceengineer.sources import synthetic  # noqa: E402

COLUMNS = ("model", "quant", "vram_mb", "pull_ok", "ttft_s", "total_s", "words", "error")
GENERATIONS = 3
MODEL_BUDGET_S = 600
PULL_TIMEOUT_S = 1200
OLLAMA = os.environ.get("RACEENGINEER_LLM_URL", "http://127.0.0.1:11434").rstrip("/")

# Requested tags first; fallbacks are official Ollama tags used on 404.
MATRIX = (
    ("llama3.2:3b", ()),
    ("llama3.1:8b-instruct-q4_K_M", ()),
    ("llama3.1:8b-instruct-q5_K_M", ()),
    ("mistral:7b-instruct", ()),
    ("qwen2.5:7b-instruct", ()),
    ("gemma2:9b-instruct", ("gemma2:9b-instruct-q4_0", "gemma2:9b")),
    ("phi4", ("phi4:14b",)),
    ("mistral-nemo:12b-instruct-q4_K_M", ("mistral-nemo",)),
    ("qwen2.5:14b-instruct-q4_K_M", ()),
    ("llama3.1:8b-instruct-q8_0", ()),
)


def session_dicts():
    engine = RulesEngine()
    samples = [sample.to_dict() for sample in synthetic()]
    alerts = []
    for sample in synthetic():
        alert = engine.process(sample)
        if alert is not None:
            alerts.append({"type": alert.type, "priority": alert.priority,
                           "timestamp": alert.timestamp, "fuel": alert.fuel,
                           "message": alert.message})
    if not any(alert["type"] == "fuel_low" for alert in alerts):
        raise SystemExit("fixed synthetic session did not produce fuel_low")
    return samples, alerts


def _post(path, payload, timeout):
    request = urllib.request.Request(
        f"{OLLAMA}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return urllib.request.urlopen(request, timeout=timeout)


def local_names():
    try:
        with urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=5) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return set()
    return {item.get("name") for item in body.get("models", []) if item.get("name")}


def pull(name):
    try:
        with _post("/api/pull", {"name": name, "stream": True}, PULL_TIMEOUT_S) as response:
            last = {}
            for raw in response:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("error"):
                    return False, str(event["error"])
                last = event
            if last.get("status") in ("success", "already exists") or last.get("digest"):
                return True, ""
            return True, ""
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:300]
        return False, f"HTTP {error.code}: {detail or error.reason}"
    except (OSError, urllib.error.URLError, TimeoutError) as error:
        return False, str(error) or error.__class__.__name__


def show_quant(name):
    try:
        with _post("/api/show", {"name": name}, 30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return quant_from_tag(name)
    details = body.get("details") or {}
    return details.get("quantization_level") or quant_from_tag(name)


def quant_from_tag(name):
    match = re.search(r"(q[0-9]+[._][0-9A-Za-z_]+|fp16|f16)$", name, re.I)
    return match.group(1) if match else "default"


def gpu_used_mb():
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True, timeout=5,
        )
        return int(float(output.splitlines()[0].strip()))
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return ""


def stop_model(name):
    try:
        subprocess.run(["ollama", "stop", name], timeout=30, check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        try:
            _post("/api/generate", {"model": name, "keep_alive": 0, "prompt": " "}, 30).close()
        except (OSError, urllib.error.URLError, TimeoutError):
            pass


def row(**fields):
    return {column: fields.get(column, "") for column in COLUMNS}


def resolve_and_pull(requested, fallbacks):
    if re.search(r"70b", requested, re.I):
        return requested, False, "refusing to pull 70B"
    tried = []
    for name in (requested, *fallbacks):
        tried.append(name)
        ok, error = pull(name)
        if ok:
            return name, True, ""
        if not re.search(r"404|not found|does not exist|file does not exist", error, re.I):
            return name, False, error
    return requested, False, f"404 after {', '.join(tried)}"


def bench_model(name, prompt, samples, alerts):
    quant = show_quant(name)
    deadline = time.monotonic() + MODEL_BUDGET_S
    rows = []
    peak = gpu_used_mb()
    for index in range(GENERATIONS):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            rows.append(row(model=name, quant=quant, vram_mb=peak, pull_ok=True,
                            error="aborted: model budget 10 minutes (swap/load)"))
            break
        try:
            completion = complete_detailed(
                prompt, model=name, timeout=remaining, backend="ollama",
            )
        except LLMUnavailable as error:
            used = gpu_used_mb()
            if used not in ("", None) and peak not in ("", None):
                peak = max(peak, used)
            rows.append(row(model=name, quant=quant, vram_mb=peak, pull_ok=True,
                            error=str(error)))
            break
        used = gpu_used_mb()
        if used not in ("", None) and peak not in ("", None):
            peak = max(peak, used)
        elif used not in ("", None):
            peak = used
        briefing = speak(samples, alerts, complete=lambda _prompt, text=completion.text: text)
        words = len((briefing or completion.text).split())
        error = "" if briefing else "sanitizer rejected briefing"
        rows.append(row(
            model=name, quant=quant, vram_mb=peak, pull_ok=True,
            ttft_s=f"{completion.ttft_s:.3f}" if completion.ttft_s is not None else "",
            total_s=f"{completion.total_s:.3f}",
            words=words, error=error,
        ))
        if index == 0:
            print(briefing or completion.text, file=sys.stderr)
    stop_model(name)
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", help="optional CSV path")
    parser.add_argument("--lang", choices=("en", "it"), default="en")
    args = parser.parse_args(argv)
    os.environ.setdefault("RACEENGINEER_LLM_BACKEND", "ollama")
    samples, alerts = session_dicts()
    prompt = build_prompt(samples, alerts, args.lang)
    preexisting = local_names()
    rows = []
    for requested, fallbacks in MATRIX:
        print(f"== {requested} ==", file=sys.stderr)
        name, pull_ok, error = resolve_and_pull(requested, fallbacks)
        if not pull_ok:
            rows.append(row(model=requested, quant=quant_from_tag(requested),
                            pull_ok=False, error=error))
            continue
        if name != requested:
            print(f"using official tag {name} instead of {requested}", file=sys.stderr)
        rows.extend(bench_model(name, prompt, samples, alerts))
        if name not in preexisting:
            try:
                subprocess.run(["ollama", "rm", name], timeout=60, check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except (OSError, subprocess.SubprocessError):
                pass
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(rows)
    text = buffer.getvalue()
    sys.stdout.write(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
