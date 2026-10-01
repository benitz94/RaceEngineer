# Model selection

Status: selected pair, 2026-10-01. Not an AMD qualification.

## Selected pair

| Role | Tag | Weights | License |
| --- | --- | --- | --- |
| Language model (briefings) | `qwen3.5:4b` | Q4_K_M, about 3.4 GB on disk, 4.66B parameters | Apache-2.0 |
| Typed decision model | `qwen3.5:0.8b` | Q8_0, about 1.0 GB on disk, 873M parameters | Apache-2.0 |

Both checkpoints are free to obtain and run locally. Paid weights and paid cloud APIs remain out of scope. Apache-2.0 weights may be used beside GPL-3.0-only project code; they do not relicense RaceEngineer.

The 0.8B model is a constrained classifier only (GBNF or a JSON enum of the declared labels). Unconstrained briefing from the 0.8B is not acceptable. If the grammar constraint fails or the call times out, the session falls back to deterministic rules and the rule radio sentence. See `docs/DECISION_MODEL.md`.

## Measured cohabitation

Development GPU only: NVIDIA GeForce RTX 3050, 6144 MiB, Windows. Not Radeon evidence.

Session measurement (not older eval notes):

- `qwen3.5:4b` alone about 4453 MiB used after load (idle about 630 MiB).
- Pair estimate that matches official weights plus a 4k KV cache and CUDA context: about 5.7 GB used, about 274 MiB free on this 6 GB card.

274 MiB free is not a safe working margin on Windows. The desktop compositor and a browser can consume more than that and force offload without warning. The 6 GB card is a development bench, not the product host.

## Purchase floor

- Minimum VRAM: 8 GB, enough for this pair plus a small desktop footprint on Linux.
- Recommended VRAM: 12 GB, so both models, context, and the desktop stay resident without offload.
- Expected family remains an AMD Radeon. The exact SKU is not chosen. NVIDIA timings and VRAM traces do not qualify a Radeon.

Do not treat a perfect fake harness score as a model benchmark. Real Ollama runs still belong in the evaluation harness, with hardware named in the report.
