# Feature ideas

Status: ideas only, recorded 2026-10-28. None of these is an approved
requirement, a roadmap commitment, or implemented. They were collected after
reviewing a commercial sim-racing coaching and strategy product and are
rewritten here in RaceEngineer's own terms. No text, code, assets, or data
from that product are used.

Every idea follows the existing architecture:

- deterministic rules compute the facts (fuel, windows, gaps, wear);
- the typed decision model decides whether, how urgently, and how long the
  engineer speaks;
- the language model says it in its own words over the radio;
- missing telemetry is reported as unavailable, never guessed;
- everything runs locally, with no account or Internet connection required.

What a simulator can provide decides what is possible. Each idea depends on
the fields its adapter exposes.

## Race strategy

- **Stop plan.** The fewest stops for the race length, from the fuel or
  energy the car really uses, with a pit window for each stop.
- **What each stop does.** Fuel to add (with a safety margin), tyres to fit,
  and repairs, under the game's pit rules.
- **Next action.** A box countdown ("box in N laps"), then the call on the
  lap itself.
- **Plan tracking.** Whether the race is still on plan, and a new plan when
  something changes (damage, weather, a caution).
- **Fuel saving offered once.** Only when saving fuel removes a whole stop,
  with how much to save per lap.
- **Cheap stop under caution.** When a safety car, virtual safety car, or
  full-course yellow makes a stop cheaper and the rules allow it.
- **Rejoin position.** Where the car would rejoin if it pitted now, and
  whether the track ahead and behind is clear.
- **Rival stops.** When nearby rivals have stopped, their likely stops, and
  undercut or overcut threats.
- **Quiet outside races.** Strategy calls stay silent in practice and
  qualifying unless the driver asks.

## Fuel

- Current fuel in litres and as a share of the tank.
- Consumption per lap: last, average, minimum, maximum, over a rolling window.
- Laps and time remaining at the current average.
- Fuel needed to finish and fuel to add at the stop.
- Push-or-save guidance and status levels (good, ok, low, critical).

## Tyres, damage, and car state

- Tyre wear in laps remaining, pressures, and temperatures.
- Damage: repair at the stop, box now, or carry on.
- Brake temperatures and car balance (understeer or oversteer by corner phase),
  when the simulator exposes the inputs to measure it.

## Weather and track

- Sky, rain, track wetness, air and track temperature, with their trend.
- Wind direction relative to the car, when published.
- A short-term outlook that labels each value honestly: a reading, fixed
  session weather, a projection with its confidence, or not enough history.
- A countdown when rain is approaching, only from measured trends.

## Race awareness

- Standings and relative gaps to the cars ahead and behind.
- Side-by-side awareness from car positions, saying "no data" rather than
  "clear" when positions are unavailable.
- Penalties and flags carried by other cars, with how long they have carried
  them, labelled as RaceEngineer's own measurement.
- A clean-laps counter.
- Pit entry help: speed limiter timing and the estimated pit-lane time.

## Driving coaching

- **Reference lap.** A benchmark to coach against: the driver's own best, a
  chosen lap, or a dynamic reference that follows the driver's pace, and the
  option to make it easier or harder.
- **Corner cues.** Before a corner, one short cue ("brake later"); after the
  exit, what went right or wrong.
- **Focus.** Coach only braking, steering, throttle, or trail braking when the
  driver is working on one skill.
- **Corners to coach.** Default to the corners that cost the most time.
- **Detail level.** Direction only in races ("brake later"), numbers in
  practice ("brake ten metres later").
- **Audio cues.** Optional short beeps at the reference braking or lift point,
  separate from the engineer's voice.
- **Suppression.** No coaching on warm-up laps, after resets, or after any
  abnormal position jump, so advice never rests on invalid data.
- **Speech speed.** Adjustable speaking rate.

## After the session

- An automatic report per lap or session: time lost by corner, traces against
  the reference, and the racing line on a track map.
- An optimal lap from the best sectors, and progress over days on the same car
  and track.
- Asking the engineer after the session: "where do I lose time?", "compare my
  last lap with my best", "is it me or the car?", "how many laps of fuel are
  left?". Answers are measured from recorded laps, never estimated.
- Setup help grounded in the laps driven: one change at a time, then compare.
- The engineer remembers what it advised for each car and track, as part of
  race-to-race memory.

## Displays

- Optional on-screen or second-screen widgets (phone, tablet, second monitor)
  for strategy, fuel, gaps, and weather, alongside the radio. On a console a
  separate screen is the only option.

## Not adopted

- Mandatory accounts, cloud chat, and subscriptions: they conflict with local
  first and free operation.
- A global online leaderboard and team sharing: possible only as optional,
  explicit online features, if ever.
