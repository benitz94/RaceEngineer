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
   into a short spoken sentence. It must be disableable.

The typed decision model sits beside the language model. It must not replace
rules and it must not replace voice generation.

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
  model (current evaluation candidate for speech: `qwen3.5:4b`). A dedicated
  0.8B–4B decision checkpoint is acceptable if it fits the same card.
- Do not route fuel, validity, or hysteresis through this model.
- Do not import product architecture from other private repositories.

## Out of scope for the first slice

Training a new foundation model, cloud routers, desktop UI, and simulator
decode.
