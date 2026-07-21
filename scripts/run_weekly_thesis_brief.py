#!/usr/bin/env python3
"""Generate Weekly Thesis Brief → Huashu HTML → optional email.

Pipeline:
  1. Resolve week_end (Friday, America/New_York by default)
  2. Ensure markdown exists under memory/weekly_reviews/
     - prefer existing filled brief
     - else auto-fill from week digests/news (LLM if ANTHROPIC_API_KEY, else rules summary)
  3. Render polished HTML via huashu-md-html (theme=report, pandoc)
  4. Write HTML to docs/weekly/ and reports/weekly/
  5. Optionally email HTML body via SMTP

Usage:
  python3 scripts/run_weekly_thesis_brief.py
  python3 scripts/run_weekly_thesis_brief.py --week-end 2026-07-18
  python3 scripts/run_weekly_thesis_brief.py --week-end 2026-07-18 --no-email
  python3 scripts/run_weekly_thesis_brief.py --preview-only   # html only, no email

Research-only. No brokerage. No buy/sell instructions.
"""

from __future__ import annotations

import argparse
import os
import re
import smtplib
import subprocess
import sys
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from zoneinfo import ZoneInfo

from utils import ROOT, env

NY = ZoneInfo("America/New_York")
TORONTO = ZoneInfo("America/Toronto")

WEEKLY_MD_DIR = ROOT / "investment-intelligence-hub" / "memory" / "weekly_reviews"
DOCS_HTML_DIR = ROOT / "docs" / "weekly"
REPORTS_HTML_DIR = ROOT / "reports" / "weekly"
DIGEST_DIR = ROOT / "reports" / "digest"
NEWS_DIR = ROOT / "investment-intelligence-hub" / "inbox" / "news"
DAILY_DIR = ROOT / "reports" / "daily"

def _resolve_huashu() -> Path:
    candidates = [
        ROOT / "vendor" / "huashu-md-html" / "scripts" / "md_to_html.py",
        Path.home() / ".agents" / "skills" / "huashu-md-html" / "scripts" / "md_to_html.py",
        Path.home() / ".skills-manager" / "skills" / "huashu-md-html" / "scripts" / "md_to_html.py",
        Path.home() / ".claude" / "skills" / "huashu-md-html" / "scripts" / "md_to_html.py",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]

HUASHU_MD_TO_HTML = _resolve_huashu()

SMTP_REQUIRED = ["SMTP_HOST", "SMTP_PORT", "EMAIL_FROM", "EMAIL_TO"]


def load_dotenv_local() -> None:
    """Load KEY=VALUE from .env.local into os.environ if not already set."""
    path = ROOT / ".env.local"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = val


def friday_on_or_before(d) -> str:
    """Nearest Friday on or before date (Mon=0 ... Fri=4)."""
    delta = (d.weekday() - 4) % 7
    return (d - timedelta(days=delta)).isoformat()


def week_start_from_end(week_end: str) -> str:
    end = datetime.fromisoformat(week_end).date()
    return (end - timedelta(days=4)).isoformat()


def daterange(start: str, end: str) -> list[str]:
    s = datetime.fromisoformat(start).date()
    e = datetime.fromisoformat(end).date()
    out = []
    cur = s
    while cur <= e:
        out.append(cur.isoformat())
        cur += timedelta(days=1)
    return out


def collect_week_sources(week_start: str, week_end: str) -> dict[str, list[tuple[str, str]]]:
    """Gather (path, text snippet) for digests/news/daily in the week window."""
    buckets: dict[str, list[tuple[str, str]]] = {
        "digest_rules": [],
        "digest_fable": [],
        "news": [],
        "daily": [],
    }
    for day in daterange(week_start, week_end):
        pairs = [
            ("digest_rules", DIGEST_DIR / f"{day}_rules.md"),
            ("digest_fable", DIGEST_DIR / f"{day}_fable.md"),
            ("news", NEWS_DIR / f"{day}_ai_infrastructure_news.md"),
            ("daily", DAILY_DIR / f"{day}.md"),
        ]
        for key, path in pairs:
            if path.exists():
                text = path.read_text(encoding="utf-8")
                # Cap each file to keep LLM/context reasonable
                buckets[key].append((str(path.relative_to(ROOT)), text[:12000]))
    return buckets


