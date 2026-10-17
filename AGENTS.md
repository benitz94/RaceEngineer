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
4. Keep RaceEngineer independent of unrelated private projects and runtimes.
5. Keep only the current operational state in `PROJECT_CONTEXT.md`; do not turn
   it into a journal or cumulative changelog.
6. Do not record file-level change details in `PROJECT_JOURNAL.md`, because Git
   preserves the technical history.

## Orchestrated Multi-Agent Development

After the session-start reads above, use these documents for orchestrated
multi-agent development:

- [Working domain](docs/agents/domain.md) — RaceEngineer invariants and boundaries.
- [Issue tracker](docs/agents/issue-tracker.md) — bounded tickets and publication approval.
- [Triage labels](docs/agents/triage-labels.md) — proposed label taxonomy only.

These documents extend existing governance. The project rules in this file
take precedence over conflicting generic orchestration guidance;
`PROJECT_JOURNAL.md` remains authoritative for project intent and decisions.

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


## Installed coding-agent skills

This project has local Matt Pocock skills in `.agents/skills`. Consult the names
in `.agents/matt-pocock-install.json` and read the relevant skill's `SKILL.md`
before applying it. Preserve user-invoked skill boundaries; planning, TDD and
review workflows come from Matt's collection when enabled.

Selected ECC skills are listed with their intended use in `.agents/ecc-README.md`.
Read and apply relevant `.agents/skills/<name>/SKILL.md` guidance for the current
task, including supporting references when needed. These skills apply to coding
agents regardless of model/provider; do not assume the host discovers them
without reading this project's instructions.

Preserve existing project rules, assigned roles, dependency policies and user
authorization. Examples do not authorize new dependencies, commits, publishing,
services, device commands or other side effects. Adapt guidance to the existing
stack and supported runtime versions. Do not load another project's skill set.

When this project is selected in Planwharf, its installed ECC instructions are
supplied to leads and workers across providers, including isolated research
workers. The Matt checkbox controls Matt skills only; ECC availability follows
this project's local installation.


## Portable skills and session-start update check

After the required project documentation reads, at the start of each working
session, read `.agents/README.md` and inspect `.agents/SKILLS.md`. Run
`python .agents/check-updates.py` from the project root (use `python3` or
`py -3` if appropriate for the environment). Report available upstream changes
and local differences briefly. If Python, network access, or GitHub is
unavailable, report the check as unavailable; never claim the skills are current.
The check is read-only. Do not install updates or overwrite local adaptations
without user authorization. Do not re-run it for every message in one session.

Skills in `.agents/skills/` are available to every agent/provider working on
this checkout. Read the relevant `SKILL.md` before using a skill, including its
supporting references when needed. Availability does not override explicit
user invocation requirements, project rules, permissions, or host controls.
Keep `.agents/`, this file, and the agent instruction entry points in version
control, including source manifests and third-party license notices. An agent
that does not load repository instructions must be explicitly directed to
`AGENTS.md` and `.agents/SKILLS.md` in its initial task prompt.
