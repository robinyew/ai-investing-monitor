#!/usr/bin/env python3
"""Send a short Daily Decision Digest email.

The digest engine is intentionally pluggable. Version 1 implements only the
rules engine; future engines can replace the decision logic without changing
source collection, rendering, or SMTP delivery.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
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

# ---------------------------------------------------------------------------
# Fable engine (preview/test only — phase 1 never sends email)
# ---------------------------------------------------------------------------

FABLE_MODEL_DEFAULT = "claude-fable-5"
FABLE_MAX_REPORT_CHARS = 10000

ALLOWED_SUGGESTED_ACTIONS = [
    "Hold current positions. No portfolio change needed.",
    "Review affected holding before taking action.",
    "Wait for primary-source confirmation.",
    "Escalate for human review.",
]

SEVERITY_TO_SUBJECT = {
    "none": "No Action Required",
    "review": "Review Required",
    "urgent": "Urgent Negative Event",
}

FABLE_SYSTEM_PROMPT = """You are a conservative investment research triage assistant for an AI-infrastructure portfolio.
You read three daily reports and output a strict JSON verdict. You are a discipline layer, not an advisor.

Hard rules:
- Default verdict: action_required "No", severity "none", thesis_status "Intact",
  suggested_action "Hold current positions. No portfolio change needed."
- Escalate to "review" or "urgent" ONLY on clear fundamental change: guidance cut,
  major earnings miss, core customer order cuts, confirmed AI capex slowdown,
  product roadmap displacement, accounting/regulatory/financing/dilution risk,
  or the Hub report explicitly showing thesis damage.
- NEVER escalate because of: ordinary price moves, pre/post-market moves, analyst
  price-target changes, emotional discussion on X/social media, rumors without
  primary-source support, or price drops without fundamental evidence.
- You must NOT output buy/sell/trim/add recommendations, position sizes, or price targets.
- suggested_action MUST be exactly one of the four allowed strings.
- Output ONLY a single JSON object. No markdown fences, no commentary."""

FABLE_USER_PROMPT = """Date: {date}

JSON schema (return exactly these keys):
{{
  "action_required": "No" | "Yes",
  "severity": "none" | "review" | "urgent",
  "thesis_status": "Intact" | "Watch" | "Damaged",
  "portfolio_impact": "None" | "Low" | "Medium" | "High",
  "major_negative_events": [
    {{"ticker": "...", "event": "...", "evidence_source": "...", "why_it_matters": "..."}}
  ],
  "what_changed": [
    {{"topic": "...", "summary": "...", "source_url": "...",
      "source_type": "primary" | "news" | "report" | "price" | "unverified",
      "confidence": "Low" | "Medium" | "High"}}
  ],
  "suggested_action": one of:
    "Hold current positions. No portfolio change needed." /
    "Review affected holding before taking action." /
    "Wait for primary-source confirmation." /
    "Escalate for human review.",
  "confidence": "Low" | "Medium" | "High"
}}

Consistency rules: severity "none" implies action_required "No"; severity "review" or
"urgent" implies action_required "Yes". major_negative_events must be [] when severity
is "none".

what_changed rules: 1-3 items, each with a source_url. Prefer URLs in this order:
1. company IR / SEC filing / earnings release / transcript (source_type "primary")
2. original news article URL from the reports (source_type "news")
3. one of the three full report URLs below (source_type "report")
For pure price moves: source_type "price", link the Pre-Market Brief, and the summary
MUST end with "price move only; no confirmed thesis damage."
For rumors without primary sources: source_type "unverified" and the summary MUST
state "no primary-source confirmation; no thesis change." Positive demand datapoints
(e.g. supplier AI-server demand) are "news"/"primary" — never use price-move wording.
Each summary must be ONE concise sentence.
If no URL is available at all, set source_url to "" and confidence to "Low".
Report URLs: Pre-Market Brief {premarket_url} | News Scan {news_url} | Hub {hub_url}

=== PRE-MARKET BRIEF (context only, never thesis-confirming) ===
{premarket}