def is_mostly_empty_template(md_text: str) -> bool:
    """Heuristic: scaffold still has empty executive fields / many blanks."""
    if "Intact / Watch / Damaged —" in md_text and re.search(
        r"\*\*Overall thesis\*\*\s*\|\s*Intact / Watch / Damaged —\s*\|", md_text
    ):
        return True
    if md_text.count("| |") > 40 and "example_filled" not in md_text:
        # many empty table cells
        if "Biggest fact this week** |  |" in md_text or "**Biggest fact this week** |  |" in md_text:
            return True
        if re.search(r"\*\*Biggest fact this week\*\*\s*\|\s*\|", md_text):
            return True
    return "Fill executive strip" in md_text


def build_rules_brief(week_start: str, week_end: str, sources: dict) -> str:
    """No-LLM fallback: structured brief from available digests."""
    facts: list[str] = []
    for key in ("digest_fable", "digest_rules", "news", "daily"):
        for rel, text in sources.get(key, []):
            # pull Notable Context bullets / Key Developments headers
            for line in text.splitlines():
                s = line.strip()
                if s.startswith("- ") and any(
                    k in s.lower()
                    for k in (
                        "capex",
                        "tsmc",
                        "hbm",
                        "power",
                        "thesis",
                        "guidance",
                        "shortage",
                        "nvidia",
                        "amd",
                        "meta",
                        "asml",
                    )
                ):
                    facts.append(f"{s[2:]}  \n  _source: {rel}_")
                if s.startswith("### ") and key == "news":
                    facts.append(f"{s[4:]}  \n  _source: {rel}_")
    # dedupe preserve order
    seen = set()
    uniq = []
    for f in facts:
        h = f[:120]
        if h not in seen:
            seen.add(h)
            uniq.append(f)
    uniq = uniq[:8]

    facts_md = "\n".join(f"{i}. {f}" for i, f in enumerate(uniq, 1)) or "_No digest/news facts extracted this week._"

    source_list = []
    for key, items in sources.items():
        for rel, _ in items:
            source_list.append(f"- `{rel}` ({key})")
    sources_md = "\n".join(source_list) or "- _(none found in window)_"

    return f"""# Weekly Thesis & Chokepoint Brief — {week_end}

```yaml
report_type: weekly_thesis_brief
week_start: {week_start}
week_end: {week_end}
timezone: America/New_York
horizon: multi_month_to_multi_year
audience: long_term_AI_infra_investor
default_posture: Hold thesis unless falsified
generation: rules_auto
auto_trade: false
price_targets: false
buy_sell_instructions: false
```

**Research-only.** No brokerage connection. No buy/sell instructions. No price targets.  
**Auto-generated (rules engine)** from weekly digests/news. Review and edit if needed.

---

## 0. Executive strip

| Field | This week |
|---|---|
| **Overall thesis** | **Intact** (default unless primary falsifier found in sources) |
| **Posture** | **Hold thesis** |
| **Biggest fact this week** | See §3 extracted signals (verify primary tier) |
| **Biggest risk this week** | Misreading price volatility as thesis damage; soft secondary rumors |
| **Portfolio logic impact** | None until primary confirmation |
| **Next falsifier to watch** | Hyperscaler capex guide softens in primary filings |

**One-liner:** Weekly auto-brief from available monitors; thesis defaults to Intact without primary damage signals.

---

## 1. Thesis status

| Dimension | Status | Note |
|---|---|---|
| Demand / capex | Watch inputs | Confirm in primary IR/earnings |
| Chokepoints binding | Carry-forward | Power / optics / HBM / networking |
| Competition / ASIC | Watch | Secondary narratives only unless quantified |
| **Overall** | **Intact** | Price moves alone do not set Damaged |

---

## 2. Chokepoint dashboard (carry-forward defaults)

| Chokepoint | Status | Note |
|---|---|---|
| Power / cooling / grid | G | Structural bottleneck narrative continues unless falsified |
| Optical interconnect | Y | High narrative + high volatility; need primary orders |
| AI networking | G | |
| ASIC / custom silicon | Y | Watch, not proven displacement |
| Memory / HBM | G | Shortage narratives if present in §3 |
| AI server / EMS | G | |
| Cloud platform (payer) | G | Awaiting earnings guides |

---

## 3. Material signals extracted this week

{facts_md}

> Source-tier reminder: Secondary/analyst text cannot alone mark thesis **Damaged**.

---

## 4. Portfolio mapping

Core lens (`DELL VRT AAOI NVTS MPWR MRVL ANET AVGO ETN MSFT GOOGL`):  
**Logic Unchanged** by default. Mark Stronger/Weaker only after primary facts.

`No classification changes` (auto).

---

## 5. Falsifiers (armed)

| ID | Falsifier | Status |
|---|---|---|
| F1 | Hyperscaler AI capex cut in primary filings | Armed |
| F2 | Power no longer binding | Armed |
| F3 | Optics demand falsified (cancels/inventory) | Armed |
| F4 | ASIC substitution quantified in results | Armed |
| F5 | Core business model damage | Armed |

---

## 6. Price context

Appendix only. Do not change thesis from tape alone.  
If large SMH / high-beta drawdown: re-read §3 for missed primary facts.

---

## 7. Research agenda

1. Verify any capex / guidance claims against primary IR  
2. Update falsifier board if earnings week  
3. Human pass: edit executive strip if auto summary is incomplete  
4. Optional: ljg-invest deep dive only if classification may change  

---

## 8. Explicit noise

- Intraday levels / open checklists  
- Analyst price targets  
- Social rumor without primary source  

---

## 9. Sources scanned

{sources_md}

---

## 10. Sign-off

| Field | Value |
|---|---|
| Engine | rules_auto |
| Generated | {datetime.now(NY).strftime("%Y-%m-%d %H:%M %Z")} |
| Next brief due | {(datetime.fromisoformat(week_end).date() + timedelta(days=7)).isoformat()} |

_Template: `templates/weekly_thesis_brief.md` · Skill HTML: huashu-md-html theme=report_
"""


