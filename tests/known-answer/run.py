#!/usr/bin/env python3
"""Known-answer runner. Run: python3 tests/known-answer/run.py  (Windows: python)

The loop, the step bookkeeping, and the checking are done for you. You write the three
hooks marked TODO so that they drive YOUR web app (for example with the Flask test client,
or HTTP calls to the running server). Translate your own state and outcome words to the
common words from the project contract inside the hooks.

Step vocabulary (contract section 3): create, move, list, restart.
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent

# Run from the repository root no matter where you start the command, so that
# "import your_app" and relative paths such as "fixtures/..." work.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)


import tempfile
import store


class AppHandle:
    def __init__(self, db_path):
        self.db_path = db_path


def new_app():
    """Start app with a fresh temporary SQLite database."""
    fd, path = tempfile.mkstemp(prefix="appt_test_", suffix=".db")
    os.close(fd)
    store.init_db(path)
    return AppHandle(path)


def restart_app(app):
    """Restart app reusing the same database path."""
    return AppHandle(app.db_path)


def do_step(app, step, items):
    """Execute one step (create / move / list) and return result dict."""
    action = step["do"]
    role = step.get("as", "client")

    if action == "create":
        res = store.create_appointment(app.db_path, step["data"], as_role=role)
        if res.get("outcome") == "accepted" and "id" in res:
            items.append(res["id"])
            return {"outcome": res["outcome"], "state": res["state"]}
        return {"outcome": res["outcome"]}

    elif action == "move":
        item_idx = step["item"] - 1
        if 0 <= item_idx < len(items):
            item_id = items[item_idx]
            return store.move_appointment(
                app.db_path, item_id, step["to"], as_role=role, reason=step.get("reason")
            )
        return {"outcome": "illegal_move"}

    elif action == "list":
        return store.list_appointments(app.db_path)

    raise ValueError(f"Unknown step action: {action}")


def run_case(case):
    """Run every step of one case on a fresh app and return the result of the LAST step."""
    app = new_app()
    items = []
    result = {}
    for step in case["input"]:
        if step["do"] == "restart":
            app = restart_app(app)
            result = {"outcome": "accepted"}
        else:
            result = do_step(app, step, items)
    return result


def matches(got, expected):
    """expected may list only some keys; every key you list must match."""
    if isinstance(expected, dict) and isinstance(got, dict):
        return all(k in got and got[k] == v for k, v in expected.items())
    return got == expected


def main():
    # Phase 1: one tests/known-answer/cases.json. Phase 2: one tests/known-answer/<member>/cases.json
    # per member, and every one of them is run (names get the member's folder as a prefix).
    files = sorted(HERE.glob("*/cases.json")) or [HERE / "cases.json"]
    cases = []
    try:
        for f in files:
            prefix = f"{f.parent.name}/" if f.parent != HERE else ""
            for c in json.loads(f.read_text())["cases"]:
                cases.append({**c, "name": prefix + c["name"]})
    except (OSError, ValueError, KeyError) as exc:
        sys.exit(f'cases.json must exist and look like {{"cases": [...]}} ({exc})')
    if not cases:
        sys.exit("cases.json has no cases yet: write them first (Step 1.3)")
    failed = 0
    for case in cases:
        try:
            got = run_case(case)
        except NotImplementedError as exc:
            sys.exit(f"{exc}: connect the hooks in run.py to your app")
        except Exception as exc:  # a crash is a FAIL, not a stop
            got = f"error: {exc}"
        if matches(got, case["expected"]):
            print(f"PASS {case['name']}")
        else:
            failed += 1
            print(f"FAIL {case['name']}: expected {case['expected']}, got {got}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