=== AI INFRASTRUCTURE NEWS SCAN (Tier 2A) ===
{news}

=== HUB INTELLIGENCE BRIEF (signal triage) ===
{hub}
"""

NOISE_EVIDENCE = re.compile(
    r"price|analyst|target|x post|twitter|social|rumou?r|premarket|pre-market|after-hours|sentiment|momentum", re.I)
TIER1_EVIDENCE = re.compile(
    r"guidance|earnings|filing|sec\b|10-k|10-q|8-k|investor relations|press release|transcript|capex|customer|order|backlog", re.I)

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
    confidence: str = ""
    engine_notes: list[str] | None = None


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


PRICE_MOVE_HINT = re.compile(r"price move|price-discipline|moved (up|down)|[+-]\d+(\.\d+)?%", re.I)


def annotate_price_move(item: str) -> str:
    """Pure price-move items must be explicitly labeled as non-thesis events."""
    if PRICE_MOVE_HINT.search(item):
        item = re.sub(r"\s*—\s*price-discipline alert, not thesis upgrade\s*$", "", item)
        return f"{item} — price move only; no confirmed thesis damage."
    return item


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
    major_negative_events: list[str] = []
    portfolio_impact = "None"

    if urgent_matches:
        subject_status = "Urgent Negative Event"
        action_required = "Yes"
        thesis_status = "Watch"
        major_negative_events = ["Potential urgent fundamental risk detected. Review primary sources before any portfolio action."]
        portfolio_impact = "High"
        suggested_action = "Review the source evidence first. Do not act on headlines or social posts alone."
    elif review_matches or hub_verdict:
        subject_status = "Review Required"
        action_required = "Review"
        thesis_status = "Watch"
        major_negative_events = [hub_verdict or "Potential thesis or risk-review item detected; confirm with primary sources."]
        portfolio_impact = "Medium"
        suggested_action = "Review the flagged evidence. Keep current positions unless primary-source confirmation changes the thesis."

    # Every Notable Context line carries a source link: the report it was parsed
    # from (rules engine has no per-item URLs, so the full report is the source).
    changes = first_material_changes(sources.get("hub", Source("", "", Path(), "")).text)
    context_url = sources.get("hub", Source("", "", Path(), "")).url
    if not changes:
        changes = first_material_changes(sources.get("premarket", Source("", "", Path(), "")).text)
        context_url = sources.get("premarket", Source("", "", Path(), "")).url
    if not changes:
        changes = ["No material change detected across available reports."]
        context_url = sources.get("hub", Source("", "", Path(), "")).url
    # Display order: fundamentals first, price moves last (rendering only).
    changes = sorted(changes, key=lambda item: 1 if PRICE_MOVE_HINT.search(item) else 0)
    changes = [f"{annotate_price_move(item)}\n  Source: {context_url}" for item in changes]

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


# ---------------------------------------------------------------------------
# Fable engine: model call, strict validation, guardrails, fallback
# ---------------------------------------------------------------------------

def call_fable(sources: dict[str, Source], date: str) -> str:
    """Return the model's raw text. FABLE_TEST_JSON_FILE overrides for offline tests."""
    test_file = env("FABLE_TEST_JSON_FILE")
    if test_file:
        return Path(test_file).read_text(encoding="utf-8")

    api_key = env("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")
    import anthropic  # lazy import: rules engine must work without the SDK

    def clip(key: str) -> str:
        text = sources.get(key, Source("", "", Path(), "")).text
        return text[:FABLE_MAX_REPORT_CHARS] if text else "(missing)"

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=env("FABLE_MODEL", FABLE_MODEL_DEFAULT),
        max_tokens=2000,
        system=FABLE_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": FABLE_USER_PROMPT.format(
                date=date, premarket=clip("premarket"), news=clip("news_scan"), hub=clip("hub"),
                premarket_url=sources["premarket"].url, news_url=sources["news_scan"].url,
                hub_url=sources["hub"].url),
        }],
    )
    # The model may return thinking / tool_use / redacted_thinking blocks alongside
    # text. Only type == "text" blocks carry the JSON verdict; skip everything else.
    text_parts = [
        getattr(block, "text", None)
        for block in response.content
        if getattr(block, "type", None) == "text"
    ]
    text_parts = [part for part in text_parts if part]
    if not text_parts:
        raise RuntimeError("no text content returned from fable")
    return "\n".join(text_parts)


