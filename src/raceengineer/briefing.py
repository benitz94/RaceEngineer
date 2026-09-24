"""Optional local briefing after a rule radio line.

Nothing here runs unless the caller asks. The typed decision model is not
involved, and a failed request must not replace the rule radio.
"""

import json
import re
import urllib.error
import urllib.request

CHAT_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen3.5:4b"
TIMEOUT_SECONDS = 15
SYSTEM_PROMPT = (
    "You are a pit-wall engineer. Speak Italian. At most two short sentences. "
    "docs/RADIO_PHRASES.md is register training, not a script and not a whitelist. "
    "Give one driver action and, when fuel is present, say that fuel as spoken Italian words "
    "(for example dieci litri). Do not say digits or field names. "
    "Never say the JSON key names type, timestamp, source, format, or version. "
    "Never say a raw timestamp such as 1.5. "
    "Do not speak English except the standard call Box, box. "
    "Do not say alert, procedura, or conferma il segnale. "
    "Do not invent corners, sectors, or rivals. "
    "The JSON is context for you. Do not read it aloud."
)
_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
_SENTENCE_END = re.compile(r"[.!?]+")
_LOG_CHARS = set("{}[]=\"`")
_BANNED_PHRASES = ("conferma il segnale", "confirm the signal")
_FORBIDDEN_WORDS = frozenset({
    "type", "timestamp", "source", "format", "version",
    "alert", "procedura",
    "corner", "corners", "sector", "sectors", "rival", "rivals",
    "curva", "curve", "settore", "settori", "rivale", "rivali", "turn", "turns",
    "fuel", "low", "lap", "the", "this", "that", "with", "from", "your", "you",
    "please", "confirm", "signal", "procedure", "now", "high", "priority",
    "message", "litres", "liters", "liter", "seconds", "second", "time", "value",
    "field", "null", "warning", "status", "level", "data", "json", "key", "keys",
    "number", "copy", "true", "false", "yes", "ok", "okay", "point",
})
_MAX_SENTENCES = 2
_MAX_WORDS = 12


class BriefingUnavailable(Exception):
    """Ollama is down, timed out, or returned nothing usable."""


class BriefRejected(BriefingUnavailable):
    """The model replied with a log line instead of a pit-wall call."""

    def __init__(self):
        super().__init__("brief rejected")


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


def _unwrap(text: str) -> str:
    cleaned = " ".join(text.split())
    while len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in "\"'`*":
        cleaned = cleaned[1:-1].strip()
    return cleaned


def _accept_radio_text(text: str) -> str:
    """Keep a short Italian pit call. Reject logs, field names, and invented facts."""
    cleaned = _unwrap(text)
    if not cleaned:
        raise BriefingUnavailable("empty response")
    lowered = cleaned.lower()
    if any(phrase in lowered for phrase in _BANNED_PHRASES):
        raise BriefRejected()
    if any(char.isdigit() for char in cleaned) or any(char in cleaned for char in _LOG_CHARS):
        raise BriefRejected()
    sentences = [part.strip() for part in _SENTENCE_END.split(cleaned) if part.strip()]
    if len(sentences) > _MAX_SENTENCES or any(len(part.split()) > _MAX_WORDS for part in sentences):
        raise BriefRejected()
    words = {word.lower() for word in _WORD.findall(cleaned)}
    if words & _FORBIDDEN_WORDS:
        raise BriefRejected()
    return cleaned


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
    an empty sentence. The caller decides whether the sentence may air.
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
