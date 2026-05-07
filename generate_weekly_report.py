#!/usr/bin/env python3
"""
generate_weekly_report.py
─────────────────────────
Aggregates every Markdown file found inside the `agent-logs/` directory and
produces a human-readable weekly summary report.

Usage
-----
    # Report for the current ISO week
    python generate_weekly_report.py

    # Report for a specific ISO year + week number
    python generate_weekly_report.py --year 2026 --week 18

    # Point at a different logs directory
    python generate_weekly_report.py --logs-dir path/to/agent-logs

    # Save the report to a file instead of printing to stdout
    python generate_weekly_report.py --output reports/week-18-2026.md

How it works
------------
1.  Every *.md file in <logs-dir> is read.
2.  Each H2 heading (`## <ISO-8601 timestamp>`) is treated as an individual
    log entry whose timestamp determines its ISO week.
3.  Entries that fall in the requested week are collected, grouped by log
    file (agent / subtask ID), and rendered as a Markdown report.
4.  The report includes:
      - A title and week date-range banner.
      - Per-agent sections with every entry they logged that week.
      - A summary table (agent → entry count).
      - Keyword tallies: successes, failures / errors, placeholders used.
"""

import argparse
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────

LOGS_DIR_DEFAULT = "agent-logs"

# Regex that matches the H2 timestamp headings written by agents.
# Accepts both:
#   ## 2026-04-29T17:42:10Z          (subtask logs)
#   **Date:** 2026-05-07 14:04 UTC   (task logs)
TIMESTAMP_H2_RE = re.compile(
    r"^##\s+(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?(?:Z|UTC)?)",
    re.MULTILINE,
)

# Fallback: bold-label date found in some task logs
BOLD_DATE_RE = re.compile(
    r"\*\*Date:\*\*\s+(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?(?:Z|UTC)?)"
)

# Keyword patterns for the summary statistics
SUCCESS_RE  = re.compile(r"\bsent\b|\bcomplete\b|\bsuccess\b", re.IGNORECASE)
FAILURE_RE  = re.compile(r"\bfail(?:ed)?\b|\berror\b|\brejected\b|\bnot sent\b", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"\bplaceholder\b", re.IGNORECASE)


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_timestamp(raw: str) -> datetime | None:
    """Try several timestamp formats; return a UTC-aware datetime or None."""
    raw = raw.strip().rstrip("Z").replace("UTC", "").strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def iso_week_bounds(year: int, week: int) -> tuple[date, date]:
    """Return (monday, sunday) for the given ISO year + week."""
    monday = date.fromisocalendar(year, week, 1)
    sunday = monday + timedelta(days=6)
    return monday, sunday


def in_week(dt: datetime, year: int, week: int) -> bool:
    iso = dt.isocalendar()
    return iso.year == year and iso.week == week


# ── Parsing ───────────────────────────────────────────────────────────────────

class LogEntry:
    """One timestamped block from an agent log file."""

    def __init__(self, agent_id: str, timestamp: datetime, body: str):
        self.agent_id  = agent_id
        self.timestamp = timestamp
        self.body      = body.strip()

    # Keyword flags (evaluated lazily)
    @property
    def is_success(self)     -> bool: return bool(SUCCESS_RE.search(self.body))
    @property
    def is_failure(self)     -> bool: return bool(FAILURE_RE.search(self.body))
    @property
    def uses_placeholder(self) -> bool: return bool(PLACEHOLDER_RE.search(self.body))


def parse_log_file(path: Path) -> list[LogEntry]:
    """
    Parse a single Markdown log file and return a list of LogEntry objects.

    Two log formats are supported:

    Format A – subtask logs (st*.md)
    ─────────────────────────────────
        ## 2026-04-29T17:42:10Z

        Complete: …

    Format B – task logs (t*.md)
    ─────────────────────────────
        # Agent Activity Log — …
        **Task ID:** t38
        **Date:** 2026-05-07 14:04 UTC
        …full prose body…
    """
    agent_id = path.stem          # e.g. "st105" or "t38"
    text     = path.read_text(encoding="utf-8")
    entries: list[LogEntry] = []

    # ── Format A: H2 timestamp headings ──────────────────────────────────────
    matches = list(TIMESTAMP_H2_RE.finditer(text))
    if matches:
        for idx, m in enumerate(matches):
            ts = parse_timestamp(m.group(1))
            if ts is None:
                continue
            # Body = text between this heading and the next heading (or EOF)
            start = m.end()
            end   = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            body  = text[start:end].strip()
            entries.append(LogEntry(agent_id, ts, body))
        return entries

    # ── Format B: bold **Date:** label (task logs) ────────────────────────────
    m = BOLD_DATE_RE.search(text)
    if m:
        ts = parse_timestamp(m.group(1))
        if ts:
            entries.append(LogEntry(agent_id, ts, text.strip()))

    return entries


def collect_entries(logs_dir: Path) -> list[LogEntry]:
    """Walk logs_dir and parse every *.md file."""
    entries: list[LogEntry] = []
    for md_file in sorted(logs_dir.glob("*.md")):
        entries.extend(parse_log_file(md_file))
    return entries


# ── Report Rendering ──────────────────────────────────────────────────────────

