# Automation Lead-In (lab output)

This is the output of the Week 7 lead-in lab. It forms part of the Phase 1 evidence folder, aligning the state machine, human checkpoint, and audit log definitions with `ARCHITECTURE.md`.

## Part 1: State machine (illegal moves count too)

| From | To | Who may do it | Notes / Classification |
|---|---|---|---|
| `booked` | `confirmed` | `staff` | Allowed (human checkpoint) |
| `confirmed` | `arrived` | `staff` | Allowed (client arrives at salon) |
| `arrived` | `completed` | `staff` | Allowed (service finished) |
| `booked` | `cancelled` | `client`, `staff` | Allowed (pre-confirmation cancellation) |
| `confirmed` | `cancelled` | `client`, `staff` | Allowed (post-confirmation cancellation) |
| `confirmed` | `no_show` | `staff` | Allowed (client missed appointment) |
| `booked` | `confirmed` | `client` | Rejected as `not_permitted` (only staff may confirm) |
| `confirmed` | `arrived` | `client` | Rejected as `not_permitted` (only staff may mark arrived) |
| `booked` | `completed` | `staff` | Rejected as `illegal_move` (skips confirmed & arrived) |
| `completed` | `cancelled` | `client` | Rejected as `illegal_move` (move out of terminal state) |
| `cancelled` | `booked` | `staff` | Rejected as `illegal_move` (move out of terminal state) |

## Part 2: Human checkpoint

| Field | Your answer |
|---|---|
| Who approves | Front desk staff |
| What they see | Client identifier, requested service & duration, stylist, scheduled time slot, and conflict status |
| On accept | Appointment transitions to `confirmed`; system logs an automated reminder entry to `reminders.log` |
| On reject / cancel | Appointment transitions to `cancelled` with reason logged in `audit_log`; slot is freed for rebooking |
| On no answer | Booking remains in `booked` status; client is not notified of confirmation and stylist is not committed |

## Part 3: Audit log (three example rows)

| item | actor | old | new | rejected attempts logged? |
|---|---|---|---|---|
| B-001 | client-a | (none) | `booked` | Initial creation accepted |
| B-001 | staff | `booked` | `confirmed` | Human checkpoint confirmed; reminder dispatched to log |
| B-001 | client-a | `confirmed` | `arrived` | Yes: rejected as `not_permitted` (only staff can check in) |
| B-001 | staff | `confirmed` | `arrived` | Check-in accepted |
| B-001 | client-a | `completed` | `cancelled` | Yes: rejected as `illegal_move` (terminal state immutable) |

## Part 4: Scheduled job (before / after)

| Item | Before | After | Side effect |
|---|---|---|---|
| B-010 (unconfirmed 24h before appointment) | `booked` | `booked` (flagged for review) | Appends a warning line to daily front-desk report; no real message sent |
| B-012 (no-show after appointment end time) | `confirmed` | `no_show` | Marked as unfulfilled after 60m past end time; log entry written |

**Safe to run twice?**
Yes. The scheduled job queries specifically for items matching `state = 'confirmed'` where current time is past the end threshold and state has not already transitioned to `no_show`. A second run finds 0 matching items and performs no further mutations (idempotent).

## Part 5: Prediction and peer check

| Question | My prediction | Partner's check |
|---|---|---|
| Will invalid start dates crash the system? | No: `bad_date_format` is caught by regex and `strptime`, returning a 400 rejection without throwing unhandled exceptions. | Verified: test case `seeded_bad_date_format` returns `bad_date_format`. |
| Can concurrent requests double-book a stylist? | No: the conflict check calculates interval intersection across existing non-cancelled bookings. | Verified: `seeded_conflict` and `count_after_all_requests` confirm early requests keep the slot. |
