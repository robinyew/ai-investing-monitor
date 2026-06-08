# Investment Intelligence Hub Source Policy

Date: 2026-06-07

This policy defines how the Hub treats input quality and what each source tier is allowed to support.

## Tier 1: Primary Sources

Examples:

- Company IR pages
- Earnings releases
- Earnings call transcripts
- SEC filings
- Investor presentations
- Official guidance, orders, backlog, capex, or similar company disclosures

Default `source_quality_score`: `0.85` to `0.95`

Allowed use:

- Confirm or reject claims from lower-tier sources
- Support durable investment thesis review
- Support durable memory update proposals after human review

Phase 8 may add a Primary Source registry for company IR, earnings, SEC filings, transcripts, and official guidance sources. Phase 7A does not create that registry.

## Tier 2: Daily Base / Core Financial News

Examples:

- Daily report
- Yahoo Finance
- CNBC
- Price, volume, and market news context

Default `source_quality_score`: `0.65` to `0.80`

Allowed use:

- Daily market context
- `risk_review`
- `monitor`
- `verify`
- Follow-up tasks

Rule:

- Tier 2 sources cannot alone update a durable investment thesis without Tier 1 confirmation or explicit human approval.

## Tier 3: ljg-invest Deep Research

Examples:

- `ljg-invest` reports
- Deep-dive research notes

Default `source_quality_score`: `0.60` to `0.75`

Role:

- Periodic, quarterly, or event-driven input
- Not a daily required input
- Creates thesis baseline, speculation thesis, `thesis_review`, and verification tasks

Rule:

- Tier 3 sources cannot confirm a durable investment thesis without Primary Source verification.

## Tier 4: User-Captured X Posts

Examples:

- Files manually captured by the user and placed into `investment-intelligence-hub/inbox/x_posts/`

Not supported in Phase 7A:

- Readwise integration
- X Bookmarks API
- X Timeline fetching
- Following-list scraping

Default `source_quality_score`: `0.40` to `0.60`

Role:

- Early signal discovery
- Market narrative awareness
- Idea generation

Rules:

- Tier 4 X signals must be marked `needs_corroboration` unless confirmed by Tier 1 or Tier 2.
- Tier 4 X sources cannot support a durable investment thesis alone.
- X content is for discovery and narrative awareness, not final truth.
