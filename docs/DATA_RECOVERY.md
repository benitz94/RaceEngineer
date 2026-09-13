# Data Recovery Demo

Python 3.10 or newer is required. Runtime and tests use only the standard library.
From the repository root in PowerShell:

```powershell
$env:PYTHONPATH = "$PWD/src"
python -m raceengineer.demo --source synthetic
python -m raceengineer.demo --source synthetic > recording.jsonl
python -m raceengineer.demo --source file recording.jsonl
python -m raceengineer.demo --source udp --port 33740
python -m unittest discover -s tests -v
```

On POSIX, first use `export PYTHONPATH="$PWD/src"`. In Windows PowerShell 5,
use `python -m raceengineer.demo --source synthetic | Set-Content -Encoding utf8
recording.jsonl` to capture UTF-8 instead of its default UTF-16 redirection.

Synthetic output defaults to 20 samples at 10 Hz. `--count` changes its length;
`--rate` controls synthetic and file delivery. Replay runs to end of file.
Ctrl+C stops replay or UDP. UDP optionally stops after `--count` datagrams;
`--host` selects the bind address.

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
