# AI-Use Log

**How to use this file**

- Add one row **at the time** you use AI, not afterward. A row takes about one minute.
- Copy the example rows' style. Each row must say what AI proposed, what you decided, and how you checked it.
- Pass condition: every AI use in this project has a row; every row names a verification method and a decision you made yourself; at least one row (from Phase 1 onward) records something you **rejected**.

## Log

| # | Date | Phase | Tool / agent | Task or prompt (short) | What it proposed | I accepted / revised / rejected | How I verified | My decision and any open problem |
|---|---|---|---|---|---|---|---|---|
| 1 | Nov 12 | 1 Personal build | agy | "Find the Phase 1 guideline in BrowserOS and give me a plan" | A summary of the Phase 1 steps, grading weights, and that the Nov 8 due date has passed | Accepted | Compared it with the Phase 1 section of START-HERE.html | I will follow Steps 1.1 to 1.9 and ask the instructor about the late submission |
| 2 | Nov 12 | 1 Personal build | agy | "Set up the repo (Step 1.1) and draft the README (Step 1.2) for Idea 2" | Copied the starter files, one setup commit, and a README draft with a cut line and 7 difficulty-bar rows | Revised | Read the draft; added the state table myself from my own rules | Added the state table with exact transitions and role permissions to README |
| 3 | Nov 12 | 1 Personal build | agy | "What do not_permitted and illegal_move mean?" and "Check my case answers" | Explained both words and the decision order (illegal_move first, then not_permitted). Gave worked answers for client_cannot_confirm, client_cannot_mark_arrived and skip_to_completed. | Revised | My first definitions were wrong (a wallet and passkey idea). I re-traced each case's steps against my state table and the contract | I wrote the other expected values (cancel, duplicate, restart, happy path, seeded rows, count) from my own reasoning; open problem: none |
| 4 | Nov 13 | 1 Personal build | agy | "Make a slice-by-slice build plan, no code" | A 5-slice plan, the command list, and a stdlib-only design | Accepted | Read the slice-by-slice plan; confirmed it covers all 11 cases in small testable increments | Approved the stdlib-only 5-slice plan |
| 5 | Nov 13 | 1 Personal build | agy | Suggested adding Flask for the web layer | Flask for the web pages | Rejected | Checked contract section 3: stdlib (wsgiref, sqlite3) is allowed and avoids external dependencies | Rejected Flask to avoid venv/pip issues on fresh clone |

## Command decision table (use from Phase 1 onward)

Before you let an agent run a command, fill in a row. If the "Risk" cell says anything you cannot explain, the decision is **do not run**.

| Command | Target (files or system) | Purpose | Risk | Recovery | Decision |
|---|---|---|---|---|---|
| `python3 tests/known-answer/run.py` | this repo | Run known-answer test cases against app | None, read/test only | None needed | run |
| `python3 app.py` | this repo, port 8000 | Start local WSGI web server | Opens local port | Ctrl+C to stop | run |
| `git add` / `git commit` | this repo | Track incremental build slices in git | None, local version control | `git reset` if needed | run |
| `grep -rniE "api[_-]?key\|secret..."` | this repo | Scan for leaked secrets | None, read-only search | None needed | run |
| `git clone midterm-vutuanlinh midterm-check` | scratch folder | Verify clean fresh-clone test run | Temporary folder created | `rm -rf midterm-check` | run |
| `git tag phase1-submit` | this repo | Tag final submission commit | None | `git tag -d phase1-submit` | run |
| `zip -r Midterm-Phase1-VuTuanLinh.zip ...` | scratch folder | Create final zip archive | Creates zip file | Delete zip file | run |

## Stop signs (do not run the command; ask first)

- It deletes files outside your project folder.
- It needs an API key, password, or login that you would have to paste.
- It sends a real message, email, or payment.
- You cannot say in one sentence what it does.
