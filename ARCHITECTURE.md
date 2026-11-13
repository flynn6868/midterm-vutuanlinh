# Architecture: Salon Appointment & Intake (Idea 2)

## Entities
The system stores two core entities in SQLite and loads one static configuration dataset:

1. **Appointment**: Represents a client's scheduled salon service.
   - `id`: Auto-incrementing integer identifier (1-based item index used by test harness).
   - `request_id`: Client/external booking request identifier (e.g. `B-001`, `T-1`). Unique.
   - `client`: Identifier or name of the client (e.g. `client-a`).
   - `service_id`: Reference to service catalog (e.g. `S1`, `S2`).
   - `stylist`: Service provider name (`Ana` or `Ben`).
   - `start_time`: Booking start timestamp formatted strictly as `YYYY-MM-DD HH:MM`.
   - `end_time`: Automatically computed end timestamp based on service duration (`start + minutes`).
   - `state`: Current lifecycle state (`booked`, `confirmed`, `arrived`, `completed`, `no_show`, `cancelled`).
   - `created_at`: Creation timestamp.

2. **AuditLog**: Immutable historical record of every state change and action.
   - `id`: Auto-incrementing primary key.
   - `appointment_id`: Foreign key reference to appointment.
   - `request_id`: Booking request identifier.
   - `from_state`: Prior state (or empty string on creation).
   - `to_state`: Resulting state.
   - `role`: Role that initiated the change (`client` or `staff`).
   - `timestamp`: Timestamp of transition.
   - `reason`: Optional justification text for exceptions/cancellations.

3. **Service (Reference Data)**:
   - Loaded from `fixtures/idea2-appointments/services.csv`: `service_id`, `name`, `minutes` (e.g. `S1`: Haircut 45m, `S2`: Color 90m, `S3`: Beard trim 20m, `S4`: Blowout 30m).

## States and Who May Move Each
The state machine strictly governs appointment lifecycles:

| From | To | Who may do it | Notes |
|---|---|---|---|
| `booked` | `confirmed` | `staff` | Human checkpoint at front desk; triggers fake reminder log |
| `confirmed` | `arrived` | `staff` | Client checks in physically at salon |
| `arrived` | `completed` | `staff` | Service rendered and finished |
| `booked` | `cancelled` | `client` or `staff` | Early cancellation prior to confirmation |
| `confirmed` | `cancelled` | `client` or `staff` | Cancellation of confirmed slot |
| `confirmed` | `no_show` | `staff` | Marked if client fails to arrive |

**Enforcement Rules:**
- Terminal states are `completed`, `cancelled`, and `no_show`.
- Any transition not listed above (or any attempt to transition out of a terminal state) is evaluated first and rejected as `illegal_move`.
- A valid transition attempted by an unauthorized role (e.g. `client` trying to confirm or mark arrived) is rejected as `not_permitted`.
- Rejected moves leave the appointment state completely unchanged.

## Roles and What Each Can See
- **`client`** (`GET /`): Can access the customer booking form to select service, stylist, date/time, and submit requests. Can view submission outcomes (`accepted` or specific rejection reasons) and submit cancellation requests for their appointments.
- **`staff`** (Front desk and stylists, `GET /desk`): Can view the consolidated schedule queue ordered by time, see all details (client, stylist, service duration, status badges), and trigger human checkpoint actions (Confirm, Mark Arrived, Mark Completed, No-Show, Cancel). Also views the sandboxed reminders feed.

## Data Store
- SQLite database stored at `appointments.db`.
- Managed through `store.py` with standard library `sqlite3`.
- Independent temporary databases (`tempfile.mkstemp()`) are used by `run.py` to guarantee test isolation across known-answer cases while preserving state across `restart` steps.

## The External Step I Sandboxed
- **Real-world action**: Sending transactional SMS/email reminders to clients when their appointments are confirmed.
- **Sandboxed implementation**: `send_reminder(appointment)` in `store.py`. It formats the notification and appends it to `reminders.log` locally. It never connects to an external network, uses third-party APIs, or requires credentials.

## Where Each Difficulty Bar Feature Lives
1. **Two or more roles with different views**: `app.py` (`/` for client, `/desk` for front-desk staff).
2. **Tracked state with rules**: `store.py` (`ALLOWED_TRANSITIONS`, `FINAL_STATES`, and `move_appointment()`).
3. **Persistence**: `store.py` (`init_db()`, `appointments.db`, tables `appointments` and `audit_log`).
4. **Staff dashboard or queue**: `app.py` (`render_staff_page()`, updated immediately when client books).
5. **Fake external step**: `store.py` (`send_reminder()`) writing to `reminders.log`.
6. **Human checkpoint**: `app.py` (Front desk "Confirm" action required before reminder is dispatched and state advances to `confirmed`).
7. **Known-answer tests plus one engineered failure**: `tests/known-answer/cases.json`, `tests/known-answer/run.py`, and `evidence/engineered-failure.md`.