def render_report(entries: list[LogEntry], year: int, week: int) -> str:
    """Build and return the full Markdown report string."""
    monday, sunday = iso_week_bounds(year, week)

    # Filter to the requested week
    week_entries = [e for e in entries if in_week(e.timestamp, year, week)]

    lines: list[str] = []

    # ── Title block ──────────────────────────────────────────────────────────
    lines += [
        f"# Weekly Agent-Log Summary",
        f"",
        f"**ISO Week:** {year}-W{week:02d}  ",
        f"**Period:** {monday.isoformat()} → {sunday.isoformat()}  ",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"**Total entries this week:** {len(week_entries)}",
        f"",
        "---",
        "",
    ]

    if not week_entries:
        lines.append("> ⚠️  No log entries were found for this week.")
        return "\n".join(lines)

    # ── Per-agent sections ────────────────────────────────────────────────────
    by_agent: dict[str, list[LogEntry]] = defaultdict(list)
    for e in sorted(week_entries, key=lambda x: x.timestamp):
        by_agent[e.agent_id].append(e)

    lines.append("## Agent Activity\n")

    for agent_id, agent_entries in sorted(by_agent.items()):
        lines.append(f"### `{agent_id}`\n")
        for e in agent_entries:
            ts_str = e.timestamp.strftime("%Y-%m-%d %H:%M UTC")
            # Status badge
            if e.is_failure:
                badge = "❌ FAILURE"
            elif e.uses_placeholder:
                badge = "⚠️  PLACEHOLDER"
            elif e.is_success:
                badge = "✅ SUCCESS"
            else:
                badge = "ℹ️  INFO"

            lines += [
                f"**{ts_str}** — {badge}",
                "",
                f"> {e.body}",
                "",
            ]

    lines += ["---", ""]

    # ── Summary table ─────────────────────────────────────────────────────────
    lines += [
        "## Summary Table",
        "",
        "| Agent | Entries | ✅ Success | ❌ Failure | ⚠️ Placeholder |",
        "|-------|--------:|----------:|----------:|---------------:|",
    ]
    total_success = total_failure = total_placeholder = 0
    for agent_id, agent_entries in sorted(by_agent.items()):
        n_success     = sum(1 for e in agent_entries if e.is_success and not e.is_failure)
        n_failure     = sum(1 for e in agent_entries if e.is_failure)
        n_placeholder = sum(1 for e in agent_entries if e.uses_placeholder)
        total_success     += n_success
        total_failure     += n_failure
        total_placeholder += n_placeholder
        lines.append(
            f"| `{agent_id}` | {len(agent_entries)} | {n_success} | {n_failure} | {n_placeholder} |"
        )

    # Totals row
    lines += [
        f"| **TOTAL** | **{len(week_entries)}** | **{total_success}** "
        f"| **{total_failure}** | **{total_placeholder}** |",
        "",
        "---",
        "",
    ]

    # ── Keyword statistics ────────────────────────────────────────────────────
    lines += [
        "## Keyword Statistics",
        "",
        f"- **Successful actions:** {total_success}",
        f"- **Failures / errors:** {total_failure}",
        f"- **Placeholder addresses used:** {total_placeholder}",
        "",
    ]

    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aggregate agent-logs into a weekly summary report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--logs-dir",
        default=LOGS_DIR_DEFAULT,
        metavar="DIR",
        help=f"Path to the agent-logs directory (default: {LOGS_DIR_DEFAULT!r})",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        metavar="YYYY",
        help="ISO year to report on (default: current year)",
    )
    parser.add_argument(
        "--week",
        type=int,
        default=None,
        metavar="WW",
        help="ISO week number to report on (default: current week)",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help="Write the report to FILE instead of stdout",
    )
    parser.add_argument(
        "--all-weeks",
        action="store_true",
        help="Generate one report per ISO week that has entries, saved to --output directory",
    )
    return parser


def main() -> None:
    parser  = build_parser()
    args    = parser.parse_args()

    logs_dir = Path(args.logs_dir)
    if not logs_dir.is_dir():
        print(f"[ERROR] Logs directory not found: {logs_dir}", file=sys.stderr)
        sys.exit(1)

    entries = collect_entries(logs_dir)
    if not entries:
        print("[WARNING] No log entries found. Check the logs directory.", file=sys.stderr)

    # ── --all-weeks mode ──────────────────────────────────────────────────────
    if args.all_weeks:
        output_dir = Path(args.output) if args.output else Path("reports")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Collect unique (iso_year, iso_week) pairs present in the data
        weeks_present: set[tuple[int, int]] = set()
        for e in entries:
            iso = e.timestamp.isocalendar()
            weeks_present.add((iso.year, iso.week))

        if not weeks_present:
            print("[WARNING] No dated entries found; no reports generated.", file=sys.stderr)
            return

        for (yr, wk) in sorted(weeks_present):
            report  = render_report(entries, yr, wk)
            out_path = output_dir / f"week-{yr}-W{wk:02d}.md"
            out_path.write_text(report, encoding="utf-8")
            print(f"[OK] Report written → {out_path}")
        return

    # ── Single-week mode (default) ────────────────────────────────────────────
    today = date.today()
    iso   = today.isocalendar()
    year  = args.year if args.year is not None else iso.year
    week  = args.week if args.week is not None else iso.week

    # Validate week number
    try:
        date.fromisocalendar(year, week, 1)
    except ValueError as exc:
        print(f"[ERROR] Invalid year/week: {exc}", file=sys.stderr)
        sys.exit(1)

    report = render_report(entries, year, week)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"[OK] Report written → {out_path}")
    else:
        print(report)


if __name__ == "__main__":
    main()
