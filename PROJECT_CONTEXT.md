# Project Context

Last updated: 2026-09-23

## Current State

Implementation of the intended Linux platform is blocked until two local
models are chosen:

1. the LLM;
2. the Jev-like AI model that sits beside the race engineer for decision
   support.

Both models must be free to obtain and run locally. Paid weights and paid
cloud APIs are not acceptable.

Those choices determine VRAM and therefore the GPU. An AMD Radeon is the
expected family; the exact card cannot be selected yet. Without that
knowledge the target machine cannot be specified, installed, or built.
Raspberry Pi is not a target.

A small simulator-independent recovery slice already exists in Python: a
nullable sample model, repeatable synthetic source, versioned JSONL recording
and file replay, text CLI output, an optional UDP metadata probe, and a
deterministic low-fuel rule. That slice is not a substitute for choosing the
models. It does not define the production hardware.

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

Choose a free local LLM and a free Jev-like companion model, document their
VRAM needs, and from that select the AMD Radeon card. Contributors should help
with that selection before proposing unrelated feature work.

## Essential Files

1. `PROJECT_JOURNAL.md` — project intent and decision history.
2. `README.md` — project overview.
3. `ARCHITECTURE.md` — architectural boundaries.
4. `ROADMAP.md` — broader implementation sequence.
5. `AGENTS.md` — repository working rules.
6. `docs/DATA_RECOVERY.md` — current demo and recording format.
