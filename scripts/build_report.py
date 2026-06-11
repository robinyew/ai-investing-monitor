from __future__ import annotations

import re
from collections import defaultdict

from analyze_market_moves import biggest_movers
from fetch_news import fetch_news
from fetch_prices import fetch_all
from utils import ROOT, ensure_dirs, fetch_timestamp, load_yaml, pct, report_base_url, today_est, write_json


REPORT_TITLE = "AI Pre-Market Brief"
DISCLAIMER = "本报告仅用于研究和信息整理，不提供具体交易动作或价格预测，也不执行任何交易。"
CORE_GROUP = "core_holdings_planned"
OBSERVATION_GROUP = "key_observation"
HIGH_RISK_GROUP = "high_risk_concepts"
THEME_ORDER = ["光互连 / 网络", "电力 / 液冷", "AI server", "Memory / HBM", "云平台 capex"]
CHOKEPOINTS = {
    "Compute / GPU": {
        "themes": ["AI server", "云平台 capex"],
        "tickers": ["NVDA", "AMD", "AVGO", "MRVL", "MSFT", "GOOGL", "AMZN", "META"],
        "keywords": ["gpu", "accelerator", "compute", "training", "inference", "cuda", "tpu", "trainium"],
    },
    "ASIC / Custom Silicon": {
        "themes": ["光互连 / 网络", "云平台 capex"],
        "tickers": ["AVGO", "MRVL", "ARM", "MSFT", "GOOGL", "AMZN", "META"],
        "keywords": ["asic", "custom silicon", "custom chip", "tpu", "trainium", "inferentia", "xpu"],
    },
    "Networking": {
        "themes": ["光互连 / 网络"],
        "tickers": ["ANET", "AVGO", "MRVL", "CSCO", "NOK"],
        "keywords": ["ethernet", "networking", "switch", "routing", "back-end network"],
    },
    "Optical Interconnect": {
        "themes": ["光互连 / 网络"],
        "tickers": ["AAOI", "COHR", "CIEN", "LITE", "NOK", "CRDO", "ALAB", "MRVL", "AVGO"],
        "keywords": ["optical", "transceiver", "800g", "1.6t", "cpo", "lpo", "serdes", "silicon photonics", "inp"],
    },
    "Power / Cooling": {
        "themes": ["电力 / 液冷"],
        "tickers": ["VRT", "ETN", "GEV", "PWR", "FIX", "MPWR", "NVTS"],
        "keywords": ["data center power", "power infrastructure", "power bottleneck", "cooling", "liquid cooling", "ups", "pdu", "switchgear", "transformer", "grid"],
    },
    "Power / Electrical Equipment": {
        "themes": ["电力 / 液冷"],
        "tickers": ["VRT", "ETN", "GEV", "PWR", "FIX", "MPWR", "NVTS"],
        "keywords": ["data center power", "power infrastructure", "power bottleneck", "electrical", "800v", "hvdc", "ups", "pdu", "switchgear", "transformer", "grid"],
    },
    "Cooling / Thermal": {
        "themes": ["电力 / 液冷", "AI server"],
        "tickers": ["VRT", "ETN", "SMCI", "DELL", "HPE"],
        "keywords": ["cooling", "liquid cooling", "thermal", "thermal management", "liquid-cooled rack"],
    },
    "Memory / HBM": {
        "themes": ["Memory / HBM"],
        "tickers": ["MU", "TSM", "ASML", "AMAT", "LRCX", "KLAC"],
        "keywords": ["hbm", "dram", "nand", "memory", "cowos", "advanced packaging"],
    },
    "Server / ODM": {
        "themes": ["AI server"],
        "tickers": ["DELL", "SMCI", "HPE", "CLS", "JBL", "FLEX"],
        "keywords": ["server", "rack", "gb200", "gb300", "nvl72", "odm", "ems"],
    },
    "Cloud / AI Platform": {
        "themes": ["云平台 capex"],
        "tickers": ["MSFT", "GOOGL", "AMZN", "META", "ORCL", "NBIS"],
        "keywords": ["cloud", "capex", "azure", "google cloud", "aws", "trainium", "tpu", "oracle cloud"],
    },
    "Enterprise AI Software": {
        "themes": ["云平台 capex"],
        "tickers": ["MSFT", "GOOGL", "ORCL", "NOW", "PLTR", "SNOW"],
        "keywords": ["enterprise ai", "agent", "workflow", "copilot", "ai software", "coding model"],
    },
}
DASHBOARD_CHOKEPOINT_ORDER = [
    "Compute / GPU",
    "ASIC / Custom Silicon",
    "Networking",
    "Optical Interconnect",
    "Power / Electrical Equipment",
    "Cooling / Thermal",
    "Memory / HBM",
    "Server / ODM",
    "Cloud / AI Platform",
    "Enterprise AI Software",
]
STOCK_CONFIDENCE_TICKERS = [
    "NVDA",
    "AVGO",
    "ANET",
    "ETN",
    "VRT",
    "MSFT",
    "GOOGL",
    "AMZN",
    "MRVL",
    "MPWR",
    "CIEN",
    "COHR",
    "DELL",
    "MU",
    "AAOI",
    "NVTS",
    "NBIS",
    "SMCI",
    "ARM",
]
HIGH_BETA_TICKERS = {"AAOI", "NVTS", "NBIS", "SMCI"}
LARGE_CORE_TICKERS = {"NVDA", "AVGO", "ANET", "ETN", "VRT", "MSFT", "GOOGL", "AMZN"}
FIXED_TICKER_THEME = {
    "DELL": "Server / Rack Integration",
    "VRT": "Power / Electrical Equipment",
    "CIEN": "Optical Interconnect",
    "COHR": "Optical Interconnect",
    "MRVL": "ASIC / Custom Silicon",
    "MPWR": "Power / Electrical Equipment",
    "AAOI": "Optical Interconnect",
    "NVTS": "Power / Electrical Equipment",
    "MU": "Memory / HBM",
    "AVGO": "ASIC / Custom Silicon",
    "ANET": "Networking",
    "ETN": "Power / Electrical Equipment",
    "MSFT": "Cloud / AI Platform",
    "GOOGL": "Cloud / AI Platform",
    "NVDA": "Compute / GPU",
    "AMZN": "Cloud / AI Platform",
    "NBIS": "Cloud / AI Platform",
    "SMCI": "Server / Rack Integration",
    "ARM": "ASIC / Custom Silicon",
}
SCOREBOARD_TICKERS = [
    "DELL",
    "VRT",
    "CIEN",
    "COHR",
    "MRVL",
    "MPWR",
    "AAOI",
    "NVTS",
    "MU",
    "AVGO",
    "ANET",
    "ETN",
    "MSFT",
    "GOOGL",
]
EVIDENCE_DASHBOARD_TICKERS = [
    "NVDA",
    "AVGO",
    "MRVL",
    "ANET",
    "MU",
    "DELL",
    "VRT",
    "ETN",
    "MPWR",
    "CIEN",
    "COHR",
    "AAOI",
    "MSFT",
    "GOOGL",
    "AMZN",
]
HYPERSCALERS = {
    "Microsoft": "MSFT",
    "Google": "GOOGL",
    "Amazon": "AMZN",
    "Meta": "META",
}
THESIS_CONFIG = {
    "AI Data Center Expansion": {
        "tickers": ["NVDA", "AVGO", "MRVL", "ANET", "DELL", "ETN", "VRT"],
        "keywords": ["ai data center", "data center expansion", "hyperscaler capex", "gpu procurement", "rack-scale", "nvl72", "gb200", "gb300"],
    },
    "Optical Interconnect": {
        "tickers": ["AAOI", "CIEN", "COHR"],
        "keywords": ["optical", "interconnect", "800g", "1.6t", "transceiver", "coherent", "silicon photonics"],
    },
    "Memory / HBM": {
        "tickers": ["MU"],
        "keywords": ["hbm", "dram", "memory", "nand", "pricing"],
    },
    "Power & Cooling": {
        "tickers": ["ETN", "VRT", "MPWR", "NVTS"],
        "keywords": ["data center power", "power infrastructure", "power bottleneck", "cooling", "thermal", "ups", "switchgear", "liquid cooling"],
    },
    "Cloud / AI Platform": {
        "tickers": ["MSFT", "GOOGL", "AMZN"],
        "keywords": ["cloud", "azure", "google cloud", "aws", "agent", "platform", "model", "ai infrastructure"],
    },
}
HYPERSCALER_CHOKEPOINT_MAP = [
    ("Compute", ["gpu", "accelerator", "trainium", "tpu", "inference", "training"]),
    ("Networking", ["networking", "ethernet", "switch", "interconnect"]),
    ("Optical", ["optical", "transceiver", "coherent", "silicon photonics"]),
    ("Power", ["data center power", "power infrastructure", "power bottleneck", "grid", "switchgear", "ups", "pdu"]),
    ("Cooling", ["cooling", "thermal", "liquid cooling"]),
    ("Memory", ["hbm", "dram", "memory", "storage"]),
]
THESIS_FIT_BASE = {
    "AVGO": 92,
    "ANET": 90,
    "VRT": 88,
    "ETN": 87,
    "MRVL": 84,
    "MPWR": 82,
    "MSFT": 82,
    "GOOGL": 80,
    "DELL": 78,
    "MU": 76,
    "COHR": 74,
    "CIEN": 72,
    "AAOI": 66,
    "NVTS": 60,
}
CHOKEPOINT_BASE = {
    "AVGO": 92,
    "ANET": 88,
    "VRT": 87,
    "ETN": 86,
    "MRVL": 82,
    "MPWR": 80,
    "MU": 78,
    "MSFT": 76,
    "GOOGL": 74,
    "DELL": 72,
    "COHR": 70,
    "CIEN": 68,
    "AAOI": 62,
    "NVTS": 58,
}
NEGATIVE_CATALYST_TERMS = [
    "dives",
    "dive",
    "sinks",
    "sink",
    "disappoints",
    "disappoint",
    "tumbling",
    "tumbles",
    "misses",
    "miss",
    "cut",
    "cuts",
    "delay",
    "delays",
    "weak guidance",
    "weak outlook",
    "plunges",
    "plunge",
    "lower guidance",
    "guidance cut",
    "earnings flop",
]
POSITIVE_CATALYST_TERMS = [
    "beats",
    "beat",
    "raises",
    "raise",
    "strong demand",
    "order",
    "orders",
    "contract",
    "capacity expansion",
    "record revenue",
    "guidance raised",
]
PRIMARY_SOURCE_TYPES = {
    "Investor Relations press release",
    "SEC filing",
    "Earnings release",
    "Earnings call transcript",
    "Investor presentation",
    "Official company blog / product announcement",
    "Official customer case study",
    "Official partnership / launch / guidance / capex update",
}
PUBLIC_SOURCE_TYPES = {
    "主流财经新闻",
    "分析师报告",
    "X 推文",
    "博客 / 二级来源",
}
EVIDENCE_TYPE_ORDER = [
    "Earnings",
    "Guidance",
    "Customer Win",
    "Capacity Expansion",
    "CapEx Increase",
    "Product Launch",
    "Partnership",
    "Supply Chain",
    "Media Only",
]
HIGH_VALUE_EVIDENCE_TYPES = {"Earnings", "Guidance", "Customer Win", "Capacity Expansion", "CapEx Increase", "Supply Chain"}
MEDIUM_VALUE_EVIDENCE_TYPES = {"Product Launch", "Partnership"}
LOW_VALUE_EVIDENCE_TYPES = {"Media Only"}
EVIDENCE_QUESTION_FIELDS = [
    ("is_evidence", "这是新闻还是证据？"),
    ("has_order", "是否涉及订单？"),
    ("has_customer", "是否涉及客户？"),
    ("has_capacity", "是否涉及产能？"),
    ("has_capex", "是否涉及 CapEx？"),
    ("has_supply_chain", "是否涉及供应链？"),
    ("changes_thesis", "是否会改变 AI Infrastructure Thesis？"),
]
BRIEF_CHOKEPOINT_LABELS = {
    "Compute / GPU": "ASIC / Custom Silicon",
    "ASIC / Custom Silicon": "ASIC / Custom Silicon",
    "Networking": "AI Networking",
    "Optical Interconnect": "Optical Interconnect",
    "Power / Electrical Equipment": "Grid / Electrical Equipment",
    "Cooling / Thermal": "Power / Cooling",
    "Power / Cooling": "Power / Cooling",
    "Memory / HBM": "Memory / HBM",
    "Server / ODM": "AI Server",
    "Cloud / AI Platform": "Data Center Construction",
}
FUNDAMENTAL_CHANGE_TYPES = {"CapEx", "Earnings / Guidance", "Backlog / Margin", "Supply Chain"}


