#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
HUB = ROOT / "investment-intelligence-hub"
TZ = ZoneInfo("America/New_York")

DISCLAIMER = "Research-only. No trading automation. No buy/sell instructions. Watchlist labels are not confirmed holdings."
# Pipeline v2 output structure (aligned with run_hub_pipeline.py).
REQUIRED_SECTIONS = [
    "1. Intelligence Verdict",
    "2. What Changed",
    "3. Source-Backed Signals",
    "4. Unverified Leads",
    "5. Chokepoint Intelligence",
    "6. Verification Queue",
]
# "(?<!to )" exempts infinitive business usage quoted from sources
# ("Meta plans to sell AI compute") — aligned with run_hub_pipeline.py.
FORBIDDEN_TRADING = re.compile(r"\b(?<!to )(buy|sell|trim|add|position size|price target)\b", re.I)
SENSITIVE_PATTERNS = [
    ("account amount", re.compile(r"\b(account value|account balance|portfolio value|net liquidation)\b", re.I)),
    ("holding quantity", re.compile(r"\b(shares|contracts|units)\s*[:=]?\s*\d+|\b\d+\s+(shares|contracts|units)\b", re.I)),
    ("cost basis", re.compile(r"\bcost basis\b|\bavg\.?\s*cost\b|\baverage cost\b", re.I)),
    ("exact trading plan", re.compile(r"\bexact trading plan\b|\bstop loss\b|\blimit order\b|\bentry at\b|\bexit at\b", re.I)),
    ("tax detail", re.compile(r"\btax lot\b|\bcapital gains?\b|\btaxable\b|\bwash sale\b", re.I)),
    ("banking sensitive information", re.compile(r"\bbank account\b|\brouting number\b|\bwire transfer\b", re.I)),
    ("company sensitive information", re.compile(r"\bconfidential\b|\bmaterial nonpublic\b|\bMNPI\b", re.I)),
    ("private personal notes", re.compile(r"\bprivate note\b|\bpersonal note\b|\bdo not publish\b", re.I)),
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def as_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    lowered = value.strip().lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("--publish must be true or false")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish a Hub Intelligence HTML report into ai-investing-monitor docs.")
    parser.add_argument("--date", required=True)
    parser.add_argument("--source-html")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--publish", type=parse_bool, default=False)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def strip_tags(value: str) -> str:
    text = re.sub(r"<script\b.*?</script>", " ", value, flags=re.I | re.S)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def validate_html(source_html: Path) -> tuple[bool, list[str], list[str]]:
    checks: list[str] = []
    errors: list[str] = []
    if not source_html.exists():
        return False, checks, [f"Source HTML missing: {rel(source_html)}"]
    raw = source_html.read_text(encoding="utf-8", errors="ignore")
    text = strip_tags(raw)
    checks.append("Source HTML exists.")
    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"Missing required section: {section}")
    if not errors:
        checks.append("Source HTML contains all required sections.")
    if DISCLAIMER not in text:
        errors.append("Missing required public disclaimer.")
    else:
        checks.append("Required public disclaimer is present.")
    # v2 structure has no Watchlist Impact section; keep the invariant that
    # unconfirmed holdings must never be presented as "Holdings Impact".
    if "Holdings Impact" in text:
        errors.append("Report must not use Holdings Impact when holdings are unconfirmed.")
    else:
        checks.append("Report does not claim confirmed holdings.")
    for label, pattern in SENSITIVE_PATTERNS:
        if pattern.search(text):
            errors.append(f"Detected forbidden sensitive content: {label}")
    if not any(error.startswith("Detected forbidden sensitive content") for error in errors):
        checks.append("No forbidden sensitive content detected.")
    bad_terms = []
    for line_no, line in enumerate(text.split(". "), start=1):
        if (
            DISCLAIMER in line
            or "No buy/sell instructions" in line
            or "forbidden-output" in line
            or "forbidden output" in line
        ):
            continue
        if FORBIDDEN_TRADING.search(line):
            bad_terms.append(f"{line_no}: {line[:160]}")
    if bad_terms:
        errors.append("Forbidden trading instruction words outside disclaimer context: " + "; ".join(bad_terms[:5]))
    else:
        checks.append("Forbidden trading instruction words appear only in disclaimer context.")
    return not errors, checks, errors


