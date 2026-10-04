# RaceEngineer working domain

Use this short reference for bounded development tasks after the session-start
reads required by [AGENTS.md](../../AGENTS.md). Existing repository rules take
precedence. [PROJECT_JOURNAL.md](../../PROJECT_JOURNAL.md) is authoritative for
intent and decisions; [ARCHITECTURE.md](../../ARCHITECTURE.md) defines the wider
architecture. This workflow does not import AI-Companion-Desktop governance.

## Invariants and boundaries

- **Local first:** core functionality must work without mandatory cloud
  services or dependence on the development PC.
- **Deterministic critical path:** critical race decisions and alerts remain
  explicit deterministic rules. An LLM is never their authority. Missing or
  invalid observations must not invent decisions.
- **Simulator-independent core:** simulator/protocol-specific acquisition and
  decoding belong in adapters, never in core race logic.
- **Optional component failure:** unavailable or failing LLM, TTS, or optional
  output must not break telemetry processing or deterministic decisions.
  Existing prototype limitations are unfinished work, not permission to weaken
  this requirement.
- **Evidence before optimization:** replacing Python modules with C++ or Rust
  requires measurements demonstrating the need and approval of any resulting
  architecture decision. Preserve module boundaries and observable behavior.
- **Evidence integrity:** benchmarks identify hardware, OS, model,
  quantization where relevant, runtime, and test conditions. Label fake and
  synthetic results explicitly; a fake harness score is not a real model
  benchmark. Windows/NVIDIA evidence does not qualify Linux/AMD Radeon.
- **Requirement discipline:** roadmap possibilities are not approved
  requirements. Stay inside the approved specification and bounded task.
- **Repository language:** documentation, files, comments, and commit messages
  are English. Discussion with the owner may be Italian.
- **Project independence:** do not depend on the private AI-Companion-Desktop
  runtime or silently copy its requirements. Reuse must respect the documented
  boundaries and licensing rules.

## Model and platform boundary

The selected pair is `qwen3.5:4b` (Q4_K_M) for briefings and `qwen3.5:0.8b`
(Q8_0) for constrained typed classification only. Current decisions remain
deterministic code; the neural grammar path is not implemented. Critical rule
radio remains available on optional-model failure.

Product VRAM guidance is 8 GB minimum and 12 GB recommended. Windows/RTX 3050
measurements are development evidence only. The intended platform is
Linux/AMD Radeon; exact SKU, Radeon qualification, final reference-machine
configuration, performance thresholds, simulator adoption, and distribution
remain unresolved. Consult [MODEL_SELECTION.md](../MODEL_SELECTION.md),
[DECISION_MODEL.md](../DECISION_MODEL.md), and
[PROJECT_CONTEXT.md](../../PROJECT_CONTEXT.md) for current details.

## Development cost boundary

NPC means "NON PAGO UN CAZZO": zero new cost. Local/free/open-source tooling
and usage already included in existing subscriptions are allowed. Paid APIs,
pay-as-you-go usage, extra credits, new paid services, and new subscriptions
are prohibited. If additional cost is possible or coverage is uncertain,
stop and report it. Subscription access does not authorize escalation or
external actions; follow [orchestration.md](orchestration.md).