def _is_primary_source_item(item: dict | None) -> bool:
    return bool(item and item.get("source_type") in PRIMARY_SOURCE_TYPES)


def _source_priority(item: dict) -> tuple[int, int, int, str]:
    confidence_rank = {"High": 0, "Medium": 1, "Low": 2}.get(item.get("confidence"), 3)
    attention_rank = 0 if item.get("needs_attention") else 1
    public_rank = 0 if _is_primary_source_item(item) else 1
    return (public_rank, confidence_rank, attention_rank, item.get("headline", ""))


def _items_for_ticker(news: list[dict], ticker: str) -> list[dict]:
    return sorted([item for item in news if ticker in item.get("tickers", [])], key=_source_priority)


def _primary_item(items: list[dict]) -> dict | None:
    return items[0] if items else None


def _authoritative_items(items: list[dict]) -> list[dict]:
    primary = [item for item in items if _is_primary_source_item(item)]
    return primary or items


def _item_text(item: dict | None) -> str:
    if not item:
        return ""
    return f"{item.get('headline', '')} {item.get('summary', '')}".lower()


def _evidence_type(item: dict | None) -> str:
    if not item:
        return "Media Only"
    text = _item_text(item)
    source_type = item.get("source_type", "")
    if source_type in {"Earnings release", "Earnings call transcript"} or "earnings" in text or "quarterly results" in text:
        return "Earnings"
    if any(
        term in text
        for term in [
            "guidance raise",
            "guidance raised",
            "raises guidance",
            "guidance cut",
            "cuts guidance",
            "revenue guidance",
            "financial guidance",
            "raises outlook",
            "cuts outlook",
            "lower outlook",
            "weak outlook",
        ]
    ):
        return "Guidance"
    if any(term in text for term in ["customer win", "new customer", "hyperscaler customer", "customer announcement", "case study"]):
        return "Customer Win"
    if any(term in text for term in ["capacity expansion", "expands capacity", "new fab", "new plant", "manufacturing expansion"]):
        return "Capacity Expansion"
    if any(term in text for term in ["capex increase", "capital expenditure", "ai capex", "data center expansion", "infrastructure investment"]):
        return "CapEx Increase"
    if source_type in {"Official partnership / launch / guidance / capex update", "Official company blog / product announcement"} and any(
        term in text for term in ["launch", "announcing", "general availability", "now available", "preview", "introduced"]
    ):
        return "Product Launch"
    if "partnership" in text or "partner" in text:
        return "Partnership"
    if any(
        term in text
        for term in [
            "supply chain delay",
            "supply chain risk",
            "supply constraint",
            "supply constraints",
            "component shortage",
            "shipment delay",
            "supplier bottleneck",
            "backlog growth",
        ]
    ):
        return "Supply Chain"
    return "Media Only"


def _evidence_value_tier(item: dict | None) -> str:
    if not item:
        return "Low Value Evidence"
    evidence_type = _evidence_type(item)
    if evidence_type in HIGH_VALUE_EVIDENCE_TYPES and _is_primary_source_item(item):
        return "High Value Evidence"
    if evidence_type in MEDIUM_VALUE_EVIDENCE_TYPES and _is_primary_source_item(item):
        return "Medium Value Evidence"
    if _is_primary_source_item(item):
        return "Low Value Evidence"
    return "Media Only"


def _evidence_strength_for_item(item: dict | None) -> str:
    if not item:
        return "Low"
    tier = _evidence_value_tier(item)
    if tier == "High Value Evidence":
        return "High"
    if tier == "Medium Value Evidence":
        return "Medium"
    if item.get("confidence") == "High" and _is_primary_source_item(item):
        return "Medium"
    return "Low"


def _evidence_score_for_item(item: dict | None) -> int:
    if not item:
        return 10
    base = {
        "High Value Evidence": 85,
        "Medium Value Evidence": 65,
        "Low Value Evidence": 42,
        "Media Only": 25,
    }.get(_evidence_value_tier(item), 25)
    if item.get("body_status") == "Headline-only":
        base -= 12
    if item.get("ticker_mapping_confidence") == "Low":
        base -= 8
    if item.get("confidence") == "High":
        base += 5
    if _is_negative_catalyst(item):
        base += 8
    return max(0, min(100, base))


def _evidence_sort_key(item: dict) -> tuple[int, int, int, str]:
    tier_rank = {
        "High Value Evidence": 0,
        "Medium Value Evidence": 1,
        "Low Value Evidence": 2,
        "Media Only": 3,
    }.get(_evidence_value_tier(item), 4)
    type_rank = EVIDENCE_TYPE_ORDER.index(_evidence_type(item)) if _evidence_type(item) in EVIDENCE_TYPE_ORDER else len(EVIDENCE_TYPE_ORDER)
    return (tier_rank, type_rank, -_evidence_score_for_item(item), item.get("headline", ""))


def _evidence_flags(item: dict | None) -> dict:
    text = _item_text(item)
    evidence_type = _evidence_type(item)
    is_evidence = "Evidence" if item and _is_primary_source_item(item) else "News signal"
    return {
        "is_evidence": is_evidence,
        "has_order": "Yes" if any(term in text for term in ["order", "booking", "backlog", "contract"]) else "No",
        "has_customer": "Yes" if any(term in text for term in ["customer", "case study", "hyperscaler", "deployed"]) else "No",
        "has_capacity": "Yes" if any(term in text for term in ["capacity", "expansion", "fab", "manufacturing", "production"]) else "No",
        "has_capex": "Yes" if any(term in text for term in ["capex", "capital expenditure", "data center expansion", "infrastructure investment"]) else "No",
        "has_supply_chain": "Yes" if any(term in text for term in ["supply chain", "supplier", "shipment", "shortage", "constraint"]) else "No",
        "changes_thesis": "Yes" if evidence_type in HIGH_VALUE_EVIDENCE_TYPES or _is_negative_catalyst(item) else "Watch",
    }


def _is_strong_evidence(item: dict | None) -> bool:
    if not item or not _is_primary_source_item(item):
        return False
    return _evidence_type(item) in HIGH_VALUE_EVIDENCE_TYPES


def _is_narrative_only(item: dict | None) -> bool:
    if not item:
        return False
    if item.get("source_type") in {"X 推文", "博客 / 二级来源"}:
        return True
    if not _is_primary_source_item(item):
        return True
    if _evidence_value_tier(item) == "Low Value Evidence":
        return True
    if item.get("body_status") == "Headline-only":
        return True
    return False


def _chokepoint_evidence_strength(items: list[dict]) -> str:
    meaningful_primary_count = sum(
        1
        for item in items
        if _is_primary_source_item(item)
        and item.get("body_status") != "Headline-only"
        and _evidence_value_tier(item) in {"High Value Evidence", "Medium Value Evidence"}
    )
    primary_earnings_count = sum(
        1
        for item in items
        if _is_primary_source_item(item) and _evidence_type(item) in {"Earnings", "Guidance"}
    )
    if meaningful_primary_count >= 2 or primary_earnings_count >= 1:
        return "High"
    if any(
        _is_primary_source_item(item)
        and item.get("body_status") != "Headline-only"
        and _evidence_value_tier(item) in {"High Value Evidence", "Medium Value Evidence"}
        for item in items
    ):
        return "Medium"
    return "Low"


def _thesis_items(news: list[dict], thesis: dict) -> list[dict]:
    tickers = set(thesis["tickers"])
    keywords = [keyword.lower() for keyword in thesis["keywords"]]
    items = []
    for item in news:
        text = _item_text(item)
        if set(item.get("tickers", [])) & tickers or any(keyword in text for keyword in keywords):
            items.append(item)
    return sorted(items, key=_evidence_sort_key)


def _thesis_status(items: list[dict]) -> str:
    strong_negative = [item for item in items if _is_negative_catalyst(item) and _evidence_score_for_item(item) >= 55]
    strong_positive = [item for item in items if _evidence_score_for_item(item) >= 55 and not _is_negative_catalyst(item)]
    if strong_negative:
        return "Weakened"
    if strong_positive:
        return "Reinforced"
    return "Neutral"


def _thesis_confidence(items: list[dict], status: str) -> str:
    if status == "Neutral":
        return "Low"
    if any(_is_strong_evidence(item) for item in items):
        return "High"
    if any(_evidence_score_for_item(item) >= 55 for item in items):
        return "Medium"
    return "Low"


def _thesis_tracker_rows(news: list[dict]) -> list[dict]:
    rows = []
    for name, config in THESIS_CONFIG.items():
        items = _thesis_items(news, config)
        status = _thesis_status(items)
        confidence = _thesis_confidence(items, status)
        evidence_items = [item for item in items if _evidence_score_for_item(item) >= 55]
        if not evidence_items:
            evidence_items = [item for item in items if not _is_narrative_only(item)][:1]
        evidence = "; ".join(_short_text(item.get("headline", ""), 100) for item in evidence_items[:3]) or "No material evidence found today."
        if status == "Reinforced":
            reason = "Evidence supports continued thesis validation, but does not imply any trade action."
        elif status == "Weakened":
            reason = "Negative evidence needs review before treating the thesis as intact."
        else:
            reason = "No material change in thesis today."
        rows.append(
            {
                "thesis": name,
                "status": status,
                "evidence": evidence,
                "confidence": confidence,
                "reason": reason,
                "items": items,
            }
        )
    return rows


def _render_what_changed_today(thesis_rows: list[dict]) -> str:
    grouped = {
        "Strengthened": [row for row in thesis_rows if row["status"] == "Reinforced"],
        "Weakened": [row for row in thesis_rows if row["status"] == "Weakened"],
        "Unchanged": [row for row in thesis_rows if row["status"] == "Neutral"],
    }
    lines = ["# What Changed Today?", "", "## Strengthened"]
    if grouped["Strengthened"]:
        lines.extend([f"- {row['thesis']}: {row['reason']} Evidence: {row['evidence']}" for row in grouped["Strengthened"]])
    else:
        lines.append("- No material change in thesis today.")
    lines.extend(["", "## Weakened"])
    if grouped["Weakened"]:
        lines.extend([f"- {row['thesis']}: {row['reason']} Evidence: {row['evidence']}" for row in grouped["Weakened"]])
    else:
        lines.append("- No material change in thesis today.")
    lines.extend(["", "## Unchanged"])
    if grouped["Unchanged"]:
        lines.extend([f"- {row['thesis']}: {row['reason']}" for row in grouped["Unchanged"]])
    else:
        lines.append("- No material change in thesis today.")
    return "\n".join(lines)


