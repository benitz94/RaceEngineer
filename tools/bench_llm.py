#!/usr/bin/env python3
"""Bench the installed llama3.2:3b on one fixed synthetic fuel_low session."""

import argparse
import csv
import io
import json
import multiprocessing
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
OLLAMA = os.environ.get("RACEENGINEER_LLM_URL", "http://127.0.0.1:11434").rstrip("/")

MODEL = "llama3.2:3b"


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
        _post("/api/generate", {"model": name, "keep_alive": 0}, 30).close()
    except (OSError, subprocess.SubprocessError):
        print(f"warning: could not unload {name}", file=sys.stderr, flush=True)


def _worker(connection, function, args, kwargs):
    try:
        connection.send((True, function(*args, **kwargs)))
    except Exception as error:
        connection.send((False, str(error) or type(error).__name__))
    finally:
        connection.close()


def bounded_call(function, budget_s, *args, **kwargs):
    """Enforce wall time even when a server keeps trickling stream bytes."""
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_worker, args=(sender, function, args, kwargs))
    process.start()
    sender.close()
    try:
        if not receiver.poll(max(0, budget_s)):
            raise LLMUnavailable("aborted: wall-time budget exceeded (load/generation)")
        try:
            ok, result = receiver.recv()
        except EOFError as error:
            raise LLMUnavailable("benchmark worker exited without a result") from error
        if not ok:
            raise LLMUnavailable(result)
        return result
    finally:
        receiver.close()
        process.join(timeout=0.1)
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
        if process.is_alive():
            process.kill()
            process.join()


def row(**fields):
    return {column: fields.get(column, "") for column in COLUMNS}

def bench_model(name, prompt, samples, alerts):
    quant = show_quant(name)
    stop_model(name)
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
            completion = bounded_call(
                complete_detailed, remaining, prompt,
                model=name, timeout=remaining, backend="ollama",
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
        sentences = len(re.split(r"(?<=[.!?])\s+", briefing)) if briefing else 0
        if briefing and not 2 <= sentences <= 5:
            error = f"tone: expected 2-5 sentences, got {sentences}"
        rows.append(row(
            model=name, quant=quant, vram_mb=peak, pull_ok=True,
            ttft_s=f"{completion.ttft_s:.3f}" if completion.ttft_s is not None else "",
            total_s=f"{completion.total_s:.3f}",
            words=words, error=error,
        ))
        print(json.dumps({"model": name, "generation": index + 1,
                          "raw": completion.text, "briefing": briefing,
                          "sentences": sentences, "metrics": rows[-1]}),
              file=sys.stderr, flush=True)
        try:
            with urllib.request.urlopen(f"{OLLAMA}/api/ps", timeout=5) as response:
                print("residency: " + response.read().decode(), file=sys.stderr, flush=True)
        except OSError:
            pass
    stop_model(name)
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=os.path.join(ROOT, "tools", "bench_stdout.csv"),
                        help="CSV path")
    parser.add_argument("--lang", choices=("en", "it"), default="en")
    args = parser.parse_args(argv)
    os.environ.setdefault("RACEENGINEER_LLM_BACKEND", "ollama")
    samples, alerts = session_dicts()
    prompt = build_prompt(samples, alerts, args.lang)
    if MODEL not in local_names():
        raise SystemExit(f"{MODEL} is not installed or Ollama is unavailable; no download started")
    print(f"== {MODEL} ==", file=sys.stderr, flush=True)
    rows = bench_model(MODEL, prompt, samples, alerts)
    write_csv(args.out, rows)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    text = buffer.getvalue()
    sys.stdout.write(text)
    return 0


def write_csv(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
