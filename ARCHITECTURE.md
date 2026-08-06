# RaceEngineer Architecture

## Document Status

This architecture describes the project's initial direction.

File formats, the real telemetry protocol, and specific libraries have not yet
been selected.

Gran Turismo 7 is a candidate for technical evaluation and is not yet an
architectural dependency.

## Initial Technology

The project's initial language is Python.

Python was selected for:

- rapid development;
- Raspberry Pi compatibility;
- integration with AI, Ollama, STT, and TTS;
- availability of a broad library ecosystem.

This choice is not a permanent constraint.

Module boundaries must allow individual Python implementations to be replaced
in the future with C++ or Rust modules if measurements demonstrate that this is
necessary to meet performance, stability, or responsiveness requirements.

Replacing a module must not change the observable behavior of the core or
introduce dependencies on a specific simulator.

## Architectural Goals

The architecture must ensure:

- local operation without mandatory cloud services;
- independence from the development PC;
- initial execution on a Raspberry Pi 3B+;
- core development and validation without a connected simulator;
- separation between simulators and core logic;
- deterministic behavior for critical decisions;
- full testability using synthetic or recorded telemetry;
- replaceable input, output, and persistence systems;
- the ability to replace individual Python modules with C++ or Rust
  implementations;
- controlled degradation of optional components;
- collection of diagnostic data and performance measurements.

## Architectural Principles

### Performance First

Every component and new feature must also be evaluated against the resources
available on the reference hardware.

The system priorities, in order, are:

1. stability;
2. reliability;
3. additional features.

Responsiveness in the main path must not be sacrificed to add nonessential
features.

Optimizations and technology replacements must be guided by real-world
measurements. If a Python module does not meet the required performance, its
implementation may be replaced with C++ or Rust while preserving its boundaries
and responsibilities.

### Simulator-Independent Core

The core must not know about protocols, packets, or behaviors specific to a
simulator.

Synthetic, recorded, and real telemetry must reach the core through the same
internal representation.

This makes it possible to fully develop, test, and validate the core before
connecting a real source.

### Deterministic Critical Decisions

Critical decisions during a session must be produced by explicit, verifiable,
and repeatable rules.

Any LLM is outside the critical path.

## Out of Scope for the First Prototype

The first prototype does not include:

- speech recognition;
- LLM-based conversation;
- cloud dependencies;
- advanced race strategies;
- adaptive driver profiling;
- a complete dashboard;
- music management;
- simultaneous support for multiple simulators.

## Logical Structure

The system is divided into the following layers:

1. telemetry sources;
2. normalization;
3. session state;
4. deterministic engine;
5. messages and priorities;
6. output systems;
7. persistence and diagnostics;
8. optional modules.

The main flow is:

Telemetry source
→ adapter
→ normalized internal model
→ session state
→ rules engine
→ event or alert
→ local output and log

## Telemetry Sources

A source produces telemetry samples without knowing the race rules.

The initially planned sources are:

### Synthetic Telemetry

Generates controlled scenarios for testing normal cases and exceptions.

It must allow the same scenario to be replayed multiple times.

### Recorded Telemetry

Reads a local recording and replays it while preserving or simulating the
original time sequence.

It must support at least:

- start;
- pause;
- stop;
- controllable replay speed;
- repeatability of the same test.

### Real Telemetry

Receives data over the local network from the simulator or console.

The first possible real adapter will be evaluated for Gran Turismo 7, but will
be implemented only after:

1. core development;
2. validation with synthetic telemetry;
3. validation with recorded telemetry;
4. verification of local voice output;
5. complete core validation on the Raspberry Pi 3B+;
6. a simulator-specific technical evaluation.

Each simulator must have a separate adapter.

## Normalized Internal Model

Adapters convert external data into a simulator-independent internal format.

The model must distinguish at least:

- source timestamp, when available;
- receipt timestamp;
- source identity or type;
- session state;
- lap number;
- lap time, when available;
- fuel, when available;
- sample validity and quality;
- missing or unsupported fields.

The definitive field list will be established during prototyping.

