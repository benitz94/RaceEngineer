# PROJECT_JOURNAL.md

# RaceEngineer - Design Journal

> Living document. Do not delete ideas: comment them out with `//`,
> always adding the reason. This document explains HOW the project came to be.

------------------------------------------------------------------------

# Project Origin

The original idea was not RaceEngineer.

The first experiments involved installing Open-LLM-VTuber with Ollama to
determine whether a completely local AI Desktop Companion was possible.

During these tests, a question arose:

"What if, instead of a simple AI Desktop Companion, we built a real assistant?"

From that moment, the project began to change.

------------------------------------------------------------------------

# AI Desktop Companion

AI Desktop Companion is NOT RaceEngineer.

It is a separate project.

Reason:

-   it can also be used outside sim racing;
-   it enables experimentation with STT, TTS, and LLMs;
-   some of its code may be reused by RaceEngineer.

Decision: Keep the two projects separate.

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

-   AI Desktop Companion to facilitate coding with comments and
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

Evaluate two distribution methods.

Method A

Distribute a ready-to-flash image directly, for example RaceEngineer OS.

The user will only need to:

1.  Flash the microSD card.
2.  Insert it into the Raspberry Pi.
3.  Connect the hardware.
4.  Start the system.

Method B

Distribute an automated installer.

The user will install Raspberry Pi OS and then RaceEngineer through an
installation script that automatically configures dependencies, services, and
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

# Session of 2026-08-06

During this session, the following project decisions were defined and approved.

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
