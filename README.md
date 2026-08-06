# RaceEngineer

RaceEngineer was conceived to bring a true personal race engineer alongside
the driver, prioritizing reliability, reproducibility, and local operation over
technological complexity.

The purpose of the project is not to demonstrate the use of artificial
intelligence, but to build a genuinely useful tool for driving sessions.

RaceEngineer is a local, open-source project for sim racing.

Its goal is to receive telemetry from a simulator, analyze it using
deterministic logic, and provide the driver with useful information during and
after the session.

The project is designed as a self-contained, reproducible platform, initially
running on a Raspberry Pi 3B+.

## Project Status

RaceEngineer is currently in the design and prototyping phase.

No usable initial version exists yet.

Gran Turismo 7 is the initial candidate simulator, but support for it is not
yet a definitive requirement. The availability, format, stability, and terms
of use of its telemetry must first be technically evaluated.

The core will initially be developed, tested, and validated using synthetic or
recorded telemetry, without requiring a connection to a real simulator.

## Initial Technology

The project's initial language is Python.

This choice is motivated by:

- rapid development;
- Raspberry Pi compatibility;
- integration with AI, Ollama, STT, and TTS;
- availability of a broad library ecosystem.

Python is the project's initial technology, not a permanent constraint.

The architecture must allow individual modules to be replaced in the future
with C++ or Rust implementations if real-world measurements demonstrate that
performance requirements make this necessary.

## Goals

RaceEngineer must be able to:

- operate independently of the PC used for development;
- operate without mandatory cloud services;
- receive telemetry over the local network from a console or simulator;
- analyze telemetry entirely locally;
- generate alerts through deterministic, verifiable rules;
- play local voice alerts;
- retain useful session data;
- be extended to additional simulators and hardware platforms in the future;
- be installed and reproduced by following the official documentation.

## Project Principles

### Utility Before Complexity

Above all, RaceEngineer must be a useful tool during a driving session.

Technologies, AI, and additional features have value only when they tangibly
improve the driver's experience without compromising system operation.

### Local First

The core must continue to operate without an Internet connection.

Any online integrations must be optional and must not be required for core
functionality.

### No LLM in the Critical Path

RaceEngineer does not require an LLM to analyze telemetry or make critical
decisions during a race.

An LLM may be added as an optional module for features such as:

- natural rephrasing of messages;
- post-session explanations;
- conversation;
- assisted data exploration.

The absence or failure of the LLM must not prevent the core from operating.

### Performance First

Every new feature must also be evaluated against the resources available on
the reference hardware.

The priority order is:

1. stability;
2. reliability;
3. additional features.

RaceEngineer must not sacrifice system responsiveness to add nonessential
features.

### Simulator Independence

The core must be fully developable, testable, and validatable without a
connected simulator.

Simulator integrations must be implemented through separate adapters and must
not introduce simulator-specific logic into the core.

### Hardware Independence

The initial platform is the Raspberry Pi 3B+, but the architecture must not
depend on a specific computer model.

The hardware may evolve based on real-world performance measurements and
needs.

Similarly, individual Python modules may be replaced in the future by C++ or
Rust implementations without requiring the entire system to be rewritten.

### Modularity

Telemetry sources, the analysis core, persistence, and output systems must be
separate.

Adding a new simulator, changing the audio system, or replacing a module's
implementation should not require the core logic to be rewritten.

### Reproducibility

The project will distribute more than code alone.

Hardware, operating system, installation, configuration, and known issues must
be documented so that another user can build a working system without direct
assistance.

## First Prototype

The first prototype will be a minimal local pipeline:

1. load or generate telemetry;
2. replay it with controlled timing;
3. convert it into a common internal format;
4. update the session state;
5. detect at least one event through a deterministic rule;
6. produce a text alert;
7. when available, play the same alert through local TTS;
8. record events, alerts, and diagnostic data.

The prototype will not initially include:

- speech recognition;
- an LLM;
- mandatory cloud services;
- a complete dashboard;
- advanced strategies;
- adaptive driver memory;
- music management;
- simultaneous support for multiple simulators.

## Planned Initial Hardware

Initial test bench:

- Raspberry Pi 3B+;
- power supply;
- microSD card, capacity and class to be determined;
- Ethernet or Wi-Fi connection;
- USB lavalier microphone, not required for the first prototype;
- USB DAC connected to a mixer;
- audio mixer;
- headphones;
- optional heat sink or fan.

Component models, alternatives, requirements, and configuration will be
documented during development.

## Documentation

- `PROJECT_JOURNAL.md`: origins, intentions, and decision rationale;
- `ARCHITECTURE.md`: system components, boundaries, and flows;
- `ROADMAP.md`: development phases and completion criteria;
- `AGENTS.md`: operating rules for repository contributors.

`PROJECT_JOURNAL.md` is the primary source for the project's intent and
decision history.

## Separate Projects

RaceEngineer is not the AI Desktop Companion created through the Open-LLM-VTuber
experiments.

The two projects must remain independent. Any reused code must be imported
explicitly, documented, and compatible with the license selected for
RaceEngineer.

## License

The repository is intended to be open source.

The license has not yet been selected.