def parse_and_validate_fable(raw: str) -> dict | None:
    """Strict schema validation. Returns None on any violation (caller falls back)."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None

    enums = {
        "action_required": {"No", "Yes"},
        "severity": {"none", "review", "urgent"},
        "thesis_status": {"Intact", "Watch", "Damaged"},
        "portfolio_impact": {"None", "Low", "Medium", "High"},
        "confidence": {"Low", "Medium", "High"},
    }
    required = set(enums) | {"major_negative_events", "what_changed", "suggested_action"}
    if set(payload) != required:
        return None
    for key, allowed in enums.items():
        if payload[key] not in allowed:
            return None
    if payload["suggested_action"] not in ALLOWED_SUGGESTED_ACTIONS:
        return None
    events = payload["major_negative_events"]
    if not isinstance(events, list):
        return None
    for event in events:
        if not isinstance(event, dict) or set(event) != {"ticker", "event", "evidence_source", "why_it_matters"}:
            return None
        if not all(isinstance(value, str) for value in event.values()):
            return None
    changed = payload["what_changed"]
    if not isinstance(changed, list):
        return None
    context_keys = {"topic", "summary", "source_url", "source_type", "confidence"}
    for item in changed:
        if not isinstance(item, dict) or set(item) != context_keys:
            return None
        if not all(isinstance(value, str) for value in item.values()):
            return None
        if item["source_type"] not in {"primary", "news", "report", "price", "unverified"}:
            return None
        if item["confidence"] not in {"Low", "Medium", "High"}:
            return None
    # Consistency: severity drives action_required.
    payload["action_required"] = "No" if payload["severity"] == "none" else "Yes"
    return payload


def apply_fable_guardrails(payload: dict, rules_digest: Digest) -> tuple[dict, list[str]]:
    """Deterministic guardrails on top of the model verdict (req: noise never escalates)."""
    notes: list[str] = []
    if payload["severity"] == "none":
        return payload, notes

    events = payload["major_negative_events"]

    def is_noise(event: dict) -> bool:
        blob = f"{event['event']} {event['evidence_source']} {event['why_it_matters']}"
        return bool(NOISE_EVIDENCE.search(blob)) and not TIER1_EVIDENCE.search(blob)

    def downgrade_to_none(reason: str) -> None:
        payload.update(severity="none", action_required="No", thesis_status="Intact",
                       portfolio_impact="None", major_negative_events=[],
                       suggested_action=ALLOWED_SUGGESTED_ACTIONS[0], confidence="Low")
        notes.append(f"GUARDRAIL: downgraded to No Action — {reason}")

    if not events:
        downgrade_to_none("escalation without any major_negative_events evidence")
    elif all(is_noise(event) for event in events):
        downgrade_to_none("all cited evidence is price/analyst/social noise (never triggers action)")
    elif payload["severity"] == "urgent":
        rules_agrees = rules_digest.subject_status == "Urgent Negative Event"
        has_tier1 = any(TIER1_EVIDENCE.search(f"{e['event']} {e['evidence_source']}") for e in events)
        if not rules_agrees and not has_tier1:
            payload.update(severity="review", confidence="Low")
            notes.append("GUARDRAIL: urgent downgraded to Review (low confidence) — no Tier-1-style evidence and rules engine did not corroborate")
    return payload, notes


PRICE_PHRASE = "price move only; no confirmed thesis damage."
UNVERIFIED_PHRASE = "no primary-source confirmation; no thesis change."

# Existing (possibly truncated) copies of the required phrases are stripped from the
# model's summary BEFORE truncation, then re-appended exactly once — this prevents
# duplicates like "no primary-s. no primary-source confirmation".
CLEAN_PHRASE_PATTERNS = [
    re.compile(r"(?i)[\s,;.]*price move only[^.]*\.?"),
    re.compile(r"(?i)[\s,;.]*no primary-s[^.]*\.?"),
    re.compile(r"(?i)[\s,;.]*no thesis change\.?"),
    re.compile(r"(?i)[\s,;.]*unconfirmed[.;]?(?=\s|$)"),
]


def clean_required_phrases(text: str) -> str:
    for pattern in CLEAN_PHRASE_PATTERNS:
        text = pattern.sub("", text)
    return text.strip(" ,;")


def truncate_sentence(text: str, limit: int) -> str:
    """One concise sentence within the limit, cut at the nearest clause boundary
    (sentence > semicolon > comma), falling back to a word boundary."""
    text = text.strip()
    if len(text) > limit:
        cut = text[:limit]
        for sep in (". ", "; ", ", "):
            pos = cut.rfind(sep)
            if pos >= limit // 3:
                cut = cut[:pos]
                break
        else:
            if " " in cut:
                cut = cut[: cut.rfind(" ")]
        text = cut.rstrip(" ,;:.")
    return (text.rstrip(".") or "No detail provided") + "."


def format_context_items(items: list[dict]) -> list[str]:
    """Render what_changed objects as Notable Context lines, each with a source link.

    Items without any source_url are demoted to low-confidence notes (never strong context).
    """
    # Order: thesis/unconfirmed risk first, business fundamentals second, price/market last.
    type_order = {"unverified": 0, "primary": 1, "news": 1, "report": 1, "price": 2}
    items = sorted(items, key=lambda item: type_order.get(item["source_type"], 1))
    rendered: list[str] = []
    for item in items[:3]:
        summary = clean_required_phrases(item["summary"])
        if item["source_type"] == "price":
            summary = f"{truncate_sentence(summary, 150)} {PRICE_PHRASE}"
        elif item["source_type"] == "unverified":
            summary = f"{truncate_sentence(summary, 150)} {UNVERIFIED_PHRASE}"
        else:
            summary = truncate_sentence(summary, 200)
        prefix = f"{item['topic']}: " if item["topic"] else ""
        if item["source_url"]:
            rendered.append(f"{prefix}{summary}\n  Source: {item['source_url']}")
        else:
            rendered.append(f"[Low confidence] {prefix}{summary}\n  Source: unavailable — review full reports.")
    return rendered


def digest_from_fable(payload: dict, sources: dict[str, Source], date: str, notes: list[str]) -> Digest:
    events = [
        f"{e['ticker']} — {e['event']} (source: {e['evidence_source']}) — {e['why_it_matters']}"
        for e in payload["major_negative_events"]
    ]
    return Digest(
        date=date,
        subject_status=SEVERITY_TO_SUBJECT[payload["severity"]],
        action_required=payload["action_required"],
        thesis_status=payload["thesis_status"],
        major_negative_events=events[:3],
        portfolio_impact=payload["portfolio_impact"],
        changed_since_yesterday=format_context_items(payload["what_changed"]),
        suggested_action=payload["suggested_action"],
        sources=sources,
        missing_sources=[s.label for s in sources.values() if s.missing],
        confidence=payload["confidence"],
        engine_notes=notes,
    )


def generate_digest_with_fable(sources: dict[str, Source], date: str) -> tuple[Digest, dict]:
    """Returns (digest, debug_info). Any failure falls back to the rules engine.

    debug_info keys: engine, call_success, fallback, fallback_reason, guardrail_notes.
    Debug info is for dry-run stdout only — it must never appear in a sent email.
    """
    rules_digest = generate_digest_with_rules(sources)
    try:
        raw = call_fable(sources, date)
    except Exception as exc:
        return rules_digest, {"engine": "rules", "call_success": False, "fallback": True,
                              "fallback_reason": f"fable call failed ({exc})", "guardrail_notes": []}
    payload = parse_and_validate_fable(raw)
    if payload is None:
        return rules_digest, {"engine": "rules", "call_success": True, "fallback": True,
                              "fallback_reason": "fable output failed strict JSON schema validation",
                              "guardrail_notes": []}
    payload, notes = apply_fable_guardrails(payload, rules_digest)
    digest = digest_from_fable(payload, sources, date, notes)
    return digest, {"engine": "fable", "call_success": True, "fallback": False,
                    "fallback_reason": "", "guardrail_notes": notes}


def subject_for_digest(digest: Digest) -> str:
    return f"AI Investing Digest — {digest.subject_status} — {digest.date}"


def render_email(digest: Digest) -> str:
    changes = "\n".join(f"- {item}" for item in digest.changed_since_yesterday[:3])
    links = "\n".join(
        f"- {source.label}: {source.url if not source.missing else 'missing'}"
        for key, source in digest.sources.items()
        if key in {"premarket", "news_scan", "hub"}
    )
    parts = [
        f"Action Required: {digest.action_required}",
        f"Thesis Status: {digest.thesis_status}",
        f"Portfolio Impact: {digest.portfolio_impact}",
        f"Suggested Action: {digest.suggested_action}",
    ]
    if digest.confidence:
        parts.append(f"Confidence: {digest.confidence}")
    if digest.major_negative_events:
        events = "\n".join(f"- {item}" for item in digest.major_negative_events)
        parts.append(f"\nMajor Negative Events\n{events}")
    parts.append(f"\nNotable Context\n{changes}")
    parts.append(f"\nLinks to Full Reports\n{links}")
    if digest.missing_sources:
        parts.append(f"\nMissing Sources: {', '.join(digest.missing_sources)}")
    # Debug info (engine, fallback, guardrail notes) is intentionally NOT rendered
    # into the email body — it is printed to stdout in dry-run mode only.
    parts.append("\nResearch-only. No automatic trading action.")
    return "\n".join(parts).strip() + "\n"


def save_digest_copy(date: str, engine: str, subject: str, body: str, engine_detail: str = "") -> None:
    """Persist the exact email content to reports/digest/ for local history/comparison."""
    path = ROOT / "reports" / "digest" / f"{date}_{engine}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"Subject: {subject}\n"
    if engine_detail:
        header += f"Engine: {engine_detail}\n"
    path.write_text(header + "\n" + body, encoding="utf-8")
    print(f"Digest copy saved: {path.relative_to(ROOT)}")


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

    if args.engine == "fable":
        # Fable runs as a parallel PREVIEW digest: subject is always marked
        # "Fable Preview" and the body carries a preview footer, so it can never
        # be mistaken for the official rules-engine digest.
        digest, info = generate_digest_with_fable(sources, args.date)
        digest.date = args.date
        subject = f"AI Investing Digest — Fable Preview — {digest.subject_status} — {digest.date}"
        body = render_email(digest).rstrip() + "\n\nPreview only. Official digest remains rules engine.\n"
        # Debug info goes to stdout (dry-run console / Actions log), never into the email.
        print("DRY RUN - Daily Decision Digest" if args.dry_run else "Daily Decision Digest (Fable Preview)")
        print(f"Engine: {info['engine']}")
        print(f"Fable call success: {'Yes' if info['call_success'] else 'No'}")
        print(f"Fallback: {'Yes' if info['fallback'] else 'No'}")
        if info["fallback_reason"]:
            print(f"Fallback reason: {info['fallback_reason']}")
        for note in info["guardrail_notes"]:
            print(note)
        print(f"Subject: {subject}")
        if args.dry_run:
            print("")
            print(body)
            return 0
        save_digest_copy(args.date, "fable", subject, body, engine_detail=info["engine"])
        return 0 if send_email(subject, body) else 1

    digest = generate_digest_with_rules(sources)
    digest.date = args.date
    subject = subject_for_digest(digest)
    body = render_email(digest)

    if args.dry_run:
        print("DRY RUN - Daily Decision Digest (engine: rules)")
        print(f"Subject: {subject}")
        print("")
        print(body)
        return 0

    save_digest_copy(args.date, "rules", subject, body, engine_detail="rules")
    return 0 if send_email(subject, body) else 1


if __name__ == "__main__":
    sys.exit(main())
