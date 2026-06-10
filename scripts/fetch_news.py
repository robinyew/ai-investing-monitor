from __future__ import annotations

import re
from datetime import datetime
from html.parser import HTMLParser
from urllib.request import Request, urlopen

import feedparser

from utils import ROOT, load_yaml, write_json


MAJOR_EVENT_TERMS = [
    "earnings",
    "guidance",
    "outlook",
    "order",
    "contract",
    "customer",
    "capex",
    "capacity",
    "expansion",
    "analyst",
    "upgrade",
    "downgrade",
    "insider",
    "selling",
    "offering",
    "dilution",
    "financing",
    "sec filing",
    "10-k",
    "10-q",
    "8-k",
    "supply chain",
    "delay",
    "shortage",
    "ai data center",
    "cloud ai",
]

NEGATIVE_TERMS = [
    "downgrade",
    "cut",
    "miss",
    "weak",
    "delay",
    "shortage",
    "lawsuit",
    "probe",
    "investigation",
    "dilution",
    "offering",
    "stock sales",
    "share sale",
    "share issuance",
    "insider selling",
    "guidance cut",
]

POSITIVE_TERMS = [
    "upgrade",
    "raise",
    "beat",
    "strong",
    "order",
    "contract",
    "expansion",
    "capacity",
    "customer",
    "partnership",
    "capex",
]

SOURCE_TYPE_RULES = [
    ("Investor Relations press release", ["investor relations", "press release", "newsroom", "nvidia newsroom"]),
    ("Earnings call transcript", ["earnings call", "transcript"]),
    ("Official company blog / product announcement", ["azure.microsoft.com", "aws.amazon.com/blogs/aws", "cloudblog.withgoogle.com", "google cloud blog", "aws news blog", "microsoft azure blog"]),
    ("主流财经新闻", ["reuters", "cnbc", "bloomberg", "marketwatch", "wall street journal", "wsj", "financial times", "barron's"]),
    ("X 推文", ["x.com", "twitter"]),
    ("博客 / 二级来源", ["blog", "yahoo finance", "investors.com", "seeking alpha", "motley fool"]),
]

HIGH_CONFIDENCE_SOURCE_TYPES = {
    "Investor Relations press release",
    "SEC filing",
    "Earnings release",
    "Earnings call transcript",
    "Investor presentation",
    "Official customer case study",
    "Official partnership / launch / guidance / capex update",
    "主流财经新闻",
}
PRIMARY_SOURCE_TYPES = {
    "Investor Relations press release",
    "Official company blog / product announcement",
    "Official customer case study",
    "Official partnership / launch / guidance / capex update",
    "SEC filing",
    "Earnings release",
    "Earnings call transcript",
    "Investor presentation",
}
MEDIUM_CONFIDENCE_SOURCES = ["the elec", "digitimes", "trendforce", "lightcounting", "servethehome", "tom's hardware"]
SOURCE_OWNER_TICKERS = {
    "NVIDIA Newsroom": ["NVDA"],
    "Microsoft Azure Blog": ["MSFT"],
    "AWS News Blog": ["AMZN"],
    "Google Cloud Blog": ["GOOGL"],
}
PRIMARY_NEGATIVE_TERMS = [
    "guidance cut",
    "demand weakness",
    "margin pressure",
    "supply constraint",
    "supply constraints",
    "customer loss",
    "regulatory issue",
    "launch delay",
    "shipment delay",
    "production delay",
    "delayed launch",
    "delayed shipment",
    "delayed production",
    "cancellation",
    "cancelled",
    "canceled",
    "capex reduction",
    "negative financial disclosure",
]
PRIMARY_POSITIVE_TERMS = [
    "customer",
    "case study",
    "launch",
    "general availability",
    "generally available",
    "performance improvement",
    "partnership",
    "new capability",
    "agent",
    "ai",
]


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            text = data.strip()
            if text:
                self.parts.append(text)


