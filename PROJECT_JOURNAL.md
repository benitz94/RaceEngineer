# PROJECT_JOURNAL.md

## Decision Model Intervenes by Skill — 2026-09-23

Decision:

The typed decision model is a control layer. It runs only when a caller has
declared one of its skills and that skill is the job. It is not called on
every sample and it does not speak on the radio.

Skills remain the declared questions: speak/hold, canned/brief, and
grounded/reject. Fuel level, validity, and hysteresis stay in deterministic
rules. A critical rule alert already has its sentence, and that sentence is
the radio call. The language model rewrites it only after a declared skill
has answered brief on a task where a briefing is allowed.

A local timing check of qwen3.5:4b showed the failure this rule stops: a fast
reply that invented a corner instead of the fuel call. Speed without a
declared skill is not a radio path.

If the decision model is missing or times out, rules continue, and the
language model continues only for a briefing that was already approved. The
session does not block.

## Typed Decision Model Beside the LLM — 2026-09-23

Decision:

RaceEngineer will add a local typed decision model beside the language model.
The language model writes short radio briefings. The decision model answers
only declared questions such as speak/hold, canned/brief, and grounded/reject.
Deterministic rules keep critical alerts. Both models must be free and local.
Paid cloud decision APIs are out of scope. Intent lives in
`docs/DECISION_MODEL.md`. No implementation in this change.

## First Deterministic Fuel Rule — 2026-09-13

The sample pipeline now produces a structured low-fuel alert from explicitly
valid observations. Hysteresis suppresses repeated alerts until valid fuel
recovers or the source restarts, preserving predictable behavior without
inventing decisions from missing data. Synthetic and recorded input validate
the rule offline; sample recordings retain their existing format.

## First Data-Recovery Slice — 2026-09-13

The first simulator-independent recovery pipeline has landed: nullable telemetry
samples, repeatable synthetic input, versioned local recordings and file replay,
and text output, validated offline. An optional UDP probe reports transport
metadata only. This bounded slice establishes reproducible acquisition before
session analysis or simulator integration; it does not target Raspberry Pi or
introduce simulator protocol decoding.
