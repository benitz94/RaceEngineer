# Proposed RaceEngineer triage labels

This is a proposed taxonomy only. No GitHub labels are created or changed by
this document. Before any approved label publication, inspect existing labels
and reuse equivalent names where possible rather than duplicating them.
Follow [issue-tracker.md](issue-tracker.md) for ticket approval and
[orchestration.md](orchestration.md) for external-action control.

| Category | Proposed labels | Use |
| --- | --- | --- |
| Type | `type:bug`, `type:feature`, `type:docs`, `type:maintenance` | Defect, approved behavior addition, documentation, or verification/refactoring/tooling work respectively. Choose one primary type. |
| Area | `area:core`, `area:telemetry`, `area:output`, `area:models`, `area:platform`, `area:workflow` | Deterministic rules/session state; sources/adapters/recording/replay; radio/TTS/output; optional models/evaluation; hardware/Linux qualification; development governance/tooling. Apply only relevant areas. |
| Priority | `priority:high`, `priority:normal`, `priority:low` | User-approved urgency/order. Normal is the default proposal; high/low need a stated rationale. |
| Blocking | `status:blocked` | A concrete unresolved dependency, approval, or decision prevents progress. State the blocker and condition for resuming in the ticket. |

Labels do not approve scope, worker selection, cost, or execution. Do not infer
product requirements from a label. Use Issue open/closed state and evidence
reports for completion rather than adding redundant completion labels.
Do not add per-model, per-agent, per-gate, or speculative simulator labels
without a concrete tracking need and user approval.
