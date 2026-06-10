"""AI Infrastructure News Scan

Fetches news via Brave Search API, analyzes with Claude, writes Markdown report
to news/YYYY-MM-DD_ai_infrastructure_news.md.

Required env vars:
  ANTHROPIC_API_KEY  — Claude API key
  BRAVE_API_KEY      — Brave Search API subscription token
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import anthropic

ROOT = Path(__file__).resolve().parents[1]
TORONTO_TZ = ZoneInfo("America/Toronto")
NEWS_MODEL = os.environ.get("NEWS_MODEL", "claude-opus-4-8")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def today_toronto() -> str:
    return datetime.now(TORONTO_TZ).date().isoformat()


# ---------------------------------------------------------------------------
# Brave Search
# ---------------------------------------------------------------------------

SEARCH_QUERIES = [
    "NVIDIA AI GPU data center demand earnings 2026",
    "Broadcom AVGO custom ASIC AI chip design wins",
    "Marvell Technology MRVL networking AI infrastructure",
    "Arista Networks ANET AI ethernet switching data center",
    "hyperscaler capex AI infrastructure Microsoft Google Amazon Meta 2026",
    "AI data center power cooling expansion buildout",
    "optical interconnect transceiver 800G 1.6T CPO AI cluster",
    "ASIC custom silicon AI inference training chip",
    "Credo CRDO SerDes optical Coherent COHR Lumentum LITE",
    "TSMC semiconductor AI chip manufacturing capacity",
    "Monolithic Power MPWR GPU power management AI server",
    "AMD AI GPU accelerator supply demand",
    "AI cluster networking buildout hyperscaler capex announcement",
    "data center supply chain bottleneck GPU memory HBM",
    "AI export control semiconductor regulatory",
]


def brave_search(query: str, count: int = 8) -> list[dict]:
    """Call Brave News Search API, return up to `count` articles from the last 24 hours."""
    api_key = env("BRAVE_API_KEY")
    if not api_key:
        return []

    params = urlencode({
        "q": query,
        "count": count,
        "freshness": "pd",  # past day
        "search_lang": "en",
        "country": "US",
        "spellcheck": "false",
    })
    url = f"https://api.search.brave.com/res/v1/news/search?{params}"
    req = Request(url, headers={
        "Accept": "application/json",
        "Accept-Encoding": "identity",
        "X-Subscription-Token": api_key,
    })
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("results", [])
    except HTTPError as exc:
        print(f"Brave Search HTTP {exc.code} for '{query}': {exc.reason}", file=sys.stderr)
        return []
    except Exception as exc:
        print(f"Brave Search error for '{query}': {exc}", file=sys.stderr)
        return []


def collect_articles() -> list[dict]:
    """Fetch and deduplicate articles across all queries."""
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    articles: list[dict] = []

    if not env("BRAVE_API_KEY"):
        print("BRAVE_API_KEY not set — no articles will be fetched.", file=sys.stderr)
        return []

    for query in SEARCH_QUERIES:
        for result in brave_search(query):
            url = (result.get("url") or "").strip()
            title = (result.get("title") or "").strip()
            title_key = title.lower()

            if not url or url in seen_urls:
                continue
            if title_key and title_key in seen_titles:
                continue

            seen_urls.add(url)
            if title_key:
                seen_titles.add(title_key)

            source = result.get("source") or {}
            source_name = source.get("name", "") if isinstance(source, dict) else str(source)

            articles.append({
                "title": title,
                "url": url,
                "source": source_name,
                "published": result.get("age") or result.get("published_at") or "",
                "description": (result.get("description") or "").strip(),
                "extra_snippets": result.get("extra_snippets") or [],
            })

    print(f"Collected {len(articles)} unique articles from Brave Search.")
    return articles


# ---------------------------------------------------------------------------
# Claude analysis
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are the AI Infrastructure News Intelligence Agent for AI Investment Monitor.

Your job: analyze recent news articles and produce a concise, high-signal infrastructure
intelligence brief. Apply rigorous importance and confidence filtering. Discard noise.

## Chokepoint Categories
- Compute / GPU
- ASIC / Custom Silicon
- Networking
- Optical Interconnect
- Memory
- Power & Cooling
- Data Center
- Server / Rack Integration
- Semiconductor Manufacturing
- Software / Cloud Platform
- Hyperscaler Capex

## Priority Signals (highest to lowest)
1. Earnings results / guidance changes
2. Hyperscaler capex announcements
3. AI cluster buildouts
4. Networking demand signals
5. Optical interconnect demand
6. ASIC / custom silicon adoption
7. GPU supply/demand
8. Memory (HBM) demand
9. Data center capacity expansion
10. Power and cooling constraints
11. Major customer wins / product launches
12. Supply chain bottlenecks
13. Regulatory / export-control changes

## De-prioritize
- Analyst price targets or upgrades/downgrades without new factual information
- Generic stock price movement
- Repeated syndicated articles
- Broad AI hype with no infrastructure-specific signal

## Importance Score
5 = ecosystem-changing signal (new capex cycle, major platform shift)
4 = major company or chokepoint impact
3 = meaningful but limited signal
2 = minor update
1 = noise
Only include items rated 3 or higher.

## Confidence Score
90–100 = confirmed by primary source (company IR, earnings, SEC filing)
75–89  = reputable outlet (Reuters, Bloomberg, CNBC, FT, WSJ, Nikkei, The Elec, DigiTimes)
60–74  = plausible but secondary/incomplete evidence
< 60   = exclude unless clearly labeled uncertain

## Primary Tickers
NVDA AVGO MRVL ANET AMD CSCO CRDO AAOI LITE COHR NOK GLW MPWR DELL JBL FN MTSI AXTI
Secondary: MSFT GOOGL AMZN META ORCL TSM ASML MU ARM SMCI HPE

## Hard Rules
- No buy/sell recommendations
- No price predictions
- No portfolio allocation advice
- Never treat stock price movement as primary evidence
- 24-hour window is hard cutoff for Key Developments; anything older goes to Background Context only
"""

