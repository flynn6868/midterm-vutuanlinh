# Governance and Credential-Handling Table (ADI501 only, 3 points)

One or two sentences per row, specific to **your** tool. Replace the example column with your own text.

| Row | Your answer | Example (Idea 2 appointments) |
|---|---|---|
| Data | All client names (`client-a`, `client-b`), stylists (`Ana`, `Ben`), and service IDs are synthetic fixture data. No real customer contact information or personally identifiable information (PII) is stored or collected. | *Fifty made-up clients with invented names and phone numbers; no real person appears.* |
| Credentials | No credentials or API keys are used in this application. A secrets scan confirms zero live keys, passwords, or tokens in the codebase. | *None in use. The agent was never given a key; `grep -rniE "key\|token\|password" . --exclude-dir=.git` finds only template wording, no real key.* |
| External step | Appointment reminders are sandboxed to `reminders.log` as local log entries. No external communications (SMS/email) are triggered. | *Reminders are appended to `reminders.log`; no email or text is sent.* |
| Who can do what | Only `staff` can advance bookings to `confirmed`, `arrived`, `completed`, or `no_show`. Clients are restricted to submitting new requests and cancelling their own bookings. | *Only front desk moves `booked` to `confirmed`; the test `client_cannot_confirm` proves a client cannot.* |
| Agent access | The agent was constrained strictly to the local workspace folder. Tool suggestions requiring network installations (such as Flask) were rejected in favor of the Python standard library. | *The agent ran only inside the project folder; I rejected a command that wrote to my home folder.* |
| If it goes wrong | If sensitive data were ever committed, the repository would be paused immediately, the commit history cleaned, and the instructor alerted. All data remains local and fictional. | *If a key leaked I would stop, tell the instructor, and rotate the key; no key exists today.* |
