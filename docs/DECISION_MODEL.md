# Typed decision model

Status: planned. Not implemented. This document records intent.

RaceEngineer will use two local inference roles. They are not the same
component.

## Roles

1. Deterministic rules (`src/raceengineer/rules.py`) remain the source of
   critical alerts such as low fuel. Missing data must not invent a decision.
   Fuel level, validity, and hysteresis stay here. A critical rule alert
   already has its sentence; that sentence is the radio call.
2. A **typed decision model** is a control layer. It answers bounded questions
   with labels and optional probabilities. It does not generate radio speech.
3. A **language model** may write a short briefing only after a declared skill
   has answered `brief` on a task where a briefing is allowed. Current
   evaluation candidate: `qwen3.5:4b`. It must stay disableable.

The typed decision model sits beside the language model. It must not replace
rules and it must not replace voice generation.

## When it runs

The decision model runs only when a caller has declared one of its skills and
that skill is the job. No declared question, no call. It is not invoked on
every sample.

Skills:

- `speak` / `hold` — whether the radio may open, when the moment is not
  already decided by rules
- `canned` / `brief` — whether the existing rule sentence is enough or a
  briefing is allowed
- `grounded` / `reject` — whether a generated sentence invents telemetry

Working sketch:

1. Rules emit a structured alert, including the rule sentence.
2. If no decision skill is declared for this task, do not call the decision
   model. A critical alert goes on the radio as the rule sentence. Do not
   send it to the language model by default.
3. If `speak`/`hold` is declared and the answer is `hold`, do not speak.
4. If `canned`/`brief` is declared and the answer is `canned`, speak the rule
   sentence. If the answer is `brief` and a briefing is allowed for that task,
   call the language model.
5. After a generated sentence, if `grounded`/`reject` is declared, reject
   drops that sentence. The rule sentence remains available.

A local check of `qwen3.5:4b` on fuel 10.0 / `fuel_low` returned in 0.98 s and
invented a corner. Speed without a declared skill is not a radio path. The
rule sentence "Fuel low. Box this lap." was already the control.

If the decision model is missing or times out, the session continues with
rules. The language model continues only for a briefing that was already
approved. The session does not block.

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
