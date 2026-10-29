# PROJECT_JOURNAL.md

## Radio Beep and Listening — 2026-10-29

Decision:

A short radio beep opens every engineer line, as on a real pit-wall radio, so
neither the driver nor the engineer is caught by surprise. The beep is an
original synthesized chirp, not a recording of any broadcast sound. It plays
right before the voice.

When the driver presses the physical push-to-talk button, a beep opens the
driver's channel as well (planned with the button).

The engineer is always listening, locally, to sense the driver's mood from
the voice, and adjusts his tone while keeping his own character. Listening is
not a question: only the push-to-talk button tells the engineer that the
driver expects an answer. Mood changes how the engineer speaks, never what
the rules detect.

Reason:

The beep makes every radio exchange explicit. The button separates "the
engineer hears me" from "I am asking the engineer".

## Istinto, the Engineer's Supporting Mind — 2026-10-28

Decision:

The typed decision model is named Istinto. It is the engineer's supporting
mind: it makes the fast decisions (whether to speak, how urgently, and how
long) that let the engineer's voice, the language model, answer quickly and
correctly. Documents no longer call it the small model.

Reason:

Its parameter count is small, but its role is fundamental. The name states
what it does.

Both the voice model and Istinto will be selected again on the new reference
machine. The current pair is the 6 GB development-bench pair; the roles and
names stay.

## GPU Vendor Not Fixed — 2026-10-27

Decision:

The Linux reference platform no longer requires an AMD Radeon. Any GPU
supported by the local inference runtime that meets the VRAM floor (8 GB
minimum, 12 GB recommended) is acceptable. The exact card remains unchosen.

Reason:

The owner removed the vendor constraint. Measurements on one GPU or OS still
do not qualify another. Earlier entries that name an AMD Radeon describe the
decision at that time.

## The Engineer Speaks in His Own Words — 2026-10-27

Decision:

Every radio line is written by the language model. The phrase book is the
engineer's baggage: it shows how a pit-wall call is built, and it is never
aired as written. There is no canned fallback line.

Deterministic rules still detect events such as low fuel. The typed decision
model decides whether to speak, how urgent the call is, and whether there is
room for a longer message or a question to the driver. Urgency sets how long
the engineer may take to find his words: 1 second for `now`, 3 seconds for
`normal`, and 6 seconds for `calm`, as starting values to measure. Until the
neural grammar path exists, deterministic code answers in its place.

If the model does not answer in time or produces a rejected line, the radio
stays silent and the failure is reported as a defect to fix.

The engineer usually says little, sometimes more, and may ask the driver for
an opinion. Planned next: driver speech recognition with a physical
push-to-talk button near the wheel (hardware not yet chosen; voice activation
is not used), and memory that lets the engineer learn from race to race.

Reason:

The engineer should sound like a real pit-wall engineer, not a list of fixed
sentences. This supersedes the 2026-09-23 entries where the rule sentence was
the radio call and the language model only added an optional briefing.

## Automatic Development Releases — 2026-10-15

Decision:

Each push to `main` that passes the complete offline test workflow generates
a new GitHub Release for the tested commit, with automatically generated notes.
Versions start at `v0.1.0` and increment the patch number of the highest existing
stable version tag. Existing releases are retained, and repeating a successful
test run does not create another version for an already released commit.

Reason:

Development progress should produce traceable snapshots automatically, while
requiring the existing offline checks to pass before publication. Release
numbers do not imply a usable initial product, simulator adoption, or
Linux/AMD Radeon qualification.

## Repository Independence — 2026-10-14

Decision:

Public RaceEngineer documentation names only this project. Independence from
unrelated private work is stated in general terms in `AGENTS.md`, `README.md`,
`ARCHITECTURE.md`, `CONTRIBUTING.md`, and `docs/agents/domain.md`.

Reason:

The public repository is RaceEngineer. Other private experiments do not belong
in these files by name.

## Model Selection — 2026-10-01

Decision:

Briefings use qwen3.5:4b (Q4_K_M, Apache-2.0). The typed decision model is
qwen3.5:0.8b (Q8_0, Apache-2.0), a constrained classifier only. Both are local
and free. A grammar constraint is required. If the grammar fails or the call
times out, deterministic rules keep the radio. Measured cohabitation on the
RTX 3050 6 GB bench, both resident with keep_alive: 5729 MiB used, 274 MiB
free. The 1.7B pair used 5905 MiB and left 98 MiB free. Product floor is 8 GB
VRAM minimum and 12 GB recommended. The expected family is an AMD Radeon. The
exact SKU is not chosen.

