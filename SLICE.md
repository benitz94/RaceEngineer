# Slice pin — programmatic replay pause, resume, and stop

Pinned: 2026-10-10

Job: Continue: docs: state replay pause and resume are programmatic only

This slice: Inspect uncommitted changes, docs, and pin the slice

Status: pinned

Baseline commit: `b6a603d` (`docs: state replay pause and resume are programmatic only`)

Branch: `main` (matches `origin/main`)

## Inspection

HEAD is documentation only. It touches `ARCHITECTURE.md`, `PROJECT_CONTEXT.md`,
`ROADMAP.md`, and `docs/DATA_RECOVERY.md`. It states that replay pause and
resume are programmatic (`ReplaySession.pause` / `ReplaySession.resume` in
`src/raceengineer/sources.py`) and that the demo has no `--pause` or
`--resume` flag. Ctrl+C is the process-level stop. HEAD `sources.py` has
`pause` and `resume` and does not define `stop`. HEAD tests cover pause and
resume and do not cover stop or CLI-flag absence.

The uncommitted working tree continues that job. It adds `ReplaySession.stop`,
treats stop as programmatic like pause and resume, and keeps the demo without
`--pause`, `--resume`, or `--stop`.

Uncommitted tracked files at pin time:

- `ARCHITECTURE.md`
- `PROJECT_CONTEXT.md`
- `ROADMAP.md`
- `docs/DATA_RECOVERY.md`
- `src/raceengineer/sources.py`
- `tests/test_recovery.py`

Untracked working file for this pin:

- `SLICE.md`

Untracked artifacts left untouched:

- `eval_runs/`
- `eval_runs_v2/`
- `tools/bench_llm.log`

`demo.py` still delivers file replay through `paced(replay(path), rate)`.
It does not import or construct `ReplaySession`. Help and argparse expose
no pause, resume, or stop flags. Verified at pin time:

- `python -m raceengineer.demo --help` lists no `--pause`, `--resume`, or
  `--stop`
- `python -m raceengineer.demo --source synthetic --pause` is
  `unrecognized arguments: --pause`
- the same unrecognized-argument error for `--resume` and `--stop`

Docs distinguish Ctrl+C process stop from programmatic
`ReplaySession.stop` in `docs/DATA_RECOVERY.md`, `ARCHITECTURE.md`,
`ROADMAP.md`, and `PROJECT_CONTEXT.md`. Those files also name the three
methods and state the demo has no `--pause`, `--resume`, or `--stop` flag.
`README.md` does not mention these controls.

Pin tests in `tests/test_recovery.py` passed (`python -m unittest
tests.test_recovery -v`, 25 tests).

## Bounded outcome

Keep the documented contract: pause, resume, and stop are
`ReplaySession` methods. They are not demo CLI flags. Do not add
`--pause`, `--resume`, or `--stop`.

Allowed files:

- `src/raceengineer/sources.py` (`ReplaySession.pause` / `resume` / `stop`)
- `tests/test_recovery.py`
- `docs/DATA_RECOVERY.md`
- `ARCHITECTURE.md`
- `ROADMAP.md`
- `PROJECT_CONTEXT.md` (operational state only)
- `SLICE.md` (this pin)

## Out of scope

- Wiring `ReplaySession` into `demo.py`
- Driver-facing or CLI pause, resume, or stop
- Replay speed-control flags
- `PROJECT_JOURNAL.md`
- `eval_runs/`, `eval_runs_v2/`, `tools/bench_llm.log`
- Simulator adapters, music, Engineer Profiles, GT7/F1 protocol work
- Commits, push, pull requests, GitHub Issues

## Acceptance

- Docs name `ReplaySession.pause`, `ReplaySession.resume`, and
  `ReplaySession.stop` in `src/raceengineer/sources.py`.
- Docs state the demo has no `--pause`, `--resume`, or `--stop` flag.
- Docs distinguish Ctrl+C process stop from programmatic
  `ReplaySession.stop`.
- `python -m raceengineer.demo --help` does not list those flags.
- Passing those flags is an unrecognized-argument error.
- Existing pause, resume, and stop `ReplaySession` tests remain green.
- Demo file replay stays on `paced`/`replay`, not `ReplaySession`.

## Pin tests

- `test_demo_has_no_pause_resume_or_stop_cli_flags`
- `test_replay_session_exposes_programmatic_pause_resume_and_stop`
- `test_demo_file_replay_stays_on_paced_replay_not_session`
- `test_docs_state_replay_pause_resume_and_stop_are_programmatic_only`
- existing `ReplaySession` pause, resume, and stop tests in
  `tests/test_recovery.py`

## Stop conditions

Stop if the work would add CLI controls, change recording format, or
touch protected untracked artifacts. Do not invent GT7, F1, or music
requirements.
