# NPC multi-agent orchestration

This development workflow extends [AGENTS.md](../../AGENTS.md); existing
RaceEngineer rules take precedence. The journal remains authoritative for
intent and decisions. Read [domain.md](domain.md) for project invariants and
[issue-tracker.md](issue-tracker.md) for specification and ticket control.
These documents define responsibilities, not installed integrations or
authorization to invoke every named service.

## Roles and worker selection

| Role | Responsibility and limits |
| --- | --- |
| Matt Pocock skills | Before implementation, when requirements are not already approved and bounded: grill/clarify requirements, expose assumptions, write design documentation, and produce a specification for user approval. After specification approval, propose bounded tickets. Never implement features, silently choose product requirements, or publish Issues without approval. |
| Astra orchestrator | Read approved specs/tickets, inspect the repository, propose execution order, select and explain workers, enforce scope, monitor work, require evidence, inspect diffs/checks, and stop at gates. Report blockers and scope changes. |
| GPT-6 Luna | Default worker for repository exploration, routine coding, small/medium implementation, tests, debugging, focused repair, evidence gathering, and documentation implementation. |
| Grok Build | Scarce premium implementation worker, subject to the specific escalation approval below. Never invoked automatically. |
| Fresh GPT-6 Astra reviewer | Independent read-only review after meaningful implementation/checkpoints. Inspect actual evidence rather than trusting the worker report. |
| Antigravity/Gemini | Optional independent second opinion only when genuinely useful and explicitly authorized, through included existing-subscription usage. Never automatic and never through a paid API. |
| MiMo | Manual and outside orchestration. Never assign work automatically. |

Normal requirements flow:

requirements -> Matt design -> user-approved specification -> proposed bounded
tickets -> user approval of ticket contents/order -> approved bounded tickets.
GitHub publication is a separately authorized external action. An already
approved, sufficiently bounded requirement need not be redesigned by Matt.

## NPC: zero new cost

NPC means "NON PAGO UN CAZZO". Use local/free/open-source tools or usage
already included in subscriptions the user already has. No paid APIs,
pay-as-you-go usage, extra credits, new paid services, or new subscriptions.
Check coverage before selecting a service. If an action may add cost, or
coverage cannot be established, stop and report; do not proceed on assumption.
User escalation approval does not waive NPC.

## Before implementation

1. Inspect Git status and branch. Identify tracked modifications and untracked
   user artifacts; preserve them and establish the task's starting baseline.
2. Analyze the approved bounded task, relevant files, acceptance criteria,
   dependencies, assumptions, and applicable domain invariants.
3. Show a numbered execution plan with allowed files, verification, and
   checkpoint boundaries.
4. State the worker for every part, including review, and explain each
   assignment. Luna is the default worker.
5. Explicitly identify any possible Grok candidate and the concrete reason, or
   state that there is none. Identification is not invocation approval.
6. Wait for user approval of this execution plan before implementation.

Approval applies to the stated bounded work. High-level roadmap approval is
never permission to execute all remaining work unattended. Do not repeatedly
request approval already granted for an unchanged plan, but stop at its
checkpoints and obtain approval for new scope or controlled actions.

Assign each worker a bounded objective, allowed files, exclusions, acceptance
criteria, expected evidence, and stop conditions. Coordinate overlapping file
ownership before parallel edits. No worker may expand scope on its own.

## Grok escalation

Stop when escalation appears justified and present a specific proposal. All
of the following are required before invoking Grok Build:

- a concrete difficult implementation problem with bounded scope;
- exact relevant files and acceptance criteria;
- Luna inspection or an attempted solution where appropriate;
- a concrete explanation of why Grok is likely to add value;
- established coverage by an existing user subscription, with no extra cost;
- explicit user approval of this particular escalation.

Never use Grok for brainstorming, planning, repository discovery, summaries,
simple tests, routine review, ordinary documentation, or trivial coding.

## Execution, visibility, and stopping

