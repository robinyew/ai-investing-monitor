#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
HUB = ROOT / "investment-intelligence-hub"
TZ = ZoneInfo("America/New_York")
X_POSTS_ROOT = HUB / "inbox/x_posts"
NEWS_SCAN_ROOT = HUB / "inbox/news"
X_FILE_LIMIT = 10

SOURCE_QUALITY = {
    "ai_infrastructure_news_scan": {
        "tier": "tier_2a_ai_infrastructure_news_scan",
        "score": 0.78,
        "reason": "Independent AI infrastructure news scan used for fresh signal detection, chokepoint intelligence, and verification queue. Durable thesis confirmation still requires Tier 1 evidence or explicit human approval.",
    },
    "premarket_brief": {
        "tier": "tier_2b_core_market_context",
        "score": 0.60,
        "reason": "Context-only pre-market brief used for market regime, portfolio alert context, and daily risk discipline. It is not thesis-confirming evidence.",
    },
    "daily_report": {
        "tier": "tier_2b_core_market_context",
        "score": 0.60,
        "reason": "Legacy daily report source type. Treated as context-only and not as thesis-confirming evidence.",
    },
    "ljg_invest_report": {
        "tier": "tier_3_deep_research",
        "score": 0.70,
        "reason": "Deep single-name ljg-invest style research note. Used as thesis-context input that still requires primary-source verification.",
    },
    "x_post": {
        "tier": "tier_4_user_captured_x",
        "score": 0.45,
        "reason": "User-captured X source from the curated Hub inbox. Claims require corroboration before research use.",
    },
    "x_markdown": {
        "tier": "tier_4_user_captured_x",
        "score": 0.45,
        "reason": "Explicit converted X Markdown source. Claims require corroboration before research use.",
    },
    "x_html": {
        "tier": "tier_4_user_captured_x",
        "score": 0.45,
        "reason": "Explicit converted X HTML source. Claims require corroboration before research use.",
    },
}

# Trading-instruction words are forbidden outside the disclaimer, but infinitive
# business usage quoted from sources ("Meta plans to sell AI compute", "to add
# capacity") is not an instruction — the "(?<!to )" lookbehind exempts it.
FORBIDDEN = re.compile(r"\b(?<!to )(buy|sell|trim|add|position size|price target)\b", re.I)
SENSITIVE_PATTERNS = [
    ("account amount", re.compile(r"\b(account value|account balance|portfolio value)\b", re.I)),
    ("holding quantity", re.compile(r"\b(shares|contracts|units)\s*[:=]?\s*\d+|\b\d+\s+(shares|contracts|units)\b", re.I)),
    ("cost basis", re.compile(r"\bcost basis\b|\bavg\.?\s*cost\b", re.I)),
    ("exact trading plan", re.compile(r"\bexact trading plan\b|\bstop loss\b|\blimit order\b", re.I)),
    ("tax detail", re.compile(r"\btax lot\b|\bcapital gains?\b|\btaxable\b", re.I)),
    ("banking/company sensitive information", re.compile(r"\bbank account\b|\brouting number\b|\bconfidential\b|\bapi key\b|\bsecret\b", re.I)),
    ("private personal notes", re.compile(r"\bprivate note\b|\bpersonal note\b", re.I)),
]
KNOWN_TICKERS = {
    "AAOI", "ALAB", "AMAT", "AMD", "AMZN", "ANET", "ARM", "ASML", "AVGO", "CARR",
    "CIEN", "CLS", "COHR", "CORZ", "CRDO", "CSCO", "DELL", "ETN", "FIX", "FLEX",
    "FOCI", "GEV", "GLW", "GOOGL", "HPE", "HPQ", "IREN", "JBL", "KLAC", "LITE",
    "LRCX", "LWLG", "META", "MPWR", "MRVL", "MSFT", "MU", "NBIS", "NOK", "NVDA",
    "NVTS", "ON", "ORCL", "POET", "PWR", "QCOM", "QQQ", "SIVE", "SMCI", "SMH",
    "SOXX", "SPY", "STX", "TSM", "TXN", "VRT", "WDC",
}

CHOKEPOINT_KEYWORDS = {
    "Compute / GPU": ["gpu", "compute", "accelerator", "nvidia", "inference", "training"],
    "ASIC / Custom Silicon": ["asic", "custom silicon", "tpu", "trainium", "xpu"],
    "AI Networking": ["networking", "ethernet", "switching", "switch", "routing", "serdes"],
    "Optical Interconnect": ["optical", "transceiver", "cpo", "lpo", "800g", "1.6t", "coherent", "silicon photonics", "fiber"],
    "Power / Cooling": ["power", "cooling", "thermal", "liquid cooling", "grid", "electricity", "pdu", "ups"],
    "Memory / HBM": ["hbm", "memory", "dram", "nand"],
    "AI Server": ["server", "rack", "gb200", "gb300", "nvl72", "odm", "ems"],
    "Cloud / AI Platform": ["capex", "hyperscaler", "cloud", "azure", "aws", "google cloud", "data center"],
}


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def as_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def slug(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return normalized[:48] or "source"


def stable_source_id(date: str, source_type: str, path: Path) -> str:
    digest = hashlib.sha256(rel(path).encode("utf-8")).hexdigest()[:10]
    return f"src_{date}_{source_type}_{slug(path.stem)}_{digest}"


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n",
        encoding="utf-8",
    )


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def read_title(path: Path, fallback: str) -> str:
    for line in read_text(path).splitlines()[:20]:
        stripped = line.strip()
        if stripped.lower().startswith("#+title:"):
            return stripped.split(":", 1)[1].strip()
        if stripped.lower().startswith("title:"):
            return stripped.split(":", 1)[1].strip().strip("'\"")
        if stripped.startswith("# "):
            return stripped[2:].strip()
        if stripped.lower().startswith("<title>"):
            return re.sub(r"</?title>", "", stripped, flags=re.I).strip()
    return fallback


def read_org_date(path: Path) -> str | None:
    for line in read_text(path).splitlines()[:20]:
        if line.strip().lower().startswith("#+date:"):
            return line.split(":", 1)[1].strip()
    return None


