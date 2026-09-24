"""Optional local briefing after a rule radio line.

Nothing here runs unless the caller asks. The typed decision model is not
involved, and a failed request must not replace the rule radio.
"""

import json
import urllib.error
import urllib.request

CHAT_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen3.5:4b"
TIMEOUT_SECONDS = 15
SYSTEM_PROMPT = (
    "You are a pit-wall engineer. Speak Italian. Two sentences maximum. "
    "docs/RADIO_PHRASES.md is register training, not a whitelist. "
    "Do not invent corners, sectors, rivals, or numbers that are not in the JSON. "
    "Ground the briefing in the alert fields actually passed: type, fuel, and timestamp."
)


class BriefingUnavailable(Exception):
    """Ollama is down, timed out, or returned nothing usable."""


def _one_line(value, limit=300) -> str:
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _http_failure(status, detail) -> str:
    detail = _one_line(detail)
    if detail:
        return f"HTTP {status}: {detail}"
    return f"HTTP {status}"


def _error_detail(error: urllib.error.HTTPError) -> str:
    try:
        raw = error.read()
    except OSError:
        return ""
    return raw.decode("utf-8", errors="replace")


def _think_rejected(status, detail) -> bool:
    """True when this 400 is the server refusing the think field."""
    if status != 400:
        return False
    lowered = detail.lower()
    if "think" not in lowered:
        return False
    markers = ("unknown", "unsupported", "unrecognized", "invalid", "not supported")
    return any(marker in lowered for marker in markers)


def _payload(user: str, *, include_think: bool) -> dict:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        "stream": False,
    }
    if include_think:
        payload["think"] = False
    return payload


def _post(payload, opener, timeout) -> bytes:
    request = urllib.request.Request(
        CHAT_URL,
        data=json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with opener(request, timeout=timeout) as response:
        return response.read()


def _chat(user, opener, timeout) -> bytes:
    try:
        return _post(_payload(user, include_think=True), opener, timeout)
    except urllib.error.HTTPError as error:
        detail = _error_detail(error)
        if not _think_rejected(error.code, detail):
            raise BriefingUnavailable(_http_failure(error.code, detail)) from error
    # Older Ollama builds reject the think field; retry once without it.
    return _post(_payload(user, include_think=False), opener, timeout)


def _sentence(raw: bytes) -> str:
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BriefingUnavailable("invalid response") from error
    message = body.get("message") if isinstance(body, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise BriefingUnavailable("empty response")
    return content.strip()


def _unavailable(error: BaseException) -> BriefingUnavailable:
    reason = getattr(error, "reason", error)
    if isinstance(error, TimeoutError) or isinstance(reason, TimeoutError):
        return BriefingUnavailable("timed out")
    text = _one_line(error)
    return BriefingUnavailable(text or "unavailable")


def brief_alert(alert, opener=None, timeout=TIMEOUT_SECONDS) -> str:
    """Return the model sentence for a fuel_low alert.

    Raises BriefingUnavailable when Ollama is down, times out, or returns
    an empty sentence. The rule radio stays the caller's responsibility.
    """
    if opener is None:
        opener = urllib.request.urlopen
    try:
        user = json.dumps(
            {"fuel": alert.fuel, "timestamp": alert.timestamp, "type": alert.type},
            sort_keys=True, separators=(",", ":"), allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise BriefingUnavailable(_one_line(error) or "unavailable") from error
    try:
        raw = _chat(user, opener, timeout)
    except BriefingUnavailable:
        raise
    except urllib.error.HTTPError as error:
        raise BriefingUnavailable(_http_failure(error.code, _error_detail(error))) from error
    except OSError as error:
        raise _unavailable(error) from error
    return _sentence(raw)
