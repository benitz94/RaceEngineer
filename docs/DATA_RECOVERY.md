# Data Recovery Demo

Python 3.10 or newer is required. Runtime and tests use only the standard library.
From the repository root in PowerShell:

```powershell
$env:PYTHONPATH = "$PWD/src"
python -m raceengineer.demo --source synthetic
python -m raceengineer.demo --source synthetic --samples-only > recording.jsonl
python -m raceengineer.demo --source file recording.jsonl
python -m raceengineer.demo --source udp --port 33740
python -m unittest discover -s tests -v
```

On POSIX, first use `export PYTHONPATH="$PWD/src"`. In Windows PowerShell 5,
use `python -m raceengineer.demo --source synthetic --samples-only | Set-Content -Encoding utf8
recording.jsonl` to capture UTF-8 instead of its default UTF-16 redirection.

Synthetic output defaults to 20 samples at 10 Hz. `--count` changes its length;
`--rate` controls synthetic and file delivery. Replay runs to end of file.
Ctrl+C stops replay or UDP. UDP optionally stops after `--count` datagrams;
`--host` selects the bind address.

## Fuel Rule and Alerts

Synthetic and file modes print each sample, then a triggered alert, then the
radio line for that alert. Use `--alerts-only` to print alerts, `--radio-only`
to print radio lines, or `--samples-only` to capture a replayable recording.
Mixed output is a diagnostic stream, not a sample recording accepted by file
replay. The sample format remains version 1. UDP stays a metadata probe and
does not run telemetry rules.

```powershell
python -m raceengineer.demo --source synthetic --alerts-only
python -m raceengineer.demo --source synthetic --radio-only
python -m raceengineer.demo --source synthetic --radio-only --speak
python -m raceengineer.demo --source synthetic --radio-only --brief
python -m raceengineer.demo --source synthetic --fuel-low-threshold 9.8 --alerts-only
```

The single fuel rule requires `valid: true` and a present fuel observation.
It fires at fuel <= 10.0 litres and remains suppressed until a valid observation
rises above 12.0 litres. `--fuel-low-threshold` configures the firing threshold
(finite, nonnegative, and below the fixed 12.0 reset threshold). Missing fuel,
false validity, and unknown validity cannot trigger or reset the alert. Session
state retains the last valid fuel and lap; stale fuel is never used to trigger.
The default synthetic scenario starts at 11.5 litres and reaches 10.0 at sample
index 15, then stays below the threshold through the remaining default samples.

Alert lines have `format: "raceengineer.alert"`, `version: 1`, and an `alert`
object containing `type: "fuel_low"`, `priority: "high"`, `timestamp`, `fuel`,
and `message: "Fuel low. Box this lap."`. The timestamp uses the triggering
sample's source time, falling back to receipt time, then null; no clock value
is invented. Each CLI run starts a fresh session. Programmatic users call
`RulesEngine.restart()` when restarting a source; restarts are not inferred
from missing fields, lap changes, or out-of-order timestamps.

A `fuel_low` alert also prints one radio line: `format: "raceengineer.radio"`,
`version: 1`, and a `radio` object with `source: "rule"`, `type: "fuel_low"`,
`text: "Box, box. Questo giro."`, and the same timestamp. The alert
message stays the English log line. Missing or
invalid fuel still produces neither an alert nor a radio line.
Without `--brief`, no language model is called. With `--brief`, after the rule
radio line, local Ollama model `qwen3.5:4b` (`http://127.0.0.1:11434/api/chat`,
about 15 seconds) may print a second `raceengineer.radio` line (`source: "llm"`,
same type and timestamp). If Ollama is down, times out, or returns empty,
nothing extra is printed, stderr gets one line, and the process does not fail.

`--speak` says the rule radio text with local Windows speech (System.Speech).
It uses an installed Italian voice when one is present. If speech fails, the
radio line is still printed and an error is written to stderr. `--speak` does
nothing when no radio line is produced and does not speak a `--brief` line.

## Version 1 Recording

Each UTF-8 JSONL line contains `format: "raceengineer.sample"`, `version: 1`,
and a `sample` object. Replay preserves file order, duplicates, timestamps,
and invalid samples. Delivery uses `--rate`, without replacing timestamps.
Malformed records, unsupported versions, unknown sample fields, and wrong types
fail with a line-number diagnostic and a nonzero exit code.

Fields: `source_ts`, `recv_ts`, `source_id`, `lap`, `lap_time`, `speed`, `fuel`,
`valid`, `quality`. Missing fields remain `None` internally and JSON `null` on
output. Numeric fields must be finite, lap an integer, valid a boolean, and
identity and quality strings. Quality is supplied by the source; no validity
or observation is inferred. Invalid samples are retained for later analysis.

Times use seconds, speed metres per second, and fuel litres. Timestamp clock
domains belong to the source. Synthetic source and receipt times use logical
seconds starting at zero, representing simulated arrival rather than wall time.
The same count and rate produce identical output.

UDP output contains only peer address/port, datagram size in bytes, and receipt
time in Unix seconds. Payloads are neither parsed nor logged. UDP metadata is
separate from samples and cannot be replayed as telemetry. Tests require no
simulator or Internet access; the UDP test uses loopback only.