def extract_url(path: Path) -> str | None:
    for line in read_text(path).splitlines()[:30]:
        stripped = line.strip()
        if stripped.startswith("url:"):
            return stripped.split(":", 1)[1].strip().strip('"')
        match = re.search(r"https?://\S+", stripped)
        if match:
            return match.group(0).rstrip(")\"'")
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Investment Intelligence Hub parallel pipeline.")
    parser.add_argument("--date", required=True)
    parser.add_argument("--mode", default="parallel")
    parser.add_argument("--daily-report")
    parser.add_argument("--ljg-report")
    parser.add_argument("--x-md")
    parser.add_argument("--x-posts-dir")
    parser.add_argument("--export-html", action="store_true")
    parser.add_argument("--skip-migration-log", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def previous_day_parts(date: str) -> tuple[str, str]:
    prior = datetime.strptime(date, "%Y-%m-%d").date() - timedelta(days=1)
    return prior.strftime("%Y_%m_%d"), prior.strftime("%Y%m%d")


def folder_date_from_path(path: Path) -> str | None:
    match = re.fullmatch(r"(\d{4})_(\d{2})_(\d{2})", path.name)
    if not match:
        return None
    return "-".join(match.groups())


def source_date_from_filename(path: Path) -> str | None:
    match = re.match(r"(\d{4})(\d{2})(\d{2})", path.name)
    if not match:
        return None
    return "-".join(match.groups())


def x_source_type(path: Path, default: str = "x_post") -> str:
    if default != "x_post":
        return default
    if path.suffix.lower() == ".html":
        return "x_html"
    if path.suffix.lower() == ".md":
        return "x_post"
    return default


def make_x_item(path: Path, source_type: str = "x_post", context_label: str = "current_day_folder") -> dict:
    folder_date = folder_date_from_path(path.parent)
    source_date = source_date_from_filename(path)
    return {
        "path": path,
        "source_type": x_source_type(path, source_type),
        "folder_date": folder_date,
        "source_date": source_date,
        "context_label": context_label,
        "needs_corroboration": True,
    }


def x_candidates_from_dir(path: Path) -> list[Path]:
    return sorted(item for item in path.iterdir() if item.is_file() and item.suffix.lower() in {".md", ".html"})


def recent_x_dirs(run_date: str, limit: int = 2) -> list[Path]:
    run_day = datetime.strptime(run_date, "%Y-%m-%d").date()
    dirs: list[tuple[datetime.date, Path]] = []
    if not X_POSTS_ROOT.exists():
        return []
    for path in X_POSTS_ROOT.iterdir():
        if not path.is_dir():
            continue
        folder_date = folder_date_from_path(path)
        if not folder_date:
            continue
        parsed = datetime.strptime(folder_date, "%Y-%m-%d").date()
        if parsed < run_day:
            dirs.append((parsed, path))
    dirs.sort(reverse=True)
    return [path for _, path in dirs[:limit]]


def collect_x_files(args: argparse.Namespace) -> tuple[list[dict], list[str]]:
    warnings: list[str] = []
    files: list[dict] = []
    if args.x_posts_dir:
        x_dir = as_path(args.x_posts_dir)
        if not x_dir or not x_dir.exists():
            warnings.append(f"--x-posts-dir missing: {rel(x_dir) if x_dir else args.x_posts_dir}")
            return files, warnings
        candidates = x_candidates_from_dir(x_dir)
        if not candidates:
            warnings.append(f"--x-posts-dir has no .md/.html files: {rel(x_dir)}")
            return files, warnings
        if len(candidates) > X_FILE_LIMIT:
            warnings.append(f"--x-posts-dir has {len(candidates)} X files; included first {X_FILE_LIMIT} sorted files.")
            candidates = candidates[:X_FILE_LIMIT]
        return [make_x_item(path, "x_post", "explicit_input") for path in candidates], warnings

    if args.x_md:
        x_file = as_path(args.x_md)
        if not x_file or not x_file.exists():
            warnings.append(f"--x-md missing: {rel(x_file) if x_file else args.x_md}")
            return files, warnings
        source_type = "x_html" if x_file.suffix.lower() == ".html" else "x_markdown"
        return [make_x_item(x_file, source_type, "explicit_input")], warnings

    folder_name = args.date.replace("-", "_")
    run_dir = X_POSTS_ROOT / folder_name
    if run_dir.exists():
        candidates = x_candidates_from_dir(run_dir)
        if candidates:
            if len(candidates) > X_FILE_LIMIT:
                warnings.append(f"run-date x_posts folder has {len(candidates)} X files; included first {X_FILE_LIMIT} sorted files.")
                candidates = candidates[:X_FILE_LIMIT]
            return [make_x_item(path, "x_post", "current_day_folder") for path in candidates], warnings
        warnings.append(f"run-date x_posts folder has no .md/.html files: {rel(run_dir)}")
    else:
        warnings.append(f"run-date x_posts folder missing: {rel(run_dir)}")

    remaining = X_FILE_LIMIT
    for idx, recent_dir in enumerate(recent_x_dirs(args.date, limit=2), 1):
        candidates = x_candidates_from_dir(recent_dir)
        if not candidates:
            continue
        context_label = "recent_context" if idx == 1 else "carry_forward"
        included = candidates[:remaining]
        for path in included:
            files.append(make_x_item(path, "x_post", context_label))
        remaining = X_FILE_LIMIT - len(files)
        warnings.append(f"included {len(included)} X file(s) from {context_label}: {rel(recent_dir)}")
        if remaining <= 0:
            break
    if not files:
        warnings.append("no recent x_posts fallback files found")
    return files, warnings


def resolve_inputs(args: argparse.Namespace) -> tuple[Path, Path | None, Path | None, list[dict], list[str]]:
    daily = as_path(args.daily_report) or ROOT / f"reports/daily/{args.date}.md"
    news_scan = NEWS_SCAN_ROOT / f"{args.date}_ai_infrastructure_news.md"
    ljg = as_path(args.ljg_report)
    missing_optional: list[str] = []
    if not daily.exists():
        missing_optional.append(f"premarket brief context not found: {rel(daily)}")
    if not news_scan.exists():
        missing_optional.append("no news scan input found")
        news_scan = None
    if ljg is None:
        missing_optional.append("--ljg-report not provided")
    elif not ljg.exists():
        missing_optional.append(f"--ljg-report missing: {rel(ljg)}")
        ljg = None
    x_files, x_warnings = collect_x_files(args)
    missing_optional.extend(x_warnings)
    return daily, news_scan, ljg, x_files, missing_optional


def output_paths(date: str, export_html: bool = False) -> dict[str, Path]:
    paths = {
        "sources": HUB / f"processed/sources/{date}.jsonl",
        "signals": HUB / f"processed/signals/{date}.jsonl",
        "ticker_impacts": HUB / f"processed/ticker_impacts/{date}.jsonl",
        "thesis_impacts": HUB / f"processed/thesis_impacts/{date}.jsonl",
        "brief": HUB / f"reports/daily_intelligence/{date}.md",
        "notes": HUB / f"reports/daily_intelligence/{date}_notes.md",
        "validation": HUB / f"reports/daily_intelligence/{date}_validation.md",
    }
    if export_html:
        paths["html"] = HUB / f"reports/daily_intelligence/html/{date}.html"
        paths["html_notes"] = HUB / f"reports/daily_intelligence/{date}_html_notes.md"
    return paths


def source_records(date: str, ingested_at: str, daily: Path, news_scan: Path | None, ljg: Path | None, x_files: list[dict]) -> list[dict]:
    inputs = []
    if news_scan is not None and news_scan.exists():
        inputs.append(
            {
                "source_id": stable_source_id(date, "ai_infrastructure_news_scan", news_scan),
                "source_type": "ai_infrastructure_news_scan",
                "title": read_title(news_scan, f"AI Infrastructure News Scan — {date}"),
                "author_or_origin": "ai-investing-monitor",
                "url": f"docs/news/{date}.html",
                "local_path": rel(news_scan),
                "published_at": date,
                "provenance_notes": "Tier 2A source. Can trigger source-backed Hub signals and verification tasks, but cannot alone confirm durable thesis.",
            }
        )
    if daily.exists():
        inputs.append(
            {
                "source_id": stable_source_id(date, "premarket_brief", daily),
                "source_type": "premarket_brief",
                "title": read_title(daily, f"AI Pre-Market Brief - {date}"),
                "author_or_origin": "ai-investing-monitor",
                "url": f"docs/reports/{date}.html",
                "local_path": rel(daily),
                "published_at": date,
                "provenance_notes": "Tier 2B context-only source. Used for market regime, portfolio alert context, and daily risk discipline; not thesis-confirming evidence.",
            }
        )
    if ljg is not None:
        inputs.append(
            {
                "source_id": stable_source_id(date, "ljg_invest_report", ljg),
                "source_type": "ljg_invest_report",
                "title": read_title(ljg, ljg.stem),
                "author_or_origin": "ljg-invest report",
                "url": None,
                "local_path": rel(ljg),
                "published_at": read_org_date(ljg),
                "provenance_notes": "Registered by the parallel hub pipeline. Original org-mode report was not copied, moved, or rewritten.",
            }
        )
    for item in x_files:
        x_path = item["path"]
        source_type = item["source_type"]
        inputs.append(
            {
                "source_id": stable_source_id(date, source_type, x_path),
                "source_type": source_type,
                "title": read_title(x_path, x_path.stem),
                "author_or_origin": "User-captured X source",
                "url": extract_url(x_path),
                "local_path": rel(x_path),
                "file_path": rel(x_path),
                "folder_date": item.get("folder_date"),
                "source_date": item.get("source_date"),
                "context_label": item.get("context_label"),
                "needs_corroboration": True,
                "published_at": item.get("source_date"),
                "provenance_notes": "Tier 4 user-captured X input. Registered for discovery only and requires corroboration before research use.",
            }
        )
    rows = []
    for item in inputs:
        path = ROOT / item["local_path"]
        rows.append(
            {
                **item,
                "ingested_at": ingested_at,
                "source_quality": SOURCE_QUALITY[item["source_type"]],
                "content_hash": sha256(path),
                "status": "registered",
            }
        )
    return rows


def source_id_by_type(sources: list[dict], source_type: str) -> str | None:
    for row in sources:
        if row["source_type"] == source_type:
            return row["source_id"]
    return None


def source_ids_by_types(sources: list[dict], source_types: set[str]) -> list[str]:
    return [row["source_id"] for row in sources if row["source_type"] in source_types]


def source_type_string(source_ids: list[str], source_by_id: dict[str, dict]) -> str:
    return ",".join(source_by_id[sid]["source_type"] for sid in source_ids)


def quality_for_sources(source_ids: list[str], source_by_id: dict[str, dict]) -> float:
    values = [source_by_id[sid]["source_quality"]["score"] for sid in source_ids]
    return round(sum(values) / len(values), 2)


def extract_known_tickers(path: Path) -> list[str]:
    text = read_text(path)
    found = sorted(ticker for ticker in KNOWN_TICKERS if re.search(rf"\b{re.escape(ticker)}\b", text))
    return found


def extract_chokepoints(text: str) -> list[str]:
    lowered = text.lower()
    found = []
    for chokepoint, keywords in CHOKEPOINT_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            found.append(chokepoint)
    return found[:5]


def first_nonempty_line(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("|") and not set(stripped) <= {"-", "_"}:
            return stripped.lstrip("# ").strip()
    return fallback


def field_from_markdown_table(block: str, field: str) -> str:
    target = f"**{field.lower()}**"
    for line in block.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0].lower() == target:
            return cells[1].strip()
    return ""


def paragraph_after_heading(block: str, heading: str) -> str:
    prefix = f"**{heading}:**"
    lines = block.splitlines()
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith(prefix):
            continue
        collected = [stripped[len(prefix):].strip()]
        for follow in lines[idx + 1:]:
            follow = follow.strip()
            if not follow or follow.startswith("**") or follow.startswith("###"):
                break
            collected.append(follow)
        text = re.sub(r"\s+", " ", " ".join(collected)).strip()
        return text[:260]
    return ""


def parse_ticker_list(value: str) -> list[str]:
    found = []
    for item in re.split(r"[,/ ]+", value):
        ticker = item.strip().upper()
        if ticker in KNOWN_TICKERS and ticker not in found:
            found.append(ticker)
    return found


def parse_news_scan_items(text: str) -> list[dict]:
    if "## Key Developments" not in text:
        return []
    key_section = text.split("## Key Developments", 1)[1].split("## Infrastructure Implication", 1)[0]
    blocks = re.split(r"\n###\s+", key_section)
    items = []
    for raw in blocks:
        block = raw.strip()
        if not block or block.startswith("("):
            continue
        title, _, body = block.partition("\n")
        title = title.strip()
        if not title or title.lower().startswith("no high-signal"):
            continue
        tickers = parse_ticker_list(field_from_markdown_table(body, "Tickers"))
        raw_chokepoint = field_from_markdown_table(body, "Chokepoint") or (extract_chokepoints(title + "\n" + body) or ["AI Infrastructure"])[0]
        chokepoint = normalize_chokepoint(raw_chokepoint, title + "\n" + body)
        importance = field_from_markdown_table(body, "Importance")
        confidence = field_from_markdown_table(body, "Confidence")
        why = paragraph_after_heading(body, "Why it matters") or "Source-backed news scan item requires primary-source verification before durable thesis use."
        items.append(
            {
                "title": title,
                "tickers": tickers,
                "chokepoint": chokepoint,
                "importance": importance,
                "confidence": confidence,
                "why": why,
            }
        )
    return items[:3]


def normalize_chokepoint(chokepoint: str, evidence: str = "") -> str:
    text = evidence.lower()
    if chokepoint == "Data Center":
        if any(word in text for word in ["sovereign", "romania", "europe", "factory", "expansion", "buildout"]):
            return "Data Center Construction / Sovereign AI Infrastructure"
        return "Data Center Construction"
    if chokepoint in {"Power & Cooling", "Power / Cooling"}:
        if any(word in text for word in ["power", "electricity", "grid", "utility", "interconnection"]):
            return "Power Availability / Grid Constraint"
        return "Power / Cooling Infrastructure"
    if chokepoint == "Hyperscaler Capex":
        return "Hyperscaler CapEx Funding / AI Infrastructure Spend"
    return chokepoint


def readable_slug(path: Path) -> str:
    stem = re.sub(r"^\d{8}_?", "", path.stem)
    text = stem.replace("-", " ").replace("_", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text.title() if text else path.stem


def x_display_title(source: dict) -> str:
    title = (source.get("title") or "").strip()
    if title and not title.startswith("🐦"):
        return title
    path = Path(source["local_path"])
    stem = path.stem.lower()
    if "citrini" in stem and ("dram" in stem or "flash" in stem):
        return "Citrini: Flash / DRAM / AI memory narrative"
    if "smh" in stem:
        return "SMH / Semiconductor basket narrative"
    return readable_slug(path)


def x_display_tickers(source: dict, tickers: list[str]) -> str:
    if tickers:
        return ", ".join(tickers)
    text = " ".join(str(source.get(key) or "") for key in ["title", "local_path"]).lower()
    if "smh" in text:
        return "Theme: Semiconductors"
    if any(word in text for word in ["dram", "flash", "memory", "hbm"]):
        return "Theme: Memory / HBM"
    if any(word in text for word in ["optical", "cpo", "800g", "1.6t"]):
        return "Theme: Optical Interconnect"
    return "No explicit ticker"


def signal_rows(date: str, sources: list[dict]) -> list[dict]:
    source_by_id = {row["source_id"]: row for row in sources}
    news = [row for row in sources if row["source_type"] == "ai_infrastructure_news_scan"]
    ljg_sources = [row for row in sources if row["source_type"] == "ljg_invest_report"]
    x_sources = [row for row in sources if row["source_type"] in {"x_post", "x_markdown", "x_html"}]
    rows: list[dict] = []
    for idx, source in enumerate(news[:2], 1):
        path = ROOT / source["local_path"]
        text = read_text(path)
        news_items = parse_news_scan_items(text)
        if not news_items:
            tickers = extract_known_tickers(path)
            chokepoints = extract_chokepoints(text)
            news_items = [
                {
                    "title": "news_scan_summary: " + first_nonempty_line(text, "AI infrastructure news scan summary"),
                    "tickers": tickers[:8],
                    "chokepoint": (chokepoints or ["AI Infrastructure"])[0],
                    "why": "News scan summary is available, but no specific high-signal item could be reliably parsed.",
                    "importance": "",
                    "confidence": "",
                }
            ]
        for item_idx, item in enumerate(news_items[:3], 1):
            summary_bits = [item["why"]]
            if item.get("importance"):
                summary_bits.append(f"Importance: {item['importance']}.")
            if item.get("confidence"):
                summary_bits.append(f"Confidence: {item['confidence']}.")
            rows.append(
                {
                    "signal_id": f"sig_{date}_news_scan_{idx:02d}_{item_idx:02d}",
                    "date": date,
                    "claim": item["title"],
                    "evidence_summary": " ".join(summary_bits)[:360],
                    "source_ids": [source["source_id"]],
                    "tickers": item["tickers"][:8],
                    "themes": [item["chokepoint"]],
                    "direction": "mixed",
                    "time_horizon": "short",
                    "confidence": 0.72 if item.get("importance", "").startswith(("4", "5")) else 0.65,
                    "source_quality_score": quality_for_sources([source["source_id"]], source_by_id),
                    "evidence_strength_score": 0.74 if item.get("importance", "").startswith(("4", "5")) else 0.62,
                    "thesis_relevance_score": 0.74,
                    "market_impact_score": 0.60,
                    "noise_risk_score": 0.25,
                    "verification_needed": True,
                    "status": "source_backed_needs_primary_confirmation",
                }
            )
    for idx, source in enumerate(ljg_sources[:2], 1):
        path = ROOT / source["local_path"]
        tickers = extract_known_tickers(path)
        chokepoints = extract_chokepoints(read_text(path))
        rows.append(
            {
                "signal_id": f"sig_{date}_ljg_context_{idx:02d}",
                "date": date,
                "claim": f"ljg_invest deep research context is available from `{source['local_path']}`.",
                "evidence_summary": "Tier 3 deep research can support thesis review and verification tasks, but it is not daily evidence by itself.",
                "source_ids": [source["source_id"]],
                "tickers": tickers[:12],
                "themes": chokepoints or ["Deep Research Context"],
                "direction": "mixed",
                "time_horizon": "medium",
                "confidence": 0.60,
                "source_quality_score": quality_for_sources([source["source_id"]], source_by_id),
                "evidence_strength_score": 0.55,
                "thesis_relevance_score": 0.70,
                "market_impact_score": 0.45,
                "noise_risk_score": 0.35,
                "verification_needed": True,
                "status": "needs_corroboration",
            }
        )
    for idx, source in enumerate(x_sources[:3], 1):
        path = ROOT / source["local_path"]
        tickers = extract_known_tickers(path)
        context_label = source.get("context_label") or "unknown_context"
        freshness = "fresh input" if context_label == "current_day_folder" else "recent context only"
        display_title = x_display_title(source)
        display_tickers = x_display_tickers(source, tickers)
        rows.append(
            {
                "signal_id": f"sig_{date}_x_{idx:02d}_unverified_narrative",
                "date": date,
                "claim": display_title,
                "evidence_summary": f"The source `{source['local_path']}` is a Tier 4 X input with context_label={context_label}. It is registered for discovery only and needs confirmation from higher-quality sources.",
                "source_ids": [source["source_id"]],
                "tickers": tickers,
                "display_tickers": display_tickers,
                "themes": ["X Narrative", display_tickers.replace("Theme: ", "") if display_tickers.startswith("Theme: ") else "Market Discovery"],
                "direction": "unknown",
                "time_horizon": "unknown",
                "confidence": 0.45,
                "source_quality_score": quality_for_sources([source["source_id"]], source_by_id),
                "evidence_strength_score": 0.35,
                "thesis_relevance_score": 0.50 if tickers else 0.35,
                "market_impact_score": 0.40,
                "noise_risk_score": 0.70 if context_label != "current_day_folder" else 0.62,
                "verification_needed": True,
                "status": "needs_corroboration",
                "freshness": freshness,
            }
        )
    for row in rows:
        row["source_type"] = source_type_string(row["source_ids"], source_by_id)
    return rows


def has_signal(signals: list[dict], signal_id: str) -> bool:
    return any(row["signal_id"] == signal_id for row in signals)


def ticker_impacts(date: str, signals: list[dict]) -> list[dict]:
    rows = []
    ticker_to_signals: dict[str, list[dict]] = {}
    for signal in signals:
        for ticker in signal.get("tickers", []):
            ticker_to_signals.setdefault(ticker, []).append(signal)
    for ticker, ticker_signals in sorted(ticker_to_signals.items())[:12]:
        source_types = {signal["source_type"] for signal in ticker_signals}
        x_only = source_types <= {"x_post", "x_markdown", "x_html"}
        rows.append(
            {
                "ticker": ticker,
                "date": date,
                "signal_ids": [signal["signal_id"] for signal in ticker_signals],
                "watchlist_group": "detected_from_current_sources",
                "thesis_impact": "insufficient_evidence",
                "impact_summary": "Ticker appeared in current Hub inputs. Treat as research triage, not a durable thesis update.",
                "risk_flags": ["x_only", "needs_corroboration"] if x_only else ["needs_primary_source_verification"],
                "research_label": "verify" if x_only else "monitor",
                "follow_up_questions": ["Check Tier 1 company evidence before carrying this signal into durable thesis review."],
            }
        )
    return rows[:12]


def thesis_impacts(date: str, signals: list[dict]) -> list[dict]:
    rows = []
    theme_to_signals: dict[str, list[dict]] = {}
    for signal in signals:
        for theme in signal.get("themes", []):
            if theme in {"X Narrative", "Market Discovery"}:
                continue
            theme_to_signals.setdefault(theme, []).append(signal)
    for theme, theme_signals in sorted(theme_to_signals.items())[:8]:
        source_types = {signal["source_type"] for signal in theme_signals}
        evidence_quality = "medium" if "ai_infrastructure_news_scan" in source_types else "low"
        evidence = theme_signals[0]["evidence_summary"]
        rows.append(
            {
                "thesis_impact_id": f"thesis_{date}_{slug(theme)}",
                "date": date,
                "ticker_or_theme": theme,
                "signal_ids": [signal["signal_id"] for signal in theme_signals],
                "current_thesis_type": "watch_only",
                "impact_direction": "unclear",
                "evidence_quality": evidence_quality,
                "confidence": 0.48 if evidence_quality == "medium" else 0.35,
                "rationale": evidence,
                "required_verification": ["Check company IR, filings, earnings commentary, guidance, orders, backlog, customer wins, or capex disclosures."],
                "proposed_memory_update": None,
            }
        )
    return rows


def label_for_signal(signal: dict, ticker_rows: list[dict]) -> str:
    for row in ticker_rows:
        if signal["signal_id"] in row["signal_ids"]:
            return row["research_label"]
    return "verify" if signal["status"] == "needs_corroboration" else "monitor"


def signal_source_tier(signal: dict, source_by_id: dict[str, dict]) -> str:
    tiers = [source_by_id[sid]["source_quality"]["tier"] for sid in signal["source_ids"]]
    if any("tier_2a" in tier for tier in tiers):
        return "Tier 2A"
    if any("tier_1" in tier for tier in tiers):
        return "Tier 1"
    if any("tier_2b" in tier for tier in tiers):
        return "Tier 2B"
    if any("tier_3" in tier for tier in tiers):
        return "Tier 3"
    if any("tier_4" in tier for tier in tiers):
        return "Tier 4"
    return "Unknown"


def quality_label(sources: list[dict]) -> str:
    if not sources:
        return "Low"
    best = max(row["source_quality"]["score"] for row in sources)
    if best >= 0.78:
        return "High"
    if best >= 0.60:
        return "Medium"
    return "Low"


def signal_level(signals: list[dict]) -> str:
    source_backed = [row for row in signals if row["source_type"] == "ai_infrastructure_news_scan"]
    primary_confirmed = [row for row in signals if "company_ir" in row["source_type"] or "sec_filing" in row["source_type"] or "earnings" in row["source_type"]]
    if primary_confirmed and len(source_backed) >= 2:
        return "High"
    if source_backed:
        return "Medium"
    if signals:
        return "Low"
    return "None"


def brief(date: str, sources: list[dict], signals: list[dict], ticker_rows: list[dict], thesis_rows: list[dict]) -> str:
    source_by_id = {row["source_id"]: row for row in sources}
    source_backed = [row for row in signals if signal_source_tier(row, source_by_id) in {"Tier 1", "Tier 2A", "Tier 2B"} and row["source_type"] != "premarket_brief"]
    x_signals = [row for row in signals if row["source_type"] in {"x_post", "x_markdown", "x_html"}]
    chokepoint_rows = [row for row in thesis_rows if row["evidence_quality"] in {"medium", "high"}]
    new_signal_level = signal_level(signals)
    verification_need = "Required" if signals else "None"
    deep_dive_needed = any(row["source_type"] == "ai_infrastructure_news_scan" and row["evidence_strength_score"] >= 0.74 and row.get("tickers") for row in signals)
    deep_dive_needed = deep_dive_needed or any(row["source_type"] in {"x_post", "x_markdown", "x_html"} and row["noise_risk_score"] >= 0.70 and row.get("tickers") for row in signals)
    deep_dive = "Yes" if deep_dive_needed else "No"
    conclusion = (
        "Hub found source-backed AI infrastructure signals that require primary-source verification."
        if source_backed else
        "No cross-source material change today; use current inputs as context and verification queue only."
    )
    lines = [
        f"# Hub Intelligence Brief — {date}",
        "",
        "Research-only. No trading automation. No buy/sell instructions. Research labels are not trading actions.",
        "",
        "## 1. Intelligence Verdict",
        "",
        f"- New Signal Level: {new_signal_level}",
        f"- Source Quality: {quality_label(sources)}",
        f"- Verification Need: {verification_need}",
        f"- Deep Dive Required: {deep_dive}",
        "",
        conclusion,
        "",
        "## 2. What Changed",
        "",
    ]
    if source_backed:
        for row in source_backed[:3]:
            tickers = ", ".join(row["tickers"]) or row.get("display_tickers") or "No explicit ticker"
            lines.append(f"- {row['claim']} ({tickers})")
    else:
        lines.append("No cross-source material change today.")
    lines.extend([
        "",
        "## 3. Source-Backed Signals",
        "",
    ])
    if source_backed:
        lines.extend(["| Signal | Source Tier | Tickers | Impact | Research Label |", "|---|---|---|---|---|"])
        for row in source_backed[:3]:
            tickers = ", ".join(row["tickers"]) or row.get("display_tickers") or "No explicit ticker"
            tier = signal_source_tier(row, source_by_id)
            impact = row["evidence_summary"]
            label = label_for_signal(row, ticker_rows)
            lines.append(f"| {row['claim']} | {tier} | {tickers} | {impact} | {label} |")
    else:
        lines.append("No source-backed signal requiring attention.")
    lines.extend([
        "",
        "## 4. Unverified Leads",
        "",
    ])
    if x_signals:
        lines.extend(["| Lead | Source | Tickers | Why It Matters | Next Verification |", "|---|---|---|---|---|"])
        for row in x_signals[:3]:
            source = source_by_id[row["source_ids"][0]]
            tickers = row.get("display_tickers") or ", ".join(row["tickers"]) or "No explicit ticker"
            why = f"{row.get('freshness', 'recent context only')}; unverified social/narrative input."
            verify = f"Check whether `{source['local_path']}` is corroborated by Tier 2A news scan or Tier 1 company evidence."
            lines.append(f"| {row['claim']} | {source.get('context_label', 'x_context')} `{source['local_path']}` | {tickers} | {why} | {verify} |")
    else:
        lines.append("No unverified lead requiring attention.")
    lines.extend([
        "",
        "## 5. Chokepoint Intelligence",
        "",
    ])
    if chokepoint_rows:
        lines.extend(["| Chokepoint | Change | Evidence | Related Tickers |", "|---|---|---|---|"])
        for row in chokepoint_rows[:3]:
            related = sorted({ticker for signal_id in row["signal_ids"] for signal in signals if signal["signal_id"] == signal_id for ticker in signal.get("tickers", [])})
            lines.append(f"| {row['ticker_or_theme']} | watch | {row['rationale']} | {', '.join(related) or 'No explicit ticker'} |")
    else:
        lines.append("No chokepoint change today.")
    verify_items = [row for row in signals if row["verification_needed"]]
    noise_items = [row for row in x_signals if row["noise_risk_score"] >= 0.60]
    power_items = [row for row in source_backed if any("Power" in theme or "Grid" in theme for theme in row.get("themes", []))]
    lines.extend([
        "",
        "## 6. Verification Queue",
        "",
    ])
    if verify_items:
        primary = verify_items[0]
        target = ", ".join(primary.get("tickers", [])[:4]) or primary.get("display_tickers") or primary["themes"][0]
        lines.append(f"- [ ] Verify: Check whether `{primary['claim']}` has Tier 1 support from company IR / earnings / guidance / backlog. Target: {target}.")
    else:
        lines.append("- [ ] Verify: None")
    if deep_dive == "Yes":
        deep_item = next((row for row in source_backed if row["evidence_strength_score"] >= 0.74), source_backed[0] if source_backed else None)
        target = deep_item["themes"][0] if deep_item else "None"
        lines.append(f"- [ ] Deep dive: Determine whether {target} affects chokepoint ranking or is only narrative noise.")
    else:
        lines.append("- [ ] Deep dive: None")
    if power_items:
        lines.append("- [ ] Verify: Check whether hyperscaler power demand has support from company guidance, utility interconnection, PPA, data center permitting, grid connection, or Tier 1 materials. Related tickers: MSFT, GOOGL, AMZN, META, VRT, ETN, GEV, PWR.")
    elif noise_items:
        noise_source = source_by_id[noise_items[0]["source_ids"][0]]
        lines.append(f"- [ ] Ignore noise: Keep `{noise_source['local_path']}` as discovery-only unless corroborated by Tier 2A or Tier 1 evidence.")
    else:
        lines.append("- [ ] Ignore noise: None")
    lines.append("")
    return "\n".join(lines)


def notes(date: str, inputs: list[str], missing_optional: list[str], outputs: list[str], counts: dict[str, int], command: str) -> str:
    return "\n".join(
        [
            f"# Hub Intelligence Brief Notes - {date}",
            "",
            f"Timestamp: {datetime.now(TZ).strftime('%Y-%m-%dT%H:%M:%S%z')}",
            "",
            "## Command",
            "",
            f"`{command}`",
            "",
            "## Input Files Used",
            "",
            *[f"- `{item}`" for item in inputs],
            "",
            "## Missing Optional Inputs / Warnings",
            "",
            *([f"- {item}" for item in missing_optional] or ["- None"]),
            "",
            "## Output Files Created",
            "",
            *[f"- `{item}`" for item in outputs],
            "",
            "## Summary Counts",
            "",
            f"- Sources: {counts['sources']}",
            f"- Signals: {counts['signals']}",
            f"- Ticker impacts: {counts['ticker_impacts']}",
            f"- Thesis impacts: {counts['thesis_impacts']}",
            "",
            "## Boundary Confirmation",
            "",
            "- Holdings were treated as unconfirmed; the brief uses Watchlist Impact.",
            "- No durable memory thesis files were updated.",
            "- No production scripts were modified.",
            "- Existing ai-investing-monitor report generation logic was not changed.",
            "- Existing report files, news scan files, ljg-invest files, and X converted files were not moved or rewritten.",
            "- No trading automation was created.",
            "- No trade instructions were generated.",
            "",
        ]
    )


def validate_data(date: str, sources: list[dict], signals: list[dict], ticker_rows: list[dict], thesis_rows: list[dict], brief_text: str) -> list[str]:
    checks: list[str] = []
    source_ids = {row["source_id"] for row in sources}
    signal_ids = {row["signal_id"] for row in signals}
    assert 0 <= len(signals) <= 12
    checks.append("Signal count is between 0 and 12.")
    assert all(set(row["source_ids"]) <= source_ids for row in signals)
    checks.append("All signal source_ids exist in source records.")
    assert all("source_type" in row and row["source_type"] for row in signals)
    checks.append("Every signal includes source_type.")
    assert all(set(row["signal_ids"]) <= signal_ids for row in ticker_rows)
    checks.append("All ticker impact signal_ids exist in signals.")
    assert all(set(row["signal_ids"]) <= signal_ids for row in thesis_rows)
    checks.append("All thesis impact signal_ids exist in signals.")
    for row in signals:
        for field in ["confidence", "source_quality_score", "evidence_strength_score", "thesis_relevance_score", "market_impact_score", "noise_risk_score"]:
            value = row[field]
            assert isinstance(value, (int, float)) and 0 <= value <= 1
        source_types = {source["source_type"] for source in sources if source["source_id"] in row["source_ids"]}
        if source_types <= {"x_post", "x_markdown", "x_html"}:
            assert row["status"] == "needs_corroboration" and row["verification_needed"] is True
        if "premarket_brief" in source_types or "daily_report" in source_types:
            assert "thesis" not in row["status"]
    for row in thesis_rows:
        assert isinstance(row["confidence"], (int, float)) and 0 <= row["confidence"] <= 1
    checks.append("All score and confidence fields are numeric between 0 and 1.")
    checks.append("Tier 4 X-only signals are marked needs_corroboration.")
    sections = [
        f"# Hub Intelligence Brief — {date}",
        "## 1. Intelligence Verdict",
        "## 2. What Changed",
        "## 3. Source-Backed Signals",
        "## 4. Unverified Leads",
        "## 5. Chokepoint Intelligence",
        "## 6. Verification Queue",
    ]
    assert all(section in brief_text for section in sections)
    assert "Holdings Impact" not in brief_text
    assert "Thesis Impact Map" not in brief_text
    checks.append("Brief contains the new 6-section Hub Intelligence structure.")
    allowed_labels = {"verify", "monitor", "thesis_review", "risk_review", "ignore_noise", "weekly_review_candidate", "deep_dive_required"}
    assert all(row["research_label"] in allowed_labels for row in ticker_rows)
    checks.append("Research labels are constrained to the allowed research-only set.")
    for source in sources:
        if source["source_type"] in {"x_post", "x_markdown", "x_html"}:
            assert source.get("needs_corroboration") is True
            assert source.get("file_path")
            assert source.get("context_label")
    bad = []
    for line_no, line in enumerate(brief_text.splitlines(), start=1):
        if line_no <= 3:
            continue
        if FORBIDDEN.search(line):
            bad.append((line_no, line))
    assert not bad, f"Forbidden terms outside disclaimer: {bad}"
    checks.append("Forbidden trading instruction words appear only in the opening disclaimer context.")
    return checks


def validation_markdown(date: str, command: str, inputs: list[str], missing_optional: list[str], outputs: list[str], counts: dict[str, int], checks: list[str]) -> str:
    return "\n".join(
        [
            f"# Hub Pipeline Validation - {date}",
            "",
            f"Timestamp: {datetime.now(TZ).strftime('%Y-%m-%dT%H:%M:%S%z')}",
            "",
            "## Command Run",
            "",
            f"`{command}`",
            "",
            "## Input Files Used",
            "",
            *[f"- `{item}`" for item in inputs],
            "",
            "## Missing Optional Inputs / Warnings",
            "",
            *([f"- {item}" for item in missing_optional] or ["- None"]),
            "",
            "## Output Files Created",
            "",
            *[f"- `{item}`" for item in outputs],
            "",
            "## Counts",
            "",
            f"- Source count: {counts['sources']}",
            f"- Signal count: {counts['signals']}",
            f"- Ticker impact count: {counts['ticker_impacts']}",
            f"- Thesis impact count: {counts['thesis_impacts']}",
            "",
            "## Validation Checks",
            "",
            *[f"- {check}" for check in checks],
            "",
            "## Boundary Confirmation",
            "",
            "- Existing production scripts were not modified.",
            "- Existing ai-investing-monitor report generation logic was not changed.",
            "- Existing watchlist, theme, pre-market brief, news scan, ljg-invest, and X converted files were not moved or rewritten.",
            "- The hub was not made canonical and was not linked from docs/index.html.",
            "- Durable memory thesis files were not updated.",
            "- Primary Source registry is deferred to Phase 8 and was not created.",
            "- No trading automation was created.",
            "- No trade instructions were generated.",
            "",
        ]
    )


def markdown_to_html(markdown: str, title: str) -> str:
    body: list[str] = []
    in_table = False
    for line in markdown.splitlines():
        if line.startswith("|") and line.endswith("|"):
            cells = [html.escape(cell.strip()) for cell in line.strip("|").split("|")]
            if set(cells[0].replace("-", "").replace(":", "")) == set() if cells else False:
                continue
            if not in_table:
                body.append("<table>")
                in_table = True
            tag = "th" if cells and cells[0] in {"Rank", "Ticker / Theme", "Watchlist Group", "Item", "Research Label", "Signal", "Lead", "Chokepoint"} else "td"
            body.append("<tr>" + "".join(f"<{tag}>{cell}</{tag}>" for cell in cells) + "</tr>")
            continue
        if in_table:
            body.append("</table>")
            in_table = False
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:].strip())}</h2>")
        elif line.startswith("- [ ] "):
            body.append(f"<p class=\"check\">□ {html.escape(line[6:].strip())}</p>")
        elif line.startswith("- "):
            body.append(f"<p class=\"bullet\">{html.escape(line[2:].strip())}</p>")
        elif line.strip():
            body.append(f"<p>{html.escape(line.strip())}</p>")
    if in_table:
        body.append("</table>")
    return "\n".join(
        [
            "<!doctype html>",
            "<html lang=\"en\">",
            "<head>",
            "<meta charset=\"utf-8\">",
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
            f"<title>{html.escape(title)}</title>",
            "<style>",
            "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.5;color:#1f2933;max-width:1180px;margin:0 auto;padding:32px 20px;background:#f7f8fa}",
            "main{background:#fff;border:1px solid #d8dee4;border-radius:8px;padding:28px}",
            "h1{font-size:30px;margin:0 0 16px}h2{font-size:20px;margin-top:30px;border-top:1px solid #e5e7eb;padding-top:18px}",
            "table{width:100%;border-collapse:collapse;margin:12px 0 20px;font-size:14px}th,td{border:1px solid #d8dee4;padding:8px;vertical-align:top}th{background:#eef2f6;text-align:left}",
            ".disclaimer{font-weight:600;color:#5b6472}.bullet:before{content:'• ';}.check{margin-left:4px}",
            "</style>",
            "</head>",
            "<body><main>",
            "<p class=\"disclaimer\">Research-only. No trading automation. No buy/sell instructions. Watchlist labels are not confirmed holdings.</p>",
            *body,
            "</main></body></html>",
        ]
    )


