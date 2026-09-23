# Typed decision model

Status: planned. Not implemented. This document records intent.

RaceEngineer will use two local inference roles. They are not the same
component.

## Roles

1. Deterministic rules (`src/raceengineer/rules.py`) remain the source of
   critical facts such as low fuel. Missing data must not invent a decision.
   Rule strings are for logs and last-resort text if the language model is
   down. They are not the voice the driver should hear in a normal session.
2. A **typed decision model** answers bounded questions with labels and
   optional probabilities. It does not generate radio speech.
3. A **language model** turns an approved alert plus session context into a
   short spoken briefing that should sound like a human race engineer.
   Current evaluation candidate: `qwen3.5:4b`. It must stay disableable for
   tests and for core operation without a GPU.

The typed decision model sits beside the language model. It must not replace
rules and it must not replace voice generation.

## When it runs

The decision model is used only on tasks where a closed label is faster or
safer than open text. If the job is already "explain this to the driver",
call the language model directly.

The concrete case list is not frozen yet. The intent is lower radio latency
and fewer invented facts, not a canned-phrase product.

A working sketch, not a contract:

1. Rules emit a structured alert (fact + machine message for the log).
2. If the task matches a declared decision question, the typed model may
   answer first (`speak`/`hold`, later cases as defined).
3. If the answer is `hold`, do not call the language model and do not speak.
4. If the answer is `speak`, or the task is a briefing outside the decision
   set, call the language model. Do not read the raw rule string on air.
5. After a generated sentence, an optional `grounded`/`reject` check may run.
   Reject drops that sentence. The log still keeps the rule text. The driver
   does not get a slogan as the intended radio style.

If the decision model is missing or times out, continue with rules plus the
language model. Do not block the session.

## Allowed question shapes

Callers declare the question and the legal answers in advance. The model
returns one of those answers. Typical first questions:

- `speak` or `hold` — whether the radio may talk now
- `grounded` or `reject` — whether a generated sentence invents telemetry

`canned` versus `brief` is not a driver-facing choice. Briefings are the
language model's job.

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
