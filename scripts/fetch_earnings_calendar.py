from __future__ import annotations

from fetch_prices import fetch_all
from utils import ROOT, write_json


def fetch_earnings_calendar() -> list[dict]:
    rows = fetch_all()
    return [
        {
            "ticker": row["ticker"],
            "group_label": row["group_label"],
            "next_earnings_date": row.get("next_earnings_date", ""),
        }
        for row in rows
        if row.get("next_earnings_date")
    ]


if __name__ == "__main__":
    earnings = fetch_earnings_calendar()
    write_json(ROOT / "reports/raw_data/earnings.json", earnings)
    print(f"Found earnings dates for {len(earnings)} tickers")
