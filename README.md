# teamflow-agent-logs

A collaborative task-management workspace powered by **NOVA-3**, an AI coding agent that automates engineering work directly from task cards.

---

## Features

### 1. Preference-Based Email Notifications

Teammates can opt in to receive email notifications about workspace activity. Notifications are sent via **Gmail SMTP** and are triggered by the following events:

| Event | Description |
|---|---|
| `task_created` | A new task has been added to the board |
| `task_assigned` | A task has been assigned to a teammate |
| `subtask_completed` | A subtask has been marked as complete |

**Delivery modes:**

- **Immediate** — an email is sent as soon as the event occurs.
- **Daily digest** — all events from the day are batched into a single summary email delivered at the end of the day.

#### How to use

1. Open `preferences.py` and locate your user entry (or add one if it does not exist yet).
2. Set `email_notifications` to `true` to opt in.
3. Choose your preferred delivery mode by setting `delivery` to either `"immediate"` or `"daily_digest"`.
4. Provide your Gmail address in the `email` field.

Example entry in `preferences.py`:

```python
{
    "user": "alice",
    "email": "alice@example.com",
    "email_notifications": True,
    "delivery": "immediate",          # or "daily_digest"
    "events": [
        "task_created",
        "task_assigned",
        "subtask_completed",
    ],
}
```

Once saved, the notification service picks up your preferences automatically — no restart required.

---

### 2. Coding Agent (NOVA-3)

NOVA-3 is an AI coding agent that can read your repository, implement a fix on a new branch, and open a Pull Request — all triggered directly from a task card.

**How it works:**

1. NOVA-3 receives the task, reads the relevant files in the repository.
2. It creates a new branch named `fix/<short-slug>`.
3. It applies the requested code change on that branch.
4. It opens a Pull Request against `main` describing what changed and how to test it.
5. Every step is logged to `agent-logs/<task_id>.md` for full auditability.

#### How to use

1. **Create a new task** on the board and **assign it to `NOVA-3`**.
2. In the **task card description**, write your request using the `/fix` command:

   ```
   /fix <description of the change you want>
   ```

   **Examples:**

   ```
   /fix add input validation to the login form so empty fields return a 400 error
   ```

   ```
   /fix rename the `getUserData` function to `fetchUserProfile` across the codebase
   ```

   ```
   /fix update the README with setup instructions for the new Docker workflow
   ```

3. Save the task card. NOVA-3 will pick it up automatically.
4. When the work is complete, a Pull Request link will appear in the task activity feed and the full agent log will be available at `agent-logs/<task_id>.md`.

> **Tip:** The more specific your `/fix` description, the more accurate the change will be. Include file names, function names, or expected behaviour wherever possible.

---

## Agent Logs

All coding-agent activity is recorded in the [`agent-logs/`](./agent-logs) directory. Each file is named after the task or subtask ID that triggered it (e.g. `agent-logs/t36.md`, `agent-logs/st105.md`) and contains:

- The original request
- Every tool call made by the agent and its result
- The branch name and Pull Request URL produced

---

## Repository Structure

```
teamflow-agent-logs/
├── README.md          # This file
└── agent-logs/        # Per-task activity logs written by NOVA-3
```