Reason:

This is the pair that fits the 6 GB development bench. Two 4B checkpoints do
not. The 0.8B is usable only as a label classifier under GBNF or a JSON enum.
NVIDIA measurements are not Radeon qualification. Details are in
docs/MODEL_SELECTION.md.

## Decision Model Intervenes by Skill — 2026-09-23

Decision:

The typed decision model is a control layer. It runs only when a caller has
declared one of its skills and that skill is the job. It is not called on
every sample and it does not speak on the radio.

Skills remain the declared questions: speak/hold, canned/brief, and
grounded/reject. Fuel level, validity, and hysteresis stay in deterministic
rules. A critical rule alert already has its sentence, and that sentence is
the radio call. The language model rewrites it only after a declared skill
has answered brief on a task where a briefing is allowed.

A local timing check of qwen3.5:4b showed the failure this rule stops: a fast
reply that invented a corner instead of the fuel call. Speed without a
declared skill is not a radio path.

If the decision model is missing or times out, rules continue, and the
language model continues only for a briefing that was already approved. The
session does not block.

## Typed Decision Model Beside the LLM — 2026-09-23

Decision:

RaceEngineer will add a local typed decision model beside the language model.
The language model writes short radio briefings. The decision model answers
only declared questions such as speak/hold, canned/brief, and grounded/reject.
Deterministic rules keep critical alerts. Both models must be free and local.
Paid cloud decision APIs are out of scope. Intent lives in
`docs/DECISION_MODEL.md`. No implementation in this change.

## First Deterministic Fuel Rule — 2026-09-13

The sample pipeline now produces a structured low-fuel alert from explicitly
valid observations. Hysteresis suppresses repeated alerts until valid fuel
recovers or the source restarts, preserving predictable behavior without
inventing decisions from missing data. Synthetic and recorded input validate
the rule offline; sample recordings retain their existing format.

## First Data-Recovery Slice — 2026-09-13

The first simulator-independent recovery pipeline has landed: nullable telemetry
samples, repeatable synthetic input, versioned local recordings and file replay,
and text output, validated offline. An optional UDP probe reports transport
metadata only. This bounded slice establishes reproducible acquisition before
session analysis or simulator integration; it does not target Raspberry Pi or
introduce simulator protocol decoding.

# RaceEngineer - Design Journal

> Living document. Do not delete ideas: comment them out with `//`,
> always adding the reason. This document explains HOW the project came to be.

------------------------------------------------------------------------

# Project Origin

The original idea was not RaceEngineer.

The first experiments involved installing Open-LLM-VTuber with Ollama to
determine whether a completely local voice assistant was possible.

During these tests, a question arose:

"What if, instead of a simple desktop assistant, we built a real race engineer?"

From that moment, the project began to change.

------------------------------------------------------------------------

# Early Local Assistant Experiments

That early local assistant work is not RaceEngineer.

It is a separate line of work.

Reason:

-   it can also be used outside sim racing;
-   it enables experimentation with STT, TTS, and LLMs;
-   some of its code may be reused by RaceEngineer.

Decision: Keep the two lines of work separate.

------------------------------------------------------------------------

# Open-LLM-VTuber

Work completed:

-   Git installation
-   GitHub configuration
-   Python installation
-   uv installation
-   FFmpeg installation
-   Ollama configuration
-   Open-LLM-VTuber installation
-   Qwen model configuration
-   initial MCP issues
-   disabling MCP to get the system running
-   customization of Mao's prompt
-   translation into Italian
-   tests with Edge TTS

Issues encountered:

-   English voice
-   unsatisfactory Italian TTS
-   random errors during conversation
-   unreliable webcam microphone

Decision:

Purchase a dedicated USB lavalier microphone.

------------------------------------------------------------------------

# Microphone

ChatGPT's initial idea:

Desktop USB microphone.

Benito's comment:

// I prefer a lavalier. I do not want a microphone in front of me while
programming or gaming.

Final decision:

Purchased a MillSO USB lavalier microphone.

To be tested upon arrival.

------------------------------------------------------------------------

