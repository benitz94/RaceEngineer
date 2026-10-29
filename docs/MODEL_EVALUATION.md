# Model evaluation

`tools/eval_models.py` is a reproducible, hardware-independent harness for the
two model roles described in `docs/DECISION_MODEL.md`:

1. the engineer's voice: one short Italian radio line, written with the
   runtime engineer prompt (`raceengineer.briefing.SYSTEM_PROMPT`);
2. Istinto's declared questions: `urgency` (`now`, `normal`, `calm`) and
   `grounded_or_reject`.

Every radio line is generated and there is no canned fallback. When a model
fails or its answer is unusable, the expected outcome is `silent`: the radio
stays silent and the failure is reported.

The runtime does not yet declare `speak`/`hold` or a long/short question. The
corpus therefore does not invent or score them. They can be added when
repository code declares their semantics.

## What it measures

The deterministic scorer can measure only properties represented explicitly
by a fixture:

- exact typed-decision labels;
- empty and out-of-vocabulary output;
- sentence and word counts;
- JSON, Markdown, log-field, and chatbot-style leakage;
- fixture-declared required and forbidden claims;
- unsupported numeric claims where the fixture identifies allowed numbers;
- whether a failure correctly leaves the radio silent;
- backend latency, with p50, p95, and maximum in the summary;
- the decision model's confidence, when the backend reports one.

The aggregate report includes total, passed, failed, accuracy, false grounded
acceptances, false rejections, their denominator-specific rates,
hallucination failures, style failures, and malformed-output failures.
`false_grounded_acceptance_rate` divides false grounded acceptances by all
cases whose expected label is `reject`. `false_rejection_rate` divides false
rejections by all cases whose expected label is `grounded`. Either rate is
`0.0` when its denominator is zero. The existing count fields remain alongside
the rates. Engineer-line case details retain sentence count, word count,
forbidden-token violations, unsupported claims, and unsupported numbers.

These are bounded checks, not a general semantic judge. Passing does not prove
that a model is safe, fluent in every Italian register, suitable for every
session, fast enough on target hardware, or correct outside the supplied
facts. A lexical check can miss paraphrased inventions. Review real model
outputs in addition to reading the aggregate score.

## Corpus

The versioned repository corpus is split by purpose:

- `tests/model_eval/briefing_cases.jsonl`: engineer-line constraints;
- `tests/model_eval/grounding_cases.jsonl`: grounded/reject examples;
- `tests/model_eval/decision_cases.jsonl`: urgency and failure examples.

Each nonblank JSONL line is one object with these required fields:

| Field | Meaning |
| --- | --- |
| `id` | Globally unique stable case identifier. |
| `category` | `grounding`, `hallucination`, `style`, `decision`, or `failure`. |
| `task` | `engineer_line`, `urgency`, or `grounded_or_reject`. |
| `input` | Facts and bounded input for the role. The retired `rule_fallback` and `brief` fields are rejected. |
| `expected` | Legal result for the selected task. |
| `rationale` | Short explanation grounded in current project semantics. |
| `fake` | Exactly one deterministic `text` or `error` result for offline evaluation. |

Engineer-line cases may also contain `checks` with `required_terms`,
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

The fake run verifies the corpus, runner, scorer, silent-radio handling, and
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
  --decision-model qwen3.5:0.8b \
  --output-json model-eval.json \
  --output-csv model-eval.csv
```

`--model` answers engineer-line cases. `--decision-model` answers Istinto's
questions and defaults to `--model`. `--decision-api` selects how Istinto is
asked:

- `chat` (default): `/api/chat` with an Ollama JSON schema (`format`) that
  allows only the declared labels, read from `{"label": ...}`;
- `systemone`: a Jev-style decision model on `/v1/systemone` (Ollama 0.35 or
  later), asked one `choice` question per case; the answer's `confidence` is
  recorded. Engineer lines always use `/api/chat`.

```bash
python3 tools/eval_models.py \
  --backend ollama \
  --model qwen3.5:4b \
  --decision-model tev1:0.8b \
  --decision-api systemone
```

`--timeout` defaults to 6 seconds, the longest urgency deadline. Compare the
reported latencies with the urgency deadlines in `docs/DECISION_MODEL.md`.

`--ollama-url` can select another loopback HTTP origin. Accepted hosts are
`localhost`, an address in `127.0.0.0/8`, or IPv6 `::1`. Public hosts, LAN
addresses, HTTPS, missing hosts, embedded credentials, and URLs with paths,
queries, or fragments are rejected before any request. Current project
documentation requires local inference and does not declare LAN-hosted model
serving. If the server or model is unavailable, the command prints a clear
diagnostic, records backend errors, starts no download, and returns a nonzero
status when no case received a model answer.

The harness sends engineer facts or a bounded decision question and requests
temperature zero on `/api/chat`. This improves repeatability but does not guarantee identical
results across model versions, runtimes, or hardware.

## Reports

The JSON report contains:

- `metadata`: backend, voice model, decision model and API, UTC timestamp for
  a real backend, and case count;
- `summary`: aggregate deterministic counters and latency p50, p95, and max;
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
  typed result. Failure fixtures pass when the result is `silent`: the radio
  stays silent and the failure is reported.

Treat an aggregate score as a way to compare the same declared corpus under a
controlled setup, not as proof of production readiness. Keep the report with
the exact model name, runtime, and environment when doing a real run.

## Hardware and model-selection limits

Functional output evaluation and hardware qualification are separate. This
harness does not select a GPU, measure sustained load, establish concurrency
limits, or prove target-platform latency. Results from one GPU or OS must
never be presented as VRAM, performance, or compatibility evidence for
another.

The selected language and decision pair is recorded in `docs/MODEL_SELECTION.md`.
This harness does not change that selection. It contains no unperformed
benchmark numbers and does not qualify a GPU.