The core must not directly interpret simulator-specific packets or formats.

## Session State

This component builds a coherent view of the session from the received
samples.

Its responsibilities include:

- identifying the start and end of a session;
- maintaining the latest valid state;
- detecting lap transitions;
- handling missing, duplicate, or out-of-order data;
- exposing a consistent state to the rules engine.

## Deterministic Engine

The engine evaluates explicit rules against the session state.

Each rule must have:

- declared inputs;
- verifiable conditions;
- a predictable result;
- a priority;
- a mechanism for avoiding unnecessary repeated alerts;
- tests that can be built with synthetic or recorded telemetry.

The engine does not depend on an LLM.

Critical decisions must remain available even when audio, the Internet
connection, or optional modules are not working.

## Events, Alerts, and Priorities

The engine's result is not sent directly to TTS.

It is first represented as a structured event or alert containing at least:

- type;
- timestamp;
- priority;
- data that triggered the alert;
- predefined message or message identifier;
- delivery status.

This separation allows the same alert to be used for logs, text, audio, or
future interfaces.

## Output

Outputs are independent adapters.

### Text Output

This is mandatory in the first prototype for debugging and automated tests.

### Local Log

Records events, alerts, errors, and diagnostic metrics.

### Local TTS

Converts approved messages into audio without requiring cloud services.

The TTS engine has not yet been selected.

A TTS failure must not stop telemetry reception or analysis.

## Persistence

In the first prototype, persistence may be based on local files.

It must retain at least:

- application logs;
- detected events;
- generated alerts;
- errors;
- essential metrics;
- information required to reproduce a test.

The need for a database will be evaluated only when concrete requirements for
sessions, setups, and driver profiles emerge.

## Optional LLM Modules

An LLM is not part of the core and is not in the critical path.

It may receive copies of events or summaries already produced by the
deterministic system, but it will not replace the rules responsible for
critical alerts.

The LLM interface must:

- be disableable;
- not block the core;
- tolerate unavailability and errors;
- clearly distinguish deterministic content from generated content;
- not make a cloud connection mandatory.

## Error Handling

The system must degrade gracefully.

Examples:

- telemetry loss: report the condition and wait for the source;
- invalid packet: discard it safely and log the event;
- missing field: mark the value as unavailable without inventing data;
- TTS error: retain the alert in the log and text output;
- unavailable optional module: continue core operation;
- insufficient hardware resources: record a metric and diagnostic report.

## Performance

The Raspberry Pi 3B+ is the initial test bench.

Complete core validation on the Raspberry Pi 3B+ must occur before selecting
and implementing the adapter for the first real simulator.

Validation will use synthetic and recorded telemetry and must measure:

- CPU usage;
- memory usage;
- sample-to-event latency;
- event-to-alert latency;
- sample loss;
- stability during extended runs;
- local storage usage.

Acceptance thresholds will be defined after the first measurements, without
assuming them in advance.

If the performance of an individual Python module proves insufficient,
replacing it with a C++ or Rust implementation may be evaluated without
changing the overall architecture.

## Gran Turismo 7 Technical Evaluation

Before declaring support for Gran Turismo 7, the following must be evaluated:

- how telemetry is transmitted;
- which platforms and configurations are supported;
- which fields are available;
- data frequency and latency;
- behavior when packets are lost or reordered;
- session, lap, and car identification;
- any required transformations or decoding;
- stability across game updates;
- Raspberry Pi 3B+ compatibility;
- licensing, distribution, and documentation considerations.

This evaluation will take place after complete core validation on the
Raspberry Pi 3B+.

The outcome must be documented before GT7 becomes a definitive requirement.

## Security and Privacy

Basic operation must be capable of remaining confined to the local network.

Session data must be stored locally by default.

Any future transmission to external services must be optional, explicit, and
documented.

## Independence from AI Desktop Companion

RaceEngineer and AI Desktop Companion are separate projects.

The RaceEngineer core must not directly import the private project or depend
on its runtime environment.

Any shared components must have:

- clear boundaries;
- a compatible license;
- documented dependencies;
- the ability to be used and tested independently.
