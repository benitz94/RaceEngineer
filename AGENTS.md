# AGENTS.md

## Session Start

Before performing any work, read the documents in the following order:

1. `PROJECT_CONTEXT.md`;
2. `PROJECT_JOURNAL.md`;
3. `README.md`;
4. `ARCHITECTURE.md`;
5. `ROADMAP.md`;
6. `AGENTS.md`.

This order provides an understanding of the current operational state first,
followed by the historical rationale, the product, the architecture, the
roadmap, and finally the operating rules.

## Project Rules

1. Treat `PROJECT_JOURNAL.md` as the source of truth for the project's intent
   and decisions.
2. Do not modify files until the user has approved the proposed plan.
3. Do not invent requirements.
4. Keep RaceEngineer independent from the private AI Desktop Companion project.
5. Keep only the current operational state in `PROJECT_CONTEXT.md`; do not turn
   it into a journal or cumulative changelog.
6. Do not record file-level change details in `PROJECT_JOURNAL.md`, because Git
   preserves the technical history.

## Repository Language

The official language of this repository is English.

All documentation, comments, commit messages, and Markdown files must be
written in English.

Discussions with the project owner may take place in Italian, but every file
committed to the repository must remain in English.

## Session End

At the end of every development session, the agent must:

1. update `PROJECT_CONTEXT.md`, replacing information that is no longer
   current;
2. update the last-updated date in `PROJECT_CONTEXT.md`;
3. if the session produced new project decisions, important new ideas, or a
   change in direction, also propose an update to `PROJECT_JOURNAL.md`;
4. not update `PROJECT_JOURNAL.md` when the only changes are code changes,
   refactoring, bug fixes, or technical implementations;
5. always wait for user approval before modifying `PROJECT_JOURNAL.md`.
