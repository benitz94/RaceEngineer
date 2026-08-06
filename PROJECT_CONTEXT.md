# PROJECT_CONTEXT.md

Last updated:
2026-08-06

## Current Phase

Phase 0 — Project Documentation and Foundations.

The project is still in the design phase. No code has been written, and no
executable prototype exists yet.

## Outcome of the Latest Session

The contents of the following files have been defined, approved, and translated
into the repository's official language, English:

- `README.md`;
- `ARCHITECTURE.md`;
- `ROADMAP.md`;
- `PROJECT_CONTEXT.md`;
- `PROJECT_JOURNAL.md`;
- `AGENTS.md`.

The following decisions have been confirmed:

- local operation without mandatory cloud services;
- a deterministic core independent of LLMs and simulators;
- Python as the initial technology, with the future option of replacing
  individual modules with C++ or Rust;
- Raspberry Pi 3B+ as the initial reference hardware;
- initial development using synthetic and recorded telemetry;
- stability, reliability, and responsiveness before additional features;
- Gran Turismo 7 as a candidate to be evaluated, not yet a requirement;
- English as the official repository language for all committed files.

No code has been written.

## Next Session

Complete the remaining decisions required to close Phase 0.

## Open Decisions

- Open-source license.
- Python runtime environment.
- Initial operating system.
- Initial project structure.
- Initial libraries.
- Internal telemetry schema.
- Recording format.
- First deterministic prototype rule.
- Local TTS engine.
- Quantitative performance criteria.
- Initial simulator, following technical evaluation.
- Final distribution method: ready-to-use image or installer.

## Issues or Blockers

- Gran Turismo 7 has not yet been technically evaluated.
- Actual core performance on the Raspberry Pi 3B+ has not yet been measured.
- Implementation must not begin before the documentation planned for Phase 0
  is complete.
- There are currently no other known technical blockers.

## Essential Documents to Read

1. `PROJECT_CONTEXT.md` — current operational state.
2. `PROJECT_JOURNAL.md` — intent, decisions, and historical rationale.
3. `README.md` — project vision, goals, and principles.
4. `ARCHITECTURE.md` — system components, boundaries, and flows.
5. `ROADMAP.md` — phases and completion criteria.
6. `AGENTS.md` — repository operating rules.
