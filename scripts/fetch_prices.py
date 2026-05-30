from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import yfinance as yf

from utils import ROOT, load_yaml, safe_float, write_json


@dataclass
class PriceRow:
    ticker: str
    group: str
    group_label: str
    open: float | None = None
    close: float | None = None
    high: float | None = None
    low: float | None = None
    previous_close: float | None = None
    daily_change_pct: float | None = None
    volume: float | None = None
    avg_volume_20d: float | None = None
    volume_vs_20d: float | None = None
    performance_5d: float | None = None
    performance_20d: float | None = None
    week_52_high: float | None = None
    week_52_low: float | None = None
    market_cap: float | None = None
    pe_ratio: float | None = None
    premarket_price: float | None = None
    premarket_change_pct: float | None = None
    after_hours_price: float | None = None
    after_hours_change_pct: float | None = None
    next_earnings_date: str = ""
    flags: list[str] | None = None
    error: str = ""


def _perf(history, periods: int) -> float | None:
    if history is None or len(history) <= periods:
        return None
    close = safe_float(history["Close"].iloc[-1])
    old = safe_float(history["Close"].iloc[-periods - 1])
    if close is None or old in (None, 0):
        return None
    return (close / old - 1) * 100


def _next_earnings(ticker: yf.Ticker) -> str:
    try:
        dates = ticker.calendar
        if dates is None or len(dates) == 0:
            return ""
        if hasattr(dates, "index"):
            for value in dates.index:
                return str(value.date() if hasattr(value, "date") else value)
        return ""
    except Exception:
        return ""


def fetch_one(symbol: str, group: str, group_label: str) -> PriceRow:
    row = PriceRow(ticker=symbol, group=group, group_label=group_label, flags=[])
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1y", auto_adjust=False)
        if hist.empty:
            row.error = "No price history returned"
            return row

        latest = hist.iloc[-1]
        previous = hist.iloc[-2] if len(hist) > 1 else None
        row.open = safe_float(latest.get("Open"))
        row.close = safe_float(latest.get("Close"))
        row.high = safe_float(latest.get("High"))
        row.low = safe_float(latest.get("Low"))
        row.previous_close = safe_float(previous.get("Close")) if previous is not None else None
        row.volume = safe_float(latest.get("Volume"))

        if row.close is not None and row.previous_close not in (None, 0):
            row.daily_change_pct = (row.close / row.previous_close - 1) * 100

        volume_20 = hist["Volume"].tail(20)
        row.avg_volume_20d = safe_float(volume_20.mean())
        if row.volume is not None and row.avg_volume_20d not in (None, 0):
            row.volume_vs_20d = row.volume / row.avg_volume_20d

        row.performance_5d = _perf(hist, 5)
        row.performance_20d = _perf(hist, 20)
        row.week_52_high = safe_float(hist["High"].max())
        row.week_52_low = safe_float(hist["Low"].min())

        high_20 = safe_float(hist["High"].tail(20).max())
        low_20 = safe_float(hist["Low"].tail(20).min())
        if row.daily_change_pct is not None and abs(row.daily_change_pct) > 5:
            row.flags.append("Daily move > 5%")
        if row.volume_vs_20d is not None and row.volume_vs_20d > 2:
            row.flags.append("Volume > 2x 20-day average")
        if row.high is not None and high_20 is not None and row.high >= high_20:
            row.flags.append("New 20-day high")
        if row.low is not None and low_20 is not None and row.low <= low_20:
            row.flags.append("New 20-day low")

        info: dict[str, Any] = {}
        try:
            info = ticker.get_info()
        except Exception:
            info = {}
        row.market_cap = safe_float(info.get("marketCap"))
        row.pe_ratio = safe_float(info.get("forwardPE") or info.get("trailingPE"))
        row.premarket_price = safe_float(info.get("preMarketPrice"))
        row.premarket_change_pct = safe_float(info.get("preMarketChangePercent"))
        row.after_hours_price = safe_float(info.get("postMarketPrice"))
        row.after_hours_change_pct = safe_float(info.get("postMarketChangePercent"))
        row.next_earnings_date = _next_earnings(ticker)
    except Exception as exc:
        row.error = str(exc)
    return row


def fetch_all() -> list[dict]:
    watchlists = load_yaml("config/watchlists.yaml")
    rows: list[dict] = []
    for group, data in watchlists.items():
        for symbol in data.get("tickers", []):
            rows.append(asdict(fetch_one(str(symbol), group, data.get("label", group))))
    return rows


if __name__ == "__main__":
    prices = fetch_all()
    write_json(ROOT / "reports/raw_data/prices.json", prices)
    print(f"Fetched price data for {len(prices)} watchlist items")
