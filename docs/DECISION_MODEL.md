# Typed decision model

Status: planned. Not implemented. This document records intent.

RaceEngineer will use two local inference roles. They are not the same
component.

## Roles

1. Deterministic rules (`src/raceengineer/rules.py`) remain the source of
   critical alerts such as low fuel. Missing data must not invent a decision.
2. A **typed decision model** answers bounded questions with labels and
   optional probabilities. It does not generate radio speech.
3. A **language model** turns an already-approved alert or briefing request
   into a short spoken sentence. Current evaluation candidate: `qwen3.5:4b`.
   It must be disableable.

The typed decision model sits beside the language model. It must not replace
rules and it must not replace voice generation.

## When it runs

The decision model is used only on tasks where a closed label is faster or
safer than open text. Otherwise the language model is called directly.

The concrete case list is not frozen yet. The intent is to cut radio latency:
skip the language model when a short label is enough; skip the decision model
when the job is already a briefing.

A working sketch, not a contract:

1. Rules emit a structured alert.
2. If the task matches a declared decision question, the typed model answers
   first (`speak`/`hold`, `canned`/`brief`, later cases as defined).
3. If the answer is `hold` or `canned`, do not call the language model.
4. If the answer is `brief`, or the task is outside the decision set, call
   the language model.
5. After a generated sentence, an optional `grounded`/`reject` check may run.
   Reject drops the sentence; the canned rule text remains available.

If the decision model is missing or times out, continue with rules plus the
language model. Do not block the session.

## Allowed question shapes

Callers declare the question and the legal answers in advance. The model
returns one of those answers. Typical first questions:

- `speak` or `hold` — whether the radio may talk now
- `canned` or `brief` — fixed rule text versus a language-model briefing
- `grounded` or `reject` — whether a generated sentence invents telemetry

Implementation may use yes/no, a fixed choice list, or an ordered score. The
wire format is an internal RaceEngineer concern. Do not depend on a paid
cloud decision API.

## Constraints

- Free weights only. Local inference only.
- Offline session operation must keep working if this model is absent.
- Prefer a small checkpoint that can share a GPU with a 4B-class language
  model. A dedicated 0.8B–4B decision checkpoint is acceptable if it fits
  the same card.
- Do not route fuel, validity, or hysteresis through this model.
- Do not import product architecture from other private repositories.

## Out of scope for the first slice

Training a new foundation model, cloud routers, desktop UI, and simulator
decode.
