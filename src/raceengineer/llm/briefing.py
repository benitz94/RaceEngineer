"""Short spoken radio briefing from structured samples and alerts."""

import json
import math
import re
import unicodedata

from .backend import LLMUnavailable, complete as default_complete

MAX_WORDS = 80
MAX_SENTENCES = 5
LANGS = ("en", "it")
LLM_DOWN_WARNING = "warning: LLM briefing unavailable; alerts only"

_SKIP_NUMBER_KEYS = {"format", "version", "message", "quality", "source_id", "type", "priority"}
_NUMBER = re.compile(r"(?<![\w.])[-+]?\d+(?:\.\d+)?")
_SENTENCE = re.compile(r"(?<=[.!?])\s+")
_MARKDOWN = (
    (re.compile(r"```.*?```", re.S), " "),
    (re.compile(r"`([^`]*)`"), r"\1"),
    (re.compile(r"\*\*([^*]*)\*\*"), r"\1"),
    (re.compile(r"__([^_]*)__"), r"\1"),
    (re.compile(r"\*([^*]*)\*"), r"\1"),
    (re.compile(r"^#+\s*", re.M), ""),
    (re.compile(r"\[([^\]]+)\]\([^)]+\)"), r"\1"),
)
_PREFIX = re.compile(
    r"^(?:sure|certainly|of course|here(?:'s| is)|as an ai)[,:.\s-]*",
    re.I,
)


def _language(lang):
    if lang not in LANGS:
        raise ValueError("lang must be en or it")
    return lang


def _number_forms(value):
    forms = set()
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return forms
    if not math.isfinite(value):
        return forms
    if isinstance(value, int) or float(value).is_integer():
        whole = str(int(value))
        forms.update((whole, f"{whole}.0"))
        return forms
    text = format(float(value), ".6f").rstrip("0").rstrip(".")
    forms.add(text)
    forms.add(str(float(value)))
    return forms


def allowed_numbers(samples, alerts):
    allowed = set()

    def walk(value, key=None):
        if key in _SKIP_NUMBER_KEYS:
            return
        if isinstance(value, dict):
            for child_key, child in value.items():
                walk(child, child_key)
        elif isinstance(value, (list, tuple)):
            for child in value:
                walk(child)
        else:
            allowed.update(_number_forms(value))

    for record in (*samples, *alerts):
        walk(record)
    return allowed


def _strip_markdown(text):
    for pattern, replacement in _MARKDOWN:
        text = pattern.sub(replacement, text)
    return text


def _has_emoji(text):
    for char in text:
        if unicodedata.category(char) == "So":
            return True
        code = ord(char)
        if 0x1F000 <= code <= 0x1FAFF or 0x2600 <= code <= 0x27BF:
            return True
    return False


def _sentences(text):
    text = _PREFIX.sub("", " ".join(_strip_markdown(text).split())).strip()
    if not text:
        return []
    parts = [part.strip() for part in _SENTENCE.split(text) if part.strip()]
    cleaned = []
    for part in parts:
        if _has_emoji(part):
            continue
        if not part.endswith((".", "!", "?")):
            part = f"{part}."
        cleaned.append(part)
    return cleaned


def _number_allowed(token, allowed):
    try:
        value = float(token)
    except ValueError:
        return False
    return bool(_number_forms(value) & allowed)


def sanitize_briefing(text, samples, alerts):
    if not text or not str(text).strip():
        return None
    allowed = allowed_numbers(samples, alerts)
    kept = []
    for sentence in _sentences(str(text)):
        if any(not _number_allowed(token, allowed) for token in _NUMBER.findall(sentence)):
            continue
        kept.append(sentence)
        if len(kept) == MAX_SENTENCES:
            break
    while kept and len(" ".join(kept).split()) > MAX_WORDS:
        kept.pop()
    if not kept:
        return None
    return " ".join(kept)


def build_prompt(samples, alerts, lang="en"):
    lang = _language(lang)
    if lang == "it":
        instructions = (
            "Sei l'ingegnere di pista alla radio. Parla solo dai dati strutturati. "
            "Scrivi da 2 a 5 frasi brevi, parlabili. Niente markdown, emoji, saluti, "
            "domande o numeri inventati. Al massimo 80 parole. Italiano."
        )
    else:
        instructions = (
            "You are the race engineer on the radio. Speak only from the structured data. "
            "Write 2 to 5 short speakable sentences. No markdown, emoji, greetings, "
            "questions, or invented numbers. At most 80 words. English."
        )
    payload = json.dumps(
        {"alerts": list(alerts), "samples": list(samples)},
        sort_keys=True, separators=(",", ":"), allow_nan=False, default=str,
    )
    return f"{instructions}\n\n{payload}"


def speak(samples, alerts, lang="en", complete=None):
    """Return a sanitized briefing, or None if the sidecar cannot speak."""
    _language(lang)
    generate = default_complete if complete is None else complete
    try:
        raw = generate(build_prompt(samples, alerts, lang))
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
    except (LLMUnavailable, OSError, TimeoutError, ValueError, RuntimeError):
        return None
    return sanitize_briefing(raw, samples, alerts)