REPORT_PROMPT = """\
Analyze the articles below and produce the AI Infrastructure News Scan report.

TODAY: {today}

ARTICLES:
{articles_json}

---

Output the report in this exact Markdown format. Do not deviate from the structure.

# AI Infrastructure News Scan — {today}

**Generated:** {today} 07:45 ET
**Scan window:** Last 24 hours
**Source discipline:** Primary and Tier-1 sources only; secondary sources included only when directly relevant

---

## Heatmap

| Chokepoint | Developments | Avg Importance | Avg Confidence |
|---|---|---|---|

(Fill rows for chokepoints with ≥1 item. Sort by Avg Importance desc, then Developments desc, then Avg Confidence desc. If no items qualify, write "No high-signal items in this period.")

---

## Key Developments

(For each item importance ≥ 3, one block per item:)

### [Item headline]

| Field | Value |
|---|---|
| **Source** | [Source name] |
| **Date** | [Publication date from article metadata] |
| **Link** | [URL] |
| **Tickers** | [Comma-separated tickers] |
| **Chokepoint** | [Category] |
| **Importance** | [N/5] |
| **Confidence** | [N/100] |

**Why it matters:** [1–2 sentences on investment significance.]

**First-order effect:** [Direct impact on companies, demand, or supply.]

**Second-order effect:** [Indirect impacts on suppliers, competitors, or adjacent chokepoints.]

**Bullish implication:** [Who benefits and how.]

**Bearish risk:** [What could make this signal less meaningful or flip negative.]

---

(Repeat for each qualifying item. If no items reach importance ≥ 3, write: "No high-signal items found in the last 24 hours.")

---

## Infrastructure Implication

### Most Bullish Signal
[Single strongest signal for the AI infrastructure investment thesis. One paragraph. Must cite a specific development above.]

### Neutral / Watch
[Items that need monitoring but have no clear directional signal yet. One paragraph.]

### Weakest Signal
[Items rated lower or requiring more confirmation. One paragraph.]

---

## Key Signals Today

- [Signal 1]
- [Signal 2]
- [Signal 3]
(3–5 bullets; the most important takeaways from today's scan)

---

## Watchlist — Next 3–5 Trading Days

- [Ticker or theme and why]
(3–5 bullets)

---

## Excluded Noise

- [Type of item] — [reason excluded]
(brief list of what was filtered out)

---

## Sources

(Numbered list of all URLs cited in Key Developments)
1. [Article title](URL) — Source Name, Date
(Continue for all cited items)

---

## Background Context

(Only if articles older than 24 h provided useful context. Label each with actual date. Omit section entirely if none.)
"""


def generate_report(today: str, articles: list[dict]) -> str:
    """Call Claude to analyze articles and generate the Markdown report."""
    api_key = env("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")

    client = anthropic.Anthropic(api_key=api_key)
    articles_json = json.dumps(articles, indent=2, ensure_ascii=False)

    response = client.messages.create(
        model=NEWS_MODEL,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": REPORT_PROMPT.format(today=today, articles_json=articles_json),
        }],
    )

    return response.content[0].text


def fallback_report(today: str, reason: str) -> str:
    return f"""\
# AI Infrastructure News Scan — {today}

**Generated:** {today} 07:45 ET
**Scan window:** Last 24 hours

---

## Key Developments

No high-signal items found in the last 24 hours.

_{reason}_

---

## Sources

None.
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    today = today_toronto()
    print(f"AI infrastructure news scan — {today}")

    articles = collect_articles()

    if not articles:
        report = fallback_report(today, "No articles retrieved. Check BRAVE_API_KEY.")
    else:
        try:
            report = generate_report(today, articles)
        except Exception as exc:
            print(f"Claude generation failed: {exc}", file=sys.stderr)
            report = fallback_report(today, f"Report generation error: {exc}")

    output_dir = ROOT / "news"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{today}_ai_infrastructure_news.md"
    output_path.write_text(report, encoding="utf-8")
    print(f"Report saved: {output_path.relative_to(ROOT)}")

    # Expose outputs for downstream workflow steps
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as fh:
            fh.write(f"report_date={today}\n")
            fh.write(f"report_path=news/{today}_ai_infrastructure_news.md\n")


if __name__ == "__main__":
    main()
