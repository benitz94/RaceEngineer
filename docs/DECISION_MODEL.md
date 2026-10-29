# Istinto, the engineer's supporting mind

Istinto is the name of RaceEngineer's typed decision model. It is not a minor
component: it makes the fast decisions that let the engineer's voice answer
quickly and correctly.

Status: neural weights selected for the 6 GB bench, grammar path not
implemented. Jev-style decision models in Ollama are the leading candidate
runtime for the new reference machine (see below). Deterministic
code in `src/raceengineer/decision.py` answers each declared question in the
model's place until then.

Selected decision checkpoint: `qwen3.5:0.8b` (Q8_0, Apache-2.0), used only as a
constrained classifier (GBNF or a JSON enum of the declared labels).
Unconstrained text from this checkpoint is not a radio path. The engineer's
voice is `qwen3.5:4b`. See `docs/MODEL_SELECTION.md`.

## Roles

1. Deterministic rules (`src/raceengineer/rules.py`) detect events such as low
   fuel. Missing data must not invent an event. Fuel level, validity, and
   hysteresis stay here. Rules do not speak.
2. **Istinto**, the typed decision model, answers bounded questions with labels. It
   decides whether the engineer speaks, how urgent the call is, and whether
   there is room for a longer message or a question to the driver. It does
   not write radio text.
3. The **language model** is the engineer's voice. It writes every radio line
   in its own words. The phrase book in `docs/RADIO_PHRASES.md` is its
   baggage: it shows how a call is built and is never aired as written.

## Declared questions

Implemented, answered by deterministic code for now:

- `urgency` — `now`, `normal`, or `calm`. It sets how long the engineer may
  take to find his words: 1, 3, and 6 seconds, starting values to measure on
  the reference machine. A `high` priority alert is `now`.
- `grounded_or_reject` — whether a generated line invents telemetry or reads
  like a log. `reject` drops the line.

Planned, not declared in code yet:

- `speak` / `hold` — whether the radio may open now;
- long / short — whether there is room for a longer message or a question to
  the driver.

## Flow

1. Rules emit a structured alert.
2. The decision model answers `urgency`.
3. The language model writes the line within the urgency deadline.
4. `grounded_or_reject` checks it, then the radio output filters run.
5. An accepted line is printed and spoken.

There is no canned fallback. A missing model, a timeout, or a rejected line
leaves the radio silent. The failure goes to stderr and the run exits
nonzero, so it is fixed rather than hidden. Telemetry analysis continues.

A local check of `qwen3.5:4b` on fuel 10.0 / `fuel_low` returned in 0.98 s and
invented a corner. That is why every line passes `grounded_or_reject`.

## Candidate runtime: Jev-style decision models

Since Ollama 0.35 (announced 2026-09-29), Ollama serves decision models that
return typed answers with probabilities instead of text, through
`POST /v1/systemone` on the local server. This matches Istinto's role and is
the leading candidate for its runtime on the new reference machine. Nothing
here is implemented or measured yet.

One request carries a `state` and several named `questions`, and the model
answers them all at once. Question types:

- `choice` — one label from declared `criteria`, with per-label
  `probabilities` and a `confidence`;
- `noul` — a yes/no answer as a probability between 0 and 1;
- `score` — a value on a declared ordered scale, with `probabilities` and a
  `confidence`.

Sketch of an Istinto request for a low-fuel alert (shape only, not final):

```json
{
  "model": "tev1:0.8b",
  "state": {"event": "fuel_low", "fuel": 10.0, "lap": 14, "position": 3},
  "questions": {
    "urgency": {
      "type": "choice",
      "instructions": "How fast must the engineer speak?",
      "criteria": {"now": "Act this lap", "normal": "Soon", "calm": "Can wait"}
    },
    "speak": {"type": "noul", "instructions": "Should the radio open now?"},
    "length": {
      "type": "choice",
      "instructions": "How much should the engineer say?",
      "criteria": {"short": "One short call", "long": "A fuller message", "ask": "Ask the driver"}
    }
  }
}
```

After the voice writes a line, a second request can ask `grounded` as a
`noul`: does the line state anything that is not in `state`?

How the answers would be used:

- an answer outside the declared criteria is treated as a failure;
- a low `confidence` makes the engineer cautious: hold, or keep it short;
- the call is plain HTTP and JSON, so it needs only the Python standard
  library, like the voice; the TypeSafe SDK is not required;
- `src/raceengineer/decision.py` keeps the same questions; only who answers
  them changes.

Candidates published with the feature:

| Model | Size | Source | Notes |
| --- | --- | --- | --- |
| `nimble` | 9B | Bespoke Labs | described as open source; licence to confirm |
| `tev1` | 4B | Together AI | experimental; licence to confirm |
| `tev1:0.8b` | 0.8B | Together AI | experimental; licence to confirm |

Ollama reports about 91 ms per decision for `nimble` on a MacBook Pro M5 Max.
That is not RaceEngineer evidence.

Before selection:

- confirm each licence allows free local use;
- measure VRAM, latency, and accuracy on the reference machine, on race
  questions, with the evaluation harness updated to the current flow;
- compare with a general model constrained by an Ollama JSON schema
  (`format`), for example the current `qwen3.5:0.8b`;
- remember that a typed answer guarantees the format, not that the decision
  is right.

Source: https://ollama.com/blog/ollama-now-supports-jev-style-decision-models

## Constraints

- Free weights only. Local inference only. Apache-2.0 for the selected pair.
- The 0.8B checkpoint shares a GPU with `qwen3.5:4b`. Product floor is 8 GB
  VRAM minimum and 12 GB recommended. A 6 GB card is a development bench only.
- Do not route fuel, validity, or hysteresis through either model.
- Do not import product architecture from other private repositories.

## Out of scope for the current slice

Training a new foundation model, cloud routers, desktop UI, simulator decode,
speech recognition, and race-to-race memory. Speech recognition with a
physical push-to-talk button and memory are planned next.
