# Investment Intelligence Hub Source Policy

Date: 2026-06-17

This policy defines how the Hub treats input quality and what each source tier is allowed to support.

The core rule is:

```text
Evidence > news > context > narrative.
```

## Tier 1: Primary Sources

Examples:

- Company IR pages
- Earnings releases
- Earnings call transcripts
- SEC filings
- Investor presentations
- Official guidance, orders, backlog, capex, capacity, or customer disclosures

Default `source_quality_score`: `0.85` to `0.95`

Allowed use:

- Confirm or reject claims from lower-tier sources
- Support durable investment thesis review
- Support durable memory update proposals after human review
- Resolve conflicts between company evidence and external media

Rule:

- Tier 1 is the highest-priority evidence class.
- Durable thesis changes require Tier 1 evidence or explicit human approval.

## Tier 2A: AI Infrastructure News Scan

Examples:

- `investment-intelligence-hub/inbox/news/YYYY-MM-DD_ai_infrastructure_news.md`
- Independent AI infrastructure news scan output

Default `source_quality_score`: `0.70` to `0.85`

Allowed use:

- Fresh signal detection
- `monitor`
- `risk_review`
- Verification queue
- Chokepoint intelligence
- Source-backed Hub signals

Rule:

- Tier 2A can trigger a Hub Intelligence Brief source-backed signal.
- Tier 2A cannot alone confirm a durable investment thesis.
- Durable thesis confirmation still requires Tier 1 evidence or explicit human approval.

## Tier 2B: Core Market / Financial Context

Examples:

- 8:15 Pre-Market Brief
- Yahoo Finance
- CNBC
- Price, volume, and market news context
- Macro context relevant to technology valuation

Default `source_quality_score`: `0.55` to `0.75`

Allowed use:

- Market regime context
- AI infrastructure score context
- Portfolio alert context
- Daily risk discipline
- `monitor`
- `risk_review`

Pre-Market Brief rule:

- The Pre-Market Brief is a context-only source.
- It must not be used as independent evidence for thesis changes.
- It must not be mined for repeated long-term ticker logic.
- It must not become the Hub's main source.

General Tier 2B rule:

- Tier 2B sources can support daily context and risk review.
- Tier 2B sources cannot alone update a durable investment thesis without Tier 1 confirmation or explicit human approval.

## Tier 3: ljg_invest Deep Research

Examples:

- `investment-intelligence-hub/reports/ljg_invest/`
- Explicitly approved current project ljg_invest report paths
- Deep-dive research notes

Default `source_quality_score`: `0.60` to `0.75`

Role:

- Periodic, quarterly, or event-driven input
- Not a daily required input
- Creates thesis baseline, speculation thesis, `thesis_review`, and verification tasks

Rule:

- Tier 3 sources are thesis context, not daily evidence by default.
- Tier 3 sources cannot confirm a durable investment thesis without Primary Source verification.

## Tier 4: User-Captured X Posts

Examples:

- Files manually captured by the user and placed into `investment-intelligence-hub/inbox/x_posts/YYYY_MM_DD/`
- X long-form articles converted to Markdown or HTML by the user

Not supported:

- Readwise integration
- X Bookmarks API
- X Timeline fetching
- Following-list scraping
- Automatic X account monitoring

Default `source_quality_score`: `0.40` to `0.60`

Role:

- Early signal discovery
- Market narrative awareness
- Idea generation

Rules:

- Tier 4 X signals default to `needs_corroboration`.
- Tier 4 X sources cannot support a durable investment thesis alone.
- Tier 4 X sources cannot directly trigger trading advice.
- X content only becomes stronger if corroborated by Tier 1 or relevant Tier 2A / Tier 2B evidence.
- X content is for discovery and narrative awareness, not final truth.

## Research Labels

Allowed labels:

- `verify`
- `monitor`
- `thesis_review`
- `risk_review`
- `ignore_noise`
- `weekly_review_candidate`
- `deep_dive_required`

Forbidden outputs:

- `buy`
- `sell`
- `trim`
- `add`
- `position size change`
- `price target`
