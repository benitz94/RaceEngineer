# Project Context

Last updated: 2026-09-16

## Current State

RaceEngineer has its first simulator-independent data-recovery slice in Python:
a nullable sample model, repeatable synthetic source, versioned JSONL recording
and file replay, text CLI output, and an optional UDP metadata probe.

A deterministic rules engine tracks the last valid fuel and lap and suppresses
repeated low-fuel alerts. Valid fuel at or below the configurable 10.0-litre
default triggers a structured alert; valid fuel above 12.0 litres or an explicit
source restart resets suppression. Missing or invalid fuel does not trigger.
Synthetic and file CLI modes print samples and alerts by default, with
`--alerts-only` and `--samples-only` output options. Sample JSONL stays version 1;
sample-only output remains replayable. The default synthetic scenario crosses
the low-fuel threshold. UDP remains a metadata probe only.

Runtime and offline tests use only the Python standard library. Python 3.10 or
newer is required. Run instructions and recording semantics are documented in
`docs/DATA_RECOVERY.md`. Expose `src/raceengineer` through `PYTHONPATH` when
running from this tree.

The `exp/llm-sidecar` branch adds an optional local LLM briefing adapter,
disabled by default and separate from deterministic rules. On this machine,
use `python3`. The owner stopped the broader model benchmark; only the
installed `llama3.2:3b` remains in scope. Three measured generations are in
`tools/bench_stdout.csv`, with methodology and factual failures documented
in `docs/LLM_SIDECAR_NOTES.md`. The benchmark tool does not download models.
No further downloads or tests are authorized by the current instruction.
Cleanup of the cancelled partial download in service-owned Ollama storage
requires administrative access. The 21 existing tests passed before work
was stopped; deterministic rules and the sample pipeline are unchanged.

The public repository is `benitz94/RaceEngineer`. English is the official
repository language. The public license is GPL-3.0-only; external contributions
require the existing CLA.

This slice does not target Raspberry Pi. Hardware references in older design
documents are historical. Development and offline validation occur on the
development PC without a simulator. No simulator protocol adapter is implemented.

## Next Objective

Select the next bounded slice with the project owner. Broader session lifecycle
handling, additional rules, alert delivery, and replay controls remain pending.

## Essential Files

1. `PROJECT_JOURNAL.md` — project intent and decision history.
2. `README.md` — project overview.
3. `ARCHITECTURE.md` — architectural boundaries.
4. `ROADMAP.md` — broader implementation sequence.
5. `AGENTS.md` — repository working rules.
6. `docs/DATA_RECOVERY.md` — current demo and recording format.
