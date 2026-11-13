# Salon Appointment & Intake (Idea 2)

> DRAFT for Step 1.2: feature names are my best guess and will be refined after the plan (Step 1.4) and in `ARCHITECTURE.md` (Step 1.7). Nothing is built yet.

## Run it
`python3 app.py`, then open `http://localhost:8000` (client booking form) and `http://localhost:8000/desk` (front desk).

## Python and version
Python 3.11+. Standard library only (`wsgiref`, `sqlite3`, `json`), so no `requirements.txt` packages are needed.

## Test it
`python3 tests/known-answer/run.py` prints one PASS or FAIL line per case.

## My cut line
**Will certainly finish:**
- Booking form for clients
- Validation: `bad_date_format`, `after_close`, `conflict`, `duplicate_request`
- Appointment state machine: `booked` → `confirmed` → `arrived` → `completed`, plus `no_show` and `cancelled`, with role limits
- Front-desk schedule page
- SQLite persistence that survives a restart
- Reminders written to a log file
- Front-desk confirm step
- Known-answer tests and the engineered failure

**Drop first:**
- Per-stylist filtered view
- Reschedule screen
- Styling and polish
- Live auto-refresh (use a manual refresh button)

## Difficulty Bar: the feature that meets each row
| # | Requirement | My feature (name the file or page) |
|---|---|---|
| 1 | Two or more roles with different views | `/` booking form for `client`; `/desk` schedule and actions for `staff` |
| 2 | A tracked state with rules | `booked → confirmed → arrived → completed`, plus `no_show` and `cancelled`; only `staff` may move a state, and any move not in the transition table is `illegal_move` |
| 3 | Persistence | SQLite `appointments.db`; state is still there after a restart |
| 4 | Staff dashboard or queue | `/desk` lists all bookings by stylist and time, and updates when a client books |
| 5 | A fake external step | `send_reminder()` appends a line to `reminders.log` and never sends a real message |
| 6 | A human checkpoint | Front desk must press "Confirm" before a booking becomes `confirmed` and a reminder is logged |
| 7 | Known-answer tests plus one engineered failure | `tests/known-answer/cases.json` and `run.py`; failure drill recorded in `evidence/engineered-failure.md` |

**Three complexity-menu items and where they appear:**
- Persistent store: SQLite `appointments.db`
- Human-approval step: front-desk confirm on `/desk`
- Automated test suite: `tests/known-answer/run.py`, plus an audit log of every state change

## State table
| From | To | Who may do it |
|---|---|---|
| `booked` | `confirmed` | `staff` |
| `confirmed` | `arrived` | `staff` |
| `arrived` | `completed` | `staff` |
| `booked` or `confirmed` | `cancelled` | `client` or `staff` |
| `confirmed` | `no_show` | `staff` |

`completed`, `cancelled` and `no_show` are final. Any move not in this table (including any move out of a final state) is `illegal_move`, checked first. A move in the table made by the wrong role is `not_permitted`.


## How `run` talks to my app
`run.py` hooks (`new_app`, `restart_app`, `do_step`) will call the app's WSGI function directly (no network), using a fresh temp SQLite file per case. The mapping table from my internal words to the contract words lives in `run.py`, and I'll copy it to `evidence/mapping-table.md` for Phase 2.

## Data-safety boundary
- All clients, stylists and services are made up (for example `client-a`, `Ana`, `Ben`).
- There are no credentials, API keys or real contact details.
- Reminders are only written to `reminders.log` and are never sent by email, SMS or any other channel.
