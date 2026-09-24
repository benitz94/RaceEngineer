"""Deterministic typed decisions for a declared question.

This is code, not a neural model. It does not call Ollama.
"""

import math
import re

_QUESTIONS: dict[str, tuple[str, ...]] = {}
_TOKEN = re.compile(r"\d+(?:[.,]\d+)?|[^\W\d_]+", re.UNICODE)
_REGISTER = frozenset({"box", "rientra", "fuel", "benzina", "litri", "giro"})
_FUNCTION = frozenset({
    "a", "ad", "ai", "al", "allo", "alla", "alle", "agli",
    "di", "del", "dello", "della", "dei", "degli", "delle",
    "da", "dal", "dallo", "dalla", "dai", "dagli",
    "in", "nel", "nello", "nella", "nei", "negli", "nelle",
    "su", "sul", "sullo", "sulla", "sui", "sugli", "sulle",
    "con", "per", "tra", "fra", "e", "ed", "o", "od", "che", "non",
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una",
    "questo", "questa", "questi", "queste",
})
_TRACK = frozenset({
    "place", "places", "posto", "luogo",
    "corner", "corners", "curva", "curve",
    "sector", "sectors", "settore", "settori",
    "tangent", "tangents", "tangente", "tangenti",
    "straight", "straights", "rettilineo", "rettilinei", "rettifilo",
    "scarica", "scaricare",
    "sud", "nord", "est", "ovest", "south", "north", "east", "west",
})
_ITALIAN = {
    0: "zero", 1: "uno", 2: "due", 3: "tre", 4: "quattro", 5: "cinque",
    6: "sei", 7: "sette", 8: "otto", 9: "nove", 10: "dieci", 11: "undici",
    12: "dodici", 13: "tredici", 14: "quattordici", 15: "quindici", 16: "sedici",
    17: "diciassette", 18: "diciotto", 19: "diciannove", 20: "venti", 30: "trenta",
    40: "quaranta", 50: "cinquanta", 60: "sessanta", 70: "settanta", 80: "ottanta",
    90: "novanta", 100: "cento",
}


def declare(question_id: str, labels) -> None:
    """Register a question id and the only labels it may return."""
    legal = tuple(labels)
    if not question_id or not legal:
        raise ValueError("a question needs an id and legal labels")
    _QUESTIONS[question_id] = legal


def answer(question_id: str, payload: dict | None = None) -> str:
    """Return one legal label for a declared question. Undeclared questions fail."""
    if question_id not in _QUESTIONS:
        raise ValueError(f"undeclared question: {question_id}")
    policy = _POLICIES.get(question_id)
    if policy is None:
        raise ValueError(f"no policy for {question_id}")
    label = policy(payload or {})
    if label not in _QUESTIONS[question_id]:
        raise ValueError(f"illegal label for {question_id}")
    return label


def _canned_or_brief(payload: dict) -> str:
    return "brief" if payload.get("brief") is True else "canned"


def _present(payload: dict, key: str) -> bool:
    return key in payload and payload[key] not in (None, "")


def _fuel_forms(fuel) -> set[str]:
    if isinstance(fuel, bool) or not isinstance(fuel, (int, float)) or not math.isfinite(fuel):
        return set()
    if float(fuel).is_integer():
        whole = int(fuel)
        forms = {str(whole), f"{whole}.0", f"{whole},0"}
        word = _ITALIAN.get(whole)
        if word:
            forms.add(word)
        return forms
    decimal = format(float(fuel), ".6f").rstrip("0").rstrip(".")
    return {decimal, decimal.replace(".", ",")}


def _grounded_or_reject(payload: dict) -> str:
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip() or "`" in text:
        return "reject"
    tokens = [match.group(0).lower() for match in _TOKEN.finditer(text)]
    if not tokens:
        return "reject"
    # No corner or sector was passed, so a place word is invented.
    if not (_present(payload, "corner") or _present(payload, "sector")) and set(tokens) & _TRACK:
        return "reject"
    allowed = set(_REGISTER | _FUNCTION | _fuel_forms(payload.get("fuel")))
    for key in ("corner", "sector"):
        if _present(payload, key):
            allowed.update(match.group(0).lower() for match in _TOKEN.finditer(str(payload[key])))
    if any(token not in allowed for token in tokens):
        return "reject"
    return "grounded"


_POLICIES = {
    "canned_or_brief": _canned_or_brief,
    "grounded_or_reject": _grounded_or_reject,
}

declare("canned_or_brief", ("canned", "brief"))
declare("grounded_or_reject", ("grounded", "reject"))