# Birth of RaceEngineer

During the discussion, the idea emerged to build a personal race engineer.

Initial hypothesis:

Use the main PC.

Subsequent decision proposed by Benito:

The PC must be used ONLY for development.

The initial platform must be a Raspberry Pi; the use of a mini PC or other
hardware will subsequently be evaluated according to performance requirements
and needs.

This became one of the most important decisions in the entire project.

------------------------------------------------------------------------

# Raspberry Pi

Test bench.

The software must operate as a standalone system.

No dependency on the PC.

The PC will be used only for:

-   development
-   testing
-   debugging

This decision affects the entire architecture.

------------------------------------------------------------------------

# Philosophy

Every new feature must be designed by asking:

"Will it run on the hardware?"

If the answer is NO:

determine whether:

-   it is truly necessary;
-   it can be rewritten;
-   the hardware needs to be upgraded.

------------------------------------------------------------------------

# AI

Important discussion.

Objection:

"A model must be trained."

Conclusion:

NO.

RaceEngineer must not create a new LLM.

It must use existing models.

The project's value will be:

-   logic
-   telemetry
-   memory
-   user experience
-   integration

NOT model training.

------------------------------------------------------------------------

# Codex

Use Codex directly inside VS Code.

ChatGPT:

in favor.

Roles established:

Benito: Product Owner.

Codex:

-   implementation
-   code
-   refactoring
-   testing

ChatGPT:

-   architecture
-   design
-   review
-   documentation
-   technical decisions

------------------------------------------------------------------------

# GitHub

Decision:

Public repository.

Reason:

-   history
-   collaboration
-   open-source project

------------------------------------------------------------------------

# Documentation

Important decision.

Write documentation BEFORE code.

Planned documents:

README.md PROJECT_CONTEXT.md ARCHITECTURE.md ROADMAP.md AGENTS.md
CHANGELOG.md PROJECT_JOURNAL.md

------------------------------------------------------------------------

# Recorded Ideas

-   A local coding assistant to facilitate coding with comments and
    suggestions.
-   Automatic opening of VS Code.
-   Opening the GitHub repository.
-   Git control.
-   Memory of simulator sessions.
-   GT7, F1, etc. setup database.
-   Fuel strategies.
-   Tire strategies.
-   Pit stop strategies.
-   Web dashboard or app for hardware tests on a phone.
-   Voice-controlled music and playlist management.
-   Future support for other simulators.
-   Modular system.
-   Interaction with the race engineer through the microphone.
-   Creation of various race engineer profiles based on language, tone,
    style, etc.
-   The race engineer must adapt to the driver and provide suggestions; if the
    driver struggles to apply them, it must find simpler alternatives and
    report driving errors during the lap.
-   Smart background music during the race, chosen from what happens on
    track (2026-10-27). Examples: losing positions starts a high-energy track
    (high-BPM hard rock or Eurobeat); a mountain-pass duel or an overtake
    gets Eurobeat in the Initial D spirit. Music always ducks under the
    engineer's radio and never covers a call. Tracks come from the owner's
    local library; RaceEngineer does not ship music.
-   Strategy, fuel, tyre, weather, race-awareness, coaching, and post-session
    ideas collected from a review of a commercial sim-racing coach
    (2026-10-28), rewritten in RaceEngineer's terms in
    `docs/FEATURE_IDEAS.md`.

Add ALL new ideas here, even if they seem useless.

Never delete them.

Comment them out and explain why.

------------------------------------------------------------------------

# Project Rule

Every important decision must be recorded here.

The goal is to allow anyone, including ourselves months from now, to
understand not only WHAT was decided, but above all WHY it was decided.

------------------------------------------------------------------------

# Hardware and Reproducibility

One of the project's main goals is to enable other users to reproduce
RaceEngineer without rebuilding the hardware environment from scratch.

The documentation must be detailed enough to allow a user to purchase the
necessary components, prepare them, and obtain a working system by following a
step-by-step guide.

## Philosophy

The goal is NOT merely to distribute the code.

The goal is to distribute an entire reproducible platform.

Every hardware component must be documented.

For each component, the following must be specified:

-   Model
-   Manufacturer
-   Rationale for selection
-   Whether it is mandatory or optional
-   Possible alternatives
-   Issues encountered
-   Configuration notes

