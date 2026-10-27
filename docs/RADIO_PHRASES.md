# Pit-wall phrase book

This list is the engineer's baggage. It shows the language model how a
pit-wall call is built: short spoken lines, a concrete instruction, and no
markdown. It is not a script and not a whitelist. No line is ever aired as
written; the engineer always speaks in his own words.

The Italian examples are mirrored in `PHRASE_BOOK` in
`src/raceengineer/briefing.py`, which places them in the model prompt.

The Italian line is the driver-facing example. The English line is the same
call for training, not a second radio script.

| id | when | example IT | example EN |
| --- | --- | --- | --- |
| box_now | The car is called in on this lap. | Box, box. Questo giro. | Box, box. This lap. |
| stay_out | The car should remain on track. | Resta fuori. Continua così. | Stay out. Keep doing that. |
| lift_and_coast | The driver should save fuel without a pit call. | Alza e veleggia. Risparmia benzina. | Lift and coast. Save fuel. |
| manage | The driver should hold the tyres and the pace. | Gestisci il passo. Non spingere. | Manage the pace. Do not push. |
| push | The driver is clear to use the car. | Spingi ora. Pista libera. | Push now. Clear track. |
| radio_check | The wall checks that the driver can hear. | Radio check. Mi ricevi? | Radio check. Do you copy? |
