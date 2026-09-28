# Model evaluation

`tools/eval_models.py` is a reproducible, hardware-independent harness for the
two optional model roles already described by RaceEngineer:

1. short Italian pit-wall briefings;
2. bounded `canned`/`brief` and `grounded`/`reject` decisions.

The harness does not move either model into the critical path. Deterministic
rules remain authoritative, and an unavailable, timed-out, empty, malformed,
or rejected model result leaves the rule radio line available.

The current deterministic decision implementation does not declare a
`speak`/`hold` question. The corpus therefore does not invent or score that
skill. It can be added only if repository code declares its semantics later.

## What it measures

The deterministic scorer can measure only properties represented explicitly
by a fixture:

- exact typed-decision labels;
- empty and out-of-vocabulary output;
- sentence and word counts;
- JSON, Markdown, log-field, and chatbot-style leakage;
- fixture-declared required and forbidden claims;
- unsupported numeric claims where the fixture identifies allowed numbers;
- whether a deterministic rule fallback remains available;
- backend latency when the backend reports it.

The aggregate report includes total, passed, failed, accuracy, false grounded
acceptances, false rejections, their denominator-specific rates,
hallucination failures, style failures, and malformed-output failures.
`false_grounded_acceptance_rate` divides false grounded acceptances by all
cases whose expected label is `reject`. `false_rejection_rate` divides false
rejections by all cases whose expected label is `grounded`. Either rate is
`0.0` when its denominator is zero. The existing count fields remain alongside
the rates. Briefing case details retain sentence count, word count,
forbidden-token violations, unsupported claims, unsupported numbers, and
fallback use.

These are bounded checks, not a general semantic judge. Passing does not prove
that a model is safe, fluent in every Italian register, suitable for every
session, fast enough on target hardware, or correct outside the supplied
facts. A lexical check can miss paraphrased inventions. Review real model
outputs in addition to reading the aggregate score.

## Corpus

The versioned repository corpus is split by purpose:

- `tests/model_eval/briefing_cases.jsonl`: generated briefing constraints;
- `tests/model_eval/grounding_cases.jsonl`: grounded/reject examples;
- `tests/model_eval/decision_cases.jsonl`: canned/brief and fallback examples.

Each nonblank JSONL line is one object with these required fields:

| Field | Meaning |
| --- | --- |
| `id` | Globally unique stable case identifier. |
| `category` | `grounding`, `hallucination`, `style`, `decision`, or `failure`. |
| `task` | `briefing`, `canned_or_brief`, or `grounded_or_reject`. |
| `input` | Facts and bounded input for the role. `rule_fallback`, when present, is the deterministic line retained on failure. |
| `expected` | Legal result for the selected task. |
| `rationale` | Short explanation grounded in current project semantics. |
| `fake` | Exactly one deterministic `text` or `error` result for offline evaluation. |

Briefing cases may also contain `checks` with `required_terms`,
`required_any`, `forbidden_terms`, and `allowed_numbers`. These declarations
bound what the scorer can claim. They do not add telemetry to the product.

Corpus loading rejects malformed JSON, duplicate IDs, missing or unknown
fields, unknown categories or tasks, illegal expected labels, and malformed
fake results. It reports the file and line where possible.

## Offline evaluation

The fake backend uses only fixture data. It makes no network request and needs
no GPU, Ollama, Piper, audio device, simulator, or external API.

From the repository root:

```bash
python3 tools/eval_models.py --validate-corpus
python3 tools/eval_models.py --list-cases
python3 tools/eval_models.py --backend fake
python3 tools/eval_models.py --backend fake --category hallucination
```

The fake run verifies the corpus, runner, scorer, fallback handling, and
reporting pipeline. A perfect fake score is expected and is not a model
benchmark. Corpus/configuration errors return a nonzero status. Ordinary case
failures are recorded in the report rather than turned into a subjective test
suite threshold.

## Optional Ollama evaluation

The Ollama backend uses Python's standard-library HTTP client. It never pulls,
downloads, installs, starts, or removes a model. The named model and Ollama
server must already exist locally.

```bash
python3 tools/eval_models.py \
  --backend ollama \
  --model qwen3.5:4b \
  --timeout 15 \
  --output-json model-eval.json \
  --output-csv model-eval.csv
```

`--ollama-url` can select another loopback HTTP origin. Accepted hosts are
`localhost`, an address in `127.0.0.0/8`, or IPv6 `::1`. Public hosts, LAN
addresses, HTTPS, missing hosts, embedded credentials, and URLs with paths,
queries, or fragments are rejected before any request. Current project
documentation requires local inference and does not declare LAN-hosted model
serving. If the server or model is unavailable, the command prints a clear
diagnostic, records backend errors, starts no download, and returns a nonzero
status when no case received a model answer.

The harness sends briefing facts or a bounded decision question and requests
temperature zero. This improves repeatability but does not guarantee identical
results across model versions, runtimes, or hardware.

## Reports

The JSON report contains:

- `metadata`: backend, model, UTC timestamp for a real backend, and case count;
- `summary`: aggregate deterministic counters;
- `cases`: per-case labels, pass state, latency, error, notes, raw output, and
  deterministic metrics.

The CSV report has one row per case with:

`case_id`, `category`, `task`, `expected`, `actual`, `pass`, `latency_s`,
`error`, `notes`, `output`, `backend`, `model`, `timestamp`, and `case_count`.

No VRAM field is emitted because this harness does not measure VRAM. Record
hardware measurements only when an appropriate measurement procedure actually
runs.

## Interpreting failures

- A false grounded acceptance is an expected `reject` labeled `grounded`.
- A false rejection is an expected `grounded` labeled `reject`.
- A hallucination or style failure means that a case in that category missed
  its expected result; inspect the per-case notes and raw output.
- A malformed-output failure is an unexpected empty, backend-error, or illegal
  typed result. Expected failure fixtures can still pass when they demonstrate
  the documented deterministic fallback.

Treat an aggregate score as a way to compare the same declared corpus under a
controlled setup, not as proof of production readiness. Keep the report with
the exact model name, runtime, and environment when doing a real run.

## Hardware and model-selection limits

Functional output evaluation and hardware qualification are separate. This
harness does not select a GPU, measure sustained load, establish concurrency
limits, or prove target-platform latency. NVIDIA measurements are not AMD
qualification. Results from an NVIDIA system must never be presented as Radeon
VRAM, performance, or compatibility evidence.

This contribution contains no unperformed benchmark numbers, does not select
the final language or decision model, and does not change current model or
hardware recommendations.