def build_index(intelligence_dir: Path, date: str) -> str:
    existing = {path.name for path in intelligence_dir.glob("*.html") if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.html", path.name)}
    existing.add(f"{date}.html")
    dates = sorted((name[:-5] for name in existing), reverse=True)
    rows = "\n".join(f'<li><a href="{html.escape(day)}.html">{html.escape(day)}</a></li>' for day in dates)
    return "\n".join(
        [
            "<!doctype html>",
            "<html lang=\"en\">",
            "<head>",
            "<meta charset=\"utf-8\">",
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
            "<title>Investment Intelligence Briefs</title>",
            "<style>",
            "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.5;max-width:900px;margin:0 auto;padding:32px 20px;color:#1f2933}",
            "h1{font-size:30px} .disclaimer{font-weight:600;color:#5b6472} li{margin:8px 0}",
            "</style>",
            "</head>",
            "<body>",
            "<h1>Investment Intelligence Briefs</h1>",
            f"<p class=\"disclaimer\">{html.escape(DISCLAIMER)}</p>",
            "<ul>",
            rows,
            "</ul>",
            "</body>",
            "</html>",
        ]
    )


def publish_notes(date: str, source_html: Path, target_html: Path, index_path: Path, publish: bool, dry_run: bool, checks: list[str], errors: list[str], files_written: list[Path]) -> str:
    result = "passed" if not errors else "failed"
    return "\n".join(
        [
            f"# Hub HTML Publish Notes - {date}",
            "",
            f"Timestamp: {datetime.now(TZ).strftime('%Y-%m-%dT%H:%M:%S%z')}",
            "",
            f"- Source HTML path: `{rel(source_html)}`",
            f"- Target HTML path: `{rel(target_html)}`",
            f"- Index path: `{rel(index_path)}`",
            f"- Publish flag: `{str(publish).lower()}`",
            f"- Dry run: `{str(dry_run).lower()}`",
            f"- Validation result: `{result}`",
            "",
            "## Validation Checks",
            "",
            *[f"- {check}" for check in checks],
            *[f"- ERROR: {error}" for error in errors],
            "",
            "## Files Written",
            "",
            *([f"- `{rel(path)}`" for path in files_written] or ["- None"]),
            "",
            "## Boundary Confirmation",
            "",
            "- No production report-generation scripts were modified.",
            "- `watchlists.yaml` and `themes.yaml` were not changed.",
            "- Root `ai-investing-monitor/docs/index.html` was not changed.",
            "- Cloudflare Worker Cron was not implemented.",
            "- GitHub schedule was not added.",
            "- No API integrations were added.",
            "- No trading automation was created.",
            "- No trade instructions were generated.",
            "",
        ]
    )


def run(args: argparse.Namespace) -> int:
    source_html = as_path(args.source_html) or HUB / f"reports/daily_intelligence/html/{args.date}.html"
    docs_root = as_path(args.docs_root) or ROOT / "ai-investing-monitor/docs"
    intelligence_dir = docs_root / "intelligence"
    target_html = intelligence_dir / f"{args.date}.html"
    index_path = intelligence_dir / "index.html"
    notes_path = HUB / f"reports/daily_intelligence/{args.date}_publish_notes.md"
    publish = bool(args.publish)
    dry_run = bool(args.dry_run)
    ok, checks, errors = validate_html(source_html)
    files_written: list[Path] = []
    print(f"Source HTML: {rel(source_html)}")
    print(f"Target HTML: {rel(target_html)}")
    print(f"Index path: {rel(index_path)}")
    print(f"Publish: {str(publish).lower()}")
    print(f"Dry run: {str(dry_run).lower()}")
    print("Validation:")
    for check in checks:
        print(f"- PASS: {check}")
    for error in errors:
        print(f"- FAIL: {error}")
    if not ok:
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        notes_path.write_text(publish_notes(args.date, source_html, target_html, index_path, publish, dry_run, checks, errors, files_written), encoding="utf-8")
        print(f"Publish notes: {rel(notes_path)}")
        return 1
    if publish and not dry_run:
        intelligence_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_html, target_html)
        files_written.append(target_html)
        index_path.write_text(build_index(intelligence_dir, args.date), encoding="utf-8")
        files_written.append(index_path)
    else:
        print("Dry-run / publish=false: public docs files were not written.")
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    notes_path.write_text(publish_notes(args.date, source_html, target_html, index_path, publish, dry_run, checks, errors, files_written), encoding="utf-8")
    files_written.append(notes_path)
    print("Files written:")
    if files_written:
        for path in files_written:
            print(f"- {rel(path)}")
    else:
        print("- None")
    print(f"Publish notes: {rel(notes_path)}")
    return 0


def main() -> None:
    raise SystemExit(run(parse_args()))


if __name__ == "__main__":
    main()