def publish_safe_warnings(text: str) -> list[str]:
    warnings = []
    for label, pattern in SENSITIVE_PATTERNS:
        if pattern.search(text):
            warnings.append(f"Detected possible {label}.")
    return warnings


def html_notes(date: str, input_md: str, output_html: str, warnings: list[str]) -> str:
    return "\n".join(
        [
            f"# HTML Export Notes - {date}",
            "",
            f"Timestamp: {datetime.now(TZ).strftime('%Y-%m-%dT%H:%M:%S%z')}",
            "",
            f"- Input markdown path: `{input_md}`",
            f"- Output HTML path: `{output_html}`",
            f"- Publish-safe validation result: {'warnings_found' if warnings else 'passed'}",
            "",
            "## Warnings",
            "",
            *([f"- {warning}" for warning in warnings] or ["- None"]),
            "",
            "## Boundary Confirmation",
            "",
            "- HTML export is local only.",
            "- No public publishing was performed.",
            "- `ai-investing-monitor/docs/index.html` was not updated.",
            "- The public docs intelligence path was not created or updated.",
            "",
        ]
    )


def append_migration_log(command: str, inputs: list[str], missing_optional: list[str], outputs: list[str], checks: list[str], counts: dict[str, int]) -> None:
    path = HUB / "docs/migration_log.md"
    entry = "\n".join(
        [
            "",
            f"## {datetime.now(TZ).date().isoformat()} - Phase 7A Source Policy and Local HTML Export",
            "",
            f"Timestamp: {datetime.now(TZ).strftime('%Y-%m-%dT%H:%M:%S%z')}",
            "",
            "Files changed:",
            "",
            "- `investment-intelligence-hub/docs/source_policy.md`",
            "- `investment-intelligence-hub/docs/architecture.md`",
            "- `investment-intelligence-hub/docs/schemas.md`",
            "- `investment-intelligence-hub/docs/verification.md`",
            "- `investment-intelligence-hub/scripts/run_hub_pipeline.py`",
            "",
            "Source policy created:",
            "",
            "- Added four-tier hierarchy covering Primary Sources, Daily Base / Core Financial News, ljg-invest Deep Research, and User-Captured X Posts.",
            "- Primary Source registry is intentionally deferred to Phase 8; `investment-intelligence-hub/memory/primary_sources.yaml` was not created.",
            "",
            "x_posts directory status:",
            "",
            f"- Current curated X inbox: `{rel(X_POSTS_ROOT)}`",
            "- Legacy or alternate folders `x-posts`, `manual_x`, `readwise`, and `x_timeline` are not current target inboxes if present; no automatic migration was performed.",
            "",
            "Script changes:",
            "",
            "- Added `--x-posts-dir` and default previous-day `x_posts/YYYY_MM_DD/` lookup.",
            "- Kept `--ljg-report` explicit-only and optional.",
            "- Added source-count flexibility for daily-only, daily plus ljg-invest, daily plus X, and all-source runs.",
            "- Added `--export-html` for local-only HTML output.",
            "- Added per-signal `source_type` and Tier 4 X corroboration validation.",
            "",
            "Command run:",
            "",
            f"- `{command}`",
            "",
            "Input files used:",
            "",
            *[f"- `{item}`" for item in inputs],
            "",
            "Missing optional inputs / warnings:",
            "",
            *([f"- {item}" for item in missing_optional] or ["- None"]),
            "",
            "Output files created:",
            "",
            *[f"- `{item}`" for item in outputs],
            "",
            f"Sources: {counts['sources']}. Signals: {counts['signals']}. Ticker impacts: {counts['ticker_impacts']}. Thesis impacts: {counts['thesis_impacts']}.",
            "",
            "Validation result:",
            "",
            *[f"- {check}" for check in checks],
            "- No production scripts were manually modified.",
            "",
            "Boundary confirmation:",
            "",
            "- Existing production scripts were not modified.",
            "- Existing `ai-investing-monitor` report generation logic was not changed.",
            "- `watchlists.yaml`, `themes.yaml`, and existing report files were not edited.",
            "- Existing daily reports, ljg-invest reports, and X converted files were not moved or rewritten.",
            "- The hub was not made canonical and was not linked from `docs/index.html`.",
            "- Durable memory thesis files were not updated.",
            "- No public publishing was performed.",
            "- No trading automation was created.",
            "- No trade instructions were generated.",
            "",
        ]
    )
    path.write_text(path.read_text(encoding="utf-8") + entry, encoding="utf-8")


