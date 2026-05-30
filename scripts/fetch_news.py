from __future__ import annotations

import re
from datetime import datetime

import feedparser

from utils import ROOT, load_yaml, write_json


COMPANY_ALIASES = {
    "AAOI": ["Applied Optoelectronics"],
    "AMZN": ["Amazon"],
    "ANET": ["Arista"],
    "AVGO": ["Broadcom"],
    "CIEN": ["Ciena"],
    "COHR": ["Coherent"],
    "CSCO": ["Cisco"],
    "DELL": ["Dell"],
    "GOOGL": ["Alphabet", "Google"],
    "HPQ": ["HP Inc", "HPQ"],
    "MRVL": ["Marvell"],
    "MSFT": ["Microsoft"],
    "MU": ["Micron"],
    "NVTS": ["Navitas"],
    "NOW": ["ServiceNow"],
    "ON": ["ON Semiconductor", "Onsemi"],
    "ORCL": ["Oracle"],
    "PLTR": ["Palantir"],
    "QCOM": ["Qualcomm"],
    "SNOW": ["Snowflake"],
    "STX": ["Seagate"],
    "TXN": ["Texas Instruments"],
    "VRT": ["Vertiv"],
    "WDC": ["Western Digital"],
}


def _mentions(text: str, ticker: str) -> bool:
    base = ticker.split(".")[0]
    aliases = COMPANY_ALIASES.get(base, [])
    if f"${base}" in text:
        return True
    if re.search(rf"\b{re.escape(base)}\b", text):
        return True
    return any(alias.lower() in text.lower() for alias in aliases)


def fetch_news(limit_per_feed: int = 25) -> list[dict]:
    sources = load_yaml("config/sources.yaml")
    watchlists = load_yaml("config/watchlists.yaml")
    tickers = [str(ticker) for group in watchlists.values() for ticker in group.get("tickers", [])]
    seen: set[str] = set()
    items: list[dict] = []

    for source in sources.get("news_feeds", []):
        try:
            parsed = feedparser.parse(source["url"])
            for entry in parsed.entries[:limit_per_feed]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                if not title or title.lower() in seen:
                    continue
                seen.add(title.lower())
                text = f"{title} {entry.get('summary', '')}"
                mentioned = [ticker for ticker in tickers if _mentions(text, ticker)]
                if mentioned or any(term in text.lower() for term in ["ai", "data center", "semiconductor", "cloud", "server", "nvidia"]):
                    items.append(
                        {
                            "headline": title,
                            "source": source.get("name", "Unknown"),
                            "link": link,
                            "summary": re.sub("<[^>]+>", "", entry.get("summary", "")).strip()[:240],
                            "tickers": mentioned,
                            "category": source.get("category", ""),
                            "confidence": source.get("confidence", "Medium"),
                            "published": entry.get("published", ""),
                        }
                    )
        except Exception as exc:
            items.append(
                {
                    "headline": f"News source unavailable: {source.get('name', 'Unknown')}",
                    "source": source.get("name", "Unknown"),
                    "link": source.get("url", ""),
                    "summary": str(exc),
                    "tickers": [],
                    "category": source.get("category", ""),
                    "confidence": "Low",
                    "published": datetime.utcnow().isoformat(),
                }
            )
    return items


if __name__ == "__main__":
    news = fetch_news()
    write_json(ROOT / "reports/raw_data/news.json", news)
    print(f"Fetched {len(news)} relevant news items")
