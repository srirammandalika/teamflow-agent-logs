# teamflow-agent-logs

---

## Features

### 1. Preference-Based Email Notifications

Teammates can opt in to receive email notifications for key project events. Notifications are sent via **Gmail SMTP** and support two delivery modes: **immediate** and **daily digest**.

#### Supported events

| Event | Description |
|---|---|
| `task_created` | Fires when a new task is added to the board |
| `task_assigned` | Fires when a task is assigned to a teammate |
| `subtask_completed` | Fires when a subtask is marked as done |

#### Delivery modes

- **Immediate** — an email is sent as soon as the event occurs.
- **Daily digest** — all events from the day are bundled into a single email delivered at the end of the day.

#### How to use

1. Open `preferences.py` and locate your user entry (or add one if it doesn't exist yet).
2. Set `email_notifications` to `true` and choose your preferred delivery mode:

   ```python
   # preferences.py
   preferences = {
       "jane@example.com": {
           "email_notifications": True,
           "delivery_mode": "immediate",   # or "daily_digest"
           "events": ["task_created", "task_assigned", "subtask_completed"],
       }
   }
   ```

3. Save the file. The notification system will pick up your preferences automatically — no restart required.
4. To opt out at any time, set `email_notifications` to `false` or remove your entry entirely.

---

### 2. Coding Agent (NOVA-3)

The coding agent **NOVA-3** automates code fixes directly from the task board. Assign a task to NOVA-3 and describe the change you need — the agent will read the repository, create a dedicated fix branch, apply the change, and open a Pull Request for review.

All activity is logged to `agent-logs/<task_id>.md` so the full audit trail lives alongside the code.

#### How it works

1. NOVA-3 receives the task and reads the relevant files in the repository.
2. It creates a new branch named `fix/<short-slug>`.
3. It applies the requested change and commits it to the branch.
4. It opens a Pull Request against `main` describing what was changed and why.
5. A log entry is written to `agent-logs/<task_id>.md` with a timestamp and outcome summary.

#### How to use

1. Create a new task on the board and **assign it to NOVA-3**.
2. In the task card description, write your fix request using the `/fix` command:

   ```
   /fix <description of the change you need>
   ```

   **Examples:**

   ```
   /fix update the API base URL in config.py from staging to production
   ```

   ```
   /fix add input validation to the register() function in auth.py
   ```

   ```
   /fix remove the hardcoded timeout value in worker.js and read it from env
   ```

3. Submit the task. NOVA-3 will process it automatically.
4. Once complete, a Pull Request will appear in the repository for your team to review and merge.
5. Check `agent-logs/<task_id>.md` for a full log of what the agent did (or why it couldn't complete the task).

> **Tip:** The more specific your `/fix` description, the better the result. Include the file name and the exact behaviour you want to change where possible.

---

## agent-logs

The `agent-logs/` directory contains one Markdown file per task, named by task ID (e.g. `agent-logs/st105.md`). Each file records timestamped entries written by NOVA-3 describing the outcome of each run. These logs are append-only and should not be edited manually.
