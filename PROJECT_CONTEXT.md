# Project Context

Last updated: 2026-09-25

## Current State

Implementation of the intended Linux platform is blocked until two local
models are chosen:

1. the language model that writes short radio briefings;
2. the typed decision model that sits beside that language model and answers
   bounded questions (speak or hold, canned text or briefing, grounded or
   reject).

Both models must be free to obtain and run locally. Paid weights and paid
cloud APIs are not acceptable. Intent and constraints are in
`docs/DECISION_MODEL.md`.

Those choices determine VRAM and therefore the GPU. An AMD Radeon is the
expected family; the exact card cannot be selected yet. Without that
knowledge the target machine cannot be specified, installed, or built.
Raspberry Pi is not a target.

A small simulator-independent recovery slice already exists in Python: a
nullable sample model, repeatable synthetic source, versioned JSONL recording
and file replay, text CLI output, an optional UDP metadata probe, and a
deterministic low-fuel rule. A `fuel_low` alert also prints a versioned radio
line (`raceengineer.radio` version 1, `source: rule`) whose driver text is
"Box, box. Questo giro." The alert log message stays English.
`--speak` says each printed radio line with local Windows speech, rule line
first and the llm line when one is printed. A deterministic gate
in `src/raceengineer/decision.py` answers `canned_or_brief` and
`grounded_or_reject`. It is code, not a neural decision model. `--brief` is
the declared brief skill. When the gate answers `brief`, local Ollama
(`qwen3.5:4b`) may add a second radio line (`source: llm`) after the rule
line. A down model, an empty reply, or a `reject` label leaves the rule line
in place. A briefing that names a track place is rejected. The neural
decision model is still not chosen. That slice is not a
substitute for choosing the models. It does not define the production
hardware. Critical alerts stay in rules code; they are not delegated to
either model.

Runtime and offline tests use only the Python standard library. Python 3.10 or
newer is required. Run instructions and recording semantics are documented in
`docs/DATA_RECOVERY.md`. Expose `src/raceengineer` through `PYTHONPATH` when
running from this tree.

The public repository is `benitz94/RaceEngineer`. English is the official
repository language. The public license is GPL-3.0-only; external contributions
require the existing CLA.

Development of further platform work waits on the model decision. No simulator
protocol adapter is implemented.

## Next Objective

Choose a free local language model and a free local typed decision model,
document their VRAM needs, and from that select the AMD Radeon card.
Contributors should help with that selection before proposing unrelated
feature work. Evaluation may start from a 4B-class local checkpoint already
used for short speech, with a smaller decision head if it fits the same GPU.

## Essential Files

1. `PROJECT_JOURNAL.md` — project intent and decision history.
2. `README.md` — project overview.
3. `ARCHITECTURE.md` — architectural boundaries.
4. `ROADMAP.md` — broader implementation sequence.
5. `AGENTS.md` — repository working rules.
6. `docs/DATA_RECOVERY.md` — current demo and recording format.
7. `docs/DECISION_MODEL.md` — planned typed decision model beside the LLM.
8. `docs/RADIO_PHRASES.md` — pit-wall phrase book for language-model training.