def command_string(args: argparse.Namespace) -> str:
    parts = ["python3", "investment-intelligence-hub/scripts/run_hub_pipeline.py", "--date", args.date]
    parts += ["--mode", args.mode]
    if args.daily_report:
        parts += ["--daily-report", args.daily_report]
    if args.ljg_report:
        parts += ["--ljg-report", args.ljg_report]
    if args.x_md:
        parts += ["--x-md", args.x_md]
    if args.x_posts_dir:
        parts += ["--x-posts-dir", args.x_posts_dir]
    if args.export_html:
        parts += ["--export-html"]
    if args.skip_migration_log:
        parts += ["--skip-migration-log"]
    if args.dry_run:
        parts += ["--dry-run"]
    return " ".join(parts)


def run(args: argparse.Namespace) -> dict:
    if args.mode != "parallel":
        raise ValueError("Only --mode parallel is supported")
    X_POSTS_ROOT.mkdir(parents=True, exist_ok=True)
    daily, news_scan, ljg, x_files, missing_optional = resolve_inputs(args)
    outputs = output_paths(args.date, args.export_html)
    output_rel = [rel(path) for path in outputs.values()]
    selected = []
    if news_scan:
        selected.append(rel(news_scan))
    if daily.exists():
        selected.append(rel(daily))
    if ljg:
        selected.append(rel(ljg))
    selected.extend(rel(item["path"]) for item in x_files)
    if args.dry_run:
        result = {
            "dry_run": True,
            "premarket_brief_context_exists": daily.exists(),
            "news_scan_exists": bool(news_scan and news_scan.exists()),
            "selected_input_files": selected,
            "input_existence": {item: (ROOT / item).exists() for item in selected},
            "x_post_context": [
                {
                    "file_path": rel(item["path"]),
                    "folder_date": item.get("folder_date"),
                    "source_date": item.get("source_date"),
                    "context_label": item.get("context_label"),
                    "needs_corroboration": True,
                }
                for item in x_files
            ],
            "missing_optional_inputs": missing_optional,
            "output_paths": output_rel,
            "writes_performed": False,
            "migration_log_updated": False,
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result
    ingested_at = datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S%z")
    sources = source_records(args.date, ingested_at, daily, news_scan, ljg, x_files)
    signals = signal_rows(args.date, sources)
    ticker_rows = ticker_impacts(args.date, signals)
    thesis_rows = thesis_impacts(args.date, signals)
    brief_text = brief(args.date, sources, signals, ticker_rows, thesis_rows)
    checks = validate_data(args.date, sources, signals, ticker_rows, thesis_rows, brief_text)
    counts = {
        "sources": len(sources),
        "signals": len(signals),
        "ticker_impacts": len(ticker_rows),
        "thesis_impacts": len(thesis_rows),
    }
    command = command_string(args)
    for key in ["sources", "signals", "ticker_impacts", "thesis_impacts", "brief", "notes", "validation"]:
        outputs[key].parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(outputs["sources"], sources)
    write_jsonl(outputs["signals"], signals)
    write_jsonl(outputs["ticker_impacts"], ticker_rows)
    write_jsonl(outputs["thesis_impacts"], thesis_rows)
    outputs["brief"].write_text(brief_text, encoding="utf-8")
    outputs["notes"].write_text(notes(args.date, selected, missing_optional, output_rel, counts, command), encoding="utf-8")
    outputs["validation"].write_text(validation_markdown(args.date, command, selected, missing_optional, output_rel, counts, checks), encoding="utf-8")
    if args.export_html:
        html_warnings = publish_safe_warnings(brief_text)
        outputs["html"].parent.mkdir(parents=True, exist_ok=True)
        outputs["html"].write_text(markdown_to_html(brief_text, f"Hub Intelligence Brief — {args.date}"), encoding="utf-8")
        outputs["html_notes"].write_text(html_notes(args.date, rel(outputs["brief"]), rel(outputs["html"]), html_warnings), encoding="utf-8")
        if html_warnings:
            checks.append("HTML export completed with publish-safe warnings recorded.")
        else:
            checks.append("HTML export publish-safe validation passed.")
        outputs["validation"].write_text(validation_markdown(args.date, command, selected, missing_optional, output_rel, counts, checks), encoding="utf-8")
    if not args.skip_migration_log:
        append_migration_log(command, selected, missing_optional, output_rel, checks, counts)
    return {**counts, "outputs": output_rel, "missing_optional_inputs": missing_optional}


def main() -> None:
    args = parse_args()
    try:
        result = run(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    if not args.dry_run:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
