"""Data store and appointment business rules for Idea 2: Salon Appointment & Intake."""
import csv
import os
import re
import sqlite3
from datetime import datetime, timedelta, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SERVICES_CSV = ROOT / "fixtures" / "idea2-appointments" / "services.csv"
REMINDERS_LOG = ROOT / "reminders.log"

ALLOWED_TRANSITIONS = {
    ("booked", "confirmed"): {"staff"},
    ("confirmed", "arrived"): {"staff"},
    ("arrived", "completed"): {"staff"},
    ("booked", "cancelled"): {"client", "staff"},
    ("confirmed", "cancelled"): {"client", "staff"},
    ("confirmed", "no_show"): {"staff"},
}

FINAL_STATES = {"completed", "cancelled", "no_show"}


def load_services():
    """Load services.csv mapping service_id -> (name, minutes)."""
    services = {}
    if not SERVICES_CSV.exists():
        return services
    with open(SERVICES_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            services[row["service_id"].strip()] = {
                "name": row["name"].strip(),
                "minutes": int(row["minutes"].strip()),
            }
    return services


def init_db(db_path):
    """Initialize database tables."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT UNIQUE NOT NULL,
            client TEXT NOT NULL,
            service_id TEXT NOT NULL,
            stylist TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            state TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER,
            request_id TEXT,
            from_state TEXT,
            to_state TEXT,
            role TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            reason TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def send_reminder(appointment):
    """Fake external step: write reminder notification to reminders.log, never send."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = (
        f"[{timestamp}] REMINDER_SENT: Client '{appointment['client']}' "
        f"appointment '{appointment['request_id']}' with stylist '{appointment['stylist']}' "
        f"at {appointment['start_time']} (Service: {appointment['service_id']})\n"
    )
    with open(REMINDERS_LOG, "a", encoding="utf-8") as f:
        f.write(log_line)


def create_appointment(db_path, data, as_role="client"):
    """
    Validate and create a new booking request.
    Rules:
      1. duplicate_request
      2. bad_date_format (YYYY-MM-DD HH:MM)
      3. after_close (ends after 17:00)
      4. conflict (same stylist overlap)
    """
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    request_id = data.get("request_id", "").strip()
    client = data.get("client", "").strip()
    service_id = data.get("service_id", "").strip()
    stylist = data.get("stylist", "").strip()
    start_str = data.get("start", "").strip()

    # Rule 5: duplicate_request
    cur.execute("SELECT id FROM appointments WHERE request_id = ?", (request_id,))
    if cur.fetchone() is not None:
        conn.close()
        return {"outcome": "duplicate_request"}

    # Rule 3: bad_date_format
    if not re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", start_str):
        conn.close()
        return {"outcome": "bad_date_format"}

    try:
        start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
    except ValueError:
        conn.close()
        return {"outcome": "bad_date_format"}

    services = load_services()
    service_info = services.get(service_id, {"name": "Service", "minutes": 30})
    duration = timedelta(minutes=service_info["minutes"])
    end_dt = start_dt + duration
    end_str = end_dt.strftime("%Y-%m-%d %H:%M")

    # Rule 1 & 2: opening hours 09:00 - 17:00, after_close if ends after 17:00
    close_time = time(17, 0)
    open_time = time(9, 0)

    if start_dt.time() < open_time:
        conn.close()
        return {"outcome": "invalid_request"}

    if end_dt.date() > start_dt.date() or end_dt.time() > close_time:
        conn.close()
        return {"outcome": "after_close"}

    # Rule 4: conflict check for same stylist
    # Non-overlapping condition: end_new <= start_existing or start_new >= end_existing
    # Overlapping condition: max(start_new, start_ex) < min(end_new, end_ex)
    cur.execute(
        """
        SELECT request_id, start_time, end_time
        FROM appointments
        WHERE stylist = ? AND state != 'cancelled'
        """,
        (stylist,),
    )
    existing = cur.fetchall()
    for row in existing:
        ex_start = datetime.strptime(row["start_time"], "%Y-%m-%d %H:%M")
        ex_end = datetime.strptime(row["end_time"], "%Y-%m-%d %H:%M")
        if max(start_dt, ex_start) < min(end_dt, ex_end):
            conn.close()
            return {"outcome": "conflict"}

    # All checks passed -> insert as booked
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        """
        INSERT INTO appointments (request_id, client, service_id, stylist, start_time, end_time, state, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'booked', ?)
        """,
        (request_id, client, service_id, stylist, start_str, end_str, now_str),
    )
    appt_id = cur.lastrowid

    cur.execute(
        """
        INSERT INTO audit_log (appointment_id, request_id, from_state, to_state, role, timestamp)
        VALUES (?, ?, '', 'booked', ?, ?)
        """,
        (appt_id, request_id, as_role, now_str),
    )

    conn.commit()
    conn.close()
    return {"outcome": "accepted", "state": "booked", "id": appt_id}


def move_appointment(db_path, appt_id, to_state, as_role="staff", reason=None):
    """
    Attempt to transition an appointment to a new state.
    Checks:
      1. illegal_move: transition not in ALLOWED_TRANSITIONS
      2. not_permitted: role not authorized for this transition
      3. accepted: update state and write audit log
    """
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM appointments WHERE id = ?", (appt_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"outcome": "illegal_move"}

    current_state = row["state"]

    # Check 1: Is transition allowed?
    transition = (current_state, to_state)
    if current_state in FINAL_STATES or transition not in ALLOWED_TRANSITIONS:
        conn.close()
        return {"outcome": "illegal_move", "state": current_state}

    # Check 2: Is role permitted?
    allowed_roles = ALLOWED_TRANSITIONS[transition]
    if as_role not in allowed_roles:
        conn.close()
        return {"outcome": "not_permitted", "state": current_state}

    # Check 3: Accepted move
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("UPDATE appointments SET state = ? WHERE id = ?", (to_state, appt_id))
    cur.execute(
        """
        INSERT INTO audit_log (appointment_id, request_id, from_state, to_state, role, timestamp, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (appt_id, row["request_id"], current_state, to_state, as_role, now_str, reason),
    )
    conn.commit()

    if to_state == "confirmed":
        send_reminder(dict(row))

    conn.close()
    return {"outcome": "accepted", "state": to_state}


def list_appointments(db_path):
    """List all appointments and return count."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM appointments")
    count = cur.fetchone()[0]
    conn.close()
    return {"outcome": "accepted", "count": count}


def get_all_appointments(db_path):
    """Retrieve full appointment records for web display."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM appointments ORDER BY start_time ASC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
