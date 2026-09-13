# Project Context

Last updated: 2026-09-13

## Current State

RaceEngineer has its first simulator-independent data-recovery slice in Python:
a nullable sample model, repeatable synthetic source, versioned JSONL recording
and file replay, text CLI output, and an optional UDP metadata probe.

Runtime and offline tests use only the Python standard library. Python 3.10 or
newer is required. Run instructions and recording semantics are documented in
`docs/DATA_RECOVERY.md`. Expose `src/raceengineer` through `PYTHONPATH` when
running from this tree.

The public repository is `benitz94/RaceEngineer`. English is the official
repository language. The public license is GPL-3.0-only; external contributions
require the existing CLA.

This slice does not target Raspberry Pi. Hardware references in older design
documents are historical. Development and offline validation occur on the
development PC without a simulator. No simulator protocol adapter is implemented.

## Next Objective

Select the next bounded slice with the project owner. Session state,
deterministic rules, alerts, and broader replay controls remain pending.

## Essential Files

1. `PROJECT_JOURNAL.md` — project intent and decision history.
2. `README.md` — project overview.
3. `ARCHITECTURE.md` — architectural boundaries.
4. `ROADMAP.md` — broader implementation sequence.
5. `AGENTS.md` — repository working rules.
6. `docs/DATA_RECOVERY.md` — current demo and recording format.
