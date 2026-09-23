# RaceEngineer Roadmap

## Principles

The roadmap progresses through incremental validation.

Each phase must produce an observable, documented result before complexity is
added.

The core must be fully developed, tested, and validated without depending on a
connected simulator.

Gran Turismo 7 remains a candidate until technical evaluation confirms its
feasibility.

The project's initial language is Python. Individual modules may be replaced
in the future with C++ or Rust implementations if real-world measurements
demonstrate the need.

Throughout all phases, the priorities are:

1. stability;
2. reliability;
3. additional features.

Responsiveness must not be sacrificed for nonessential features.

## Gate — Local models and GPU VRAM

Before the intended Linux platform can be specified or built, the project must
choose:

1. the local language model for short radio briefings;
2. the local typed decision model that sits beside that language model and
   answers bounded questions only.

Both models must be free to obtain and run locally. Paid weights and paid
cloud APIs are not acceptable. See `docs/DECISION_MODEL.md`.

Those choices determine VRAM and the AMD Radeon card. Later roadmap phases
that assume a target machine wait on this gate.

## Phase 0 — Project Documentation and Foundations

Goal: make the scope, constraints, and decision criteria explicit before
implementation.

Activities:

- complete the README, ARCHITECTURE, and ROADMAP;
- record approved decisions in the PROJECT_JOURNAL;
- select and add an open-source license (GPL-3.0-only and CLA; done);
- define the process for documenting decisions;
- define the minimum requirements for the first prototype;
- define the initial Python project structure;
- choose a free language model and a free typed decision model;
- derive VRAM and AMD Radeon requirements from those models;
- document the available hardware configuration after that choice.

Completion criteria:

- the prototype's scope and out-of-scope items are documented;
- open assumptions are identifiable;
- Python is documented as the initial technology rather than a permanent
  constraint;
- the license has been selected (GPL-3.0-only, with CLA for inbound
  contributions);
- the free language model and free typed decision model are named, with VRAM
  notes;
- the initial development environment has been defined;
- no library is mandatory without documented rationale.

## Phase 1 — Deterministic Pipeline with Synthetic Telemetry

Goal: demonstrate the complete flow without a real simulator.

Activities:

- define the first version of the internal telemetry model;
- create a synthetic telemetry source;
- build the minimum session state;
- implement at least one deterministic rule;
- produce a structured alert;
- provide text output;
- record events and errors locally;
- create repeatable scenarios for normal behavior and invalid data.

Completion criteria:

- the same scenario always produces the same result;
- the core operates without Internet access;
- missing or invalid data does not cause fabricated decisions;
- events can be verified automatically;
- the pipeline contains no dependencies on a specific simulator.

## Phase 2 — Recorded Telemetry Replay

Goal: test the core with realistic, reproducible sequences without connecting
a simulator.

Activities:

- define a local, versioned recording format;
- implement replay start, pause, stop, and speed control;
- preserve timestamps and source information;
- handle duplicate, missing, or out-of-order samples;
- measure processing times and stability;
- prepare test recordings free of sensitive or non-distributable data.

Completion criteria:

- a recording can be replayed multiple times;
- results are repeatable;
- the system handles interruptions and imperfect data;
- the format and its versioning are documented;
- replay uses the same internal model intended for future real sources.

## Phase 3 — Local Voice Output

Goal: deliver alerts to the driver without mandatory cloud services.

Activities:

- evaluate local TTS engines compatible with Linux;
- select an initial Italian voice;
- add a TTS adapter separate from the core;
- manage alert priority, queuing, and duplicate suppression;
- verify output through the DAC, mixer, and headphones;
- measure event-to-playback latency.

Completion criteria:

- at least one event generates a local voice alert;
- a TTS failure does not block the core;
- the alert remains available through the log and text output;
- resource usage and latency are documented.

## Phase 4 — Complete Validation on the Reference Linux Machine

Goal: verify self-contained, continuous core operation on the reference Linux
hardware before integrating a real simulator.

This phase assumes the model and GPU decision from the gate above.

Validation will use synthetic and recorded telemetry.

Activities:

- install the core on the reference Linux machine;
- configure automatic startup;
- verify the pipeline with synthetic telemetry;
- verify recorded telemetry replay;
- verify local text and voice output;
- run extended tests;
- measure CPU, memory, latency, temperature, and local storage;
- verify Wi-Fi and Ethernet;
- verify behavior after a restart and source loss;
- verify degradation in the event of a TTS error;
- document mandatory and optional hardware;
- identify any limitations that require optimization;
- evaluate replacing individual Python modules with C++ or Rust only when
  justified by measurements.

Completion criteria:

- the system starts without the development PC;
- it does not require Internet access for basic operation;
- the core operates using synthetic and recorded telemetry;
- it recovers from anticipated errors;
- a voice-output failure does not block analysis;
- Linux and GPU performance and limitations are documented;
- any optimizations are justified by real-world measurements;
- another user can reproduce the test bench by following the guide;
- the core is considered validated before connection to a real simulator.

## Phase 5 — Technical Evaluation of the First Real Simulator

Goal: decide which simulator can become the first officially supported one.

The current candidate is Gran Turismo 7, but it is not yet a definitive
requirement.

Activities:

- evaluate the telemetry transmission mechanism;
- identify supported platforms and configurations;
- identify the available fields, frequency, and format;
- verify reception over the local network;
- investigate data loss, duplication, and ordering;
- verify session, lap, and car identification;
- check stability across game updates;
- evaluate any required transformations or decoding;
- evaluate licensing, distribution, and documentation considerations;
- capture a short technical recording, if legally and technically possible;
- measure reception on the reference Linux machine;
- document results, limitations, and risks.

Completion criteria:

- a reproducible technical report exists;
- the useful data that is actually available is known;
- technical and legal risks are documented;
- the real source can be mapped to the internal model without introducing
  source-specific logic into the core;
- an explicit decision is made and recorded:

  - adopt GT7 as the first simulator;
  - postpone support for it;
  - select another simulator.

## Phase 6 — Adapter for the First Approved Simulator

Goal: connect the first real simulator without modifying the already validated
core.

Activities:

- implement the adapter for the selected simulator;
- convert real data into the internal model;
- handle connection, disconnection, and resumption;
- handle missing, duplicate, or out-of-order data;
- compare real and recorded data;
- run an end-to-end session;
- measure latency and resource usage on the reference Linux machine;
- document console or simulator, network, and Linux host configuration.

Completion criteria:

- the core contains no simulator-specific parsing;
- the adapter uses the same interface as synthetic and recorded sources;
- disconnection does not stop the service;
- a real session produces local events and alerts;
- performance and latency remain compatible with the validation results;
- installation and configuration are reproducible.

## Subsequent Phases

Subsequent phases will be detailed only after validation of the prototype and
the first real adapter.

Possible directions:

- additional rules and strategies;
- post-session analysis;
- driver memory;
- setup management;
- voice profiles;
- speech recognition;
- web dashboard or application;
- support for other simulators;
- optional remote language model;
- distribution through a ready-to-use image or installer;
- support for additional Linux workstations and mini PCs.

These items represent future possibilities, not already approved requirements.

## Decisions Still Required

The following must be decided before the intended platform can be built:

- the free local language model;
- the free local typed decision model that sits beside it;
- VRAM required to run both models together;
- the AMD Radeon card that meets that VRAM need;
- Python runtime environment;
- initial operating system;
- initial project structure;
- initial libraries;
- internal telemetry schema;
- recording format;
- first prototype rule;
- local TTS engine;
- quantitative performance criteria;
- initial simulator following technical evaluation;
- final distribution method.