def _render_thesis_tracker(thesis_rows: list[dict]) -> str:
    lines = [
        "# Thesis Reinforcement Tracker",
        "",
        "| Thesis | Related Stocks | Status | Evidence | Confidence | Reason |",
        "|---|---|---|---|---|---|",
    ]
    for row in thesis_rows:
        stocks = ", ".join(THESIS_CONFIG[row["thesis"]]["tickers"])
        lines.append(
            f"| {_escape_table(row['thesis'])} | {_escape_table(stocks)} | {row['status']} | "
            f"{_escape_table(row['evidence'])} | {row['confidence']} | {_escape_table(row['reason'])} |"
        )
    return "\n".join(lines)


def _render_evidence_vs_narrative(news: list[dict], limit: int = 8) -> str:
    strong = sorted([item for item in news if _is_strong_evidence(item)], key=_evidence_sort_key)[:limit]
    narrative = sorted([item for item in news if _is_narrative_only(item)], key=_evidence_sort_key)[:limit]
    lines = ["# Evidence vs Narrative", "", "## Strong Evidence"]
    if strong:
        lines.extend(
            [
                f"- {item.get('ticker', 'General')}: {_evidence_type(item)} / {item.get('headline', '')} ({item.get('source_type')})"
                for item in strong
            ]
        )
    else:
        lines.append("- No strong evidence found today.")
    lines.extend(["", "## Narrative Only"])
    if narrative:
        lines.extend(
            [
                f"- {item.get('ticker', 'General')}: {_evidence_type(item)} / {item.get('headline', '')} ({item.get('source_type')})"
                for item in narrative
            ]
        )
    else:
        lines.append("- No narrative-only items found today.")
    return "\n".join(lines)


def _news_line(item: dict | None) -> str:
    if not item:
        return "未发现重大相关新闻"
    return item.get("headline", "未发现重大相关新闻")


def _source_line(item: dict | None) -> str:
    if not item:
        return "N/A"
    return f"{item.get('source', 'Unknown')}（{item.get('source_type', '博客 / 二级来源')}）"


def _attention_label(item: dict | None, row: dict | None = None) -> str:
    if item and item.get("strategy_impact") in {"需要关注", "风险上升", "与当前主题相关", "高风险概念观察"}:
        return "是"
    if row and row.get("flags"):
        return "是"
    return "否"


def _direction(item: dict | None, row: dict | None = None) -> str:
    if item:
        return item.get("direction", "中性")
    if row and row.get("daily_change_pct") is not None:
        if row["daily_change_pct"] >= 5:
            return "正面"
        if row["daily_change_pct"] <= -5:
            return "负面"
    return "中性"


def _core_section(prices: list[dict], news: list[dict], watchlists: dict) -> str:
    by_ticker = {row["ticker"]: row for row in prices}
    lines = []
    for ticker in watchlists.get(CORE_GROUP, {}).get("tickers", []):
        row = by_ticker.get(ticker, {})
        item = _primary_item(_items_for_ticker(news, ticker))
        price_note = ""
        if row:
            price_note = f"；前一交易日涨跌 {pct(row.get('daily_change_pct'))}"
            if row.get("flags"):
                price_note += f"；价格/成交量提示：{'; '.join(row.get('flags') or [])}"
        lines.extend(
            [
                f"### {ticker}",
                f"- 今日新闻: {_news_line(item)}{price_note}",
                f"- 来源: {_source_line(item)}",
                f"- 来源类型: {item.get('source_type', 'N/A') if item else 'N/A'}",
                f"- 影响方向: {_direction(item, row)}",
                f"- 是否需要关注: {_attention_label(item, row)}",
            ]
        )
        if item:
            lines.extend(
                [
                    f"- 摘要: {item.get('summary', 'Summary based on headline/metadata only.')}",
                    f"- 为什么重要: {item.get('why_it_matters', '')}",
                    f"- 相关主题: {item.get('related_ai_theme', 'general market')}",
                ]
            )
        lines.append("")
    return "\n".join(lines).strip()


def _theme_section(news: list[dict], themes: dict) -> str:
    grouped = defaultdict(list)
    for item in news:
        grouped[item.get("related_ai_theme", "general market")].append(item)

    lines = []
    for theme in THEME_ORDER:
        lines.append(f"### {theme}")
        items = grouped.get(theme, [])[:5]
        if not items:
            related = ", ".join(themes.get(theme, {}).get("related_tickers", []))
            lines.append(f"- 未发现重大新闻；相关标的：{related or 'N/A'}")
        else:
            for item in items:
                lines.append(
                    f"- {item.get('ticker', 'General')}: {item.get('headline', '')} "
                    f"[{item.get('source_type', '来源未知')}, {item.get('confidence', 'Low')}, {item.get('direction', '中性')}]"
                )
                lines.append(f"  - 影响: {item.get('why_it_matters', '')}")
                lines.append(f"  - URL: {item.get('url') or item.get('link', '')}")
        lines.append("")
    return "\n".join(lines).strip()


def _risk_section(news: list[dict], prices: list[dict]) -> str:
    risk_terms = {
        "insider selling": "insider selling",
        "融资/稀释": "offering|dilution|financing",
        "指引下调": "guidance cut|lower guidance|cuts outlook|weak outlook",
        "客户集中风险": "customer concentration|large customer|hyperscaler customer",
        "估值过热": "valuation|multiple|overvalued",
        "供应链延迟": "supply chain delay|supply chain risk|supply chain disruption|delay|shortage",
    }
    lines = []
    text_items = [(item, f"{item.get('headline', '')} {item.get('summary', '')}".lower()) for item in news]
    for label, pattern in risk_terms.items():
        matched = [item for item, text in text_items if re.search(pattern, text)]
        if matched:
            for item in matched[:3]:
                lines.append(f"- {label}: {item.get('ticker', 'General')} - {item.get('headline', '')} ({item.get('source_type', 'N/A')})")
        else:
            lines.append(f"- {label}: 未发现重大信号")

    unusual = [row for row in prices if row.get("flags")]
    if unusual:
        lines.append("- 异常涨跌/成交量:")
        for row in unusual[:8]:
            lines.append(f"  - {row['ticker']}: {'; '.join(row.get('flags') or [])}")
    return "\n".join(lines)


def _chokepoint_items(news: list[dict], config: dict) -> list[dict]:
    tickers = set(config["tickers"])
    themes = set(config["themes"])
    keywords = [keyword.lower() for keyword in config["keywords"]]
    items = []
    for item in news:
        text = f"{item.get('headline', '')} {item.get('summary', '')}".lower()
        if set(item.get("tickers", [])) & tickers:
            items.append(item)
        elif item.get("related_ai_theme") in themes:
            items.append(item)
        elif any(keyword in text for keyword in keywords):
            items.append(item)
    return items


def _chokepoint_strength(items: list[dict], prices: list[dict], tickers: list[str]) -> str:
    if any(item.get("strategy_impact") == "风险上升" or item.get("direction") == "负面" for item in items):
        return "减弱"
    price_rows = [row for row in prices if row.get("ticker") in tickers]
    if any((row.get("daily_change_pct") or 0) >= 5 for row in price_rows):
        return "增强"
    if any(item.get("direction") == "正面" or item.get("strategy_impact") in {"需要关注", "与当前主题相关"} for item in items):
        return "增强"
    return "不变"


def _escape_table(value: object) -> str:
    text = str(value) if value is not None else ""
    return text.replace("|", "/").replace("\n", " ").strip()


def _clamp_score(value: float, low: float = 1.0, high: float = 10.0) -> float:
    return max(low, min(high, value))


def _price_row(prices: list[dict], ticker: str) -> dict:
    return next((row for row in prices if row.get("ticker") == ticker), {})


def _trend_from_strength(strength: str) -> str:
    if strength == "增强":
        return "↑"
    if strength == "减弱":
        return "↓"
    return "→"


def _strength_score(items: list[dict], prices: list[dict], tickers: list[str]) -> float:
    score = 5.0
    high_conf = sum(1 for item in items if item.get("confidence") == "High")
    medium_conf = sum(1 for item in items if item.get("confidence") == "Medium")
    positive = sum(1 for item in items if item.get("direction") == "正面")
    negative = sum(1 for item in items if item.get("direction") == "负面" or item.get("strategy_impact") == "风险上升")
    price_rows = [row for row in prices if row.get("ticker") in tickers]
    strong_moves = sum(1 for row in price_rows if (row.get("daily_change_pct") or 0) >= 5)
    weak_moves = sum(1 for row in price_rows if (row.get("daily_change_pct") or 0) <= -5)
    score += min(2.5, high_conf * 0.9 + medium_conf * 0.35 + positive * 0.45 + strong_moves * 0.35)
    score -= min(2.5, negative * 0.8 + weak_moves * 0.35)
    if not items and not any(row.get("flags") for row in price_rows):
        score = 5.0
    return _clamp_score(score)


def _key_evidence(items: list[dict], prices: list[dict], tickers: list[str]) -> str:
    if items:
        item = items[0]
        return f"{item.get('ticker', 'General')}: {item.get('headline', '今日无明确证据')}"
    price_rows = [row for row in prices if row.get("ticker") in tickers and row.get("flags")]
    if price_rows:
        row = price_rows[0]
        return f"{row.get('ticker')}: {'; '.join(row.get('flags') or [])}"
    return "今日未发现足以改变判断的新证据。"


def _chokepoint_ranking_rows(news: list[dict], prices: list[dict]) -> list[dict]:
    rows = []
    for name in DASHBOARD_CHOKEPOINT_ORDER:
        config = CHOKEPOINTS[name]
        items = _chokepoint_items(news, config)
        dynamic = _strength_score(items, prices, config["tickers"])
        base_importance = max([CHOKEPOINT_BASE.get(ticker, 50) for ticker in config["tickers"]] or [50]) / 10
        importance = _clamp_score((base_importance * 0.75) + (dynamic * 0.25))
        negative_items = sum(1 for item in items if _is_negative_catalyst(item))
        positive_items = sum(1 for item in items if _is_positive_catalyst(item))
        sentiment_score = 5.0 + min(2.0, positive_items * 0.8) - min(2.5, negative_items * 1.0)
        price_rows = [row for row in prices if row.get("ticker") in config["tickers"]]
        if any((row.get("daily_change_pct") or 0) <= -7 for row in price_rows):
            sentiment_score -= 1.0
        if any((row.get("daily_change_pct") or 0) >= 7 for row in price_rows):
            sentiment_score += 0.6
        sentiment_score = _clamp_score(sentiment_score)
        if sentiment_score >= 5.8:
            sentiment = "Positive"
            trend = "↑"
        elif sentiment_score <= 4.2:
            sentiment = "Negative"
            trend = "↓"
        else:
            sentiment = "Neutral"
            trend = "→"
        rows.append(
            {
                "chokepoint": name,
                "score": importance,
                "importance": round(importance * 10),
                "evidence_strength": _chokepoint_evidence_strength(items),
                "sentiment_score": sentiment_score,
                "sentiment": sentiment,
                "trend": trend,
                "evidence": _key_evidence(items, prices, config["tickers"]),
                "stocks": ", ".join(config["tickers"][:8]),
                "items": items,
            }
        )
    return sorted(rows, key=lambda row: row["score"], reverse=True)


