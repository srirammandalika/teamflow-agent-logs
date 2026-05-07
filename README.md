# teamflow-agent-logs

---

## Table of Contents

1. [Preference-Based Email Notifications](#1-preference-based-email-notifications)
2. [Coding Agent (NOVA-3)](#2-coding-agent-nova-3)

---

## 1. Preference-Based Email Notifications

Teammates can opt in to receive email notifications for key task events. Notifications are delivered via **Gmail SMTP** and support two delivery modes: **immediate** and **daily digest**.

### Supported Events

| Event | Description |
|---|---|
| `task_created` | Fired when a new task is created in the project |
| `task_assigned` | Fired when a task is assigned to a teammate |
| `subtask_completed` | Fired when a subtask is marked as complete |

### Delivery Modes

| Mode | Description |
|---|---|
| `immediate` | An email is sent as soon as the event is triggered |
| `daily_digest` | All events from the day are batched and sent once per day |

### How to Use

#### Step 1 — Opt in via `preferences.py`

Open `preferences.py` and configure your notification preferences. Each teammate sets their own preferences independently:

```python
# preferences.py

NOTIFICATION_PREFERENCES = {
    "jane@example.com": {
        "enabled": True,
        "delivery": "immediate",          # "immediate" | "daily_digest"
        "events": [
            "task_created",
            "task_assigned",
            "subtask_completed",
        ],
    },
    "alex@example.com": {
        "enabled": True,
        "delivery": "daily_digest",       # receive one summary email per day
        "events": [
            "task_assigned",
            "subtask_completed",
        ],
    },
}
```

#### Step 2 — Configure Gmail SMTP credentials

Ensure the following environment variables are set before running the application:

```bash
GMAIL_SENDER_ADDRESS=your-sender@gmail.com
GMAIL_APP_PASSWORD=your-app-password        # use a Gmail App Password, not your account password
```

> **Tip:** Generate a Gmail App Password at **Google Account → Security → 2-Step Verification → App passwords**.

#### Step 3 — Trigger an event

Events are triggered automatically by normal teamflow actions (creating a task, assigning it, completing a subtask). No extra steps are needed once preferences are saved and credentials are set.

---

## 2. Coding Agent (NOVA-3)

NOVA-3 is a built-in coding agent that can read a repository, create a dedicated fix branch, apply code changes, and open a Pull Request — all from a task card.

Activity for every run is logged to **`agent-logs/<task_id>.md`** (e.g. `agent-logs/st105.md`).

### How It Works

```
Task card  ──►  NOVA-3 picks up the task
           ──►  Reads the repository
           ──►  Creates branch  fix/<short-slug>
           ──►  Applies the change
           ──►  Opens a Pull Request
           ──►  Writes agent-logs/<task_id>.md
```

### How to Use

#### Step 1 — Create a task and assign it to NOVA-3

In teamflow, create a new task and set the **Assignee** to **NOVA-3**.

#### Step 2 — Write the task card

In the task card's description, use the `/fix` command followed by a plain-English description of the change you need:

```
/fix <description>
```

**Examples:**

```
/fix rename the `user_name` variable to `username` in auth/login.py
```

```
/fix add input validation to the email field in src/forms/contact.py
```

```
/fix update the API base URL from http://localhost:3000 to https://api.example.com in config.js
```

> **Tips for a good description:**
> - Reference the exact file path when you know it (e.g. `src/utils/helpers.py`).
> - Describe *what* should change and *why* if relevant.
> - One `/fix` command per task card; open separate tasks for unrelated changes.

#### Step 3 — Review the Pull Request

Once NOVA-3 finishes, a Pull Request will appear in your repository targeting `main`. Review the diff, request changes if needed, and merge when satisfied.

#### Step 4 — Check the agent log

The full activity log for the run is written to:

```
agent-logs/<task_id>.md
```

For example, if your task ID is `st121`, check `agent-logs/st121.md` for a step-by-step record of what NOVA-3 read, changed, and committed.