COMPANY_ALIASES = {
    "AAOI": ["Applied Optoelectronics"],
    "ALAB": ["Astera Labs"],
    "AMAT": ["Applied Materials"],
    "AMZN": ["Amazon", "AWS"],
    "ANET": ["Arista"],
    "ARM": ["Arm Holdings"],
    "ASML": ["ASML"],
    "AVGO": ["Broadcom"],
    "CARR": ["Carrier"],
    "CIEN": ["Ciena"],
    "CLS": ["Celestica"],
    "COHR": ["Coherent"],
    "CORZ": ["CoreWeave", "Core Scientific"],
    "CRDO": ["Credo"],
    "DELL": ["Dell"],
    "ETN": ["Eaton"],
    "FIX": ["Comfort Systems"],
    "FLEX": ["Flex"],
    "FOCI": ["FOCI"],
    "GEV": ["GE Vernova"],
    "GOOGL": ["Alphabet", "Google"],
    "HPE": ["Hewlett Packard Enterprise", "HPE"],
    "IREN": ["IREN"],
    "JBL": ["Jabil"],
    "KLAC": ["KLA"],
    "LITE": ["Lumentum"],
    "LRCX": ["Lam Research"],
    "LWLG": ["Lightwave Logic"],
    "META": ["Meta"],
    "MPWR": ["Monolithic Power"],
    "MRVL": ["Marvell"],
    "MSFT": ["Microsoft", "Azure"],
    "MU": ["Micron"],
    "NBIS": ["Nebius"],
    "NOK": ["Nokia"],
    "NVTS": ["Navitas"],
    "ORCL": ["Oracle"],
    "POET": ["POET Technologies"],
    "PWR": ["Quanta Services"],
    "SMCI": ["Super Micro", "Supermicro"],
    "SIVE": ["Sivers"],
    "TSM": ["TSMC", "Taiwan Semiconductor"],
    "TT": ["Trane"],
    "VRT": ["Vertiv"],
}


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub("<[^>]+>", "", value or "")).strip()


def _html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html or "")
    text = _clean_text(" ".join(parser.parts))
    boilerplate_terms = ["cookie", "privacy policy", "subscribe", "sign up"]
    if sum(1 for term in boilerplate_terms if term in text.lower()) >= 3 and len(text) < 1200:
        return ""
    return text


def _entry_body_text(entry: dict, url: str, source_type: str) -> tuple[str, str]:
    pieces = []
    for content in entry.get("content", []) or []:
        pieces.append(_clean_text(content.get("value", "")))
    body = _clean_text(" ".join(pieces))
    if len(body) >= 280:
        return body, "Full"

    summary_detail = entry.get("summary_detail", {}) or {}
    summary_value = summary_detail.get("value", "") or entry.get("summary", "")
    summary_text = _clean_text(summary_value)
    if len(summary_text) >= 180:
        return summary_text, "Partial"

    if source_type in PRIMARY_SOURCE_TYPES and url:
        try:
            request = Request(url, headers={"User-Agent": "ai-investing-monitor/1.0"})
            with urlopen(request, timeout=8) as response:
                html = response.read(600_000).decode("utf-8", errors="ignore")
            fetched = _html_to_text(html)
            if len(fetched) >= 800:
                return fetched, "Full"
            if len(fetched) >= 220:
                return fetched, "Partial"
        except Exception:
            pass

    if summary_text:
        return summary_text, "Headline-only"
    return "", "Headline-only"


def _watchlist_context() -> dict:
    watchlists = load_yaml("config/watchlists.yaml")
    core = set(watchlists.get("core_holdings_planned", {}).get("tickers", []))
    observation = set(watchlists.get("key_observation", {}).get("tickers", []))
    high_risk = set(watchlists.get("high_risk_concepts", {}).get("tickers", []))
    benchmarks = set(watchlists.get("benchmarks", {}).get("tickers", []))
    all_tickers = sorted(core | observation | high_risk | benchmarks)
    return {
        "core": core,
        "observation": observation,
        "high_risk": high_risk,
        "benchmarks": benchmarks,
        "all": all_tickers,
    }


def _theme_config() -> dict:
    return load_yaml("config/themes.yaml").get("themes", {})


def _mentions(text: str, ticker: str) -> bool:
    aliases = COMPANY_ALIASES.get(ticker, [])
    if f"${ticker}" in text:
        return True
    if ticker not in {"ON"} and re.search(rf"\b{re.escape(ticker)}\b", text):
        return True
    return any(re.search(rf"\b{re.escape(alias)}\b", text, flags=re.IGNORECASE) for alias in aliases)


def _mentioned_tickers(text: str, tickers: list[str]) -> list[str]:
    return [ticker for ticker in tickers if _mentions(text, ticker)]