## Planned Hardware

This section will be updated during development.

Planned initial configuration:

-   Raspberry Pi 3B+ (initial platform)
// Later decision: Raspberry Pi is not the RaceEngineer runtime target. See README.
-   Power supply
-   microSD card (capacity and class to be determined)
-   Wi-Fi or Ethernet connection
-   USB lavalier microphone
-   USB DAC connected to a mixer
-   Audio mixer
-   Headphones
-   Optional heat sink or fan
-   USB flash drive containing FLAC or MP3 songs; the maximum capacity
    supported by the Raspberry Pi must be verified

The following may be added in the future:

-   Raspberry Pi 5
-   Mini PC
-   Other compatible platforms

The software architecture must NOT depend on the selected hardware.

## Operating System

// Evaluate two distribution methods.

// Method A

// Distribute a ready-to-flash image directly, for example RaceEngineer OS.

// The user will only need to:

// 1.  Flash the microSD card.
// 2.  Insert it into the Raspberry Pi.
// 3.  Connect the hardware.
// 4.  Start the system.

// Method B

Distribute an automated installer.

The user will install the RaceEngineer project through an
installation script that automatically detects the OS, configures dependencies, services, and
settings.

The final solution will be selected during development.

## Final Goal

Anyone must be able to reproduce the project solely by following the official
documentation, without requesting additional information from the developers.

------------------------------------------------------------------------

# Journal Conventions

To keep the document simple and readable, fields such as "Active," "Paused,"
or "Discarded" will not be used.

Ideas must NOT be deleted.

Conventions:

-   A valid idea simply remains in the document.
-   `//` is used for personal comments, rationale, discarded ideas, paused
    ideas, and future reminders.
-   `#` and `##` are reserved exclusively for document headings and
    subheadings.

The goal is to preserve the reasoning that led to decisions, not to classify
every idea with a status.

------------------------------------------------------------------------

# Engineer Profiles

Decision:

RaceEngineer separates race-engineering logic from presentation.

The telemetry analysis, strategy engine, and deterministic decision-making
must remain completely independent from the way information is presented to
the driver.

Engineer Profiles are independent from any simulator or game.

Users choose the Engineer Profile they prefer from the profiles available,
regardless of the simulator currently in use.

An Engineer Profile may define:

- Voice Profile
- Communication style
- Verbosity
- Coaching level
- Intervention frequency
- Emotional tone

Engineer Profiles must never contain simulator-specific telemetry logic.

Rationale:

Changing the engineer should only change how technical information is
presented, never the underlying technical decisions.

------------------------------------------------------------------------

# Telemetry Adapter

Decision:

Telemetry acquisition is an independent architectural layer.

A Telemetry Adapter is responsible only for:

- acquiring telemetry from any supported source;
- translating telemetry into the internal RaceEngineer data model;
- exposing a common interface to the Race Engineer Core.

It must never define personality, communication style, or voice.

Rationale:

Keeping telemetry isolated allows the same Engineer Profile to operate
across every supported simulator without duplicating race-engineering
logic.

------------------------------------------------------------------------

# Voice Profiles

Decision:

Voice identity is independent from telemetry and Engineer Profiles.

A Voice Profile defines only how the engineer sounds.

The default configuration should associate one Voice Profile with each
Engineer Profile.

Multiple Engineer Profiles may share the same Voice Profile, and a single
Engineer Profile may optionally support different Voice Profiles.

Rationale:

Voice should be replaceable without affecting race logic or engineer
behavior.

// Idea still not completely defined, will decide later while working on it.

------------------------------------------------------------------------

# Layered Architecture

Decision:

RaceEngineer is composed of independent architectural layers.

A running configuration combines:

- Telemetry Adapter
- Race Engineer Core
- Engineer Profile
- Voice Profile

Each layer has a single responsibility and can evolve independently.

Rationale:

Separating responsibilities improves maintainability, portability,
testing, and future expansion.

------------------------------------------------------------------------

# User Freedom

Decision:

RaceEngineer never associates a specific Engineer Profile with a specific
simulator.

Any compatible Engineer Profile should be usable with any supported
simulator.

Users may create personal presets combining telemetry adapters,
Engineer Profiles, and Voice Profiles, but these mappings are optional and
user-defined.

Rationale:

The engineer is part of the user experience, not part of simulator
support.

