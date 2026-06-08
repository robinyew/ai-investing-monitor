# Investment Intelligence Hub Schemas

Date: 2026-06-07

These schemas are copied from `IMPLEMENTATION_PLAN.md` for Phase 1 documentation only. They are not implemented yet.

## Source Record

Recommended file: `processed/sources/YYYY-MM-DD.jsonl`

```json
{
  "source_id": "src_20260607_daily_001",
  "source_type": "daily_report",
  "title": "AI 投资新闻日报 - 2026-06-05",
  "author_or_origin": "ai-investing-monitor",
  "url": "docs/reports/2026-06-05.html",
  "local_path": "ai-investing-monitor/reports/daily/2026-06-05.md",
  "published_at": "2026-06-05",
  "ingested_at": "2026-06-07T00:00:00-04:00",
  "source_quality": {
    "tier": "medium",
    "score": 0.65,
    "reason": "Generated from RSS/news metadata and yfinance raw snapshots."
  },
  "content_hash": "sha256:...",
  "provenance_notes": "Existing pre-market report used as input, not as final truth.",
  "status": "ingested"
}
```

Allowed `source_type` values:

- `daily_report`
- `daily_raw_prices`
- `daily_raw_news`
- `yahoo_finance`
- `cnbc`
- `ljg_invest_report`
- `x_post`
- `x_markdown`
- `x_html`
- `company_ir`
- `earnings_release`
- `earnings_call_transcript`
- `sec_filing`
- `investor_presentation`
- `official_guidance`
- `public_news`
- `other`

Bookmark, timeline, and viral-social source categories are intentionally absent from the current Hub source-type list.

## X Posts Folder Logic

The curated Hub X inbox is:

```text
investment-intelligence-hub/inbox/x_posts/
```

User-captured X post files should use one of these filename formats:

```text
YYYYMMDD_slug.md
YYYYMMDD_slug.html
```

Examples:

```text
20260607_hyperliquid.md
20260607_ai-24.md
20260606_spacex.md
```

The first 8 characters represent the capture or post date in `YYYYMMDD` format.

Archive folders use this format:

```text
YYYY_MM_DD
```

For run date `YYYY-MM-DD`:

- Daily report default path: `ai-investing-monitor/reports/daily/YYYY-MM-DD.md`
- Default X folder: `investment-intelligence-hub/inbox/x_posts/YYYY_MM_DD_OF_PREVIOUS_DAY/`

Example:

- Run date: `2026-06-08`
- Default X folder: `investment-intelligence-hub/inbox/x_posts/2026_06_07/`
- Preferred files: `20260607_*.md` and `20260607_*.html`

Root-level files under `investment-intelligence-hub/inbox/x_posts/` are considered newly captured current-day files and should not be read by default.

## Extracted Signal

Recommended file: `processed/signals/YYYY-MM-DD.jsonl`

```json
{
  "signal_id": "sig_20260607_001",
  "date": "2026-06-07",
  "claim": "Optical interconnect demand is becoming a bottleneck signal for AI data-center scaling.",
  "evidence_summary": "Daily report and X article both point to scale-out networking/optical constraints; needs confirmation from company or industry sources.",
  "source_ids": ["src_20260607_daily_001", "src_20260607_x_001"],
  "source_type": "daily_report,x_post",
  "tickers": ["NOK", "CIEN", "COHR", "AAOI", "MRVL", "AVGO"],
  "themes": ["Optical Interconnect", "Networking", "AI Infrastructure"],
  "direction": "constructive",
  "time_horizon": "medium",
  "confidence": 0.55,
  "source_quality_score": 0.45,
  "evidence_strength_score": 0.50,
  "thesis_relevance_score": 0.80,
  "market_impact_score": 0.60,
  "noise_risk_score": 0.55,
  "verification_needed": true,
  "status": "needs_corroboration"
}
```

Allowed `direction` values:

- `constructive`
- `negative`
- `mixed`
- `neutral`
- `unknown`

Allowed `status` values:

- `confirmed`
- `needs_corroboration`
- `watch_only`
- `noise_candidate`
- `rejected`

## Ticker Impact

Recommended file: `processed/ticker_impacts/YYYY-MM-DD.jsonl`

```json
{
  "ticker": "NOK",
  "date": "2026-06-07",
  "signal_ids": ["sig_20260607_001"],
  "watchlist_group": "key_observation",
  "thesis_impact": "supports_speculation_thesis",
  "impact_summary": "Potential relevance to AI scale-out networking narrative, but not yet enough to upgrade durable investment thesis.",
  "risk_flags": ["source_is_social", "needs_company_confirmation"],
  "research_label": "verify",
  "follow_up_questions": [
    "Is there company or customer evidence that AI data-center optical demand is material to NOK revenue?",
    "Is the signal already reflected in recent company guidance?"
  ]
}
```

Allowed `thesis_impact` values:

- `supports_investment_thesis`
- `weakens_investment_thesis`
- `supports_speculation_thesis`
- `weakens_speculation_thesis`
- `no_material_impact`
- `insufficient_evidence`

## Action Label

These are research workflow labels only. They are not trading instructions.

```json
{
  "label": "thesis_review",
  "definition": "Signal may change a durable thesis and needs human review.",
  "allowed_outputs": ["follow-up question", "source verification task", "memory update proposal"],
  "forbidden_outputs": ["buy", "sell", "trim", "add", "position size change", "price target"]
}
```

Allowed action labels:

| Label | Meaning |
|---|---|
| `verify` | Needs source confirmation before it can affect a thesis. |
| `monitor` | Worth tracking but no immediate thesis change. |
| `thesis_review` | May strengthen or weaken a durable thesis. |
| `risk_review` | Could indicate elevated business, valuation, dilution, customer, supply-chain, or narrative risk. |
| `ignore_noise` | Low-quality, repetitive, or unsupported item. |
| `weekly_review_candidate` | Not urgent daily, but useful for weekly pattern review. |

## Daily Intelligence Brief

Recommended file: `reports/daily_intelligence/YYYY-MM-DD.md`

```markdown
# Investment Intelligence Brief - YYYY-MM-DD

## Executive Summary

- Top cross-source change:
- Most important thesis impact:
- Highest-quality source:
- Biggest unresolved verification question:

## Cross-Source Signal Table

| Signal | Tickers | Sources | Source Quality | Thesis Impact | Noise Risk | Research Label |
|---|---|---|---:|---|---:|---|

## Thesis Impact Map

| Ticker / Theme | Investment Thesis Impact | Speculation Thesis Impact | Evidence | Follow-up |
|---|---|---|---|---|

## Holdings / Watchlist Impact

| Group | Ticker | Impact | Risk Flag | Research Label |
|---|---|---|---|---|

## Noise / Hype Filter

| Item | Why filtered | What would confirm it |
|---|---|---|

## Follow-Up Checklist

- [ ] Verify:
- [ ] Read:
- [ ] Update memory proposal:
```
