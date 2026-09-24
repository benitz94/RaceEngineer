"""Deterministic typed decisions for a declared question.

This is code, not a neural model. It does not call Ollama.
"""

import re

_QUESTIONS: dict[str, tuple[str, ...]] = {}
_WORD = re.compile(r"[^\W\d_]+(?:_[^\W\d_]+)*", re.UNICODE)
_TIMESTAMP = re.compile(r"\d+\.\d+")
_LOG_WORDS = frozenset({"type", "timestamp", "format", "version", "source", "fuel_low"})
_TRACK_FIELDS = {
    "place": frozenset({
        "place", "places", "posto", "luogo",
        "sud", "nord", "est", "ovest", "south", "north", "east", "west",
    }),
    "corner": frozenset({"corner", "corners", "curva", "curve"}),
    "sector": frozenset({"sector", "sectors", "settore", "settori"}),
    "tangent": frozenset({"tangent", "tangents", "tangente", "tangenti"}),
    "straight": frozenset({"straight", "straights", "rettilineo", "rettilinei", "rettifilo"}),
    "scarica": frozenset({"scarica", "scaricare"}),
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


def _grounded_or_reject(payload: dict) -> str:
    text = payload.get("text")
    if not isinstance(text, str):
        return "reject"
    if "`" in text or _TIMESTAMP.search(text):
        return "reject"
    tokens = {match.group(0).lower() for match in _WORD.finditer(text)}
    if tokens & _LOG_WORDS:
        return "reject"
    # A place word is invented when that kind of field was not passed.
    for field, words in _TRACK_FIELDS.items():
        if not _present(payload, field) and tokens & words:
            return "reject"
    return "grounded"


_POLICIES = {
    "canned_or_brief": _canned_or_brief,
    "grounded_or_reject": _grounded_or_reject,
}

declare("canned_or_brief", ("canned", "brief"))
declare("grounded_or_reject", ("grounded", "reject"))