def _ticker_chokepoint(ticker: str) -> str:
    if ticker in FIXED_TICKER_THEME:
        return FIXED_TICKER_THEME[ticker]
    for name in DASHBOARD_CHOKEPOINT_ORDER:
        if ticker in CHOKEPOINTS[name]["tickers"]:
            return name
    return "general market"


def _is_negative_catalyst(item: dict | None) -> bool:
    if not item:
        return False
    if _is_primary_source_item(item) and item.get("primary_source_sentiment") != "Negative":
        return False
    if _is_primary_source_item(item) and item.get("body_status") == "Headline-only":
        return False
    text = f"{item.get('headline', '')} {item.get('summary', '')}".lower()
    return any(term in text for term in NEGATIVE_CATALYST_TERMS) or item.get("direction") == "负面" or item.get("strategy_impact") == "风险上升"


def _is_positive_catalyst(item: dict | None) -> bool:
    if not item or _is_negative_catalyst(item):
        return False
    if _is_primary_source_item(item) and item.get("primary_source_sentiment") in {
        "Positive signal",
        "Product momentum",
        "Customer adoption signal",
        "Platform capability update",
    }:
        return True
    text = f"{item.get('headline', '')} {item.get('summary', '')}".lower()
    return any(term in text for term in POSITIVE_CATALYST_TERMS) or item.get("direction") == "正面"


def _catalyst_type(items: list[dict]) -> str:
    if any(_is_negative_catalyst(item) for item in items):
        return "Risk catalyst"
    if any(_is_positive_catalyst(item) for item in items):
        return "Positive catalyst"
    if items:
        return "Neutral catalyst"
    return "No clear catalyst"


def _financial_evidence_score(items: list[dict]) -> float:
    if not items:
        return 5.0
    text = " ".join(f"{item.get('headline', '')} {item.get('summary', '')}" for item in items).lower()
    evidence_terms = [
        "earnings",
        "revenue",
        "order",
        "guidance",
        "outlook",
        "customer",
        "capex",
        "capacity",
        "contract",
        "quarter",
        "shipment",
    ]
    source_bonus = sum(
        1
        for item in items
        if item.get("confidence") == "High"
        or item.get("source_type") in PRIMARY_SOURCE_TYPES
        or item.get("source_type") in {"分析师报告", "主流财经新闻"}
    )
    term_bonus = sum(1 for term in evidence_terms if term in text)
    risk_count = sum(1 for item in items if item.get("strategy_impact") == "风险上升" or item.get("direction") == "负面")
    return _clamp_score(4.5 + min(3.0, source_bonus * 0.8 + term_bonus * 0.35) - min(2.5, risk_count * 1.0))


def _market_confirmation_score(row: dict) -> float:
    if not row:
        return 5.0
    score = 5.0
    daily = row.get("daily_change_pct")
    perf_5d = row.get("performance_5d")
    perf_20d = row.get("performance_20d")
    volume = row.get("volume_vs_20d")
    if daily is not None:
        score += max(-1.4, min(1.4, daily / 5))
    if perf_5d is not None:
        score += max(-1.0, min(1.0, perf_5d / 10))
    if perf_20d is not None:
        score += max(-1.0, min(1.0, perf_20d / 20))
    if volume is not None and volume >= 1.5:
        score += 0.4
    return _clamp_score(score)


def _narrative_risk_score(ticker: str, items: list[dict], row: dict) -> float:
    risk = 3.0
    if ticker in HIGH_BETA_TICKERS:
        risk += 1.4
    low_conf = sum(1 for item in items if item.get("confidence") == "Low")
    weak_source = sum(1 for item in items if item.get("source_type") in {"X 推文", "博客 / 二级来源"})
    high_conf = sum(1 for item in items if item.get("confidence") == "High")
    risk += min(2.2, low_conf * 0.7 + weak_source * 0.45)
    risk -= min(1.2, high_conf * 0.5)
    if row and (row.get("daily_change_pct") or 0) >= 8:
        risk += 1.0
    return _clamp_score(risk, 1.0, 10.0)


def _stock_confidence_rows(news: list[dict], prices: list[dict], ranking_rows: list[dict]) -> list[dict]:
    choke_scores = {row["chokepoint"]: row["score"] for row in ranking_rows}
    rows = []
    for ticker in STOCK_CONFIDENCE_TICKERS:
        items = _authoritative_items(_items_for_ticker(news, ticker))
        row = _price_row(prices, ticker)
        chokepoint = _ticker_chokepoint(ticker)
        choke_score = choke_scores.get(chokepoint, 5.0)
        financial = _financial_evidence_score(items)
        market = _market_confirmation_score(row)
        narrative_risk = _narrative_risk_score(ticker, items, row)
        score = (0.40 * choke_score) + (0.25 * financial) + (0.20 * market) + (0.15 * (10 - narrative_risk))
        if ticker in HIGH_BETA_TICKERS:
            score = min(score, 7.9)
        score = _clamp_score(score)
        risk_signal = any(item.get("strategy_impact") == "风险上升" or item.get("direction") == "负面" for item in items)
        positive_signal = any(item.get("confidence") == "High" and item.get("direction") != "负面" for item in items)
        high_move = bool(row and (row.get("daily_change_pct") or 0) >= 8)
        if risk_signal or score < 4.8:
            trend = "↓"
        elif positive_signal or (row and (row.get("daily_change_pct") or 0) >= 5 and items):
            trend = "↑"
        else:
            trend = "→"
        evidence = _key_evidence(items, prices, [ticker])
        if risk_signal:
            action = "Reduce Risk"
        elif high_move or (ticker in HIGH_BETA_TICKERS and score >= 7.0):
            action = "Avoid Chasing"
        elif score >= 8 and ticker in LARGE_CORE_TICKERS:
            action = "Hold Core"
        elif score >= 7.3:
            action = "Hold"
        elif score >= 6.6 and not items:
            action = "Watch"
        elif score >= 6.6:
            action = "Add on Pullback"
        else:
            action = "Watch"
        rows.append(
            {
                "ticker": ticker,
                "chokepoint": chokepoint,
                "score": score,
                "trend": trend,
                "evidence": evidence,
                "action": action,
            }
        )
    return rows


def _has_company_confirmation(items: list[dict]) -> bool:
    strong_sources = PRIMARY_SOURCE_TYPES | {"分析师报告", "主流财经新闻"}
    return any(item.get("confidence") == "High" or item.get("source_type") in strong_sources for item in items)


def _catalyst_strength(items: list[dict]) -> str:
    if items and all(_is_primary_source_item(item) and item.get("body_status") == "Headline-only" for item in items):
        return "Weak"
    catalyst = _catalyst_type(items)
    if catalyst == "Risk catalyst":
        return "Risk"
    if catalyst == "Positive catalyst" and any(item.get("confidence") == "High" for item in items):
        return "Strong"
    if catalyst in {"Positive catalyst", "Neutral catalyst"} and any(item.get("confidence") in {"High", "Medium"} for item in items):
        return "Medium"
    return "Weak"


def _risk_level(ticker: str, row: dict, items: list[dict]) -> str:
    daily = row.get("daily_change_pct") if row else None
    perf_5d = row.get("performance_5d") if row else None
    perf_20d = row.get("performance_20d") if row else None
    market_cap = row.get("market_cap") if row else None
    risk_points = 0
    if ticker in HIGH_BETA_TICKERS:
        risk_points += 2
    if market_cap is not None and market_cap < 10_000_000_000:
        risk_points += 1
    if daily is not None and abs(daily) >= 12:
        risk_points += 2
    elif daily is not None and abs(daily) >= 7:
        risk_points += 1
    if daily is not None and daily <= -8:
        risk_points += 1
    if perf_5d is not None and abs(perf_5d) >= 12:
        risk_points += 1
    if perf_20d is not None and abs(perf_20d) >= 25:
        risk_points += 1
    if row and (row.get("volume_vs_20d") or 0) >= 2:
        risk_points += 1
    if not items and ((perf_5d is not None and perf_5d >= 10) or (perf_20d is not None and perf_20d >= 20)):
        risk_points += 1
    if any(_is_negative_catalyst(item) for item in items):
        risk_points += 2
    if ticker in HIGH_BETA_TICKERS and not _has_company_confirmation(items):
        return "High"
    if risk_points >= 4:
        return "High"
    if risk_points >= 2:
        return "Medium"
    return "Low"


def _price_action(row: dict) -> str:
    if not row:
        return "Neutral"
    daily = row.get("daily_change_pct")
    premarket = row.get("premarket_change_pct")
    perf_5d = row.get("performance_5d")
    perf_20d = row.get("performance_20d")
    volume = row.get("volume_vs_20d") or 0
    score = 0
    for value, strong_cutoff, weak_cutoff in [
        (daily, 3, -3),
        (premarket, 2, -2),
        (perf_5d, 5, -5),
        (perf_20d, 10, -10),
    ]:
        if value is None:
            continue
        if value >= strong_cutoff:
            score += 1
        elif value <= weak_cutoff:
            score -= 1
    if volume >= 1.5 and score > 0:
        score += 1
    if score >= 2:
        return "Strong"
    if score <= -2:
        return "Weak"
    return "Neutral"


def _scoreboard_chokepoint_score(ticker: str, ranking_rows: list[dict]) -> int:
    chokepoint = _ticker_chokepoint(ticker)
    ranking_key = "Server / ODM" if chokepoint == "Server / Rack Integration" else chokepoint
    dynamic = next((row["importance"] for row in ranking_rows if row["chokepoint"] == ranking_key), 50)
    base = CHOKEPOINT_BASE.get(ticker, 55)
    return round(_clamp_score((base * 0.70) + (dynamic * 0.30), 0, 100))


def _scoreboard_confidence_score(ticker: str, row: dict, items: list[dict], chokepoint_score: int) -> int:
    base = THESIS_FIT_BASE.get(ticker, 55)
    financial = _financial_evidence_score(items) * 10
    market = _market_confirmation_score(row) * 10
    risk = _narrative_risk_score(ticker, items, row) * 10
    score = (base * 0.42) + (chokepoint_score * 0.25) + (financial * 0.18) + (market * 0.10) + ((100 - risk) * 0.05)
    if any(_is_negative_catalyst(item) for item in items):
        score -= 8
    if ticker in HIGH_BETA_TICKERS and not _has_company_confirmation(items):
        score = min(score, 68)
    return round(_clamp_score(score, 0, 100))


def _sharp_run(row: dict) -> bool:
    if not row:
        return False
    return any(
        (row.get(key) is not None and row.get(key) >= cutoff)
        for key, cutoff in [("daily_change_pct", 8), ("performance_5d", 12), ("performance_20d", 25)]
    )


def _action_bias(confidence: int, risk_level: str, price_action: str, row: dict, ticker: str) -> str:
    if row and (row.get("daily_change_pct") is not None and row.get("daily_change_pct") <= -8):
        return "Watch only"
    if _sharp_run(row):
        return "Avoid chase" if risk_level in {"Medium", "High"} or ticker in HIGH_BETA_TICKERS else "Watch only"
    if risk_level == "High":
        return "Watch only"
    if confidence >= 80 and price_action != "Strong":
        return "Add on pullback"
    if confidence >= 70:
        return "Hold"
    return "Watch only"


