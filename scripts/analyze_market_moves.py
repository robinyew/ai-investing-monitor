from __future__ import annotations


def classify_market_tone(prices: list[dict]) -> dict:
    benchmarks = {row["ticker"]: row for row in prices if row["ticker"] in {"SPY", "QQQ", "SMH", "SOXX"}}
    ai_core = [row for row in prices if row.get("group") == "core_aggressive_ai_infrastructure"]
    software = [row for row in prices if row.get("group") == "second_stage_ai_software_cloud_agents"]

    def avg(rows: list[dict], key: str) -> float | None:
        values = [row.get(key) for row in rows if row.get(key) is not None]
        return sum(values) / len(values) if values else None

    def label(value: float | None) -> str:
        if value is None:
            return "Unavailable"
        if value >= 1:
            return "Strong"
        if value <= -1:
            return "Weak"
        return "Neutral"

    return {
        "overall_market_tone": label(avg(list(benchmarks.values()), "daily_change_pct")),
        "ai_infrastructure_tone": label(avg(ai_core, "daily_change_pct")),
        "ai_software_agent_tone": label(avg(software, "daily_change_pct")),
    }


def biggest_movers(prices: list[dict]) -> dict:
    valid = [row for row in prices if row.get("daily_change_pct") is not None]
    gainers = sorted(valid, key=lambda row: row["daily_change_pct"], reverse=True)[:5]
    decliners = sorted(valid, key=lambda row: row["daily_change_pct"])[:5]
    unusual_volume = sorted(
        [row for row in prices if row.get("volume_vs_20d") is not None],
        key=lambda row: row["volume_vs_20d"],
        reverse=True,
    )[:5]
    return {"gainers": gainers, "decliners": decliners, "unusual_volume": unusual_volume}


def risk_flags(prices: list[dict], news: list[dict]) -> list[str]:
    flags: list[str] = []
    news_tickers = {ticker for item in news for ticker in item.get("tickers", [])}
    for row in prices:
        ticker = row["ticker"]
        if row.get("flags"):
            flags.extend([f"{ticker}: {flag}" for flag in row["flags"]])
        if row.get("daily_change_pct") is not None and abs(row["daily_change_pct"]) > 5 and ticker not in news_tickers:
            flags.append(f"{ticker}: large move without obvious matched news")
        if ticker in {"NVTS", "AAOI"} and row.get("daily_change_pct") is not None and abs(row["daily_change_pct"]) > 5:
            flags.append(f"{ticker}: high-risk name moved more than 5%, review thesis")
        if row.get("market_cap") is not None and row["market_cap"] < 1_000_000_000:
            flags.append(f"{ticker}: market cap under $1B, treat as high-risk")
    return flags[:20]


def theme_signals(prices: list[dict]) -> dict:
    groups = {
        "AI server": ["DELL", "VRT"],
        "Data center power / cooling": ["VRT"],
        "Optical interconnect / CPO / 800G / 1.6T": ["CIEN", "COHR", "AAOI"],
        "AI networking / DSP / ASIC": ["AVGO", "ANET", "MRVL", "CSCO", "ARM"],
        "Memory / storage / HBM": ["MU", "WDC", "STX"],
        "AI software / agent / enterprise workflow": ["NOW", "ORCL", "SNOW", "PLTR", "MSFT", "GOOGL", "AMZN"],
        "AI PC / edge AI": ["QCOM", "ON", "HPQ", "TXN"],
        "Semiconductor testing / equipment bottlenecks": ["SMH", "SOXX"],
    }
    by_ticker = {row["ticker"]: row for row in prices}
    signals = {}
    for theme, tickers in groups.items():
        values = [by_ticker[t].get("daily_change_pct") for t in tickers if t in by_ticker and by_ticker[t].get("daily_change_pct") is not None]
        if not values:
            signals[theme] = "Needs attention"
        else:
            avg = sum(values) / len(values)
            signals[theme] = "Strong" if avg >= 1 else "Weak" if avg <= -1 else "Neutral"
    return signals