def _mapped_tickers(source_name: str, text: str, tickers: list[str], source_type: str, explicit_text: str = "") -> tuple[list[str], str]:
    mentioned = _mentioned_tickers(text, tickers)
    owner = SOURCE_OWNER_TICKERS.get(source_name, [])
    if source_type in PRIMARY_SOURCE_TYPES and owner:
        explicit_mentions = _mentioned_tickers(explicit_text, tickers)
        extras = [ticker for ticker in explicit_mentions if ticker not in owner]
        if extras:
            return sorted(set(owner + extras)), "Medium"
        return owner, "High"
    if mentioned:
        return mentioned, "High"
    return [], "Low"


def _contains_keyword(text: str, keyword: str) -> bool:
    lowered = text.lower()
    key = str(keyword).lower()
    if len(key) <= 4 or key.replace(".", "").isalnum() and key.upper() == keyword:
        return bool(re.search(rf"(?<![a-z0-9]){re.escape(key)}(?![a-z0-9])", lowered))
    return key in lowered


def _related_theme(text: str, tickers: list[str], themes: dict) -> str:
    for theme_name, data in themes.items():
        related = set(data.get("related_tickers", []))
        if any(_contains_keyword(text, str(keyword)) for keyword in data.get("keywords", [])):
            return theme_name
        if any(ticker in related for ticker in tickers):
            return theme_name
    return "general market"


def _source_type(source: str, url: str, headline: str) -> str:
    text = f"{source} {url} {headline}".lower()
    if "sec.gov" in text or re.search(r"\b(10-k|10-q|8-k|s-1|13f)\b", text):
        return "SEC filing"
    if re.search(r"\b(earnings release|quarterly results|financial results)\b", text):
        return "Earnings release"
    if re.search(r"\b(investor presentation|presentation)\b", text):
        return "Investor presentation"
    if re.search(r"\b(customer case study|case study|customer story)\b", text):
        return "Official customer case study"
    if re.search(r"\b(partnership|launch|guidance|capex update)\b", text) and any(
        official in text for official in ["newsroom", "investor relations", "press release", "azure.microsoft.com", "aws.amazon.com", "cloudblog.withgoogle.com"]
    ):
        return "Official partnership / launch / guidance / capex update"
    if re.search(r"\b(analyst|rating|upgrade|downgrade|price target)\b", text):
        return "分析师报告"
    for label, terms in SOURCE_TYPE_RULES:
        if any(term in text for term in terms):
            return label
    return "博客 / 二级来源"


def _confidence(source: str, source_type: str) -> str:
    lowered = source.lower()
    if source_type in HIGH_CONFIDENCE_SOURCE_TYPES:
        return "High"
    if source_type == "Official company blog / product announcement":
        return "Medium"
    if any(name in lowered for name in MEDIUM_CONFIDENCE_SOURCES):
        return "Medium"
    if source_type == "X 推文":
        return "Low"
    if "yahoo finance" in lowered:
        return "Low"
    return "Medium" if source_type == "博客 / 二级来源" else "Low"


def _direction(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ["stock sales", "share sale", "share issuance", "offering", "dilution"]):
        return "负面"
    if any(term in lowered for term in NEGATIVE_TERMS):
        return "负面"
    if any(term in lowered for term in POSITIVE_TERMS):
        return "正面"
    return "中性"


def _primary_source_sentiment(text: str, body_status: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in PRIMARY_NEGATIVE_TERMS):
        return "Negative"
    if body_status == "Headline-only":
        return "Watch"
    if any(term in lowered for term in ["customer", "case study", "adoption", "built with", "deployed"]):
        return "Customer adoption signal"
    if any(term in lowered for term in ["launch", "announcing", "general availability", "generally available", "now available"]):
        return "Product momentum"
    if any(term in lowered for term in ["performance", "capability", "platform", "feature", "agent", "model"]):
        return "Platform capability update"
    if any(term in lowered for term in PRIMARY_POSITIVE_TERMS):
        return "Positive signal"
    return "Neutral"


def _primary_direction(sentiment: str) -> str:
    if sentiment == "Negative":
        return "负面"
    if sentiment in {"Positive signal", "Product momentum", "Customer adoption signal", "Platform capability update"}:
        return "正面"
    return "中性"


