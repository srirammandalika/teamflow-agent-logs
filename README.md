# teamflow-agent-logs

---

## Features

### 1. Preference-Based Email Notifications

Teammates can opt in to receive email notifications for key project events. Notifications are delivered via **Gmail SMTP** and support two delivery modes: **immediate** alerts and **daily digest** summaries.

#### Supported Events

| Event | Description |
|---|---|
| `task_created` | A new task has been created in the project |
| `task_assigned` | A task has been assigned to a teammate |
| `subtask_completed` | A subtask has been marked as complete |

#### How to opt in

Edit `preferences.py` and add or update your entry with your preferred delivery mode:

```python
# preferences.py

NOTIFICATION_PREFERENCES = {
    "your.email@example.com": {
        "events":   ["task_created", "task_assigned", "subtask_completed"],
        "delivery": "immediate"   # or "daily_digest"
    }
}
```

- Set `"delivery"` to `"immediate"` to receive an email as soon as the event fires.
- Set `"delivery"` to `"daily_digest"` to receive a single summary email at the end of each day.
- Remove an event from the `"events"` list to stop receiving notifications for that event type.

#### How to use in a task card

No special syntax is needed in the task card itself — notifications are triggered automatically when the relevant event occurs (task created, task assigned, or subtask completed), and are sent to every teammate who has opted in for that event in `preferences.py`.

---

### 2. Coding Agent (NOVA-3)

The coding agent **NOVA-3** can autonomously fix bugs and implement changes directly in the repository. When triggered, it reads the codebase, creates a dedicated fix branch, applies the requested change, and opens a Pull Request for review. All activity is logged to `agent-logs/<task_id>.md`.

#### Workflow

```
Task card created & assigned to NOVA-3
        │
        ▼
Agent reads the repository
        │
        ▼
Agent creates a fix branch  (e.g. fix/short-slug)
        │
        ▼
Agent applies the change
        │
        ▼
Agent opens a Pull Request
        │
        ▼
Activity logged → agent-logs/<task_id>.md
```

#### How to use in a task card

1. **Create a new task** (or subtask) in your project board.
2. **Assign it to `NOVA-3`**.
3. **Write the task description** using the `/fix` command followed by a clear description of what needs to be changed:

```
/fix <description>
```

**Examples:**

```
/fix add input validation to the login form so empty usernames are rejected
```

```
/fix update README with setup instructions for the new Docker workflow
```

```
/fix rename `get_user` to `fetch_user` across all files in the services/ directory
```

> **Tips for a great task card**
> - Be specific: include file names, function names, or error messages where relevant.
> - One fix per task — keep the scope small so the agent can produce a clean, reviewable PR.
> - After NOVA-3 opens the PR, review the diff and merge or request changes as you would with any teammate's contribution.

#### Activity log

Every run is recorded at `agent-logs/<task_id>.md`, for example:

```
agent-logs/st120.md
```

Each log entry includes a timestamp, a summary of the action taken, and the outcome (success or any follow-up steps required).
