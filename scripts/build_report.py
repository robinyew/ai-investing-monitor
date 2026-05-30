from __future__ import annotations

from collections import defaultdict

from analyze_market_moves import biggest_movers, classify_market_tone, risk_flags, theme_signals
from fetch_news import fetch_news
from fetch_prices import fetch_all
from utils import ROOT, ensure_dirs, fetch_timestamp, load_yaml, money, pct, report_base_url, today_est, write_json


BRIEF_TITLE = "AI Investing Pre-Market Brief"
DISCLAIMER = "This report is for research only. It does not contain buy/sell instructions and does not execute trades."


def _price_table(rows: list[dict], include_news: bool = False, news_counts: dict[str, int] | None = None) -> str:
    headers = ["Ticker", "Prev close", "Prev day %", "Pre-market", "Pre-market %", "5-day %", "20-day %", "Volume vs 20d", "News", "Important note"]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        note = "; ".join(row.get("flags") or []) or row.get("error") or ""
        lines.append(
            "| "
            + " | ".join(
                [
                    row["ticker"],
                    f"{row['close']:.2f}" if row.get("close") is not None else "N/A",
                    pct(row.get("daily_change_pct")),
                    f"{row['premarket_price']:.2f}" if row.get("premarket_price") is not None else "N/A",
                    pct(row.get("premarket_change_pct")),
                    pct(row.get("performance_5d")),
                    pct(row.get("performance_20d")),
                    f"{row['volume_vs_20d']:.2f}x" if row.get("volume_vs_20d") is not None else "N/A",
                    str((news_counts or {}).get(row["ticker"], 0)),
                    note,
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _mover_list(rows: list[dict], value_key: str = "daily_change_pct") -> str:
    if not rows:
        return "- None"
    return "\n".join([f"- {row['ticker']}: {pct(row.get(value_key))}" for row in rows])


def _news_section(news: list[dict]) -> str:
    if not news:
        return "No matched news items found from configured feeds."
    lines = []
    for item in news[:20]:
        tickers = ", ".join(item.get("tickers") or ["General AI / market"])
        summary = item.get("summary") or "Headline metadata only."
        lines.append(
            f"### {item['headline']}\n"
            f"- Source: {item.get('source', 'Unknown')}\n"
            f"- Link: {item.get('link', '')}\n"
            f"- Tickers: {tickers}\n"
            f"- Summary: {summary}\n"
            f"- Why it may matter: Potential signal for AI infrastructure, cloud, semiconductor, or market risk review.\n"
            f"- Confidence: {item.get('confidence', 'Medium')}"
        )
    return "\n\n".join(lines)


def _questions(flags: list[str], tone: dict) -> list[str]:
    questions = [
        "Before the open, does the previous close strengthen or weaken the AI data center infrastructure thesis?",
        "Are overnight AI software / agent headlines stronger than AI hardware infrastructure headlines?",
        "Which pre-market move, if any, needs explanation before the market opens?",
    ]
    if any("DELL" in flag for flag in flags):
        questions.append("Does DELL's previous close or pre-market action strengthen or weaken the AI server thesis?")
    if any("AAOI" in flag for flag in flags):
        questions.append("Is AAOI moving because of company-specific news or broad optical momentum?")
    if any("NVTS" in flag for flag in flags):
        questions.append("Does NVTS still deserve a small high-risk watchlist slot?")
    if tone.get("ai_infrastructure_tone") == "Weak":
        questions.append("Is weakness in AI capex names a temporary pullback or a thesis warning before the open?")
    questions.append("Are there any catalysts today that require special attention during market hours?")
    return questions[:8]


def _premarket_snapshot(prices: list[dict]) -> str:
    rows = [row for row in prices if row.get("premarket_price") is not None or row.get("premarket_change_pct") is not None]
    if not rows:
        return "- Pre-market price data was not available from the current data source at fetch time."
    lines = []
    for row in sorted(rows, key=lambda item: abs(item.get("premarket_change_pct") or 0), reverse=True)[:10]:
        price = f"{row['premarket_price']:.2f}" if row.get("premarket_price") is not None else "N/A"
        lines.append(f"- {row['ticker']}: {price}, {pct(row.get('premarket_change_pct'))}")
    return "\n".join(lines)


def _after_hours_snapshot(prices: list[dict]) -> str:
    rows = [row for row in prices if row.get("after_hours_price") is not None or row.get("after_hours_change_pct") is not None]
    if not rows:
        return "- After-hours price data was not available from the current data source at fetch time."
    lines = []
    for row in sorted(rows, key=lambda item: abs(item.get("after_hours_change_pct") or 0), reverse=True)[:10]:
        price = f"{row['after_hours_price']:.2f}" if row.get("after_hours_price") is not None else "N/A"
        lines.append(f"- {row['ticker']}: {price}, {pct(row.get('after_hours_change_pct'))}")
    return "\n".join(lines)


def build_reports() -> dict:
    ensure_dirs()
    report_date = today_est()
    prices = fetch_all()
    news = fetch_news()
    write_json(ROOT / f"reports/raw_data/{report_date}-prices.json", prices)
    write_json(ROOT / f"reports/raw_data/{report_date}-news.json", news)

    watchlists = load_yaml("config/watchlists.yaml")
    by_group = defaultdict(list)
    for row in prices:
        by_group[row["group"]].append(row)
    news_counts = defaultdict(int)
    for item in news:
        for ticker in item.get("tickers", []):
            news_counts[ticker] += 1

    tone = classify_market_tone(prices)
    movers = biggest_movers(prices)
    flags = risk_flags(prices, news)
    themes = theme_signals(prices)
    questions = _questions(flags, tone)
    base_url = report_base_url()
    report_url = f"{base_url.rstrip('/')}/{report_date}.html" if base_url else f"docs/reports/{report_date}.html"

    md = [
        f"# {BRIEF_TITLE} - {report_date}",
        "",
        f"- Report date: {report_date}",
        f"- Brief date: {report_date}",
        f"- Data fetch time: {fetch_timestamp()}",
        "- Market status: Best-effort scheduled pre-market run",
        f"- HTML report: {report_url}",
        "",
        "## Pre-Market Executive Brief",
        f"- Previous trading day market tone: {tone['overall_market_tone']}",
        f"- Previous close AI infrastructure tone: {tone['ai_infrastructure_tone']}",
        f"- Previous close AI software / agent tone: {tone['ai_software_agent_tone']}",
        f"- Previous close biggest positive signals: {', '.join(row['ticker'] for row in movers['gainers'][:3]) or 'N/A'}",
        f"- Previous close biggest negative signals: {', '.join(row['ticker'] for row in movers['decliners'][:3]) or 'N/A'}",
        f"- Needs ChatGPT review: {'Yes' if flags else 'No'}",
        "",
        "## Pre-Market Price Changes",
        _premarket_snapshot(prices),
        "",
        "## Overnight and Pre-Market News",
        _news_section(news),
        "",
        "## After-Hours Earnings and Company Announcements",
        _after_hours_snapshot(prices),
        "- Review company investor relations pages and filings for after-hours earnings releases or announcements not captured by feeds.",
        "",
        "## Analyst Upgrades / Downgrades",
        "- Not available from current free data sources. Check major financial news or brokerage research manually when needed.",
        "",
        "## Previous Trading Day Close Performance",
        "### Core Watchlist",
        _price_table(by_group["core_aggressive_ai_infrastructure"], True, news_counts),
    ]
    for group, data in watchlists.items():
        if group == "core_aggressive_ai_infrastructure":
            continue
        md.extend(["", f"## {data.get('label', group)}", _price_table(by_group[group], True, news_counts)])

    md.extend(
        [
            "",
            "## Previous Close Biggest Movers",
            "### Top 5 Gainers",
            _mover_list(movers["gainers"]),
            "",
            "### Top 5 Decliners",
            _mover_list(movers["decliners"]),
            "",
            "### Highest Unusual Volume",
            "\n".join([f"- {row['ticker']}: {row.get('volume_vs_20d'):.2f}x average volume" for row in movers["unusual_volume"] if row.get("volume_vs_20d") is not None]) or "- None",
            "",
            "## AI Theme Summary",
            "\n".join([f"- {theme}: {signal}" for theme, signal in themes.items()]),
            "",
            "## Today's Upcoming Catalysts",
            "\n".join([f"- {row['ticker']}: next earnings {row['next_earnings_date']}" for row in prices if row.get("next_earnings_date")]) or "- No earnings dates available from current data source.",
            "- Track investor events, AI conferences, product announcements, and NVIDIA / Microsoft / Amazon / Google / ServiceNow events manually when dates are known.",
            "",
            "## Risk Flags",
            "\n".join([f"- {flag}" for flag in flags]) or "- No major automated risk flags.",
            "",
            "## Questions for ChatGPT Analysis Before Market Open",
            "\n".join([f"- {question}" for question in questions]),
            "",
            "## No Trade Instruction Disclaimer",
            DISCLAIMER,
        ]
    )

    handoff = build_handoff(report_date, prices, news, themes, flags, questions)
    daily_path = ROOT / f"reports/daily/{report_date}.md"
    handoff_path = ROOT / f"reports/chatgpt_handoff/{report_date}.md"
    daily_path.write_text("\n".join(md), encoding="utf-8")
    handoff_path.write_text(handoff, encoding="utf-8")
    return {"date": report_date, "title": f"{BRIEF_TITLE} - {report_date}", "markdown": str(daily_path), "handoff": str(handoff_path)}


def build_handoff(report_date: str, prices: list[dict], news: list[dict], themes: dict, flags: list[str], questions: list[str]) -> str:
    by_ticker = {row["ticker"]: row for row in prices}
    def line(ticker: str) -> str:
        row = by_ticker.get(ticker, {})
        note = "; ".join(row.get("flags") or []) or row.get("error") or "No major automated note"
        return f"- {ticker}: {pct(row.get('daily_change_pct'))}, {note}"

    strategy = "Needs ChatGPT review" if flags else "No obvious change needed"
    if any("market cap under $1B" in flag for flag in flags):
        strategy = "Potential risk signal"

    lines = [
        f"# ChatGPT Pre-Market Handoff - {report_date}",
        "",
        "## 1. Previous Close Market Snapshot",
        line("SPY"),
        line("QQQ"),
        line("SMH"),
        line("SOXX"),
        "",
        "## 2. Core Watchlist Previous Close Moves",
        *[line(t) for t in ["DELL", "VRT", "CIEN", "COHR", "MRVL", "MPWR", "AAOI", "NVTS"]],
        "",
        "## 3. Overnight / Pre-Market News",
        *[f"- {item['headline']} ({item.get('source', 'Unknown')}) - {item.get('link', '')}" for item in news[:10]],
        "",
        "## 4. Pre-Market Price Data",
        _premarket_snapshot(prices),
        "",
        "## 5. Theme Signals",
        f"- AI server: {themes.get('AI server', 'Needs attention')}",
        f"- Power/cooling: {themes.get('Data center power / cooling', 'Needs attention')}",
        f"- Optical/CPO: {themes.get('Optical interconnect / CPO / 800G / 1.6T', 'Needs attention')}",
        f"- AI networking: {themes.get('AI networking / DSP / ASIC', 'Needs attention')}",
        f"- AI software/agent: {themes.get('AI software / agent / enterprise workflow', 'Needs attention')}",
        f"- Memory/storage: {themes.get('Memory / storage / HBM', 'Needs attention')}",
        "",
        "## 6. Possible Strategy Impact",
        f"- {strategy}",
        "- Do not provide buy/sell instructions.",
        "",
        "## 7. Questions for ChatGPT Before Market Open",
        *[f"- {question}" for question in questions],
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    result = build_reports()
    print(f"Wrote {result['markdown']}")
    print(f"Wrote {result['handoff']}")
