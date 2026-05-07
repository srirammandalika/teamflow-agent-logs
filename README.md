# teamflow-agent-logs

---

## Table of Contents

- [Preference-Based Email Notifications](#preference-based-email-notifications)
- [Coding Agent (NOVA-3)](#coding-agent-nova-3)
- [Agent Logs](#agent-logs)

---

## Preference-Based Email Notifications

Teammates can opt in to receive email notifications for key task events. Notifications are delivered via **Gmail SMTP** and can be configured for **immediate** delivery or bundled into a **daily digest**.

### Supported Events

| Event | Description |
|---|---|
| `task_created` | Fired when a new task is created in the project |
| `task_assigned` | Fired when a task is assigned to a teammate |
| `subtask_completed` | Fired when a subtask is marked as complete |

### Delivery Modes

- **Immediate** — an email is sent as soon as the event occurs.
- **Daily Digest** — all events from the day are bundled into a single summary email delivered once per day.

### How to Use

1. **Opt in via `preferences.py`** — open the file and locate your user entry (or add one). Set the events you want to subscribe to and your preferred delivery mode:

   ```python
   # preferences.py
   USER_PREFERENCES = {
       "alice@example.com": {
           "subscribed_events": ["task_created", "task_assigned", "subtask_completed"],
           "delivery_mode": "immediate",   # or "daily_digest"
       },
       "bob@example.com": {
           "subscribed_events": ["task_assigned"],
           "delivery_mode": "daily_digest",
       },
   }
   ```

2. **Configure Gmail SMTP credentials** — ensure the following environment variables are set in your `.env` file:

   ```
   GMAIL_SMTP_USER=your-address@gmail.com
   GMAIL_SMTP_PASSWORD=your-app-password
   ```

3. **That's it.** The system reads `preferences.py` on each event and dispatches emails only to teammates who have opted in for that specific event, using their chosen delivery mode.

---

## Coding Agent (NOVA-3)

NOVA-3 is an automated coding agent that can read your repository, implement a requested code change, and open a Pull Request — all triggered from a task card.

### How It Works

1. A teammate creates a task and **assigns it to NOVA-3**.
2. The task card description contains a `/fix` command describing the change needed.
3. NOVA-3 reads the repository, creates a dedicated fix branch, applies the change, and opens a Pull Request against `main`.
4. All activity is logged to `agent-logs/<task_id>.md` for full traceability.

### How to Use

1. **Create a new task** in your project board and assign it to **NOVA-3**.

2. **Write your request in the task card description** using the `/fix` command:

   ```
   /fix <description of the change you want made>
   ```

   **Examples:**

   ```
   /fix Add input validation to the login form so empty fields show an error message
   ```

   ```
   /fix Rename the `get_user` function to `fetch_user` across all files in src/
   ```

   ```
   /fix Update the README to document the new rate-limiting middleware
   ```

3. **NOVA-3 will automatically:**
   - Read the relevant files in the repository.
   - Create a new branch named `fix/<short-slug>`.
   - Apply the requested change.
   - Open a Pull Request with a description of what was changed and why.

4. **Review the Pull Request** on GitHub. All activity — including what the agent read, what it changed, and the PR link — is recorded in:

   ```
   agent-logs/<task_id>.md
   ```

> **Tip:** The more specific your `/fix` description, the more accurate the agent's output will be. Include file names, function names, or expected behaviour wherever possible.

---

## Agent Logs

The `agent-logs/` directory contains a Markdown log file for every task handled by NOVA-3. Each file is named after the task ID (e.g. `agent-logs/st105.md`) and records a timestamped summary of the agent's activity, including any errors or follow-up actions required.

```
agent-logs/
├── st105.md
├── st106.md
└── ...
```