def build_llm_brief(week_start: str, week_end: str, sources: dict) -> str | None:
    """Optional Anthropic fill when ANTHROPIC_API_KEY is present."""
    api_key = env("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import urllib.request
        import json
    except ImportError:
        return None

    chunks = []
    for key, items in sources.items():
        for rel, text in items:
            chunks.append(f"### FILE {rel}\n{text[:6000]}")
    corpus = "\n\n".join(chunks)[:80000]
    if not corpus.strip():
        return None

    system = (
        "You write a Weekly Thesis & Chokepoint Brief for a long-term AI infrastructure investor. "
        "Research-only: no buy/sell, no price targets, no position sizes. "
        "Default Overall thesis = Intact unless clear primary fundamental damage. "
        "Price moves alone never set Damaged. Max 5 material facts. "
        "Output pure Markdown matching the project weekly template sections 0-10. "
        "Use tables. Chinese or bilingual OK; executive strip in English labels is fine. "
        "Cite source file names inline."
    )
    user = (
        f"Week: {week_start} → {week_end} (week_end Friday).\n"
        f"Master thesis: hyperscaler AI capex continues; bottlenecks in power/cooling, optics, networking, HBM; "
        f"own/research chokepoint businesses not theme beta.\n\n"
        f"SOURCE CORPUS:\n{corpus}\n\n"
        f"Write the full weekly brief markdown starting with H1: "
        f"# Weekly Thesis & Chokepoint Brief — {week_end}"
    )

    body = {
        "model": env("FABLE_MODEL") or env("WEEKLY_MODEL") or "claude-opus-4-8",
        "max_tokens": 8000,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        parts = data.get("content") or []
        text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:markdown|md)?\n", "", text)
            text = re.sub(r"\n```$", "", text)
        if len(text) < 400:
            return None
        # stamp generation meta
        if "generation:" not in text[:800]:
            text = text.replace(
                f"# Weekly Thesis & Chokepoint Brief — {week_end}",
                f"# Weekly Thesis & Chokepoint Brief — {week_end}\n\n"
                f"```yaml\nweek_start: {week_start}\nweek_end: {week_end}\n"
                f"generation: llm_auto\nauto_trade: false\n```",
                1,
            )
        return text
    except Exception as exc:
        print(f"[warn] LLM weekly fill failed: {exc}", file=sys.stderr)
        return None


def ensure_markdown(week_end: str, force_regen: bool = False) -> Path:
    week_start = week_start_from_end(week_end)
    WEEKLY_MD_DIR.mkdir(parents=True, exist_ok=True)
    md_path = WEEKLY_MD_DIR / f"{week_end}.md"

    if md_path.exists() and not force_regen:
        text = md_path.read_text(encoding="utf-8")
        if not is_mostly_empty_template(text):
            print(f"[md] using existing filled brief: {md_path}")
            return md_path
        print(f"[md] existing file looks empty/scaffold — regenerating content")

    sources = collect_week_sources(week_start, week_end)
    n_files = sum(len(v) for v in sources.values())
    print(f"[md] collected {n_files} source files for {week_start}..{week_end}")

    content = build_llm_brief(week_start, week_end, sources)
    engine = "llm_auto"
    if not content:
        content = build_rules_brief(week_start, week_end, sources)
        engine = "rules_auto"
        print("[md] wrote rules_auto brief (no LLM or LLM failed)")
    else:
        print("[md] wrote llm_auto brief")

    md_path.write_text(content, encoding="utf-8")
    # optional digest mirror
    digest_copy = DIGEST_DIR / f"{week_end}_weekly_thesis.md"
    DIGEST_DIR.mkdir(parents=True, exist_ok=True)
    digest_copy.write_text(content, encoding="utf-8")
    print(f"[md] engine={engine} → {md_path}")
    return md_path


def render_html(md_path: Path, week_end: str) -> Path:
    if not HUASHU_MD_TO_HTML.exists():
        raise SystemExit(
            f"huashu md_to_html not found at {HUASHU_MD_TO_HTML}. "
            "Install skill: https://github.com (huashu-md-html)"
        )
    DOCS_HTML_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_HTML_DIR.mkdir(parents=True, exist_ok=True)
    out_docs = DOCS_HTML_DIR / f"{week_end}.html"
    title = f"Weekly Thesis & Chokepoint Brief — {week_end}"
    cmd = [
        sys.executable,
        str(HUASHU_MD_TO_HTML),
        str(md_path),
        "--theme",
        "report",
        "--title",
        title,
        "-o",
        str(out_docs),
    ]
    print(f"[html] huashu render theme=report → {out_docs}")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or proc.stdout or "huashu render failed\n")
        raise SystemExit(proc.returncode)
    if proc.stdout:
        print(proc.stdout.strip())
    # mirror
    out_reports = REPORTS_HTML_DIR / f"{week_end}.html"
    out_reports.write_text(out_docs.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[html] mirrored → {out_reports}")
    return out_docs


def smtp_user() -> str:
    return env("SMTP_USER") or env("SMTP_USERNAME")


def smtp_pass() -> str:
    return env("SMTP_PASS") or env("SMTP_PASSWORD")


def send_weekly_email(week_end: str, md_path: Path, html_path: Path) -> bool:
    missing = [k for k in SMTP_REQUIRED if not env(k)]
    if not smtp_user():
        missing.append("SMTP_USER|SMTP_USERNAME")
    if not smtp_pass():
        missing.append("SMTP_PASS|SMTP_PASSWORD")
    if missing:
        print(f"[email] skipped: missing {', '.join(missing)}")
        return False

    html = html_path.read_text(encoding="utf-8")
    md = md_path.read_text(encoding="utf-8")
    plain = (
        f"Weekly Thesis & Chokepoint Brief — {week_end}\n\n"
        "Research-only. No buy/sell. No trading automation.\n\n"
        + md[:5000]
        + ("\n\n[... see HTML part for full formatted brief ...]" if len(md) > 5000 else "")
    )

    pages_hint = env("REPORT_BASE_URL")
    if pages_hint:
        # e.g. https://robinyew.github.io/ai-investing-monitor/reports → weekly sibling
        base = pages_hint.rstrip("/")
        if base.endswith("/reports"):
            weekly_url = base[: -len("/reports")] + f"/weekly/{week_end}.html"
        else:
            weekly_url = f"{base}/weekly/{week_end}.html"
        plain = f"HTML (if published):\n{weekly_url}\n\n" + plain

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Weekly Thesis Brief — {week_end}"
    msg["From"] = env("EMAIL_FROM")
    msg["To"] = env("EMAIL_TO")
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    port = int(env("SMTP_PORT", "587"))
    try:
        with smtplib.SMTP(env("SMTP_HOST"), port, timeout=60) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(smtp_user(), smtp_pass())
            smtp.send_message(msg)
        print(f"[email] sent to {env('EMAIL_TO')}")
        return True
    except Exception as exc:
        print(f"[email] failed: {exc}")
        return False


def update_weekly_index(week_end: str) -> None:
    """Simple index for docs/weekly/index.html"""
    DOCS_HTML_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(DOCS_HTML_DIR.glob("*.html"), reverse=True)
    files = [f for f in files if f.name != "index.html"]
    items = "\n".join(
        f'    <li><a href="{f.name}">Weekly Thesis — {f.stem}</a></li>' for f in files[:52]
    )
    index = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Weekly Thesis Briefs</title>
  <style>
    body {{ font-family: "PingFang SC", "Source Han Serif SC", Georgia, serif;
           max-width: 720px; margin: 3rem auto; padding: 0 1.25rem;
           line-height: 1.75; color: #1a1a1a; background: #faf8f5; }}
    h1 {{ font-weight: 600; letter-spacing: -0.02em; }}
    li {{ margin: 0.4rem 0; }}
    a {{ color: #8b4513; }}
    .note {{ color: #666; font-size: 0.95rem; }}
  </style>
</head>
<body>
  <h1>Weekly Thesis &amp; Chokepoint Briefs</h1>
  <p class="note">Research-only · long-horizon · no trading automation</p>
  <ul>
{items}
  </ul>
  <p class="note">Latest generated marker: {week_end}</p>
</body>
</html>
"""
    (DOCS_HTML_DIR / "index.html").write_text(index, encoding="utf-8")


def main() -> int:
    load_dotenv_local()
    parser = argparse.ArgumentParser(description="Weekly thesis brief pipeline")
    parser.add_argument("--week-end", default=None, help="Friday YYYY-MM-DD")
    parser.add_argument("--force-regen", action="store_true", help="Regenerate md even if filled")
    parser.add_argument("--no-email", action="store_true", help="Skip SMTP")
    parser.add_argument(
        "--preview-only",
        action="store_true",
        help="Alias of --no-email (HTML generate only)",
    )
    parser.add_argument(
        "--html-only",
        action="store_true",
        help="Only render HTML from existing md (no md regen)",
    )
    args = parser.parse_args()

    today = datetime.now(NY).date()
    week_end = args.week_end or friday_on_or_before(today)

    print(f"=== Weekly Thesis Brief pipeline week_end={week_end} ===")

    if args.html_only:
        md_path = WEEKLY_MD_DIR / f"{week_end}.md"
        if not md_path.exists():
            raise SystemExit(f"Missing md: {md_path}")
    else:
        md_path = ensure_markdown(week_end, force_regen=args.force_regen)

    html_path = render_html(md_path, week_end)
    update_weekly_index(week_end)

    send = not (args.no_email or args.preview_only)
    emailed = False
    if send:
        emailed = send_weekly_email(week_end, md_path, html_path)
    else:
        print("[email] skipped (--no-email / --preview-only)")

    print("---")
    print(f"MD:   {md_path}")
    print(f"HTML: {html_path}")
    print(f"Email: {'sent' if emailed else 'not sent'}")
    print(f"Open preview: open '{html_path}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
