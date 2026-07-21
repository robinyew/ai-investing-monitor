#!/usr/bin/env python3
"""Scaffold a Weekly Thesis & Chokepoint Brief instance.

Usage:
  python3 scripts/scaffold_weekly_thesis_brief.py
  python3 scripts/scaffold_weekly_thesis_brief.py --week-end 2026-07-25
  python3 scripts/scaffold_weekly_thesis_brief.py --week-end 2026-07-25 --also-digest

Default week_end = upcoming Friday (America/New_York), or today if Friday.
Writes:
  investment-intelligence-hub/memory/weekly_reviews/YYYY-MM-DD.md
Optional copy:
  reports/digest/YYYY-MM-DD_weekly_thesis.md

Does not auto-fill facts. Research-only. No email, no trading.
"""

from __future__ import annotations

import argparse
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "weekly_thesis_brief.md"
OUT_DIR = ROOT / "investment-intelligence-hub" / "memory" / "weekly_reviews"
DIGEST_DIR = ROOT / "reports" / "digest"
NY = ZoneInfo("America/New_York")


def today_ny() -> datetime:
    return datetime.now(NY).date()


def friday_on_or_after(d) -> str:
    # Monday=0 ... Sunday=6; Friday=4
    add = (4 - d.weekday()) % 7
    return (d + timedelta(days=add)).isoformat()


def week_start_from_end(week_end: str) -> str:
    end = datetime.fromisoformat(week_end).date()
    start = end - timedelta(days=4)  # Mon–Fri week
    return start.isoformat()


def next_week_end(week_end: str) -> str:
    end = datetime.fromisoformat(week_end).date()
    return (end + timedelta(days=7)).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold weekly thesis brief")
    parser.add_argument(
        "--week-end",
        default=None,
        help="Friday date YYYY-MM-DD (default: this week’s Friday ET)",
    )
    parser.add_argument(
        "--also-digest",
        action="store_true",
        help="Also copy to reports/digest/WEEKEND_weekly_thesis.md",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing")
    parser.add_argument(
        "--regime-note",
        default="Fill executive strip and chokepoint dashboard from this week’s digests.",
        help="Optional note injected into summary placeholder",
    )
    args = parser.parse_args()

    week_end = args.week_end or friday_on_or_after(today_ny())
    week_start = week_start_from_end(week_end)
    nxt = next_week_end(week_end)

    if not TEMPLATE.exists():
        raise SystemExit(f"Missing template: {TEMPLATE}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{week_end}.md"
    if out.exists() and not args.force:
        raise SystemExit(f"Exists (use --force): {out}")

    text = TEMPLATE.read_text(encoding="utf-8")
    text = (
        text.replace("{{WEEK_END}}", week_end)
        .replace("{{WEEK_START}}", week_start)
        .replace("{{NEXT_WEEK_END}}", nxt)
        .replace("{{THESIS_ONE_LINER}}", "")
        .replace("{{BIGGEST_FACT}}", "")
        .replace("{{BIGGEST_RISK}}", "")
        .replace("{{PORTFOLIO_IMPACT}}", "")
        .replace("{{NEXT_FALSIFIER}}", "")
        .replace("{{WEEK_SUMMARY_1_SENTENCE}}", args.regime_note)
        .replace("{{THESIS_DELTA}}", "Unchanged / Improved / Deteriorated")
    )

    # Leave remaining {{...}} as fill-ins for the human/agent
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out}")

    if args.also_digest:
        DIGEST_DIR.mkdir(parents=True, exist_ok=True)
        digest_path = DIGEST_DIR / f"{week_end}_weekly_thesis.md"
        if digest_path.exists() and not args.force:
            print(f"Skip digest copy (exists): {digest_path}")
        else:
            shutil.copyfile(out, digest_path)
            print(f"Wrote {digest_path}")

    remaining = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", out.read_text(encoding="utf-8"))))
    if remaining:
        print(f"Placeholders still present: {len(remaining)} (fill while writing)")
    print(f"week_start={week_start} week_end={week_end} next={nxt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
