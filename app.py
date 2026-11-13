#!/usr/bin/env python3
"""WSGI web application for Salon Appointment & Intake (Idea 2).

Standard library only (wsgiref, sqlite3, json).
Routes:
  GET  /         - Client booking form
  GET  /desk     - Staff dashboard and schedule queue
  POST /api/book - Create booking
  POST /api/move - Advance appointment state
  GET  /api/list - List appointments JSON
"""
import cgi
import json
import os
import sqlite3
import urllib.parse
from pathlib import Path
from wsgiref.simple_server import make_server

import store

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / "appointments.db"


def render_client_page(message=None, error=None):
    """HTML for client booking form."""
    services = store.load_services()
    svc_options = "".join(
        f'<option value="{sid}">{s["name"]} ({s["minutes"]} min)</option>'
        for sid, s in services.items()
    )

    alert_html = ""
    if message:
        alert_html = f'<div class="alert success">{message}</div>'
    elif error:
        alert_html = f'<div class="alert error">Error: {error}</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Salon Booking — Client Portal</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 2rem; background: #f8fafc; color: #1e293b; }}
  .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }}
  h1 {{ margin-top: 0; color: #0f172a; font-size: 1.5rem; }}
  label {{ display: block; margin-top: 1rem; font-weight: 600; font-size: 0.875rem; }}
  input, select {{ width: 100%; padding: 0.5rem; margin-top: 0.25rem; border: 1px solid #cbd5e1; border-radius: 4px; box-sizing: border-box; }}
  button {{ margin-top: 1.5rem; width: 100%; background: #2563eb; color: white; padding: 0.75rem; border: none; border-radius: 4px; font-weight: 600; cursor: pointer; }}
  button:hover {{ background: #1d4ed8; }}
  .alert {{ padding: 0.75rem 1rem; margin-bottom: 1rem; border-radius: 4px; font-size: 0.875rem; }}
  .alert.success {{ background: #dcfce7; color: #166534; border: 1px solid #86efac; }}
  .alert.error {{ background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }}
  .nav {{ margin-bottom: 1rem; font-size: 0.875rem; }}
  .nav a {{ color: #2563eb; text-decoration: none; }}
  .nav a:hover {{ text-decoration: underline; }}
  .cancel-box {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; }}
</style>
</head>
<body>
<div class="container">
  <div class="nav">
    <strong>Client Portal</strong> | <a href="/desk">Switch to Front Desk Staff View &rarr;</a>
  </div>
  <h1>Book a Salon Appointment</h1>
  {alert_html}
  <form method="POST" action="/book">
    <label>Request ID</label>
    <input type="text" name="request_id" placeholder="e.g. B-101" required>

    <label>Your Name / Client ID</label>
    <input type="text" name="client" placeholder="e.g. client-alex" required>

    <label>Service</label>
    <select name="service_id">
      {svc_options}
    </select>

    <label>Preferred Stylist</label>
    <select name="stylist">
      <option value="Ana">Ana</option>
      <option value="Ben">Ben</option>
    </select>

    <label>Date & Start Time (YYYY-MM-DD HH:MM, 09:00 - 17:00)</label>
    <input type="text" name="start" placeholder="2026-11-02 09:00" required>

    <button type="submit">Submit Booking Request</button>
  </form>

  <div class="cancel-box">
    <h3>Need to cancel a booking?</h3>
    <form method="POST" action="/cancel">
      <label>Appointment Number (Item ID)</label>
      <input type="number" name="item_id" placeholder="e.g. 1" required>
      <button type="submit" style="background: #dc2626;">Cancel My Booking</button>
    </form>
  </div>
</div>
</body>
</html>"""


def render_staff_page(db_path, message=None, error=None):
    """HTML for front-desk staff dashboard."""
    appts = store.get_all_appointments(db_path)
    services = store.load_services()

    alert_html = ""
    if message:
        alert_html = f'<div class="alert success">{message}</div>'
    elif error:
        alert_html = f'<div class="alert error">Error: {error}</div>'

    rows_html = []
    for a in appts:
        s_name = services.get(a["service_id"], {}).get("name", a["service_id"])
        st = a["state"]

        actions = []
        if st == "booked":
            actions.append(
                f'<form method="POST" action="/move" style="display:inline;">'
                f'<input type="hidden" name="item_id" value="{a["id"]}">'
                f'<input type="hidden" name="to_state" value="confirmed">'
                f'<input type="hidden" name="as_role" value="staff">'
                f'<button type="submit" class="btn btn-confirm">Confirm (Send Reminder)</button>'
                f'</form>'
            )
            actions.append(
                f'<form method="POST" action="/move" style="display:inline;">'
                f'<input type="hidden" name="item_id" value="{a["id"]}">'
                f'<input type="hidden" name="to_state" value="cancelled">'
                f'<input type="hidden" name="as_role" value="staff">'
                f'<button type="submit" class="btn btn-cancel">Cancel</button>'
                f'</form>'
            )
        elif st == "confirmed":
            actions.append(
                f'<form method="POST" action="/move" style="display:inline;">'
                f'<input type="hidden" name="item_id" value="{a["id"]}">'
                f'<input type="hidden" name="to_state" value="arrived">'
                f'<input type="hidden" name="as_role" value="staff">'
                f'<button type="submit" class="btn btn-arrive">Mark Arrived</button>'
                f'</form>'
            )
            actions.append(
                f'<form method="POST" action="/move" style="display:inline;">'
                f'<input type="hidden" name="item_id" value="{a["id"]}">'
                f'<input type="hidden" name="to_state" value="no_show">'
                f'<input type="hidden" name="as_role" value="staff">'
                f'<button type="submit" class="btn btn-noshow">No-Show</button>'
                f'</form>'
            )
            actions.append(
                f'<form method="POST" action="/move" style="display:inline;">'
                f'<input type="hidden" name="item_id" value="{a["id"]}">'
                f'<input type="hidden" name="to_state" value="cancelled">'
                f'<input type="hidden" name="as_role" value="staff">'
                f'<button type="submit" class="btn btn-cancel">Cancel</button>'
                f'</form>'
            )
        elif st == "arrived":
            actions.append(
                f'<form method="POST" action="/move" style="display:inline;">'
                f'<input type="hidden" name="item_id" value="{a["id"]}">'
                f'<input type="hidden" name="to_state" value="completed">'
                f'<input type="hidden" name="as_role" value="staff">'
                f'<button type="submit" class="btn btn-complete">Mark Completed</button>'
                f'</form>'
            )
        else:
            actions.append(f'<span class="badge badge-final">Final</span>')

        action_str = " ".join(actions)
        badge_class = f"badge badge-{st}"

        rows_html.append(
            f"<tr>"
            f"<td><strong>#{a['id']}</strong> ({a['request_id']})</td>"
            f"<td>{a['client']}</td>"
            f"<td>{s_name}</td>"
            f"<td><strong>{a['stylist']}</strong></td>"
            f"<td>{a['start_time']} - {a['end_time']}</td>"
            f"<td><span class=\"{badge_class}\">{st}</span></td>"
            f"<td>{action_str}</td>"
            f"</tr>"
        )

    table_body = (
        "".join(rows_html)
        if rows_html
        else "<tr><td colspan='7' style='text-align:center;'>No bookings scheduled yet.</td></tr>"
    )

    # Read last 5 reminder log lines if file exists
    reminder_feed = ""
    if store.REMINDERS_LOG.exists():
        lines = store.REMINDERS_LOG.read_text(encoding="utf-8").strip().splitlines()
        recent = lines[-5:] if lines else []
        if recent:
            items = "".join(f"<li>{r}</li>" for r in reversed(recent))
            reminder_feed = f"""
            <div style="margin-top: 2rem;">
              <h3>Recent Sandboxed Reminders Log (Fake External Step)</h3>
              <ul style="font-family: monospace; font-size: 0.8rem; background: #f1f5f9; padding: 1rem 1.5rem; border-radius: 4px;">
                {items}
              </ul>
            </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Salon Desk — Front Desk Staff Dashboard</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 2rem; background: #f8fafc; color: #1e293b; }}
  .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }}
  h1 {{ margin-top: 0; color: #0f172a; font-size: 1.5rem; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.875rem; }}
  th, td {{ padding: 0.75rem; border-bottom: 1px solid #e2e8f0; text-align: left; }}
  th {{ background: #f1f5f9; font-weight: 600; color: #475569; }}
  .badge {{ padding: 0.25rem 0.5rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }}
  .badge-booked {{ background: #e0f2fe; color: #0369a1; }}
  .badge-confirmed {{ background: #fef3c7; color: #b45309; }}
  .badge-arrived {{ background: #e0e7ff; color: #4338ca; }}
  .badge-completed {{ background: #dcfce7; color: #15803d; }}
  .badge-cancelled {{ background: #fee2e2; color: #b91c1c; }}
  .badge-no_show {{ background: #f3f4f6; color: #4b5563; }}
  .badge-final {{ background: #e2e8f0; color: #64748b; }}
  .btn {{ border: none; padding: 0.35rem 0.65rem; border-radius: 4px; cursor: pointer; font-size: 0.75rem; font-weight: 600; margin-right: 0.25rem; }}
  .btn-confirm {{ background: #0284c7; color: white; }}
  .btn-arrive {{ background: #4f46e5; color: white; }}
  .btn-complete {{ background: #16a34a; color: white; }}
  .btn-cancel {{ background: #ef4444; color: white; }}
  .btn-noshow {{ background: #6b7280; color: white; }}
  .alert {{ padding: 0.75rem 1rem; margin-bottom: 1rem; border-radius: 4px; font-size: 0.875rem; }}
  .alert.success {{ background: #dcfce7; color: #166534; border: 1px solid #86efac; }}
  .alert.error {{ background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }}
  .nav {{ margin-bottom: 1rem; font-size: 0.875rem; }}
  .nav a {{ color: #2563eb; text-decoration: none; }}
</style>
</head>
<body>
<div class="container">
  <div class="nav">
    <a href="/">&larr; Switch to Client Booking Portal</a> | <strong>Front Desk Dashboard</strong>
  </div>
  <h1>Front Desk Schedule Queue</h1>
  {alert_html}
  <table>
    <thead>
      <tr>
        <th>ID / Request</th>
        <th>Client</th>
        <th>Service</th>
        <th>Stylist</th>
        <th>Scheduled Time</th>
        <th>State</th>
        <th>Actions (Human Checkpoint)</th>
      </tr>
    </thead>
    <tbody>
      {table_body}
    </tbody>
  </table>
  {reminder_feed}
</div>
</body>
</html>"""


def make_app(db_path=DEFAULT_DB):
    """Create a WSGI application using the specified db_path."""
    store.init_db(db_path)

    def app(environ, start_response):
        path = environ.get("PATH_INFO", "/")
        method = environ.get("REQUEST_METHOD", "GET")

        # Parse POST form body
        post_data = {}
        if method == "POST":
            try:
                content_length = int(environ.get("CONTENT_LENGTH", 0))
            except ValueError:
                content_length = 0
            body = environ["wsgi.input"].read(content_length)
            content_type = environ.get("CONTENT_TYPE", "")
            if "application/json" in content_type:
                try:
                    post_data = json.loads(body.decode("utf-8"))
                except Exception:
                    post_data = {}
            else:
                post_data = urllib.parse.parse_qs(body.decode("utf-8"))
                # Flatten single values
                post_data = {k: v[0] for k, v in post_data.items()}

        # Routing
        if path == "/" and method == "GET":
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [render_client_page().encode("utf-8")]

        elif path == "/desk" and method == "GET":
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [render_staff_page(db_path).encode("utf-8")]

        elif path == "/book" and method == "POST":
            res = store.create_appointment(db_path, post_data, as_role="client")
            if res.get("outcome") == "accepted":
                msg = f"Booking accepted! Your appointment ID is #{res['id']} (State: booked)."
                start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
                return [render_client_page(message=msg).encode("utf-8")]
            else:
                err = f"Booking rejected with outcome: {res.get('outcome')}"
                start_response("400 Bad Request", [("Content-Type", "text/html; charset=utf-8")])
                return [render_client_page(error=err).encode("utf-8")]

        elif path == "/cancel" and method == "POST":
            try:
                item_id = int(post_data.get("item_id", 0))
            except ValueError:
                item_id = 0
            res = store.move_appointment(db_path, item_id, "cancelled", as_role="client")
            if res.get("outcome") == "accepted":
                msg = f"Appointment #{item_id} successfully cancelled."
                start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
                return [render_client_page(message=msg).encode("utf-8")]
            else:
                err = f"Could not cancel: {res.get('outcome')}"
                start_response("400 Bad Request", [("Content-Type", "text/html; charset=utf-8")])
                return [render_client_page(error=err).encode("utf-8")]

        elif path == "/move" and method == "POST":
            try:
                item_id = int(post_data.get("item_id", 0))
            except ValueError:
                item_id = 0
            to_state = post_data.get("to_state", "")
            as_role = post_data.get("as_role", "staff")
            res = store.move_appointment(db_path, item_id, to_state, as_role=as_role)
            if res.get("outcome") == "accepted":
                msg = f"Appointment #{item_id} moved to state '{to_state}'."
                start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
                return [render_staff_page(db_path, message=msg).encode("utf-8")]
            else:
                err = f"Move rejected: outcome '{res.get('outcome')}'"
                start_response("400 Bad Request", [("Content-Type", "text/html; charset=utf-8")])
                return [render_staff_page(db_path, error=err).encode("utf-8")]

        elif path == "/api/list" and method == "GET":
            data = store.get_all_appointments(db_path)
            start_response("200 OK", [("Content-Type", "application/json")])
            return [json.dumps(data).encode("utf-8")]

        else:
            start_response("404 Not Found", [("Content-Type", "text/plain")])
            return [b"Not Found"]

    return app


def main():
    port = int(os.environ.get("PORT", 8000))
    app = make_app(DEFAULT_DB)
    print(f"Starting Salon Booking Web App on http://localhost:{port}")
    print(f"Client Portal:    http://localhost:{port}/")
    print(f"Staff Dashboard:  http://localhost:{port}/desk")
    with make_server("0.0.0.0", port, app) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")


if __name__ == "__main__":
    main()
