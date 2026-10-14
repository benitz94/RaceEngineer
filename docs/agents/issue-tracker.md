# Bounded tasks and Issue publication

This policy extends [AGENTS.md](../../AGENTS.md) and
[orchestration.md](orchestration.md). It defines ticket preparation and
evidence, not permission to create GitHub Issues.

## When to use an Issue

Use an Issue for an approved bounded outcome that needs durable tracking,
dependencies, acceptance criteria, or a reviewable handoff. A small local
correction may use an approved bounded task in the session instead; not every
edit requires publication. Roadmap possibilities and unapproved ideas do not
become implementation tickets automatically.

Before proposing tickets, inspect existing Issues and relevant local
planning/specification documents for overlapping work. Reference or refine an
existing ticket rather than duplicate it. If Issue inspection is unavailable
or outside the authorized gate, report that duplicate checking is incomplete
and defer publication; do not claim no duplicate exists.

## Requirements and approval flow

When requirements are not already approved and bounded:

1. Matt clarifies requirements, exposes assumptions, and produces a design.
2. The user approves a specification with observable outcomes and exclusions.
3. Matt converts that approved specification into proposed bounded tickets.
4. The user approves exact ticket contents and dependency/execution order.
5. Publish GitHub Issues only with explicit publication approval, after
   duplicate checking and the NPC check.

Specification approval does not authorize ticket publication. Ticket approval
does not replace Astra's implementation-plan approval. GitHub authentication
and available integrations are not permission to publish. Material ticket
changes require renewed approval for the changed scope.

## Ticket boundaries and required sections

Each ticket covers one independently verifiable outcome, with manageable scope
and known dependencies. Split unrelated outcomes before approval. Name exact
relevant files when known; repository exploration can be a separate bounded
task when files or feasibility are not yet established.

| Required section | Content |
| --- | --- |
| Problem and intended outcome | Concrete current problem and observable resulting behavior. |
| Approved requirement/specification | Reference to the approved spec or bounded requirement and approval evidence. |
| Scope and exclusions | Allowed files/areas, preserved user work, and explicit out-of-scope behavior. |
| Acceptance criteria | Objective, inspectable conditions; no invented performance thresholds. |
| Dependencies and order | Existing related Issues, prerequisite decisions, and approved sequence. |
| Verification and evidence | Focused checks, relevant E00–E09 gates, offline regression applicability, degradation checks, and measurement environment when relevant. |
| Assumptions, risks, and checkpoints | Known uncertainties and triggers for stopping or requesting a decision. |

Proposed labels follow [triage-labels.md](triage-labels.md). Worker assignments
and any specific escalation request belong in Astra's approved execution plan;
a ticket alone never authorizes Grok.

## Completion and evidence

At handoff, map each acceptance criterion to the actual diff and supporting
checks. Report exact commands/results, applicable gate evidence, fresh Astra
review verdict, blockers, and residual risks. Identify hardware, OS, runtime,
model, quantization, and test conditions for measurements. Label synthetic/fake
results and do not generalize NVIDIA evidence into Radeon qualification.

Failed or unperformed checks cannot be reported as passing. An implementation
report alone does not establish completion. Keep incomplete criteria open and
stop at E09 before moving beyond an important checkpoint. Issue publication,
comments, label changes, closure, PR creation, and other remote writes require
explicit authorization; do not automatically commit or publish a completion
report. Preserve the existing contribution and licensing rules.
