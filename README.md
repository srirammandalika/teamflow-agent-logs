# teamflow-agent-logs

A collaborative task-management workspace powered by **NOVA-3**, an AI coding agent that automates engineering work and keeps the team informed — right from your task board.

---

## Features

- [Preference-based Email Notifications](#1-preference-based-email-notifications)
- [Coding Agent (NOVA-3)](#2-coding-agent-nova-3)

---

## 1. Preference-based Email Notifications

Teammates can opt in to receive automatic email notifications triggered by activity on the task board. Notifications are delivered via **Gmail SMTP** and can be configured for either **immediate** or **daily digest** delivery.

### Supported trigger events

| Event | Description |
|---|---|
| `task_created` | A new task has been added to the board |
| `task_assigned` | A task has been assigned to a teammate |
| `subtask_completed` | A subtask has been marked as complete |

### Opt-in via `preferences.py`

Each teammate configures their own notification preferences in `preferences.py`. The available options are:

```python
# preferences.py

EMAIL_NOTIFICATIONS = {
    "enabled": True,                        # Set to False to opt out entirely
    "email": "you@example.com",             # Recipient address (must be verified)
    "delivery": "immediate",                # "immediate" or "daily_digest"
    "events": [
        "task_created",
        "task_assigned",
        "subtask_completed",
    ],
}
```

- **`immediate`** — an email is sent as soon as the triggering event occurs.
- **`daily_digest`** — all events from the day are bundled into a single summary email delivered at the end of the day.

### How to use

1. Open `preferences.py` and set `"enabled": True`.
2. Enter your verified Gmail recipient address in `"email"`.
3. Choose your preferred `"delivery"` mode (`"immediate"` or `"daily_digest"`).
4. List the events you want to be notified about under `"events"`.
5. Save the file — your preferences take effect immediately for all future events.

> **Note:** The sending account must be configured with valid Gmail SMTP credentials (host, port, and an app password) in the project's environment variables. If the recipient address is not verified or credentials are missing, delivery will fail and the agent will log the error for manual follow-up.

---

## 2. Coding Agent (NOVA-3)

NOVA-3 is an AI coding agent that lives on the task board. Assign it a task and it will autonomously read the repository, create a dedicated fix branch, apply the requested code change, and open a Pull Request — all without leaving your workflow.

### How it works

1. A teammate creates a task and **assigns it to `NOVA-3`**.
2. The task card's description begins with `/fix` followed by a plain-English description of the change needed.
3. NOVA-3 picks up the task, reads the relevant source files, and reasons about the required change.
4. It creates a new branch named `fix/<short-slug>` off `main`.
5. It writes the corrected file(s) to that branch with a descriptive commit message.
6. It opens a **Pull Request** summarising what changed, which lines were affected, and how to test the fix.
7. Every step is recorded in `agent-logs/<task_id>.md` for full auditability.

### How to use

1. **Create a new task** on the board.
2. **Assign it to `NOVA-3`**.
3. **Write your task card description** using the `/fix` command:

   ```
   /fix <plain-English description of the bug or change>
   ```

   **Examples:**

   ```
   /fix the login button does not redirect to the dashboard after a successful auth
   ```

   ```
   /fix add input validation to the signup form — reject empty username and password fields
   ```

   ```
   /fix rename the `getUserData` function to `fetchUserProfile` across all files
   ```

4. **Save the task.** NOVA-3 will begin working automatically.
5. **Review the Pull Request** that NOVA-3 opens on GitHub and merge when satisfied.
6. **Check the activity log** at `agent-logs/<task_id>.md` to see a timestamped record of everything the agent did.

### Activity logs

Every task handled by NOVA-3 produces a Markdown log file at:

```
agent-logs/<task_id>.md
```

Each entry includes a UTC timestamp and a summary of the action taken or any errors encountered. Example:

```markdown
## 2026-05-05T10:45:23Z

Complete: Fixed redirect logic in auth controller — branch fix/login-redirect created,
changes applied to src/controllers/auth.js, Pull Request #42 opened.
```

If something goes wrong (e.g. the description is ambiguous or a required file cannot be found), NOVA-3 logs the issue and flags the task for manual follow-up.

---

## Repository structure

```
teamflow-agent-logs/
├── README.md          # This file
├── preferences.py     # Per-teammate notification preferences
└── agent-logs/        # Timestamped activity logs for every NOVA-3 task
    ├── st105.md
    ├── st106.md
    └── ...
```