------------------------------------------------------------------------


## Local and Deterministic Core

Decision:

The core will operate locally, without depending on the development PC,
mandatory cloud services, or an LLM. The local network may be used to receive
telemetry.

Rationale:

During a driving session, continuity of operation and predictability are more
important than technological complexity. An LLM may enrich the experience, but
it must not become a point of failure for critical decisions.

## Python as the Initial Technology

Decision:

Development will begin in Python while retaining the option to replace
individual modules with C++ or Rust in the future.

Rationale:

Python enables rapid development, runs on Raspberry Pi, and provides an
ecosystem suitable for future audio and AI integrations. However, it must not
become a constraint if real-world measurements reveal performance limitations.

## Performance First

Decision:

Stability, reliability, and responsiveness will take priority over additional
features.

Rationale:

The Raspberry Pi 3B+ has limited resources, and RaceEngineer must be useful
while driving. A nonessential feature does not justify a loss of system
responsiveness or reliability.

## Simulator-Independent Core

Decision:

The core will be developed and validated with synthetic and recorded telemetry
before integrating a real simulator. Gran Turismo 7 remains a candidate subject
to technical evaluation.

Rationale:

Separating the core from the real source makes it possible to proceed without a
connected simulator, create repeatable tests, and first verify compatibility
with the Raspberry Pi 3B+.

## Introduction of PROJECT_CONTEXT.md

Decision:

PROJECT_CONTEXT.md will represent only the current operational state and will
be rewritten at the end of each session, removing outdated information.

Rationale:

The Journal preserves the project's history and rationale, but it is not
suitable for quickly communicating the current state of work. A concise
operational document prevents the Journal from becoming a changelog or a copy
of the other documents.

## Workflow Change

Decision:

Each session will begin with the current state, continue with the historical
record and project documentation, and end by updating PROJECT_CONTEXT.md.

PROJECT_JOURNAL.md will be updated only when decisions, rationale, important
ideas, or changes in direction emerge, and always after user approval.

Rationale:

Separating operational state, project history, technical documentation, and
Git history reduces duplication and makes both the present state and the
reasons behind past decisions easier to understand.

------------------------------------------------------------------------

# Repository Language Decision — 2026-08-06

Decision:

The official language of the repository has been changed from Italian to
English. All repository documentation will be maintained in English.

Rationale:

The project is intended to become an international open-source project;
therefore, maintaining all repository documentation in English makes it
accessible and consistent for an international community.

------------------------------------------------------------------------

# Licensing Decision — 2026-09-03

Status when this entry is inserted: adopted.

Decision:

- The public outbound license of RaceEngineer is the GNU General Public
  License version 3 only (`GPL-3.0-only`).
- External contributions are accepted only under the Individual or
  Entity Contributor License Agreement.
- Contributors retain copyright in their Contributions.
- The maintainer receives a copyright license and a patent license
  sufficient to use, modify, distribute, sublicense, and relicense
  Contributions in the official project.
- The public project remains available under GPL-3.0-only.
- In parallel, the maintainer may offer alternative or proprietary
  licenses for the official project and for Contributions covered by
  the CLA.
- Commercial use, paid distribution, and paid support of the public
  project are allowed under GPL-3.0-only.
- A separate license is required only to distribute this software or a
  covered derivative without complying with the applicable GPL-3.0-only
  obligations.
- The rights holder of the official project is Benito Cifiello,
  personally, not a company.
- No governing-law or forum clause was adopted with the CLA.

Reason:

- The project is intended to remain genuinely open source.
- A permissive outbound license such as MIT was not adopted for the
  official project.
- `GPL-3.0-only` was chosen instead of `GPL-3.0-or-later` for
  outbound predictability.
- Copyleft applies to conveyed covered works. It does not prevent
  independent reimplementations or competing forks that comply with
  GPL-3.0-only.
- The CLA separates inbound rights from outbound terms so that a
  future parallel license does not depend on collecting consent from
  every past contributor.
- Copyright assignment was not adopted.
- AGPL was not adopted. The current product is a local system.
  Network copyleft remains a separate product decision.

Not adopted:

- MIT / BSD / Apache-2.0 as the project outbound license.
- AGPL as the initial outbound license.
- DCO as the only inbound instrument.
- Automatic CLA tooling.
- A public file of contributor personal data.