def _short_text(text: str, limit: int = 110) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "..."


def _short_reason(ticker: str, row: dict, items: list[dict], risk_level: str, catalyst: str) -> str:
    item = _primary_item(items)
    if item:
        return _short_text(f"{catalyst} catalyst; {item.get('headline', '')}")
    if row and row.get("flags"):
        return _short_text(f"No major company news; price flag: {'; '.join(row.get('flags') or [])}")
    if risk_level == "High":
        return "High beta or extended move without clear company-specific confirmation."
    return "Fits AI infrastructure thesis; no major new catalyst today."


def _compute_dashboard_data(news: list[dict], prices: list[dict]) -> dict:
    ranking_rows = _chokepoint_ranking_rows(news, prices)
    scoreboard_rows = []
    for ticker in SCOREBOARD_TICKERS:
        row = _price_row(prices, ticker)
        all_items = _items_for_ticker(news, ticker)
        items = _authoritative_items(all_items)
        if not row and not items:
            continue
        chokepoint_score = _scoreboard_chokepoint_score(ticker, ranking_rows)
        confidence = _scoreboard_confidence_score(ticker, row, items, chokepoint_score)
        if any(_is_primary_source_item(item) and not _is_negative_catalyst(item) for item in items):
            confidence = min(100, confidence + 3)
        catalyst = _catalyst_strength(items)
        catalyst_type = _catalyst_type(items)
        risk = _risk_level(ticker, row, items)
        price = _price_action(row)
        action = _action_bias(confidence, risk, price, row, ticker)
        scoreboard_rows.append(
            {
                "ticker": ticker,
                "theme": _ticker_chokepoint(ticker),
                "confidence": confidence,
                "chokepoint": chokepoint_score,
                "catalyst": catalyst,
                "catalyst_type": catalyst_type,
                "risk": risk,
                "price": price,
                "action": action,
                "reason": _short_reason(ticker, row, items, risk, catalyst),
            }
        )

    scoreboard_rows.sort(key=lambda item: item["confidence"], reverse=True)
    positive = [row for row in scoreboard_rows if row["catalyst_type"] == "Positive catalyst"]
    risk_rows = [row for row in scoreboard_rows if row["risk"] == "High" or row["catalyst_type"] == "Risk catalyst"]
    avoid = [row for row in scoreboard_rows if row["action"] == "Avoid chase"]
    strongest = ranking_rows[0]["chokepoint"] if ranking_rows else "无"
    confidence_leaders = ", ".join(row["ticker"] for row in scoreboard_rows[:3]) or "无"
    risk_line = ", ".join(row["ticker"] for row in risk_rows[:5]) or "无"
    avoid_line = ", ".join(row["ticker"] for row in avoid[:5]) or "无"
    add_watch = ", ".join(row["ticker"] for row in positive[:3]) or "暂不新增"
    signals = [
        f"今日最重要 Chokepoint: {strongest}",
        f"Scoreboard 最高信心标的: {confidence_leaders}",
        f"今日风险复核名单: {risk_line}",
        f"今日需要避免追高: {avoid_line}",
        f"是否需要新增观察名单: {add_watch}",
    ]
    return {
        "chokepoint_ranking": ranking_rows,
        "scoreboard": scoreboard_rows,
        "today_signal": signals,
        "risk_review": risk_rows,
        "avoid_chase": avoid,
    }


def _render_scoreboard(data: dict, limit: int | None = None) -> str:
    rows = data["scoreboard"][:limit] if limit else data["scoreboard"]
    lines = [
        "## AI Infrastructure Confidence Scoreboard",
        "",
        "| Ticker | Theme | Confidence Score | Chokepoint Score | Catalyst Strength | Risk Level | Price Action | Action Bias | Short Reason |",
        "|---|---|---:|---:|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['ticker']} | {_escape_table(row['theme'])} | {row['confidence']} | {row['chokepoint']} | "
            f"{row['catalyst']} | {row['risk']} | {row['price']} | {row['action']} | {_escape_table(row['reason'])} |"
        )
    lines.append("")
    lines.append("_Action Bias is a neutral research label, not a trade instruction._")
    return "\n".join(lines).strip()


def _render_confidence_dashboard(data: dict) -> str:
    ranking_rows = data["chokepoint_ranking"]
    lines = [
        "# AI Infrastructure Confidence Dashboard",
        "",
        "## 1. Chokepoint Ranking",
        "",
        "| Rank | Chokepoint | Chokepoint Importance | Evidence Strength | Near-term Sentiment | Trend | Key Evidence | Related Stocks |",
        "|---|---|---:|---|---|---|---|---|",
    ]
    for rank, row in enumerate(ranking_rows, start=1):
        lines.append(
            f"| {rank} | {_escape_table(row['chokepoint'])} | {row['importance']} | {row['evidence_strength']} | {row['sentiment']} | {row['trend']} | "
            f"{_escape_table(row['evidence'])} | {_escape_table(row['stocks'])} |"
        )
    lines.extend(
        [
            "",
            "## 2. Today's Signal",
            "",
        ]
    )
    lines.extend([f"- {signal}" for signal in data["today_signal"]])
    return "\n".join(lines).strip()


def _render_handoff_dashboard_snapshot(data: dict) -> str:
    required_tickers = [
        "DELL",
        "VRT",
        "AAOI",
        "NVTS",
        "MPWR",
        "MRVL",
        "ANET",
        "AVGO",
        "ETN",
        "MSFT",
        "GOOGL",
        "MU",
        "CIEN",
        "COHR",
    ]
    rows_by_ticker = {row["ticker"]: row for row in data["scoreboard"]}
    selected = []
    for row in data["scoreboard"][:6]:
        selected.append(row["ticker"])
    for row in data["risk_review"]:
        selected.append(row["ticker"])
    for row in data["avoid_chase"]:
        selected.append(row["ticker"])
    selected.extend(required_tickers)
    selected_rows = []
    seen = set()
    for ticker in selected:
        if ticker in seen or ticker not in rows_by_ticker:
            continue
        seen.add(ticker)
        selected_rows.append(rows_by_ticker[ticker])

    lines = [
        "## AI Infrastructure Dashboard Snapshot",
        "",
        "### 1. Chokepoint Ranking",
        "| Rank | Chokepoint | Importance | Evidence Strength | Sentiment | Evidence |",
        "|---|---|---:|---|---|---|",
    ]
    for rank, row in enumerate(data["chokepoint_ranking"][:4], start=1):
        lines.append(
            f"| {rank} | {_escape_table(row['chokepoint'])} | {row['importance']} | {row['evidence_strength']} | "
            f"{row['sentiment']} | {_escape_table(row['evidence'])} |"
        )
    lines.extend(["", "### 2. Stock Scoreboard"])
    lines.append("| Ticker | Theme | Confidence | Chokepoint | Catalyst | Risk | Action Bias |")
    lines.append("|---|---|---:|---:|---|---|---|")
    for row in selected_rows:
        lines.append(
            f"| {row['ticker']} | {_escape_table(row['theme'])} | {row['confidence']} | {row['chokepoint']} | "
            f"{row['catalyst']} | {row['risk']} | {row['action']} |"
        )
    lines.extend(["", "### 3. Today's Signal"])
    lines.extend([f"- {signal}" for signal in data["today_signal"]])
    lines.extend(["", "### 4. Risk Review list"])
    risk = data["risk_review"]
    lines.extend([f"- {row['ticker']}: {row['risk']} risk; {row['reason']}" for row in risk] or ["- 无"])
    lines.extend(["", "### 5. Avoid Chase list"])
    avoid = data["avoid_chase"]
    lines.extend([f"- {row['ticker']}: {row['reason']}" for row in avoid] or ["- 无"])
    return "\n".join(lines).strip()


def _render_handoff_chokepoint_radar(data: dict) -> str:
    lines = [
        "## Chokepoint Radar",
        "",
        "| Chokepoint | Importance | Evidence Strength | Sentiment | Evidence |",
        "|---|---:|---|---|---|",
    ]
    for row in data["chokepoint_ranking"]:
        lines.append(
            f"| {_escape_table(row['chokepoint'])} | {row['importance']} | {row['evidence_strength']} | {row['sentiment']} | {_escape_table(row['evidence'])} |"
        )
    avoid = ", ".join(row["ticker"] for row in data["avoid_chase"]) or "无"
    leaders = ", ".join(row["ticker"] for row in data["scoreboard"][:3]) or "无"
    strongest = data["chokepoint_ranking"][0]["chokepoint"] if data["chokepoint_ranking"] else "无"
    lines.extend(
        [
            "",
            "### Radar 总结",
            f"1. 今日最强 Chokepoint: {strongest}",
            f"2. 今日最值得观察的 3 只股票: {leaders}",
            f"3. 今日不建议追高的股票: {avoid}",
            "4. 对现有组合是否需要调整: 仅做研究复核，不输出具体交易动作。",
        ]
    )
    return "\n".join(lines).strip()


def _current_holding_impact(items: list[dict], core_tickers: set[str]) -> str:
    affected = sorted({ticker for item in items for ticker in item.get("tickers", []) if ticker in core_tickers})
    if not affected:
        return "未直接影响核心持仓/计划标的。"
    risk = any(item.get("strategy_impact") == "风险上升" or item.get("direction") == "负面" for item in items)
    if risk:
        return f"{', '.join(affected)} 需要验证风险是否扩大。"
    return f"{', '.join(affected)} 与当前主题相关，值得关注证据是否持续。"


def _watchlist_add_label(items: list[dict], config: dict, core_tickers: set[str], observation_tickers: set[str]) -> str:
    candidates = sorted(set(config["tickers"]) - core_tickers - observation_tickers)
    if not items or not candidates:
        return "否"
    if any(item.get("confidence") == "High" and item.get("strategy_impact") in {"需要关注", "与当前主题相关"} for item in items):
        return f"可观察：{', '.join(candidates[:3])}"
    return "否"


def _concept_hype_label(items: list[dict]) -> str:
    if not items:
        return "否"
    low_conf = sum(1 for item in items if item.get("confidence") == "Low")
    secondary = sum(1 for item in items if item.get("source_type") in {"X 推文", "博客 / 二级来源"})
    return "是" if low_conf + secondary >= max(2, len(items)) else "否"


def _importance_label(value: int) -> str:
    if value >= 80:
        return "High / Rising"
    if value >= 65:
        return "Medium / Stable"
    return "Low / Watch"


