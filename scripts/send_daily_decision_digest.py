#!/usr/bin/env python3
"""Send a short Daily Decision Digest email.

The digest engine is intentionally pluggable. Version 1 implements only the
rules engine; future engines can replace the decision logic without changing
source collection, rendering, or SMTP delivery.
"""

from __future__ import annotations

import argparse
import html as html_lib
import re
import smtplib
import sys
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

from utils import ROOT, env


TORONTO_TZ = ZoneInfo("America/Toronto")


def today_toronto() -> str:
    return datetime.now(TORONTO_TZ).date().isoformat()


REPORT_BASE = "https://robinyew.github.io/ai-investing-monitor"
CORE_SOURCE_KEYS = ["premarket", "news_scan", "hub"]
SMTP_REQUIRED = ["SMTP_HOST", "SMTP_PORT", "EMAIL_FROM", "EMAIL_TO"]

URGENT_NEGATIVE_PATTERNS = [
    r"\baccounting irregularit",
    r"\bsec investigation\b",
    r"\bregulatory investigation\b",
    r"\bfraud\b",
    r"\bdefault\b",
    r"\bbankruptcy\b",
    r"\binsolvenc",
    r"\bdilution\b",
    r"\bsecondary offering\b",
    r"\bmaterial weakness\b",
]

REVIEW_PATTERNS = [
    r"\bthesis damaged\b",
    r"\bthesis weakening\b",
    r"\bthesis watch\b",
    r"\bthesis status\s*[:|-]\s*watch\b",
    r"\bguidance (cut|lowered|reduced|down)\b",
    r"\bweak guidance\b",
    r"\bmiss(?:ed|es)? guidance\b",
    r"\bcapex (slowdown|slowing|cut|reduction|reduced|pause)\b",
    r"\bcustomer (cut|reduction|loss|cancel)",
    r"\border (cut|cancellation|delay)",
    r"\broadmap (replaced|displaced|cancelled|delayed)\b",
    r"\bmargin pressure\b",
    r"\bsupply constraint\b",
    r"\bnegative financial disclosure\b",
]

IGNORE_CONTEXT_PATTERNS = [
    r"\bprice target\b",
    r"\banalyst\b",
    r"\bpremarket\b",
    r"\bpre-market\b",
    r"\bafter-hours\b",
    r"\bstock (rose|fell|jumped|dropped|moved)\b",
    r"\bx post\b",
    r"\bunverified\b",
    r"\brumou?r\b",
]


@dataclass
class Source:
    key: str
    label: str
    path: Path
    url: str
    required_for_core: bool = False
    text: str = ""
    missing: bool = False


@dataclass
class Digest:
    date: str
    subject_status: str
    action_required: str
    thesis_status: str
    major_negative_events: list[str]
    portfolio_impact: str
    changed_since_yesterday: list[str]
    suggested_action: str
    sources: dict[str, Source]
    missing_sources: list[str]


