#!/usr/bin/env python3
"""
generate_weekly_summary.py
──────────────────────────
Aggregates all agent-log Markdown files found inside the `agent-logs/`
directory and produces a weekly summary report.

Usage
-----
    # Summarise every log file found under ./agent-logs/
    python generate_weekly_summary.py

    # Point to a custom logs directory
    python generate_weekly_summary.py --logs-dir /path/to/agent-logs

    # Write the report to a file instead of stdout
    python generate_weekly_summary.py --output weekly_report.md

    # Restrict to a specific ISO week (year-Www)
    python generate_weekly_summary.py --week 2026-W18
"""

import argparse
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


# ── Constants ────────────────────────────────────────────────────────────────

# Matches a Markdown H2 timestamp heading such as:
#   ## 2026-04-29T17:42:10Z
ENTRY_HEADING_RE = re.compile(
    r"^##\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s*$", re.MULTILINE
)

LOGS_DIR_DEFAULT = "agent-logs"


# ── Data helpers ──────────────────────────────────────────────────────────────


def parse_log_file(path: Path) -> list[dict]:
    """
    Parse a single agent-log Markdown file.

    Returns a list of entry dicts, each with keys:
        subtask_id  – stem of the filename (e.g. "st105")
        timestamp   – aware datetime object (UTC)
        iso_week    – "YYYY-Www"  (e.g. "2026-W18")
        body        – the text that follows the heading line
    """
    raw = path.read_text(encoding="utf-8")
    entries: list[dict] = []

    # Split the file on every H2 timestamp heading.
    # finditer gives us each match; the body lives between consecutive matches.
    matches = list(ENTRY_HEADING_RE.finditer(raw))
    for idx, match in enumerate(matches):
        ts_str = match.group(1)
        try:
            ts = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            # Malformed timestamp – skip gracefully.
            continue

        # Body: everything between the end of this heading and the start of the next.
        body_start = match.end()
        body_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw)
        body = raw[body_start:body_end].strip()

        iso_year, iso_week_num, _ = ts.isocalendar()
        iso_week = f"{iso_year}-W{iso_week_num:02d}"

        entries.append(
            {
                "subtask_id": path.stem,
                "timestamp": ts,
                "iso_week": iso_week,
                "body": body,
            }
        )

    return entries


def collect_entries(logs_dir: Path) -> list[dict]:
    """Collect parsed entries from every *.md file in *logs_dir*."""
    all_entries: list[dict] = []
    md_files = sorted(logs_dir.glob("*.md"))
    if not md_files:
        print(f"[WARNING] No Markdown files found in '{logs_dir}'.", file=sys.stderr)
    for md_file in md_files:
        all_entries.extend(parse_log_file(md_file))
    return all_entries


# ── Report builder ────────────────────────────────────────────────────────────


def build_report(entries: list[dict], filter_week: str | None = None) -> str:
    """
    Build a Markdown weekly-summary report string from *entries*.

    Parameters
    ----------
    entries     : list of entry dicts produced by parse_log_file()
    filter_week : optional "YYYY-Www" string; when provided only that week
                  is included in the report.
    """
    # Group entries by ISO week.
    by_week: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        if filter_week and entry["iso_week"] != filter_week:
            continue
        by_week[entry["iso_week"]].append(entry)

    if not by_week:
        if filter_week:
            return f"# Weekly Agent-Log Summary\n\n_No entries found for week {filter_week}._\n"
        return "# Weekly Agent-Log Summary\n\n_No entries found._\n"

    lines: list[str] = ["# Weekly Agent-Log Summary", ""]

    for week in sorted(by_week.keys()):
        week_entries = sorted(by_week[week], key=lambda e: e["timestamp"])

        # Derive friendly date range for the week header.
        first_ts = week_entries[0]["timestamp"]
        iso_year, iso_week_num = int(week[:4]), int(week[6:])
        # Monday of the ISO week:
        monday = datetime.fromisocalendar(iso_year, iso_week_num, 1)
        sunday = datetime.fromisocalendar(iso_year, iso_week_num, 7)
        date_range = f"{monday.strftime('%B %-d')} – {sunday.strftime('%B %-d, %Y')}"

        lines.append(f"## Week {week}  ({date_range})")
        lines.append("")

        # Stats block
        subtask_ids = sorted({e["subtask_id"] for e in week_entries})
        lines.append(f"- **Total log entries :** {len(week_entries)}")
        lines.append(f"- **Unique subtasks    :** {len(subtask_ids)}")
        lines.append(f"- **Subtask IDs        :** {', '.join(subtask_ids)}")
        lines.append("")

        # Detect common themes / keywords for a quick insight line.
        all_body = " ".join(e["body"].lower() for e in week_entries)
        observations: list[str] = []
        if "placeholder" in all_body:
            observations.append(
                "⚠️  Some entries reference placeholder email addresses — "
                "manual follow-up may be required."
            )
        if "failed" in all_body or "not sent" in all_body or "rejected" in all_body:
            observations.append(
                "❌  One or more email sends failed or were rejected."
            )
        if observations:
            lines.append("### Observations")
            lines.append("")
            for obs in observations:
                lines.append(f"- {obs}")
            lines.append("")

        # Individual entries
        lines.append("### Entries")
        lines.append("")
        for entry in week_entries:
            ts_fmt = entry["timestamp"].strftime("%Y-%m-%d %H:%M UTC")
            lines.append(f"#### `{entry['subtask_id']}` — {ts_fmt}")
            lines.append("")
            lines.append(entry["body"])
            lines.append("")

        lines.append("---")
        lines.append("")

    # Append generation timestamp.
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines.append(f"_Report generated at {now_utc}_")
    lines.append("")

    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate agent-logs into a weekly summary report."
    )
    parser.add_argument(
        "--logs-dir",
        default=LOGS_DIR_DEFAULT,
        help=f"Path to the agent-logs directory (default: '{LOGS_DIR_DEFAULT}').",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="File path to write the report to. Omit to print to stdout.",
    )
    parser.add_argument(
        "--week",
        default=None,
        metavar="YYYY-Www",
        help="Restrict the report to a single ISO week, e.g. '2026-W18'.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logs_dir = Path(args.logs_dir)
    if not logs_dir.is_dir():
        print(
            f"[ERROR] Logs directory not found: '{logs_dir}'. "
            "Use --logs-dir to specify a valid path.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Validate --week format if provided.
    if args.week:
        if not re.fullmatch(r"\d{4}-W\d{2}", args.week):
            print(
                f"[ERROR] --week must be in 'YYYY-Www' format (e.g. '2026-W18'), "
                f"got: '{args.week}'",
                file=sys.stderr,
            )
            sys.exit(1)

    entries = collect_entries(logs_dir)
    report = build_report(entries, filter_week=args.week)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(report, encoding="utf-8")
        print(f"[INFO] Report written to '{out_path}'.")
    else:
        print(report)


if __name__ == "__main__":
    main()