Execute incrementally within the approved plan. Report worker start and
finish, tests/checks start and finish, reviewer start and verdict, blockers,
and scope changes. Name the worker/task, relevant result, and next checkpoint.
Never report a check as passing before inspecting its result.

If a worker appears inactive for approximately 90 seconds, report that it may
be stalled and state what is being checked (worker status, pending tool call,
or available output). Inactivity is not proof of failure or completion; do not
silently duplicate its work or escalate it.

Stop immediately and report when scope materially expands, architecture needs
a new decision, assumptions become invalid, a paid resource appears necessary,
Grok escalation appears justified, or destructive/external action becomes
necessary. Require explicit approval before controlled actions or proceeding
beyond important project checkpoints. Paid resources remain prohibited.

External actions include creating Issues or labels, opening PRs, pushes,
publishing, and releases. Authentication is not authorization. Never
automatically stage, commit, push, merge, rewrite history, delete meaningful
files, or clean untracked files. Do not assume a clean working tree. Preserve
existing work, including `eval_runs/`, `eval_runs_v2/`, and
`tools/bench_llm.log`; they are not scratch space.

## Fresh review and handoff

After meaningful implementation/checkpoints, use a fresh read-only GPT-6
Astra review, separate from the worker's implementation context. Give the
reviewer approved requirements, baseline/current diff, allowed scope, check
results, and evidence locations. The reviewer must inspect the actual diff,
requirement coverage, scope, architecture, tests, evidence integrity,
regressions, and remaining risks. Report findings and a PASS/BLOCKED verdict.
Review is not approval to publish or continue beyond the checkpoint.

Repairs stay within approved scope and receive appropriate verification and
review; new requirements return to the user. Handoff lists changed files,
acceptance coverage, actual checks/results, gate status, remaining risks, and
pending approvals. Apply the existing AGENTS.md session-end rules. If the
user explicitly forbids Context/Journal edits for a bounded gate, preserve
them and report that scoped exception; never write the journal without
explicit approval.

## Stable evidence gates

For each applicable gate, record PASS or BLOCKED with evidence. When a gate
does not apply, state why; when checks were not run, say so. Neither is a PASS.
Documentation-only work may omit application execution when its approved scope
permits, but must still validate its diff and file scope.

| Gate | Required evidence |
| --- | --- |
| E00 — Repository safety | Git status and branch known; starting modifications and artifacts identified and protected. |
| E01 — Requirements | Approved bounded requirement/spec exists; no invented requirement. |
| E02 — Architecture | Relevant simulator-independent core, deterministic critical decisions, local-first operation, and optional modules outside the critical path verified. |
| E03 — NPC | Zero new cost; no paid API, credits, or new paid service. |
| E04 — Focused verification | Ticket-specific tests/checks pass; documentation checks include whitespace, links, and allowed-file scope as relevant. |
| E05 — Full offline regression | Both baseline commands below pass for application implementation; report environment and actual results. Approved future checks may be added; existing checks must not silently disappear. |
| E06 — Degradation | When relevant, unavailable LLM/TTS/optional output does not invalidate telemetry processing or deterministic core operation. |
| E07 — Evidence integrity | Measurements identify environment and conditions; fake/synthetic results are labelled; platform conclusions stay within collected evidence. |
| E08 — Fresh review | Fresh read-only Astra review after meaningful implementation, with inspected evidence and verdict. |
| E09 — User checkpoint | Explicit approval before architecture decisions, material scope expansion, Grok escalation, external/destructive actions, and proceeding beyond important checkpoints. |

E05 baseline from the repository root, with `PYTHONPATH=src`:

```text
python -m unittest discover -s tests -v
python -m raceengineer.demo --source synthetic --radio-only
```

In PowerShell set `$env:PYTHONPATH = "src"`; on POSIX use
`export PYTHONPATH=src`. Do not enable model or speech calls as part of these
offline baseline commands. Preserve existing artifacts when gathering results.
