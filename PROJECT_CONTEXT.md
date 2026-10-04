# Project Context

Last updated: 2026-10-03

## Current State

The two local models are selected:

1. `qwen3.5:4b` (Q4_K_M) for short radio briefings;
2. `qwen3.5:0.8b` (Q8_0) for typed decisions, constrained classification only.

Both models must be free to obtain and run locally. Paid weights and paid
cloud APIs are not acceptable. Intent and constraints are in
`docs/DECISION_MODEL.md`.

Product VRAM guidance is 8 GB minimum and 12 GB recommended. The intended
platform remains Linux with an AMD Radeon. The exact SKU, Radeon qualification,
and final reference-machine configuration remain unresolved. Windows/RTX 3050
measurements are development evidence only and do not qualify Radeon. See
`docs/MODEL_SELECTION.md`. Raspberry Pi is not a target.

A small simulator-independent recovery slice already exists in Python: a
nullable sample model, repeatable synthetic source, versioned JSONL recording
and file replay, text CLI output, an optional UDP metadata probe, and a
deterministic low-fuel rule. A `fuel_low` alert also prints a versioned radio
line (`raceengineer.radio` version 1, `source: rule`) whose driver text is
"Box, box. Questo giro." The alert log message stays English.
`--speak` says each printed radio line with local Piper Italian when the
selected `it_IT` model is installed, and otherwise Windows speech, rule line first and
the llm line when one is printed. `--voice` selects Paola, Riccardo, Serena,
or Dii. The default spoken voice is Serena. Engineer Profiles are not implemented. A deterministic gate
in `src/raceengineer/decision.py` answers `canned_or_brief` and
`grounded_or_reject`. It is code, not a neural decision model. `--brief` is
the declared brief skill. When the gate answers `brief`, local Ollama
(`qwen3.5:4b`, temperature 0) may add a second radio line (`source: llm`)
after the rule line. A rejected line is tried once more. A down model, an empty reply, or a `reject` label leaves the rule line
in place. A briefing that names a track place, or that reads like a log,
is rejected. Ordinary Italian is kept. The selected neural decision model's
grammar-constrained path is not implemented; the current gate remains
deterministic. The recovery slice does not define the production
hardware. Critical alerts stay in rules code; they are not delegated to
either model.

Runtime and offline tests use only the Python standard library. Python 3.10 or
newer is required. Run instructions and recording semantics are documented in
`docs/DATA_RECOVERY.md`. Expose `src/raceengineer` through `PYTHONPATH` when
running from this tree.

An offline GitHub Actions regression workflow validates the supported Ubuntu
and Windows Python/OS matrix.

The public repository is `benitz94/RaceEngineer`. English is the official
repository language. The public license is GPL-3.0-only; external contributions
require the existing CLA.

Model selection is established; hardware/platform qualification remains open.
No simulator protocol adapter is implemented.

## Next Objective

Qualify the selected pair on Linux/AMD Radeon, select the exact Radeon SKU,
and define the reference-machine configuration using the documented VRAM
guidance. Quantitative performance thresholds remain to be established.
Contributors should help with this hardware/platform work before proposing
unrelated feature work.

## Essential Files

1. `PROJECT_JOURNAL.md` — project intent and decision history.
2. `README.md` — project overview.
3. `ARCHITECTURE.md` — architectural boundaries.
4. `ROADMAP.md` — broader implementation sequence.
5. `AGENTS.md` — repository working rules.
6. `docs/DATA_RECOVERY.md` — current demo and recording format.
7. `docs/DECISION_MODEL.md` — planned typed decision model beside the LLM.
8. `docs/RADIO_PHRASES.md` — pit-wall phrase book for language-model training.
