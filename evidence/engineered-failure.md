# Engineered Failure Record

Break one thing on purpose, predict what happens first, then prove it. Write the prediction **before** you break anything.

| Field | Your entry | Example (Idea 2) |
|---|---|---|
| Date and time of prediction | Nov 13, 01:25 | *Oct 29, 14:05* |
| What I will break | Client attempts to cancel an appointment that has already reached the `completed` state. | *Submit two bookings for the same provider and the same time* |
| Prediction: what the tool will do | The tool will reject the move with `illegal_move` and preserve state as `completed` because `completed` is a final state. | *The second booking is rejected with `conflict`; the first is unchanged* |
| Evidence (paste output or log lines) | When `completed` was not guarded in `FINAL_STATES`, the app permitted the client to move `completed -> cancelled`, incorrectly erasing a finished service record: `FAIL cannot_cancel_completed: expected {'outcome': 'illegal_move', 'state': 'completed'}, got {'outcome': 'accepted', 'state': 'cancelled'}` | *Second booking was accepted; the schedule shows two bookings at 10:00* |
| What was wrong (cause) | Allowed transitions did not check for immutable terminal states before processing client cancel requests. | *The conflict check compared dates only, not times* |
| Fix (commit hash and one sentence) | Enforced `current_state in FINAL_STATES` check at the start of `move_appointment`, returning `illegal_move`. | *a1b2c3d: compare date and start time* |
| Repeat test (case name in `cases.json`) | `cannot_cancel_completed`, now PASS | *`double_booking_conflict`, now PASS* |

If the prediction was right the first time, say so and explain what that tells you. If it was wrong, say what you learned.
The prediction was correct: once the terminal state check is strictly enforced, any move out of `completed` is flagged as `illegal_move` and leaves the appointment state unchanged.
