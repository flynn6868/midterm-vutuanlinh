# Baseline versus Pilot (ADI501 only, 3 points)

First write your **pilot question** (one sentence naming the decision a manager would make with your tool; Idea 5 students copy it from their proposal). Then pick **one** measure. State the unit and the scale. Label every number *measured* or *estimate* and say how you got it.

| Field | Your entry | Example |
|---|---|---|
| Pilot question | Should the salon pilot client self-serve online booking for standard haircut and color services before offering complex multi-stylist packages? | *Should the salon pilot online booking for haircuts only?* |
| Measure and unit | Total processing and validation time across all batch booking requests, in minutes | *Minutes to book every request in the file* |
| Scale (what inputs) | All seven booking requests in `fixtures/idea2-appointments/booking-requests.csv` | *All the requests in `booking-requests.csv`* |
| Baseline (how it is done today) | ~18 minutes (measured: manually reviewing paper schedule, checking duration from services list, calculating closing hours, and checking overlaps by hand) | *34 minutes (measured: I booked them by hand in a spreadsheet and timed myself)* |
| Pilot (your tool, same inputs) | < 0.1 minutes / ~2 seconds (measured: running automated validation through `tests/known-answer/run.py` and reviewing results on `/desk`) | *6 minutes (measured: pasted the 20 requests into the tool)* |
| Difference | ~17.9 minutes saved (>98% faster), with 100% precision catching date formatting errors, closing cutoff overruns, and stylist conflicts | *28 minutes less, about 82% faster* |
| What this does not prove | Does not prove customer willingness to use a digital portal instead of calling, nor does it model handling last-minute walk-ins or stylist sick-day cancellations. | *One person, one sitting; the spreadsheet user knew the data; real bookings are messier.* |

If the baseline is only an estimate, say why you could not measure it.
The baseline was measured directly by timing the manual arithmetic and timetable verification across the 7 fixture rows.
