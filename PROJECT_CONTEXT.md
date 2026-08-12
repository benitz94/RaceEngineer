# Project Context

Last updated: 2026-08-13

## Current State

RaceEngineer is in its documented foundation stage. The initial project documentation and architecture are complete, but no application code has been written.

Git has been initialized, the initial commits have been created, and the public GitHub repository is available at `benitz94/RaceEngineer`.

English is the official repository language.

## Available Hardware and Roles

The main development PC remains the environment for development, testing, and debugging.

A Raspberry Pi 3B+ is available as the initial standalone RaceEngineer target platform and practical test bench.

The old Acer All-in-One Linux machine was recovered on 2026-08-13. Its previous Debian 10.9 installation was removed, and MX Linux 25.2 Xfce with SysVinit was installed successfully on the internal 1 TB Toshiba HDD. The Acer boots correctly from the internal disk.

The Acer provides approximately 3.7 GiB of RAM. MX Linux uses approximately 1.0 GiB at idle, leaving approximately 2.8 GiB available, and an active 2 GiB swap file provides additional memory headroom. Basic desktop operation and browser/YouTube playback were satisfactory.

The Acer is not the RaceEngineer target hardware and is not the main development PC. Its planned role is a Linux support and test workstation for Raspberry Pi work when the project reaches the appropriate stage.

The operational hardware distinction remains:

- development PC: development, testing, and debugging;
- Acer with MX Linux: Linux support and test workstation for Raspberry Pi work;
- Raspberry Pi: initial standalone RaceEngineer target and test platform.

## Next Objective

Begin the first implementation task defined by `ROADMAP.md`.

## Essential Files

1. `README.md` — project overview and scope.
2. `ARCHITECTURE.md` — architectural boundaries and component design.
3. `ROADMAP.md` — implementation sequence and milestones.
4. `PROJECT_JOURNAL.md` — permanent decisions and project history.
5. `AGENTS.md` — repository working rules.
