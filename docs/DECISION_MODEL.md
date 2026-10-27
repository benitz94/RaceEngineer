# Typed decision model

Status: neural weights selected, grammar path not implemented. Deterministic
code in `src/raceengineer/decision.py` answers each declared question in the
model's place until then.

Selected decision checkpoint: `qwen3.5:0.8b` (Q8_0, Apache-2.0), used only as a
constrained classifier (GBNF or a JSON enum of the declared labels).
Unconstrained text from this checkpoint is not a radio path. The engineer's
voice is `qwen3.5:4b`. See `docs/MODEL_SELECTION.md`.

## Roles

1. Deterministic rules (`src/raceengineer/rules.py`) detect events such as low
   fuel. Missing data must not invent an event. Fuel level, validity, and
   hysteresis stay here. Rules do not speak.
2. The **typed decision model** answers bounded questions with labels. It
   decides whether the engineer speaks, how urgent the call is, and whether
   there is room for a longer message or a question to the driver. It does
   not write radio text.
3. The **language model** is the engineer's voice. It writes every radio line
   in its own words. The phrase book in `docs/RADIO_PHRASES.md` is its
   baggage: it shows how a call is built and is never aired as written.

## Declared questions

Implemented, answered by deterministic code for now:

- `urgency` — `now`, `normal`, or `calm`. It sets how long the engineer may
  take to find his words: 1, 3, and 6 seconds, starting values to measure on
  the reference machine. A `high` priority alert is `now`.
- `grounded_or_reject` — whether a generated line invents telemetry or reads
  like a log. `reject` drops the line.

Planned, not declared in code yet:

- `speak` / `hold` — whether the radio may open now;
- long / short — whether there is room for a longer message or a question to
  the driver.

## Flow

1. Rules emit a structured alert.
2. The decision model answers `urgency`.
3. The language model writes the line within the urgency deadline.
4. `grounded_or_reject` checks it, then the radio output filters run.
5. An accepted line is printed and spoken.

There is no canned fallback. A missing model, a timeout, or a rejected line
leaves the radio silent. The failure goes to stderr and the run exits
nonzero, so it is fixed rather than hidden. Telemetry analysis continues.

A local check of `qwen3.5:4b` on fuel 10.0 / `fuel_low` returned in 0.98 s and
invented a corner. That is why every line passes `grounded_or_reject`.

## Constraints

- Free weights only. Local inference only. Apache-2.0 for the selected pair.
- The 0.8B checkpoint shares a GPU with `qwen3.5:4b`. Product floor is 8 GB
  VRAM minimum and 12 GB recommended. A 6 GB card is a development bench only.
- Do not route fuel, validity, or hysteresis through either model.
- Do not import product architecture from other private repositories.

## Out of scope for the current slice

Training a new foundation model, cloud routers, desktop UI, simulator decode,
speech recognition, and race-to-race memory. Speech recognition with a
physical push-to-talk button and memory are planned next.
