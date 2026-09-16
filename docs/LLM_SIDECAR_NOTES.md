# Optional LLM Sidecar Notes

The optional sidecar turns sample and alert dicts into a short radio
briefing. It is off by default and outside the deterministic alert path.

## Current scope

Only `llama3.2:3b` is retained. The owner stopped the larger benchmark on
2026-09-16. No further downloads, generations, or tests were run after that
instruction. The benchmark tool now uses this installed model only and
never downloads or removes models.

The completed measurements below were taken on this machine: WSL2 Linux
`6.18.33.2-microsoft-standard-WSL2`, NVIDIA GeForce RTX 5070 Ti Laptop GPU
(12,227 MiB VRAM), 15 GiB RAM visible to WSL, 4 GiB swap, NVIDIA driver
610.62, Ollama 0.34.1, Python 3.12.3.

## Usage

Ollama must be running with `llama3.2:3b` already installed. Use `python3`
on this machine. These commands are for a future explicitly requested run:

```bash
export PYTHONPATH=src
python3 -m raceengineer.demo --source synthetic --brief
python3 -u tools/bench_llm.py 2> tools/bench_llm.log
```

On Windows PowerShell, set `$env:PYTHONPATH = "$PWD\src"` instead.
The tool writes `tools/bench_stdout.csv` and prints CSV to stdout.
`tools/bench_llm.log` is ignored and must not be committed.

## Method

All three generations used the same existing synthetic session: 20
samples from 0.0 to 1.9 seconds and one `fuel_low` alert at 1.5 seconds,
with 10.0 L and the deterministic message "Fuel low. Box this lap."
The last valid sample is lap 2 with 9.6 L. No telemetry was invented.

The English prompt and backend settings were unchanged: temperature 0.2,
120 output tokens maximum, context 2048, no fixed random seed. The model
was unloaded before generation 1; generations 2 and 3 were warm requests
with identical input and potential prompt-cache reuse. A separate process
enforces a ten-minute wall-time budget for loading and all generations.

`vram_mb` is total GPU memory used in MiB, sampled before and after
generations, including desktop allocations; it is not isolated model
memory or a continuously sampled peak. Ollama reported full GPU residency
for this model. `pull_ok=True` records the successful pull check during
the original run; future runs only check that the model is installed.
TTFT measures request to first nonempty text, and total time ends when
streaming finishes. Pulling, process startup, sanitization and TTS are
excluded. Words count sanitized output.

## Results

Rows are generations 1, 2 and 3 in order. Errors below are manual factual
review findings, added after measurement; the automatic sanitizer accepted
all three responses.

| model | quant | vram_mb | pull_ok | ttft_s | total_s | words | error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| llama3.2:3b | Q4_K_M | 3610 | True | 2.451 | 2.735 | 21 | Unsupported driving advice; historical fuel presented as current |
| llama3.2:3b | Q4_K_M | 3610 | True | 0.025 | 0.253 | 18 | Unsupported driving advice; historical fuel presented as current |
| llama3.2:3b | Q4_K_M | 3610 | True | 0.028 | 0.251 | 18 | Unsupported driving advice; historical fuel presented as current |

## Tone and factual review

Each sanitized response contained three sentences. However, all added
unsupported downshifting advice; generations 2 and 3 also suggested throttle
adjustments. They described historical fuel readings of 10.5, 10.6 and
10.9 L as current, instead of the final valid 9.6 L. Generation 1 also used
the 10.5 L reading from the invalid sample. Quotation marks produced an
awkward final punctuation sequence in the sanitized output.

The numeric sanitizer only checks whether numbers appear somewhere in the
input. It does not validate chronology, relationships, or driving advice.
These outputs therefore fail the requested grounded radio briefing standard,
despite meeting the two-to-five-sentence count.

Warm generation completed below two seconds, but cold generation did not.
Identical cached prompts do not establish latency for changing telemetry.
Keep `llama3.2:3b` for local experimentation; this run does not justify
using its unchecked output for live radio or post-lap briefings. The
deterministic alert remains available independently. No comparative model
recommendation is made because the larger benchmark was cancelled.

## Validation and cleanup

The 21 existing unit tests passed without GPU inference before the stop
instruction. No tests were rerun afterward. The deterministic rules and
sample pipeline were not changed.

The benchmark and pull workers were terminated. Ollama lists only
`llama3.2:3b`, with no loaded model. The cancelled download did not create
another installed model. On 2026-09-16, the owner confirmed completing the
targeted sudo cleanup of that download's partial files in the service-owned
model store. The cleanup preserves `llama3.2:3b`.
