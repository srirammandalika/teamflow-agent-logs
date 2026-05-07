# teamflow-agent-logs

---

## Features

### 1. Preference-Based Email Notifications

Teammates can opt in to receive email notifications for key project events. Notifications are delivered via **Gmail SMTP** and can be configured per-user through `preferences.py`.

#### Supported Events

| Event | Description |
|---|---|
| `task_created` | Fired when a new task is added to the board |
| `task_assigned` | Fired when a task is assigned to a teammate |
| `subtask_completed` | Fired when a subtask is marked as complete |

#### Delivery Modes

- **Immediate** — an email is sent as soon as the event occurs.
- **Daily Digest** — all events for the day are batched and delivered in a single summary email.

#### How to use

1. Open `preferences.py` and locate your user entry (or create one if it doesn't exist).
2. Set `notifications_enabled: true` to opt in.
3. Choose your preferred delivery mode:
   ```python
   # preferences.py
   user_preferences = {
       "jane@example.com": {
           "notifications_enabled": True,
           "delivery_mode": "immediate",   # or "daily_digest"
           "events": ["task_created", "task_assigned", "subtask_completed"]
       }
   }
   ```
4. Save the file. No server restart is required — preferences are read at event time.
5. Ensure the Gmail SMTP credentials are configured in your environment variables (`GMAIL_USER`, `GMAIL_APP_PASSWORD`) before events are triggered.

> **Note:** Only events listed in your `events` array will generate notifications. Remove any event name from the list to silence that specific trigger.

---

### 2. Coding Agent (NOVA-3)

The coding agent **NOVA-3** automates repository fixes directly from a task card. When a task is assigned to NOVA-3 and contains a `/fix` command, the agent reads the repository, creates a dedicated fix branch, applies the requested change, and opens a Pull Request — all without manual intervention.

#### How it works

1. A teammate creates a task on the board and assigns it to **NOVA-3**.
2. The task card body includes a `/fix <description>` command describing the change needed.
3. NOVA-3:
   - Reads the relevant files in the repository.
   - Creates a new branch named `fix/<short-slug>`.
   - Applies the targeted change.
   - Opens a Pull Request with a summary of what changed and how to test it.
4. All activity is logged to **`agent-logs/<task_id>.md`** for full auditability.

#### How to use

Create a task card with the following structure:

```
Title:    Fix login redirect bug
Assignee: NOVA-3
Body:
  /fix The login page redirects to /home instead of /dashboard after
  a successful authentication. Update the redirect target in
  auth/login.py so it points to /dashboard.
```

**Rules for the `/fix` command:**

- The command must appear in the **task card body** (description field), not the title.
- Start the line with `/fix` followed by a plain-English description of the change — no code required.
- Be as specific as possible: mention the file, function, or behaviour that needs to change.
- Only one `/fix` command per task card is processed. For multiple fixes, create separate tasks.

**Checking agent output:**

- The opened Pull Request will be linked in the task card comments once NOVA-3 completes its run.
- The full step-by-step activity log is available at `agent-logs/<task_id>.md` (e.g. `agent-logs/st105.md`).
- If the agent cannot complete the fix (e.g. missing context), the log will describe what manual follow-up is required.