def _strategy_impact(text: str, tickers: list[str], core: set[str], high_risk: set[str], theme: str, source_type: str = "", primary_sentiment: str = "") -> str:
    lowered = text.lower()
    if source_type in PRIMARY_SOURCE_TYPES:
        if primary_sentiment == "Negative":
            return "风险上升"
        if any(ticker in high_risk for ticker in tickers):
            return "高风险概念观察"
        if any(ticker in core for ticker in tickers):
            return "需要关注"
        if primary_sentiment in {"Positive signal", "Product momentum", "Customer adoption signal", "Platform capability update"}:
            return "与当前主题相关"
        return "仅作背景"
    if any(ticker in high_risk for ticker in tickers):
        return "高风险概念观察"
    if any(term in lowered for term in ["dilution", "offering", "stock sales", "share sale", "share issuance", "insider selling", "downgrade", "guidance cut", "delay", "shortage"]):
        return "风险上升"
    if any(ticker in core for ticker in tickers):
        return "需要关注"
    if theme != "general market":
        return "与当前主题相关"
    return "仅作背景"


def _summary_from_body(headline: str, body_text: str, body_status: str) -> str:
    if body_status == "Headline-only" or not body_text:
        return "Body unavailable / headline-only."
    sentences = re.split(r"(?<=[.!?])\s+", body_text)
    selected = []
    for sentence in sentences:
        clean = _clean_text(sentence)
        if len(clean) < 45:
            continue
        selected.append(clean)
        if len(selected) >= 2:
            break
    if not selected:
        return _clean_text(body_text[:320])
    summary = " ".join(selected)
    if len(summary) > 520:
        summary = summary[:519].rstrip() + "."
    return summary


def _why_it_matters(tickers: list[str], theme: str, impact: str, direction: str) -> str:
    ticker_text = ", ".join(tickers) if tickers else "AI 大基建主题"
    if impact == "风险上升":
        return f"{ticker_text} 出现潜在负面线索，需验证是否影响 {theme} 主题。"
    if impact == "需要关注":
        return f"{ticker_text} 属于核心持仓/计划买入组，相关新闻需要进入每日重点监控。"
    if impact == "与当前主题相关":
        return f"该信息与 {theme} 主题相关，可作为需求、订单、capex 或供应链变化线索。"
    if impact == "高风险概念观察":
        return "属于低权重高风险概念股，只在重大新闻、财报、订单或监管文件出现时记录。"
    return f"方向暂为{direction}，目前只作为背景信息。"


def _is_major_event(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in MAJOR_EVENT_TERMS)


def _is_theme_or_event_text(text: str) -> bool:
    lowered = text.lower()
    strong_terms = [
        "ai infrastructure",
        "ai data center",
        "data center power",
        "cloud ai",
        "ai capex",
        "hyperscaler capex",
        "optical",
        "interconnect",
        "800g",
        "1.6t",
        "cpo",
        "lpo",
        "hbm",
        "ai server",
        "gb200",
        "gb300",
        "rack-scale",
        "liquid cooling",
        "transformer",
        "switchgear",
    ]
    return _is_major_event(text) or any(term in lowered for term in strong_terms)


def _is_relevant(item: dict, context: dict) -> bool:
    tickers = set(item.get("tickers", []))
    source = item.get("source", "").lower()
    text = f"{item.get('headline', '')} {item.get('summary', '')}".lower()
    if item.get("source_type") == "博客 / 二级来源" and not _is_theme_or_event_text(text):
        return False
    if tickers & context["core"]:
        return _is_theme_or_event_text(text) or item.get("source_type") in (PRIMARY_SOURCE_TYPES | {"主流财经新闻", "分析师报告"})
    if tickers & context["observation"]:
        return _is_theme_or_event_text(text) or item.get("source_type") in (PRIMARY_SOURCE_TYPES | {"主流财经新闻", "分析师报告"})
    if tickers & context["high_risk"]:
        return _is_major_event(text)
    if item.get("related_ai_theme") != "general market" and _is_major_event(text):
        return True
    if "yahoo finance" in source and not tickers and not _is_major_event(text):
        return False
    return item.get("related_ai_theme") != "general market" and any(
        term in text
        for term in ["ai data center", "capex", "optical", "power", "cooling", "hbm", "server", "cloud ai"]
    )


