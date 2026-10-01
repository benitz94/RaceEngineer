# Model selection

Status: selected pair, 2026-10-01. Chosen to fit the development RTX 3050 with 6 GB. Not an AMD qualification.

## Selected pair

| Role | Tag | Weights | License |
| --- | --- | --- | --- |
| Language model (briefings) | `qwen3.5:4b` | Q4_K_M, about 3.4 GB on disk, 4.66B parameters | Apache-2.0 |
| Typed decision model | `qwen3.5:0.8b` | Q8_0, about 1.0 GB on disk, 873M parameters | Apache-2.0 |

Both checkpoints are free to obtain and run locally. Paid weights and paid cloud APIs remain out of scope. Apache-2.0 weights may be used beside GPL-3.0-only project code; they do not relicense RaceEngineer.

This pair was selected because it is the combination that still fits on the development NVIDIA GeForce RTX 3050 (6144 MiB). Two 4B checkpoints do not fit on that card. It is the best pair for that 6 GB bench, not a claim that these are the best models on a larger GPU.

The 0.8B model is a constrained classifier only (GBNF or a JSON enum of the declared labels). Asked for one word it returned `brief`. Unconstrained briefing from the 0.8B is not acceptable. If the grammar constraint fails or the call times out, the session falls back to deterministic rules and the rule radio sentence. See `docs/DECISION_MODEL.md`.

License-clean spare, not loaded in this session and not a measured radio replacement: Phi-4-mini-instruct (`phi4-mini`, about 3.8B, MIT, about 2.5 GB). Other decision-sized weights (Qwen2.5-1.5B-Instruct, Phi-3-mini) remain generators until a grammar constraint exists.

## Measured cohabitation

Development GPU only: NVIDIA GeForce RTX 3050, 6144 MiB, Windows. Not Radeon evidence. Both models were resident with `keep_alive`. Older `eval_runs` notes that said the 1.7B or 2B evicted the 4B, or that the 0.8B produced no usable label, are not this session.

Measured 2026-10-01:

| Pair | nvidia-smi used | Free |
| --- | --- | --- |
| `qwen3.5:4b` + `qwen3.5:0.8b` | 5729 MiB | 274 MiB |
| `qwen3.5:4b` + `qwen3:1.7b` | 5905 MiB | 98 MiB |

Earlier load of `qwen3.5:4b` alone was about 4453 MiB after load, with idle about 630 MiB. That figure is a separate check, not this pair table.

274 MiB free is not a safe working margin on Windows. The desktop compositor and a browser can consume more than that and force offload without warning. 98 MiB free on the 1.7B pair is worse. The 6 GB card is a development bench, not the product host.

## Purchase floor

- Minimum VRAM: 8 GB, enough for this pair plus a small desktop footprint on Linux.
- Recommended VRAM: 12 GB, so both models, context, and the desktop stay resident without offload.
- Expected family remains an AMD Radeon. The exact SKU is not chosen. No Radeon pair VRAM was measured. NVIDIA timings and VRAM traces do not qualify a Radeon.

Do not treat a perfect fake harness score as a model benchmark. Real Ollama runs still belong in the evaluation harness, with hardware named in the report.