def strip_html(html: str) -> str:
    """Convert an HTML report to plain text, keeping h1/h2 headings as markdown."""
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?i)<h1[^>]*>", "\n# ", text)
    text = re.sub(r"(?i)<h2[^>]*>", "\n## ", text)
    text = re.sub(r"(?i)<(br|/p|/div|/li|/tr|/h[1-6]|/table)[^>]*>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    return text


def read_text(path: Path) -> tuple[str, bool]:
    if not path.exists():
        return "", True
    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() in {".html", ".htm"}:
        text = strip_html(text)
    return text, False


def collect_sources(date: str) -> dict[str, Source]:
    """Collect available report inputs without failing on missing optional files."""
    hub_md = ROOT / "investment-intelligence-hub" / "reports" / "daily_intelligence" / f"{date}.md"
    hub_html = ROOT / "docs" / "intelligence" / f"{date}.html"
    hub_path = hub_md if hub_md.exists() else hub_html
    specs = [
        ("premarket", "Pre-Market Brief", ROOT / "reports" / "daily" / f"{date}.md", f"{REPORT_BASE}/reports/{date}.html", True),
        ("news_scan", "AI Infrastructure News Scan", ROOT / "investment-intelligence-hub" / "inbox" / "news" / f"{date}_ai_infrastructure_news.md", f"{REPORT_BASE}/news/{date}.html", True),
        ("hub", "Hub Intelligence Brief", hub_path, f"{REPORT_BASE}/intelligence/{date}.html", True),
        ("premarket_html", "Pre-Market HTML", ROOT / "docs" / "reports" / f"{date}.html", f"{REPORT_BASE}/reports/{date}.html", False),
        ("hub_html", "Hub Intelligence HTML", ROOT / "docs" / "intelligence" / f"{date}.html", f"{REPORT_BASE}/intelligence/{date}.html", False),
    ]
    sources: dict[str, Source] = {}
    for key, label, path, url, required in specs:
        text, missing = read_text(path)
        sources[key] = Source(key, label, path, url, required, text, missing)
    return sources


NOISE_SECTION_TITLE = re.compile(r"unverified|noise|hype|x post|social|watchlist", re.I)

# Words that mean the match itself is fundamental, so the ignore window may not veto it.
HARD_SIGNAL_HINTS = ("guidance", "capex", "thesis")

# Bullish/easing context: a risk keyword inside clearly positive framing
# (e.g. "reduces one supply constraint", "bullish implication") is not a risk.
BULLISH_CONTEXT_PATTERNS = [
    r"\bbullish\b",
    r"\beas(?:e|es|ed|ing)\b",
    r"\bpositive for\b",
    r"\bimproving\b",
    r"\bresolved\b",
    r"\btailwind",
]


def extract_signal_sections(text: str) -> str:
    """Keep only Hub sections that may carry source-backed signal (sections 1-3).

    Excludes noise-type sections (Unverified Leads, Noise / Hype Filter, X/social)
    per the source hierarchy: Tier 4 content must never trigger action.
    """
    parts = re.split(r"(?m)^##\s+", text)
    if len(parts) <= 1:
        return text
    keep: list[str] = []
    for part in parts[1:]:
        title = part.splitlines()[0].strip() if part.splitlines() else ""
        if NOISE_SECTION_TITLE.search(title):
            continue
        num_match = re.match(r"(\d+)\.", title)
        if num_match and int(num_match.group(1)) > 3:
            continue
        keep.append(part)
    return "\n## ".join(keep) if keep else text


def matches_with_context(text: str, patterns: list[str], window: int = 160) -> list[str]:
    """Return patterns that match outside of an ignorable (noise) local context.

    Unlike a whole-document check, only the +/-window characters around each
    match may veto it, so one 'analyst' mention elsewhere cannot mute real signals.
    """
    found: list[str] = []
    lowered = text.lower()
    for pattern in patterns:
        for m in re.finditer(pattern, lowered, re.I):
            local = lowered[max(0, m.start() - window): m.end() + window]
            hard = any(hint in m.group(0) for hint in HARD_SIGNAL_HINTS)
            noisy = any(re.search(p, local, re.I) for p in IGNORE_CONTEXT_PATTERNS)
            noisy = noisy or any(re.search(p, local, re.I) for p in BULLISH_CONTEXT_PATTERNS)
            if hard or not noisy:
                found.append(pattern)
                break
    return found


def extract_hub_verdict(text: str) -> str:
    for line in text.splitlines():
        if "thesis damaged" in line.lower() or "thesis weakening" in line.lower():
            return line.strip("- |")
    for line in text.splitlines():
        lowered = line.lower()
        if ("thesis watch" in lowered or "thesis status" in lowered and "watch" in lowered) and "chokepoint" not in lowered:
            return line.strip("- |")
    return ""


def first_material_changes(text: str, limit: int = 3) -> list[str]:
    """Pull the first bullets or table rows from the '## 2. ...' changes section."""
    changes: list[str] = []
    capture = False
    table_rows_seen = 0
    for raw in text.splitlines():
        line = raw.strip()
        if re.match(r"##\s*2\.", line):
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if not capture or not line:
            continue
        if line.startswith("- ") and "No cross-source material change" not in line:
            changes.append(line[2:].strip())
        elif line.startswith("|") and not set(line) <= set("|-: "):
            table_rows_seen += 1
            if table_rows_seen == 1:  # header row
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|") if cell.strip()]
            if cells:
                changes.append(" — ".join(cells[:3])[:200])
        if len(changes) >= limit:
            break
    return changes


def generate_digest_with_rules(sources: dict[str, Source]) -> Digest:
    """Rules engine v1. Conservative default: no action unless fundamentals changed."""
    date = next(iter(sources.values())).path.stem[:10] if sources else today_toronto()
    missing = [source.label for source in sources.values() if source.missing]

    # Escalation scanning scope (source hierarchy): Hub signal sections (1-3,
    # excluding unverified/noise sections) + News Scan (Tier 2A). Pre-Market
    # Brief and X content are context/narrative only and never trigger action.
    hub_text = sources.get("hub", Source("", "", Path(), "")).text
    news_text = sources.get("news_scan", Source("", "", Path(), "")).text
    signal_text = extract_signal_sections(hub_text) + "\n\n" + news_text

    urgent_matches = matches_with_context(signal_text, URGENT_NEGATIVE_PATTERNS)
    review_matches = matches_with_context(signal_text, REVIEW_PATTERNS)
    hub_verdict = extract_hub_verdict(hub_text)

    subject_status = "No Action Required"
    action_required = "No"
    thesis_status = "Intact"
    suggested_action = "Hold current positions. No portfolio change needed."
    major_negative_events = [
        "None found in available source files. If a later filing, earnings release, guidance update, customer announcement, or capex disclosure contradicts this, treat that primary source as higher priority than this digest."
    ]
    portfolio_impact = (
        "No confirmed portfolio-level change. The available reports do not show earnings damage, guidance reduction, core customer loss, AI CapEx slowdown, "
        "product replacement, accounting issue, regulatory issue, financing stress, or dilution event. Treat price movement, analyst commentary, and unverified social discussion as noise unless supported by primary evidence."
    )

    if urgent_matches:
        subject_status = "Urgent Negative Event"
        action_required = "Yes"
        thesis_status = "Watch"
        major_negative_events = ["Potential urgent fundamental risk detected. Review primary sources before taking any portfolio action."]
        portfolio_impact = (
            "Risk review required. Confirm whether the event is supported by SEC filings, company IR, earnings materials, or official guidance. "
            "Do not treat social posts, price movement, or analyst commentary as sufficient evidence."
        )
        suggested_action = "Review the source evidence first. Do not make portfolio changes from headlines or social posts alone."
    elif review_matches or hub_verdict:
        subject_status = "Review Required"
        action_required = "Review"
        thesis_status = "Watch"
        major_negative_events = [hub_verdict or "Potential thesis or risk-review item detected; confirm with primary sources."]
        portfolio_impact = (
            "Review required, but no automatic portfolio change. Separate fundamental evidence from market noise, and check whether the signal appears in company materials, "
            "earnings commentary, guidance, backlog, customer announcements, or capex disclosures."
        )
        suggested_action = "Review the flagged evidence. Keep current positions unless primary-source confirmation changes the thesis."

    changes = first_material_changes(sources.get("hub", Source("", "", Path(), "")).text)
    if not changes:
        changes = first_material_changes(sources.get("premarket", Source("", "", Path(), "")).text)
    if not changes:
        changes = ["No material change detected across available reports. The digest stays in discipline mode: preserve the existing thesis unless primary-source evidence says otherwise."]

    return Digest(
        date=date,
        subject_status=subject_status,
        action_required=action_required,
        thesis_status=thesis_status,
        major_negative_events=major_negative_events[:3],
        portfolio_impact=portfolio_impact,
        changed_since_yesterday=changes[:3],
        suggested_action=suggested_action,
        sources=sources,
        missing_sources=missing,
    )


def subject_for_digest(digest: Digest) -> str:
    return f"AI Investing Digest — {digest.subject_status} — {digest.date}"


def render_email(digest: Digest) -> str:
    missing_note = "None" if not digest.missing_sources else ", ".join(digest.missing_sources)
    negative_events = "\n".join(f"- {item}" for item in digest.major_negative_events)
    changes = "\n".join(f"- {item}" for item in digest.changed_since_yesterday)
    links = "\n".join(
        f"- {source.label}: {source.url if not source.missing else 'missing'}"
        for key, source in digest.sources.items()
        if key in {"premarket", "news_scan", "hub", "premarket_html", "hub_html"}
    )
    body = f"""Action Required
{digest.action_required}
The rules engine is conservative by design. It only escalates when the reports contain evidence of a material business change, not when the market is noisy.

Thesis Status
{digest.thesis_status}
The default thesis state is intact unless there is primary-source or clearly source-backed evidence that AI infrastructure demand, customer orders, guidance, backlog, margins, or financing risk has changed.

Major Negative Events
{negative_events}

Portfolio Impact
{digest.portfolio_impact}

What Changed Since Yesterday
{changes}

Suggested Action
{digest.suggested_action}
This is a research-only discipline note. It is not a trading order, and it should not override the full reports when a deeper review is required.

Links to Full Reports
{links}

Missing Sources
{missing_note}

Research-only. No brokerage connection, no trade execution, and no automatic portfolio action.
"""
    return body.strip() + "\n"


def smtp_user() -> str:
    return env("SMTP_USER") or env("SMTP_USERNAME")


def smtp_pass() -> str:
    return env("SMTP_PASS") or env("SMTP_PASSWORD")


def send_email(subject: str, body: str) -> bool:
    missing = [name for name in SMTP_REQUIRED if not env(name)]
    if not smtp_user():
        missing.append("SMTP_USER")
    if not smtp_pass():
        missing.append("SMTP_PASS")
    if missing:
        print(f"Email skipped: missing env vars: {', '.join(missing)}")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = env("EMAIL_FROM")
    msg["To"] = env("EMAIL_TO")
    msg.set_content(body)

    port = int(env("SMTP_PORT", "587"))
    try:
        with smtplib.SMTP(env("SMTP_HOST"), port, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(smtp_user(), smtp_pass())
            smtp.send_message(msg)
        print(f"Daily Decision Digest sent to {env('EMAIL_TO')}")
        return True
    except Exception as exc:
        print(f"Daily Decision Digest email failed: {exc}")
        return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send Daily Decision Digest email.")
    parser.add_argument("--date", default=today_toronto())
    parser.add_argument("--engine", default="rules", choices=["rules", "fable"])
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sources = collect_sources(args.date)
    missing_core = [key for key in CORE_SOURCE_KEYS if sources[key].missing]
    if len(missing_core) == len(CORE_SOURCE_KEYS):
        print(f"ERROR: core reports missing for {args.date}: {', '.join(missing_core)}")
        return 2

    if args.engine != "rules":
        print(f"ERROR: engine '{args.engine}' is reserved for future integration and is not implemented yet.")
        return 2

    digest = generate_digest_with_rules(sources)
    digest.date = args.date
    subject = subject_for_digest(digest)
    body = render_email(digest)

    if args.dry_run:
        print("DRY RUN - Daily Decision Digest")
        print(f"Subject: {subject}")
        print("")
        print(body)
        return 0

    return 0 if send_email(subject, body) else 1


if __name__ == "__main__":
    sys.exit(main())