def _priority(item: dict, context: dict) -> tuple[int, int, str]:
    tickers = set(item.get("tickers", []))
    if tickers & context["core"]:
        group_rank = 0
    elif tickers & context["observation"]:
        group_rank = 1
    elif item.get("related_ai_theme") != "general market":
        group_rank = 2
    elif tickers & context["high_risk"]:
        group_rank = 3
    else:
        group_rank = 4
    impact_rank = {
        "风险上升": 0,
        "需要关注": 1,
        "与当前主题相关": 2,
        "高风险概念观察": 3,
        "仅作背景": 4,
    }.get(item.get("strategy_impact"), 5)
    return (group_rank, impact_rank, item.get("headline", ""))


def _summary(source_type: str) -> str:
    if source_type == "X 推文":
        return "未验证，仅作为线索。"
    return "Summary based on headline/metadata only."


def _build_item(source: dict, entry: dict, context: dict, themes: dict) -> dict:
    headline = _clean_text(entry.get("title", ""))
    metadata = _clean_text(entry.get("summary", ""))
    url = entry.get("link", "").strip()
    source_name = source.get("name", "Unknown")
    source_type = _source_type(source_name, url, headline)
    body_text, body_status = _entry_body_text(entry, url, source_type)
    explicit_mapping_text = f"{headline} {metadata}"
    analysis_text = f"{headline} {metadata} {body_text}"
    tickers, mapping_confidence = _mapped_tickers(source_name, analysis_text, context["all"], source_type, explicit_mapping_text)
    theme = _related_theme(analysis_text, tickers, themes)
    confidence = _confidence(source_name, source_type)
    primary_sentiment = _primary_source_sentiment(analysis_text, body_status) if source_type in PRIMARY_SOURCE_TYPES else ""
    direction = _primary_direction(primary_sentiment) if source_type in PRIMARY_SOURCE_TYPES else _direction(analysis_text)
    impact = _strategy_impact(analysis_text, tickers, context["core"], context["high_risk"], theme, source_type, primary_sentiment)
    summary = _summary_from_body(headline, body_text, body_status) if source_type in PRIMARY_SOURCE_TYPES else _summary(source_type)
    return {
        "ticker": ", ".join(tickers) if tickers else "General",
        "headline": headline,
        "source": source_name,
        "source_type": source_type,
        "link": url,
        "url": url,
        "summary": summary,
        "original_summary": summary,
        "why_it_matters": _why_it_matters(tickers, theme, impact, direction),
        "related_ai_theme": theme,
        "confidence": confidence,
        "primary_source_sentiment": primary_sentiment,
        "body_status": body_status if source_type in PRIMARY_SOURCE_TYPES else "Metadata",
        "ticker_mapping_confidence": mapping_confidence,
        "strategy_impact": impact,
        "direction": direction,
        "needs_attention": impact in {"需要关注", "风险上升", "与当前主题相关", "高风险概念观察"},
        "tickers": tickers,
        "category": source.get("category", ""),
        "published": entry.get("published", ""),
    }


def fetch_news(limit_per_feed: int = 25) -> list[dict]:
    sources = load_yaml("config/sources.yaml")
    context = _watchlist_context()
    themes = _theme_config()
    seen: set[str] = set()
    items: list[dict] = []

    for source in sources.get("news_feeds", []):
        try:
            parsed = feedparser.parse(source["url"])
            for entry in parsed.entries[:limit_per_feed]:
                title = _clean_text(entry.get("title", ""))
                if not title or title.lower() in seen:
                    continue
                seen.add(title.lower())
                item = _build_item(source, entry, context, themes)
                if _is_relevant(item, context):
                    items.append(item)
        except Exception as exc:
            items.append(
                {
                    "ticker": "General",
                    "headline": f"News source unavailable: {source.get('name', 'Unknown')}",
                    "source": source.get("name", "Unknown"),
                    "source_type": "博客 / 二级来源",
                    "link": source.get("url", ""),
                    "url": source.get("url", ""),
                    "summary": f"Source fetch failed: {exc}",
                    "original_summary": f"Source fetch failed: {exc}",
                    "why_it_matters": "A configured news source was unavailable, so the brief may miss relevant headlines.",
                    "related_ai_theme": "general market",
                    "confidence": "Low",
                    "strategy_impact": "仅作背景",
                    "direction": "中性",
                    "needs_attention": False,
                    "tickers": [],
                    "category": source.get("category", ""),
                    "published": datetime.utcnow().isoformat(),
                }
            )
    return sorted(items, key=lambda item: _priority(item, context))


if __name__ == "__main__":
    news = fetch_news()
    write_json(ROOT / "reports/raw_data/news.json", news)
    print(f"Fetched {len(news)} relevant news items")
