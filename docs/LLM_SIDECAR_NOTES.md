# Optional LLM Sidecar Notes

The sidecar turns structured sample and alert dicts into a short spoken
radio briefing. It is off by default. The deterministic `fuel_low` rule
does not call it.

Host for this bench: Windows development PC, NVIDIA GeForce RTX 3050
6 GB, 16 GB RAM, Ollama 0.34.0, Python 3.12. Date: 2026-09-14.

## Setup

Runtime and tests still use the Python standard library. A local
generator is required only when `--brief` is used.

### Ollama (default)

1. Install Ollama and leave the service running on `127.0.0.1:11434`.
2. Pull a small instruct model, for example `ollama pull llama3.2:3b`.
3. From the repository root:

```powershell
$env:PYTHONPATH = "$PWD/src"
python -m raceengineer.demo --source synthetic --brief
python -m raceengineer.demo --source synthetic --brief --lang it --alerts-only
```

If Ollama is down, the CLI still prints alerts, writes one warning to
stderr, and exits 0.

### llama.cpp

Run a local server (default `http://127.0.0.1:8080`) and set:

```powershell
$env:RACEENGINEER_LLM_BACKEND = "llamacpp"
$env:RACEENGINEER_LLM_URL = "http://127.0.0.1:8080"
```

### Optional OpenAI-compatible HTTP

No keys belong in git. If a server requires a token, keep it in the
environment:

```powershell
$env:RACEENGINEER_LLM_BACKEND = "openai"
$env:RACEENGINEER_LLM_URL = "http://127.0.0.1:1234/v1"
$env:RACEENGINEER_LLM_API_KEY = "..."   # optional, local only
$env:RACEENGINEER_LLM_MODEL = "local-model"
```

Other optional variables: `RACEENGINEER_LLM_MODEL` (default
`llama3.2:3b`), `RACEENGINEER_LLM_TIMEOUT` (seconds, default 60).

## Bench

Same fixed synthetic session (20 samples, one `fuel_low` at 10.0 L) for
every model. N=3 generations. 10 minute abort per model after pull.

```powershell
$env:PYTHONPATH = "$PWD/src"
python tools/bench_llm.py --out docs/llm_bench.csv
```

Columns: `model`, `quant`, `vram_mb`, `pull_ok`, `ttft_s`, `total_s`,
`words`, `error`.

## Results

Bench running; table will be filled from `docs/llm_bench.csv`.

| model | quant | vram_mb | pull_ok | ttft_s | total_s | words | error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pending | | | | | | | |

## Best pick

Pending bench numbers.

- Live radio: lowest reliable TTFT that stays on-GPU and keeps the
  radio tone, without inventing numbers.
- Post-lap: a larger quant or size if it finishes without swapping.

## Failures

Pending. Expected on this 6 GB card: 12B/14B and 8B Q8 will likely
offload or abort. `gemma2:9b-instruct` is not an official tag;
the bench falls back to `gemma2:9b-instruct-q4_0`.
