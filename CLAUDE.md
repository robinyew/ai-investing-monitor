# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

Cloud-based daily AI investing research monitor. Before US market open, it fetches previous-close prices, pre-market data, and news metadata, then generates Markdown + HTML reports published via GitHub Pages and a GitHub Issue notification. **Not a trading system** — no brokerage connections, no orders, no buy/sell signals. All tickers are watchlist items only.

## Running the Pipeline

```bash
# Install dependencies once
pip install -r requirements.txt

# Run the full pipeline locally
python scripts/run_daily_report.py
```

This single command runs the entire pipeline: fetch prices → fetch news → analyze moves → build Markdown brief → build ChatGPT handoff → build HTML report → update `docs/index.html`.

There are no tests and no linters configured in this project.

## Architecture

### Pipeline Flow

```
Cloudflare Worker (DST-aware cron scheduler)
    → GitHub Actions workflow_dispatch
        → python scripts/run_daily_report.py   ← single entry point
            ├── fetch_prices.py      (yfinance: OHLC, fundamentals, flags)
            ├── fetch_news.py        (feedparser: RSS headlines → ticker matching)
            ├── analyze_market_moves.py  (signals: tone, movers, risk flags, themes)
            ├── build_report.py      (Markdown brief + ChatGPT handoff, 1400+ lines)
            └── build_html.py        (Markdown→HTML, update docs/index.html)
```

GitHub Actions commits the generated output files back to the repo. GitHub Pages serves `docs/` as the static site.

### Configuration-Driven Design

All watchlist, theme, and source data lives in `config/` — change these without touching Python:

- `config/watchlists.yaml` — stock groups (core holdings, observations, benchmarks, high-risk) with labels, priorities, and `daily_focus` flags
- `config/themes.yaml` — investment themes (optical interconnect, power/liquid cooling, AI server, memory/HBM, cloud CapEx) each with related tickers
- `config/sources.yaml` — RSS feed URLs and source confidence tiers
- `config/report_settings.yaml` — timezone (EST), report URL, number of recent reports shown on index

To add/remove tickers, edit `config/watchlists.yaml` only — no Python changes needed.

### Two Reporting Systems

**1. Daily Pre-Market Pipeline** (`scripts/` + `.github/workflows/daily-report.yml`):
- Produces: `reports/daily/YYYY-MM-DD.md`, `reports/chatgpt_handoff/YYYY-MM-DD.md`, `docs/reports/YYYY-MM-DD.html`, `reports/raw_data/*.json`

**2. Investment Intelligence Hub** (`investment-intelligence-hub/`):
- Secondary layer that distills daily reports + deep research + user-captured X posts into research signals and thesis impacts
- Entry point: `investment-intelligence-hub/scripts/run_hub_pipeline.py`
- Triggered by `.github/workflows/publish-hub-intelligence.yml` (runs after daily report exists)
- Outputs to `docs/intelligence/`
- **Does not replace or modify the daily pipeline**

### Scheduling

The daily pipeline does not use GitHub Actions' built-in cron. Instead:
- Cloudflare Worker (`cloudflare-workers/investment-report-dispatcher/src/index.js`) fires at 08:15 and 08:30 EST/EDT, handling DST automatically
- It calls GitHub `workflow_dispatch` to trigger `daily-report.yml` and `publish-hub-intelligence.yml`

### Key Python Conventions

- `from __future__ import annotations` at the top of every script (PEP 563 deferred annotations)
- Typed dataclasses for structured data (`PriceRow` in `fetch_prices.py`)
- `safe_float()` in `utils.py` for NaN/None/numpy-safe float conversion — use this whenever handling yfinance numeric output
- `pathlib.Path` for all file operations
- `zoneinfo.ZoneInfo("America/New_York")` for timezone handling
- Graceful degradation: individual ticker/feed failures are caught and logged; the pipeline continues

### Intelligence Hub Source Tiers

When working in `investment-intelligence-hub/`, respect the source confidence hierarchy:

| Tier | Source | Confidence | Use |
|------|--------|-----------|-----|
| 1 | Company IR, SEC filings, earnings calls | 0.85–0.95 | Confirm durable thesis |
| 2 | Daily report, Yahoo Finance, CNBC | 0.65–0.80 | Daily context, risk review |
| 3 | Deep research notes | 0.60–0.75 | Periodic thesis baseline |
| 4 | User-captured X posts (`inbox/x_posts/`) | 0.40–0.60 | Discovery only, must be `needs_corroboration` |

X posts are treated as discovery/narrative awareness, never as confirmed facts.

## GitHub Actions Secrets

Optional secrets for features beyond the default GitHub Issue notification:

| Secret | Purpose |
|--------|---------|
| `REPORT_BASE_URL` | Override GitHub Pages URL in report links |
| `SMTP_HOST/PORT/USERNAME/PASSWORD` | Enable email via `scripts/send_email.py` |
| `EMAIL_FROM`, `EMAIL_TO` | Email recipients |
| `AI_MONITOR_SEND_EMAIL` | Repository variable, set to `true` to enable email |

Email is skipped silently if SMTP secrets are absent.