def _chokepoint_radar(news: list[dict], prices: list[dict], watchlists: dict, data: dict) -> str:
    core_tickers = set(watchlists.get(CORE_GROUP, {}).get("tickers", []))
    observation_tickers = set(watchlists.get(OBSERVATION_GROUP, {}).get("tickers", []))
    lines = []
    ranking_by_name = {row["chokepoint"]: row for row in data["chokepoint_ranking"]}
    for name in DASHBOARD_CHOKEPOINT_ORDER:
        config = CHOKEPOINTS[name]
        items = _chokepoint_items(news, config)
        ranking = ranking_by_name.get(name, {})
        related = ", ".join(config["tickers"])
        event = ranking.get("evidence") or (items[0].get("headline", "未发现重大相关新闻") if items else "未发现重大相关新闻")
        impact = _current_holding_impact(items, core_tickers)
        add_watch = _watchlist_add_label(items, config, core_tickers, observation_tickers)
        hype = _concept_hype_label(items)
        importance = ranking.get("importance", 0)
        sentiment = ranking.get("sentiment", "Neutral")
        evidence_strength = ranking.get("evidence_strength", "Low")
        lines.extend(
            [
                f"### {name}",
                f"- Chokepoint Importance: {_importance_label(importance)} ({importance})",
                f"- Evidence Strength: {evidence_strength}",
                f"- Near-term Sentiment: {sentiment}",
                f"- Evidence: {event}",
                f"- 相关股票: {related}",
                f"- 对当前持仓的影响: {impact}",
                f"- 是否需要加入观察名单: {add_watch}",
                f"- 是否只是概念炒作: {hype}",
                "",
            ]
        )

    strongest = data["chokepoint_ranking"][0]["chokepoint"] if data["chokepoint_ranking"] else "无"
    observe = [row["ticker"] for row in data["scoreboard"][:3]]
    chase_risk = [row["ticker"] for row in data["avoid_chase"]]
    adjustment = "不基于单日新闻做组合动作；当前只需要验证瓶颈是否持续增强、风险是否扩大。"
    lines.extend(
        [
            "### Radar 总结",
            f"1. 今日最强 Chokepoint: {strongest}",
            f"2. 今日最值得观察的 3 只股票: {', '.join(observe[:3]) if observe else '无'}",
            f"3. 今日不建议追高的股票: {', '.join(chase_risk) if chase_risk else '无'}",
            f"4. 对现有组合是否需要调整: {adjustment}",
        ]
    )
    return "\n".join(lines).strip()


def _new_signals(news: list[dict]) -> str:
    signals = [
        item
        for item in news
        if item.get("related_ai_theme") != "general market" and item.get("strategy_impact") in {"与当前主题相关", "需要关注", "风险上升"}
    ][:3]
    if not signals:
        return "- 今日未发现需要新增跟踪的强信号。"
    return "\n".join(
        [
            f"- {item.get('related_ai_theme')}: {item.get('ticker')} - {item.get('headline')} ({item.get('source_type')})"
            for item in signals
        ]
    )


def _high_risk_section(news: list[dict], watchlists: dict) -> str:
    high_risk = set(watchlists.get(HIGH_RISK_GROUP, {}).get("tickers", []))
    items = [item for item in news if set(item.get("tickers", [])) & high_risk]
    if not items:
        return "- POET, LWLG, SIVE, FOCI 等高风险概念股今日未发现重大新闻、财报、订单或监管文件。"
    return "\n".join(
        [
            f"- {item.get('ticker')}: {item.get('headline')}；来源：{item.get('source')}（{item.get('source_type')}）；仅记录，不做推荐。"
            for item in items[:5]
        ]
    )


def _evidence_strength(item: dict) -> str:
    source_type = item.get("source_type")
    if source_type in {"SEC filing", "Earnings release", "Earnings call transcript", "Investor Relations press release"}:
        return "High"
    if source_type in {
        "Investor presentation",
        "Official company blog / product announcement",
        "Official customer case study",
        "Official partnership / launch / guidance / capex update",
    }:
        return "Medium"
    if item.get("confidence") == "High":
        return "High"
    return "Low"


def _primary_source_results(news: list[dict]) -> list[dict]:
    results = []
    for item in sorted([entry for entry in news if _is_primary_source_item(entry)], key=_source_priority):
        takeaway = item.get("summary") or "Body unavailable / headline-only."
        relevance = item.get("why_it_matters") or f"与 {item.get('related_ai_theme', 'general market')} 主题相关，需人工复核。"
        results.append(
            {
                "ticker": item.get("ticker", "General"),
                "source_type": item.get("source_type", "Unknown"),
                "title": item.get("headline", ""),
                "date": item.get("published", "") or "N/A",
                "url": item.get("url") or item.get("link", ""),
                "key_takeaway": takeaway,
                "evidence_strength": _evidence_strength(item),
                "thesis_relevance": relevance,
                "sentiment": item.get("primary_source_sentiment") or "Neutral",
                "body_status": item.get("body_status", "Headline-only"),
                "ticker_mapping_confidence": item.get("ticker_mapping_confidence", "Low"),
                "item": item,
            }
        )
    return results


def _public_news_results(news: list[dict]) -> list[dict]:
    return [item for item in news if not _is_primary_source_item(item)]


