# Midterm Workbook

Type your answers here, in your own words. Short is fine. Where a section says "evidence", put the detail in the named file and summarize here. Do not paste AI output as answers.

| Section | Summarize here | Full detail |
|---|---|---|
| 1 Setup and cut line | Cut line, seven rows | `README.md` |
| 2 Tests first | What your cases cover | `tests/known-answer/cases.json` |
| 3 Plan review | Plan summary, what you rejected | `ai-use-log.md` |
| 4 Engineered failure | Prediction, result | `evidence/engineered-failure.md` |
| 5 Merge (Phase 2) | Base, what you dropped | `evidence/merge-decision-log.md` |
| 6 Presentation prep | Your contribution, your challenge answers | (this file) |
| 7 Reflection | Answers | (this file) |
| ADI501 | Summary | `evidence/governance-table.md`, `baseline-vs-pilot.md`, `support-burden.md`, `thresholds.md` |

## Section 1: Setup and cut line

**1.1** My idea, team, and one-sentence user and job:
Idea 2; A front-desk manager and clients who need an intake and conflict-free booking system with staff confirmation.

**1.2** Features I will certainly finish:
Client booking form, four rejection validation checks (duplicate_request, bad_date_format, after_close, conflict), appointment state machine with role enforcement, front-desk schedule queue, SQLite persistence, sandboxed reminder logging, and human checkpoint confirmation.

**1.3** Features I will drop first:
Per-stylist filter views, client reschedule screen, CSS visual styling polish, and automated live websocket polling.

**1.4** For each Difficulty Bar row, the exact feature that meets it (one line per row, 1 to 7):
1. Two roles with different views: `/` for client booking form; `/desk` for front-desk staff schedule queue.
2. Tracked state with rules: `booked -> confirmed -> arrived -> completed`, plus `no_show` and `cancelled`; only staff can advance state.
3. Persistence: SQLite database `appointments.db` storing appointments and audit logs.
4. Staff dashboard: `/desk` queue listing bookings in chronological order.
5. Fake external step: `send_reminder()` writing notification records to `reminders.log`.
6. Human checkpoint: Front desk "Confirm" action required before reminder is logged and appointment is confirmed.
7. Known-answer tests + engineered failure: `tests/known-answer/cases.json`, `run.py`, and `evidence/engineered-failure.md`.

## Section 2: Tests first

**2.1** Which fixture rows are seeded failures, and how did I find them without asking an agent to list them?
- `B-005`: `bad_date_format` because date is formatted as `11/02/2026 10:30` instead of `YYYY-MM-DD HH:MM`.
- `B-007`: `after_close` because service S4 (30m) starting at 16:45 finishes at 17:15, after 17:00 closing.
- `B-002`: `conflict` because Ana is already booked with B-001 (09:00 - 09:45).
- `B-006`: `conflict` because Ben is already booked with B-004 (09:30 - 10:15).
Found by inspecting `booking-requests.csv` in file order and calculating durations from `services.csv` against the 09:00-17:00 schedule.

**2.2** One total or count I computed by hand, with the arithmetic:
Accepted bookings count = 3 items (B-001 Ana 45m, B-003 Ana 20m, B-004 Ben 45m). Rejected = 4 items (B-002 conflict, B-005 bad date, B-006 conflict, B-007 after close). Total items remaining after full file ingestion: 3 items.

**2.3** Did my `tests:` commit come before my first build commit? Paste the two `git log --oneline` lines.
```
cd22830 tests: known-answer cases written before build
4370211 build: core store, state validation rules, and known-answer test hooks
```

## Section 3: Plan review

**3.1** The first three slices the agent proposed, in one sentence each:
- Slice 1: Database store initialization and the four input validation rules (`duplicate_request`, `bad_date_format`, `after_close`, `conflict`).
- Slice 2: State transition engine enforcing role permissions and immutable terminal states.
- Slice 3: Known-answer test runner hooks in `run.py` demonstrating data persistence across restarts.

**3.2** One thing in the plan I rejected or changed, and why:
Rejected using Flask for web routing; Python standard library `wsgiref` is zero-dependency and eliminates package installation risks during fresh clone grading.

**3.3** One command I did not approve, and the row of the command decision table that explains it:
Did not approve `pip install flask`; row 5 of the command decision table records this rejection to keep the build strictly standard library.

## Section 4: Engineered failure

**4.1** What I broke and what I predicted:
Attempted a move from terminal state `completed` to `cancelled` by a client. Predicted: Rejected as `illegal_move` and state remains `completed`.

**4.2** What happened, and was my prediction right? What did I learn?
When the `FINAL_STATES` check was bypassed, the system erroneously allowed cancellation of a completed appointment. Once the check was re-enabled, the repeat test `cannot_cancel_completed` passed. Learned that terminal state immutability must precede role-based checks.

## Section 5: Merge (Phase 2)

**5.1** Which build was the base and why (about the system, not the person):
(Phase 2)

**5.2** One case that failed after porting a component, and what I did:
(Phase 2)

**5.3** One thing the transfer trial teammate got stuck on:
(Phase 2)

## Section 6: Presentation prep

**6.1** The commit that shows my own contribution (hash and one sentence):
`cd22830` — Created and committed 11 hand-crafted known-answer test cases covering all edge cases, seeded failures, and role restrictions before any application code was written.

**6.2** Pick a component I did not write. Explain in three sentences what it does and one thing that would break if it were removed:
(Phase 2 / 3)

**6.3** If the instructor asks me to add a new state live, which three files change?
1. `store.py`: Add the state to `ALLOWED_TRANSITIONS` (and `FINAL_STATES` if terminal).
2. `app.py`: Add the action button / badge styling to `render_staff_page()`.
3. `tests/known-answer/cases.json`: Add a known-answer test case exercising the new transition.

## Section 7: Reflection

**7.1** One thing the agent got wrong that my known-answer tests caught:
The initial state validation logic permitted cancellation from any state; tests caught that cancelled moves from `completed` must be rejected as `illegal_move`.

**7.2** One thing I would do differently if I started again:
I would define the exact data structures and role dictionaries earlier to make the initial test writing even faster.

**7.3 (required) Job link.** Name one real job task this tool maps to (for example, "a front-desk manager checks a booking for conflicts") and one thing it would still need before anyone could use it for real work (for example, real data, accounts, or a human review step):
Maps to a front-desk receptionist managing daily intake, verifying schedule conflicts, and confirming clients. For real production use, it would need secure multi-user authentication (passwords/sessions), automated SMS notifications via Twilio, and calendar synchronization with external provider schedules.

## ADI501 additions (summaries)

**A.1** The biggest governance risk in my tool and what I did about it:
Unauthorized client modification of appointments and data exposure. Mitigated through role-enforced state transitions in `store.py` and sandboxed local logging.

**A.2** My baseline and pilot numbers (label measured or estimate), and what they do not prove:
Baseline ~18 minutes (measured manually on spreadsheet) vs. Pilot < 0.1 minutes (measured automated test run); does not prove client willingness to book digitally rather than calling.

**A.3** The thing most likely to break in six months, and who would fix it:
Stylist roster changes, altered service durations, or special holiday hours; a salon manager would update `services.csv` and opening hour constants.

**A.4** My thresholds, and why those numbers:
09:00 - 17:00 operating window, fixed by salon policy in `fixtures/idea2-appointments/RULES.md`.
