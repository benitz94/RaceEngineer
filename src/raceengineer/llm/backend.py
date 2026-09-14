"""Local Ollama or llama.cpp, with optional OpenAI-compatible HTTP."""

from dataclasses import dataclass
import json
import os
import time
import urllib.error
import urllib.request

DEFAULT_OLLAMA = "http://127.0.0.1:11434"
DEFAULT_LLAMACPP = "http://127.0.0.1:8080"
DEFAULT_MODEL = "llama3.2:3b"
DEFAULT_TIMEOUT = 60.0
NUM_PREDICT = 120
TEMPERATURE = 0.2
NUM_CTX = 2048

BACKENDS = ("ollama", "llamacpp", "openai")


class LLMUnavailable(Exception):
    """Local or remote generator is not reachable."""


@dataclass
class Completion:
    text: str
    ttft_s: float | None = None
    total_s: float = 0.0


def env_backend():
    value = os.environ.get("RACEENGINEER_LLM_BACKEND", "").strip().lower()
    return value if value in BACKENDS else ""


def env_url():
    return os.environ.get("RACEENGINEER_LLM_URL", "").strip().rstrip("/")


def env_model():
    return os.environ.get("RACEENGINEER_LLM_MODEL", "").strip() or DEFAULT_MODEL


def env_timeout():
    raw = os.environ.get("RACEENGINEER_LLM_TIMEOUT", "").strip()
    if not raw:
        return DEFAULT_TIMEOUT
    try:
        timeout = float(raw)
    except ValueError as error:
        raise LLMUnavailable("RACEENGINEER_LLM_TIMEOUT must be a number") from error
    if timeout <= 0:
        raise LLMUnavailable("RACEENGINEER_LLM_TIMEOUT must be greater than zero")
    return timeout


def _headers():
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    key = os.environ.get("RACEENGINEER_LLM_API_KEY", "").strip()
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


def _reachable(url, timeout=2.0):
    try:
        urllib.request.urlopen(url, timeout=timeout).close()
        return True
    except (OSError, urllib.error.URLError):
        return False


def detect_backend():
    chosen = env_backend()
    if chosen:
        return chosen
    if env_url():
        return "openai"
    if _reachable(f"{DEFAULT_OLLAMA}/api/tags"):
        return "ollama"
    if _reachable(f"{DEFAULT_LLAMACPP}/health") or _reachable(f"{DEFAULT_LLAMACPP}/v1/models"):
        return "llamacpp"
    raise LLMUnavailable("no local LLM (Ollama or llama.cpp) is reachable")


def _base_url(backend):
    override = env_url()
    if override:
        return override
    if backend == "llamacpp":
        return DEFAULT_LLAMACPP
    return DEFAULT_OLLAMA


def _openai_url(base):
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def _post_stream(url, payload, timeout):
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=_headers(), method="POST",
    )
    return urllib.request.urlopen(request, timeout=timeout)


def _decode_line(raw):
    line = raw.decode("utf-8", errors="replace").strip()
    if not line:
        return None
    if line.startswith("data:"):
        line = line[5:].strip()
    if not line or line == "[DONE]":
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def _chunk_text(backend, event):
    if not isinstance(event, dict):
        return ""
    if event.get("error"):
        raise LLMUnavailable(str(event["error"]))
    if backend == "ollama":
        return event.get("response") or ""
    if backend == "llamacpp":
        if "content" in event:
            return event.get("content") or ""
        choices = event.get("choices")
        if isinstance(choices, list) and choices:
            choice = choices[0]
            return (choice.get("text") or choice.get("delta", {}).get("content") or "")
        return ""
    choices = event.get("choices")
    if isinstance(choices, list) and choices:
        delta = choices[0].get("delta") or {}
        return delta.get("content") or choices[0].get("text") or ""
    return ""


def complete_detailed(prompt, *, model=None, timeout=None, backend=None) -> Completion:
    backend = backend or detect_backend()
    model = model or env_model()
    timeout = env_timeout() if timeout is None else timeout
    base = _base_url(backend)
    if backend == "ollama":
        url = f"{base}/api/generate"
        payload = {
            "model": model, "prompt": prompt, "stream": True,
            "options": {"temperature": TEMPERATURE, "num_predict": NUM_PREDICT, "num_ctx": NUM_CTX},
        }
    elif backend == "llamacpp":
        url = f"{base}/completion" if not base.endswith("/completion") else base
        payload = {
            "prompt": prompt, "n_predict": NUM_PREDICT, "temperature": TEMPERATURE,
            "stream": True, "cache_prompt": True,
        }
    else:
        url = _openai_url(base)
        payload = {
            "model": model, "stream": True, "temperature": TEMPERATURE, "max_tokens": NUM_PREDICT,
            "messages": [{"role": "user", "content": prompt}],
        }
    started = time.monotonic()
    first = None
    chunks = []
    try:
        with _post_stream(url, payload, timeout) as response:
            for raw in response:
                event = _decode_line(raw)
                if event is None:
                    continue
                piece = _chunk_text(backend, event)
                if piece:
                    if first is None:
                        first = time.monotonic()
                    chunks.append(piece)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:300]
        raise LLMUnavailable(f"HTTP {error.code}: {detail or error.reason}") from error
    except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise LLMUnavailable(str(error) or error.__class__.__name__) from error
    text = "".join(chunks).strip()
    if not text:
        raise LLMUnavailable("empty LLM response")
    ended = time.monotonic()
    return Completion(text, None if first is None else first - started, ended - started)


def complete(prompt, **kwargs) -> str:
    return complete_detailed(prompt, **kwargs).text
