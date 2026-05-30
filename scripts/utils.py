from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


ROOT = Path(__file__).resolve().parents[1]
REPORT_TZ = ZoneInfo("America/New_York")


def load_yaml(path: str) -> dict:
    with (ROOT / path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def today_est() -> str:
    return datetime.now(REPORT_TZ).date().isoformat()


def fetch_timestamp() -> str:
    return datetime.now(REPORT_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")


def ensure_dirs() -> None:
    for path in [
        "reports/daily",
        "reports/chatgpt_handoff",
        "reports/raw_data",
        "docs/reports",
    ]:
        (ROOT / path).mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def report_base_url() -> str:
    configured = env("REPORT_BASE_URL")
    if configured:
        return configured.rstrip("/")
    repository = env("GITHUB_REPOSITORY")
    if repository and "/" in repository:
        owner, repo = repository.split("/", 1)
        return f"https://{owner}.github.io/{repo}/reports"
    return ""


def pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:+.2f}%"


def money(value: float | None) -> str:
    if value is None:
        return "N/A"
    if value >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value:,.2f}"


def number(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.0f}"


def safe_float(value) -> float | None:
    try:
        if value is None:
            return None
        if hasattr(value, "item"):
            value = value.item()
        if value != value:
            return None
        return float(value)
    except Exception:
        return None