def _render_primary_source_scan(primary_source_results: list[dict], limit: int | None = None) -> str:
    records = primary_source_results[:limit] if limit else primary_source_results
    if not records:
        return "No new primary-source updates found for monitored tickers today."
    lines = [
        "| Ticker | Source Type | Title | Date | Sentiment | Body Status | Ticker Mapping Confidence | Evidence Strength | Key Takeaway | Thesis Relevance | URL |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for record in records:
        lines.append(
            f"| {_escape_table(record['ticker'])} | {_escape_table(record['source_type'])} | {_escape_table(record['title'])} | "
            f"{_escape_table(record['date'])} | {_escape_table(record['sentiment'])} | {_escape_table(record['body_status'])} | "
            f"{_escape_table(record['ticker_mapping_confidence'])} | {record['evidence_strength']} | {_escape_table(record['key_takeaway'])} | "
            f"{_escape_table(record['thesis_relevance'])} | {record['url']} |"
        )
    return "\n".join(lines)


def _render_public_news_scan(public_news_results: list[dict], limit: int = 10) -> str:
    records = public_news_results[:limit]
    if not records:
        return "- No public-news updates found for monitored tickers today."
    lines = [
        "| Ticker | Headline | Source | Source Type | Confidence | Strategy Impact | URL |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in records:
        lines.append(
            f"| {_escape_table(item.get('ticker', 'General'))} | {_escape_table(item.get('headline', ''))} | "
            f"{_escape_table(item.get('source', 'Unknown'))} | {_escape_table(item.get('source_type', '来源未知'))} | "
            f"{item.get('confidence', 'Low')} | {_escape_table(item.get('strategy_impact', '仅作背景'))} | {item.get('url') or item.get('link', '')} |"
        )
    return "\n".join(lines)


def _evidence_dashboard_rows(news: list[dict]) -> list[dict]:
    rows = []
    for ticker in EVIDENCE_DASHBOARD_TICKERS:
        items = _items_for_ticker(news, ticker)
        best = sorted(items, key=_evidence_sort_key)[0] if items else None
        rows.append(
            {
                "ticker": ticker,
                "score": _evidence_score_for_item(best),
                "type": _evidence_type(best),
                "strength": _evidence_strength_for_item(best),
                "why": _short_text(best.get("why_it_matters") or best.get("headline", "") if best else "No company-specific evidence found today.", 150),
                "item": best,
            }
        )
    return sorted(rows, key=lambda row: row["score"], reverse=True)


def _render_evidence_dashboard(evidence_rows: list[dict]) -> str:
    lines = [
        "## Evidence Dashboard",
        "",
        "| Ticker | Evidence Score | Evidence Type | Strength | Why It Matters |",
        "|---|---:|---|---|---|",
    ]
    for row in evidence_rows:
        lines.append(
            f"| {row['ticker']} | {row['score']} | {_escape_table(row['type'])} | {row['strength']} | {_escape_table(row['why'])} |"
        )
    lines.extend(
        [
            "",
            "_Evidence Score prioritizes primary-source evidence. Media-only items are treated as signals, not proof._",
        ]
    )
    return "\n".join(lines)


def _render_primary_source_ranking(primary_source_results: list[dict], limit_per_group: int = 6) -> str:
    grouped = {
        "High Value Evidence": [],
        "Medium Value Evidence": [],
        "Low Value Evidence": [],
    }
    for record in primary_source_results:
        item = record.get("item", {})
        grouped.setdefault(_evidence_value_tier(item), []).append(record)

    lines = ["## Primary Source Ranking"]
    for label in ["High Value Evidence", "Medium Value Evidence", "Low Value Evidence"]:
        records = sorted(grouped.get(label, []), key=lambda record: _evidence_sort_key(record.get("item", {})))[:limit_per_group]
        lines.extend(["", f"### {label}"])
        if not records:
            lines.append("- None found today.")
            continue
        lines.append("| Ticker | Evidence Type | Title | Strength | Body Status | Why It Matters |")
        lines.append("|---|---|---|---|---|---|")
        for record in records:
            item = record.get("item", {})
            lines.append(
                f"| {_escape_table(record['ticker'])} | {_evidence_type(item)} | {_escape_table(record['title'])} | "
                f"{_evidence_strength_for_item(item)} | {_escape_table(record['body_status'])} | {_escape_table(record['thesis_relevance'])} |"
            )
    return "\n".join(lines)


def _hyperscaler_status(item: dict | None) -> str:
    if not item:
        return "Neutral"
    text = _item_text(item)
    if _is_negative_catalyst(item) or any(term in text for term in ["capex reduction", "guidance cut", "demand weakness"]):
        return "Bearish"
    if any(term in text for term in ["capex", "data center", "infrastructure", "gpu", "networking", "trainium", "tpu", "bedrock", "azure ai"]):
        return "Bullish"
    if _is_primary_source_item(item):
        return "Neutral"
    return "Neutral"


def _signal_from_terms(item: dict | None, terms: list[str]) -> str:
    text = _item_text(item)
    return "Yes" if any(term in text for term in terms) else "No"


def _reinforced_chokepoints_for_item(item: dict | None) -> str:
    text = _item_text(item)
    reinforced = [name for name, terms in HYPERSCALER_CHOKEPOINT_MAP if any(term in text for term in terms)]
    return ", ".join(reinforced) if reinforced else "None"


def _render_hyperscaler_tracker(news: list[dict]) -> str:
    lines = [
        "## Hyperscaler CapEx Tracker",
        "",
        "_Framework: Hyperscaler = AI Super City Developer. The tracker checks whether the AI super-city builders are adding CapEx, data centers, GPU capacity, networking, or power investment._",
        "",
        "| Hyperscaler | Ticker | Status | CapEx | Data Center | GPU | Networking | Power | Reinforced Chokepoints | Basis |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name, ticker in HYPERSCALERS.items():
        items = _items_for_ticker(news, ticker)
        capex_items = [
            item
            for item in items
            if any(term in _item_text(item) for term in ["capex", "capital expenditure", "data center", "infrastructure", "gpu", "networking", "trainium", "tpu"])
        ]
        item = sorted(capex_items or items, key=_evidence_sort_key)[0] if (capex_items or items) else None
        capex = _signal_from_terms(item, ["capex", "capital expenditure", "infrastructure investment"])
        data_center = _signal_from_terms(item, ["data center", "datacenter", "capacity expansion"])
        gpu = _signal_from_terms(item, ["gpu", "accelerator", "trainium", "tpu", "inference", "training"])
        networking = _signal_from_terms(item, ["networking", "ethernet", "switch", "interconnect"])
        power = _signal_from_terms(item, ["data center power", "power infrastructure", "power bottleneck", "grid", "switchgear", "ups", "pdu"])
        reinforced = _reinforced_chokepoints_for_item(item)
        basis = item.get("headline", "No direct primary-source or media signal found today.") if item else "No direct primary-source or media signal found today."
        lines.append(
            f"| {name} | {ticker} | {_hyperscaler_status(item)} | {capex} | {data_center} | {gpu} | {networking} | {power} | "
            f"{_escape_table(reinforced)} | {_escape_table(_short_text(basis, 140))} |"
        )
    return "\n".join(lines)


def _render_investment_relevance_review(news: list[dict], limit: int = 10) -> str:
    important = sorted([item for item in news if item.get("needs_attention") or _is_primary_source_item(item)], key=_evidence_sort_key)[:limit]
    lines = [
        "## Investment Relevance Review",
        "",
        "| Ticker | Item | News or Evidence | Order | Customer | Capacity | CapEx | Supply Chain | Thesis Impact |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    if not important:
        lines.append("| N/A | No important items found today. | News signal | No | No | No | No | No | Watch |")
        return "\n".join(lines)
    for item in important:
        flags = _evidence_flags(item)
        lines.append(
            f"| {_escape_table(item.get('ticker', 'General'))} | {_escape_table(_short_text(item.get('headline', ''), 120))} | "
            f"{flags['is_evidence']} | {flags['has_order']} | {flags['has_customer']} | {flags['has_capacity']} | "
            f"{flags['has_capex']} | {flags['has_supply_chain']} | {flags['changes_thesis']} |"
        )
    return "\n".join(lines)


def _top_conclusions(news: list[dict], prices: list[dict], primary_source_results: list[dict], evidence_rows: list[dict] | None = None) -> str:
    lines = []
    risk_items = [item for item in news if item.get("strategy_impact") == "风险上升"]
    core_items = [item for item in news if item.get("strategy_impact") == "需要关注"]
    theme_items = [item for item in news if item.get("strategy_impact") == "与当前主题相关"]
    movers = biggest_movers(prices)
    if evidence_rows:
        leader = evidence_rows[0]
        lines.append(f"- 最高证据分：{leader['ticker']} {leader['score']} / {leader['type']} / {leader['strength']}")
    if primary_source_results:
        source = primary_source_results[0]
        lines.append(
            f"- Primary Source 优先信号：{source['ticker']} - {source['title']}（Evidence Strength: {source['evidence_strength']}）"
        )
    if core_items:
        lines.append(f"- 核心组需要关注：{core_items[0].get('ticker')} - {core_items[0].get('headline')}")
    if risk_items:
        lines.append(f"- 风险上升信号：{risk_items[0].get('ticker')} - {risk_items[0].get('headline')}")
    if theme_items:
        lines.append(f"- 主题相关信号：{theme_items[0].get('related_ai_theme')} - {theme_items[0].get('headline')}")
    if movers.get("gainers"):
        lines.append(f"- 前一交易日涨幅较大：{', '.join(row['ticker'] for row in movers['gainers'][:3])}")
    if movers.get("decliners"):
        lines.append(f"- 前一交易日跌幅较大：{', '.join(row['ticker'] for row in movers['decliners'][:3])}")
    return "\n".join(lines[:5]) if lines else "- 今日未发现需要立即升级处理的重大信号。"


def _chatgpt_summary(news: list[dict], prices: list[dict], watchlists: dict, primary_source_results: list[dict] | None = None) -> str:
    core_tickers = watchlists.get(CORE_GROUP, {}).get("tickers", [])
    core_news = [item for item in news if set(item.get("tickers", [])) & set(core_tickers)]
    risk_news = [item for item in news if item.get("strategy_impact") == "风险上升"]
    theme_news = [item for item in news if item.get("related_ai_theme") in THEME_ORDER]
    primary_source_results = primary_source_results or []
    movers = biggest_movers(prices)
    gainers = ", ".join(f"{row['ticker']} {pct(row.get('daily_change_pct'))}" for row in movers.get("gainers", [])[:3]) or "无"
    decliners = ", ".join(f"{row['ticker']} {pct(row.get('daily_change_pct'))}" for row in movers.get("decliners", [])[:3]) or "无"
    core_line = "；".join([f"{item.get('ticker')}: {item.get('headline')}" for item in core_news[:4]]) or "核心组未发现重大新闻。"
    risk_line = "；".join([f"{item.get('ticker')}: {item.get('headline')}" for item in risk_news[:3]]) or "暂未发现明确融资/稀释、insider selling、指引下调或供应链延迟等重大风险信号。"
    theme_line = "；".join([f"{item.get('related_ai_theme')}: {item.get('headline')}" for item in theme_news[:5]]) or "主题关键词未抓到强信号。"
    primary_line = (
        "；".join(
            [
                f"{record['ticker']}: {record['source_type']} - {record['title']}（{record['evidence_strength']}）"
                for record in primary_source_results[:3]
            ]
        )
        or "今日未发现 monitored tickers 的新增公司官方/SEC 一手来源。"
    )
    return (
        f"今日 AI 大基建监控重点围绕核心持仓/计划买入组展开：{', '.join(core_tickers)}。"
        f"前一交易日主要涨幅标的为 {gainers}；主要跌幅标的为 {decliners}。"
        f"Primary Source Scan 方面，{primary_line}。若一手来源与媒体新闻冲突，应优先以公司官方披露或 SEC/IR 文件为准。"
        f"核心新闻方面，{core_line}。"
        f"主题层面，系统按光互连/网络、电力/液冷、AI server、Memory/HBM、云平台 capex 分类，当前抓到的重点线索包括：{theme_line}。"
        f"风险方面，{risk_line}。"
        "请重点分析这些新闻是否有财报、订单、客户、产能、capex 或供应链证据支撑；如果来源是 X 推文或二级博客，只能作为线索，不能当作事实。"
        "请不要给出具体交易动作或价格预测，只判断哪些信息值得关注、哪些需要验证、哪些风险在上升，以及哪些与 AI 大基建主题相关。"
    )


def _score_label(score: int, bands: list[tuple[int, str]]) -> str:
    for cutoff, label in bands:
        if score >= cutoff:
            return label
    return bands[-1][1]


def _score_from_market_row(row: dict) -> float:
    if not row:
        return 50.0
    score = 50.0
    for key, divisor in [("daily_change_pct", 0.35), ("premarket_change_pct", 0.25), ("performance_5d", 0.8), ("performance_20d", 2.0)]:
        value = row.get(key)
        if value is not None:
            score += value / divisor
    return max(0.0, min(100.0, score))


def _market_regime_score(prices: list[dict], news: list[dict]) -> int:
    market_rows = [_price_row(prices, ticker) for ticker in ["QQQ", "SPY"]]
    semi_rows = [_price_row(prices, ticker) for ticker in ["SMH", "SOXX"]]
    market_score = sum(_score_from_market_row(row) for row in market_rows) / len(market_rows)
    semi_score = sum(_score_from_market_row(row) for row in semi_rows) / len(semi_rows)
    score = (market_score * 0.65) + (semi_score * 0.35)
    macro_text = " ".join(_item_text(item) for item in news if item.get("related_ai_theme") == "general market")
    if any(term in macro_text for term in ["vix spike", "yields rise", "10-year yield", "strong dollar", "hawkish fed", "tariff"]):
        score -= 8
    if any(term in macro_text for term in ["soft inflation", "dovish fed", "yields fall", "rate cut"]):
        score += 6
    return round(max(0, min(100, score)))


def _material_change_type(item: dict) -> str:
    evidence_type = _evidence_type(item)
    text = _item_text(item)
    if evidence_type in {"Earnings", "Guidance"}:
        return "Earnings / Guidance"
    if any(term in text for term in ["backlog", "margin"]):
        return "Backlog / Margin"
    if any(term in text for term in ["capex", "capital expenditure", "data center expansion"]):
        return "CapEx"
    if evidence_type == "Supply Chain":
        return "Supply Chain"
    if any(term in text for term in ["tariff", "policy", "fed", "rate cut", "rate hike", "inflation"]):
        return "Policy / Macro"
    return "None"


def _is_material_signal_item(item: dict) -> bool:
    change_type = _material_change_type(item)
    if change_type == "None":
        return False
    if item.get("source_type") in {"X 推文", "博客 / 二级来源"} and item.get("confidence") != "High":
        return False
    if _is_primary_source_item(item):
        return item.get("body_status") != "Headline-only" or change_type in {"Earnings / Guidance", "Supply Chain"}
    return item.get("confidence") == "High" or _is_negative_catalyst(item)


def _material_changes(news: list[dict], prices: list[dict], dashboard_data: dict, limit: int = 6) -> list[dict]:
    changes = []
    seen = set()
    for item in sorted(news, key=_evidence_sort_key):
        change_type = _material_change_type(item)
        if not _is_material_signal_item(item):
            continue
        key = (change_type, item.get("headline", ""))
        if key in seen:
            continue
        seen.add(key)
        changes.append(
            {
                "type": change_type,
                "change": _short_text(item.get("headline", ""), 120),
                "impact": _short_text(item.get("why_it_matters") or item.get("strategy_impact") or "Needs review.", 110),
                "tickers": ", ".join(item.get("tickers") or [item.get("ticker", "General")]),
            }
        )

    watched = {row["ticker"] for row in dashboard_data["scoreboard"]}
    for row in prices:
        ticker = row.get("ticker")
        daily = row.get("daily_change_pct")
        if ticker not in watched or daily is None or abs(daily) <= 5:
            continue
        direction = "up" if daily > 0 else "down"
        changes.append(
            {
                "type": "Major Price Move",
                "change": f"{ticker} moved {direction} {pct(daily)} in the previous session.",
                "impact": "price-discipline alert, not thesis upgrade",
                "tickers": ticker,
            }
        )
    return changes[:limit]


def _has_fundamental_material_signal(changes: list[dict]) -> bool:
    return any(change["type"] in FUNDAMENTAL_CHANGE_TYPES for change in changes)


def _ai_infrastructure_score(dashboard_data: dict, changes: list[dict]) -> int:
    top_chokepoints = dashboard_data["chokepoint_ranking"][:5]
    base = round(sum(row["importance"] for row in top_chokepoints) / len(top_chokepoints)) if top_chokepoints else 50
    material_strength = sum(1 for change in changes if change["type"] in FUNDAMENTAL_CHANGE_TYPES)
    risk_signals = sum(1 for row in dashboard_data["chokepoint_ranking"] if row["sentiment"] == "Negative")
    score = base + min(10, material_strength * 4) - min(15, risk_signals * 5)
    if not _has_fundamental_material_signal(changes):
        score = min(score, 79)
    return round(max(0, min(100, score)))


def _portfolio_alerts(dashboard_data: dict, prices: list[dict], limit: int = 6) -> list[dict]:
    rows_by_ticker = {row["ticker"]: row for row in dashboard_data["scoreboard"]}
    selected = []
    for row in dashboard_data["risk_review"]:
        if row["catalyst_type"] == "Risk catalyst" and row["ticker"] not in selected:
            selected.append(row["ticker"])
    for row in prices:
        ticker = row.get("ticker")
        if ticker in rows_by_ticker and row.get("daily_change_pct") is not None and abs(row["daily_change_pct"]) > 5 and ticker not in selected:
            selected.append(ticker)

    alerts = []
    for ticker in selected:
        row = rows_by_ticker.get(ticker)
        price_row = _price_row(prices, ticker)
        if not row:
            continue
        daily = price_row.get("daily_change_pct") if price_row else None
        if row["catalyst_type"] == "Risk catalyst" or (daily is not None and daily <= -5):
            action = "Risk Control"
        elif daily is not None and daily > 5 and (ticker in HIGH_BETA_TICKERS or row["action"] == "Avoid chase"):
            action = "Avoid Chasing"
        elif row["risk"] == "High":
            action = "Watch"
        else:
            action = "Do Nothing"
        alert = row["reason"]
        if daily is not None and abs(daily) >= 7:
            alert = f"Major price move: {pct(daily)}; {alert}"
        alerts.append({"ticker": ticker, "alert": _short_text(alert, 120), "action": action})
    return alerts[:limit]


def _portfolio_action_score(dashboard_data: dict, prices: list[dict], changes: list[dict], alerts: list[dict]) -> int:
    material_count = len(changes)
    strong_count = sum(1 for change in changes if change["type"] in FUNDAMENTAL_CHANGE_TYPES)
    major_moves = sum(
        1
        for row in prices
        if row.get("ticker") in {score_row["ticker"] for score_row in dashboard_data["scoreboard"]}
        and row.get("daily_change_pct") is not None
        and abs(row["daily_change_pct"]) > 5
    )
    chase_count = sum(1 for alert in alerts if alert["action"] == "Avoid Chasing")
    risk_count = sum(1 for alert in alerts if alert["action"] == "Risk Control")
    score = 25 + material_count * 8 + strong_count * 10 + major_moves * 4 - chase_count * 8 - risk_count * 18
    if material_count == 0:
        score = min(score, 39)
    return round(max(0, min(100, score)))


def _brief_scores(prices: list[dict], news: list[dict], dashboard_data: dict, changes: list[dict], alerts: list[dict]) -> dict:
    market_score = _market_regime_score(prices, news)
    ai_score = _ai_infrastructure_score(dashboard_data, changes)
    portfolio_score = _portfolio_action_score(dashboard_data, prices, changes, alerts)
    return {
        "market": market_score,
        "market_label": _score_label(market_score, [(80, "risk-on"), (60, "constructive"), (40, "neutral"), (30, "cautious"), (0, "risk-off")]),
        "ai_infrastructure": ai_score,
        "ai_infrastructure_label": _score_label(ai_score, [(80, "thesis strengthening"), (60, "thesis intact"), (40, "neutral / mixed"), (20, "thesis weakening"), (0, "thesis materially damaged")]),
        "portfolio_action": portfolio_score,
        "portfolio_action_label": _score_label(portfolio_score, [(80, "action allowed"), (60, "small buy possible"), (40, "watch only"), (20, "do nothing"), (0, "risk control / avoid")]),
    }


def _brief_verdict(scores: dict, changes: list[dict], alerts: list[dict]) -> str:
    if not changes:
        return "AI infrastructure thesis remains intact, with no fresh signal strong enough to require action this morning."
    if any(alert["action"] in {"Risk Control", "Avoid Chasing"} for alert in alerts):
        return "AI infrastructure thesis remains intact, but portfolio discipline matters because today’s strongest signals are risk or chase-control alerts."
    if _has_fundamental_material_signal(changes):
        return "AI infrastructure thesis has fresh evidence to monitor, but the brief still avoids turning a single signal into a trade instruction."
    return "AI infrastructure thesis remains intact, but there is no fresh signal strong enough to justify chasing high-beta names today."


def _render_material_changes(changes: list[dict]) -> str:
    if not changes:
        return "No material change in the last 24 hours."
    lines = ["| Type | Change | Impact | Related Tickers |", "|---|---|---|---|"]
    for change in changes:
        lines.append(f"| {change['type']} | {_escape_table(change['change'])} | {_escape_table(change['impact'])} | {_escape_table(change['tickers'])} |")
    return "\n".join(lines)


def _brief_chokepoint_change(row: dict) -> str:
    if not any(_is_material_signal_item(item) for item in row.get("items", [])):
        return "unchanged"
    if row["sentiment"] == "Negative":
        return "weakened"
    if row["sentiment"] == "Positive" and row["evidence_strength"] in {"High", "Medium"}:
        return "improved"
    return "watch" if row["sentiment"] != "Neutral" else "unchanged"


def _render_chokepoint_snapshot(dashboard_data: dict, has_material_change: bool) -> str:
    rows = []
    used = set()
    for row in dashboard_data["chokepoint_ranking"]:
        label = BRIEF_CHOKEPOINT_LABELS.get(row["chokepoint"], row["chokepoint"])
        if label in used:
            continue
        used.add(label)
        change = _brief_chokepoint_change(row) if has_material_change else "unchanged"
        rows.append({**row, "label": label, "change": change})
        if len(rows) == 5:
            break
    lines = ["| Rank | Chokepoint | Score | Change | Key Tickers |", "|---|---|---:|---|---|"]
    for rank, row in enumerate(rows, start=1):
        lines.append(f"| {rank} | {_escape_table(row['label'])} | {row['importance']} | {row['change']} | {_escape_table(row['stocks'])} |")
    reasons = [f"- {row['label']}: {_short_text(row['evidence'], 120)}" for row in rows if row["change"] != "unchanged" and "今日未发现足以改变判断" not in row["evidence"]]
    if reasons:
        lines.extend(["", *reasons[:3]])
    return "\n".join(lines)


def _render_portfolio_alerts(alerts: list[dict]) -> str:
    if not alerts:
        return "No portfolio-level alert today."
    lines = ["| Ticker | Alert | Action |", "|---|---|---|"]
    for alert in alerts:
        lines.append(f"| {alert['ticker']} | {_escape_table(alert['alert'])} | {alert['action']} |")
    return "\n".join(lines)


def _action_from_portfolio_score(score: int) -> str:
    if score <= 19:
        return "Risk Control"
    if score <= 39:
        return "Do Nothing"
    if score <= 59:
        return "Watch"
    if score <= 79:
        return "Small Buy Candidate"
    return "Action Allowed"


def _today_action(changes: list[dict], alerts: list[dict], scores: dict) -> tuple[str, list[str]]:
    action = _action_from_portfolio_score(scores["portfolio_action"])
    reasons = []
    if not changes:
        reasons.append("No material change in the last 24 hours.")
    elif not _has_fundamental_material_signal(changes):
        reasons.append("Material signal is price-related only, not a thesis upgrade.")
    else:
        reasons.append("There is a fundamental material signal that may deserve review.")
    if any(alert["action"] == "Avoid Chasing" for alert in alerts):
        reasons.append("At least one ticker needs watch/avoid-chasing discipline, but the overall action follows the score.")
    elif any(alert["action"] == "Risk Control" for alert in alerts):
        reasons.append("At least one ticker needs risk review, but the overall action follows the score.")
    else:
        reasons.append("No portfolio-level alert overrides the score.")
    return action, reasons[:3]


def _render_today_action(action: str, reasons: list[str]) -> str:
    return "\n".join([action, "", *[f"- {reason}" for reason in reasons]])


def _render_brief(report_date: str, report_url: str, prices: list[dict], news: list[dict], dashboard_data: dict, changes: list[dict], alerts: list[dict]) -> str:
    scores = _brief_scores(prices, news, dashboard_data, changes, alerts)
    action, action_reasons = _today_action(changes, alerts, scores)
    sections = [
        f"# AI Pre-Market Brief — {report_date}",
        "",
        f"- Generated: {fetch_timestamp()}",
        f"- HTML report: {report_url}",
        f"- Research-only: no brokerage connection, no orders, no trade execution, no price prediction.",
        "",
        "## 1. Today’s Verdict",
        f"- Market Regime Score: {scores['market']} / 100 ({scores['market_label']})",
        f"- AI Infrastructure Score: {scores['ai_infrastructure']} / 100 ({scores['ai_infrastructure_label']})",
        f"- Portfolio Action Score: {scores['portfolio_action']} / 100 ({scores['portfolio_action_label']})",
        "",
        _brief_verdict(scores, changes, alerts),
        "",
        "## 2. Material Changes Only",
        _render_material_changes(changes),
        "",
        "## 3. Chokepoint Snapshot",
        _render_chokepoint_snapshot(dashboard_data, bool(changes)),
        "",
        "## 4. Portfolio Alerts",
        _render_portfolio_alerts(alerts),
        "",
        "## 5. Today’s Action",
        _render_today_action(action, action_reasons),
        "",
        "_This brief is for research review only. It does not provide buy/sell instructions and does not execute trades._",
    ]
    return "\n".join(sections)


def _render_handoff_brief(report_date: str, report_url: str, prices: list[dict], news: list[dict], dashboard_data: dict, changes: list[dict], alerts: list[dict]) -> str:
    return "\n".join(
        [
            _render_brief(report_date, report_url, prices, news, dashboard_data, changes, alerts),
            "",
            "## Hand-off Focus",
            "- Use the Material Changes table as the only source of new-change review.",
            "- Treat Portfolio Alerts as watch/risk labels, not trading instructions.",
            "- If no material change is listed, do not invent a thesis change.",
        ]
    )


def build_reports() -> dict:
    ensure_dirs()
    report_date = today_est()
    prices = fetch_all()
    news = fetch_news()
    primary_source_results = _primary_source_results(news)
    public_news_results = _public_news_results(news)
    write_json(ROOT / f"reports/raw_data/{report_date}-prices.json", prices)
    write_json(ROOT / f"reports/raw_data/{report_date}-news.json", news)
    write_json(
        ROOT / f"reports/raw_data/{report_date}-primary-sources.json",
        [{key: value for key, value in record.items() if key != "item"} for record in primary_source_results],
    )

    base_url = report_base_url()
    report_url = f"{base_url.rstrip('/')}/{report_date}.html" if base_url else f"docs/reports/{report_date}.html"
    dashboard_data = _compute_dashboard_data(news, prices)
    changes = _material_changes(news, prices, dashboard_data)
    alerts = _portfolio_alerts(dashboard_data, prices)
    md = _render_brief(report_date, report_url, prices, news, dashboard_data, changes, alerts)
    handoff = _render_handoff_brief(report_date, report_url, prices, news, dashboard_data, changes, alerts)

    daily_path = ROOT / f"reports/daily/{report_date}.md"
    handoff_path = ROOT / f"reports/chatgpt_handoff/{report_date}.md"
    daily_path.write_text(md, encoding="utf-8")
    handoff_path.write_text(handoff, encoding="utf-8")
    return {"date": report_date, "title": f"{REPORT_TITLE} - {report_date}", "markdown": str(daily_path), "handoff": str(handoff_path)}


def _news_section_for_handoff(news: list[dict]) -> str:
    items = [item for item in news if item.get("needs_attention")][:8]
    if not items:
        return "- 未发现需要 ChatGPT 深入分析的高优先级新闻。"
    lines = []
    for item in items:
        summary = item.get("summary") or "Body unavailable / headline-only."
        if summary == "Summary based on headline/metadata only.":
            summary = "Body unavailable / headline-only."
        lines.extend(
            [
                f"- Ticker: {item.get('ticker', 'General')}",
                f"  Headline: {item.get('headline', '')}",
                f"  Source: {item.get('source', 'Unknown')}（{item.get('source_type', '来源未知')}）",
                f"  Summary: {summary}",
                f"  Why it matters: {item.get('why_it_matters', '')}",
                f"  Related theme: {item.get('related_ai_theme', 'general market')}",
                f"  Confidence: {item.get('confidence', 'Low')}",
                f"  Strategy impact: {item.get('strategy_impact', '仅作背景')}",
            ]
        )
    return "\n".join(lines)


if __name__ == "__main__":
    result = build_reports()
    print(f"Wrote {result['markdown']}")
    print(f"Wrote {result['handoff']}")
