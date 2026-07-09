# Investment Intelligence Hub Schemas

Date: 2026-06-17

These schemas describe the current Hub Intelligence Brief data contract. They are documentation and implementation guidance; code should be checked against this file before changing ingestion or output behavior.

## Source Record

Recommended file: `processed/sources/YYYY-MM-DD.jsonl`

```json
{
  "source_id": "src_2026-06-17_ai_infrastructure_news_scan_001",
  "source_type": "ai_infrastructure_news_scan",
  "title": "AI Infrastructure News Scan — 2026-06-17",
  "author_or_origin": "ai-investing-monitor",
  "url": "docs/news/2026-06-17.html",
  "local_path": "investment-intelligence-hub/inbox/news/2026-06-17_ai_infrastructure_news.md",
  "published_at": "2026-06-17",
  "ingested_at": "2026-06-17T08:30:00-04:00",
  "source_quality": {
    "tier": "tier_2a_ai_infrastructure_news_scan",
    "score": 0.78,
    "reason": "Independent AI infrastructure news scan used for fresh signal detection and verification queue."
  },
  "content_hash": "sha256:...",
  "provenance_notes": "Can trigger source-backed Hub signals, but durable thesis confirmation still requires Tier 1 evidence or explicit human approval.",
  "status": "ingested"
}
```

Allowed `source_type` values:

- `ai_infrastructure_news_scan`
- `premarket_brief`
- `serenity_chokepoint_report`
- `ticker_infocard`
- `hub_intelligence_brief`
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

Bookmark, timeline, automatic-following, and viral-social source categories are intentionally absent from the current Hub source-type list.

## X Posts Folder Logic

The curated Hub X inbox is date-folder based:

```text
investment-intelligence-hub/inbox/x_posts/YYYY_MM_DD/
```

File formats:

```text
YYYYMMDD_slug.md
YYYYMMDD_slug.html
```

Examples:

```text
investment-intelligence-hub/inbox/x_posts/2026_06_17/20260617_smh-4.md
investment-intelligence-hub/inbox/x_posts/2026_06_17/20260616_citrini-research-smh-ai.md
```

Recommended X source fields:

```json
{
  "source_id": "src_2026-06-17_x_post_20260616_citrini_research_smh_ai",
  "source_type": "x_post",
  "folder_date": "2026-06-17",
  "source_date": "2026-06-16",
  "file_path": "investment-intelligence-hub/inbox/x_posts/2026_06_17/20260616_citrini-research-smh-ai.md",
  "status": "needs_corroboration",
  "needs_corroboration": true,
  "context_label": "current_day_folder"
}
```

Rules:

- `folder_date` comes from the `YYYY_MM_DD` folder name and represents user archive / processing date.
- `source_date` comes from the first 8 filename characters when present.
- If `folder_date` and `source_date` differ, do not move the file and do not fail ingestion.
- Default Hub input is the run-date folder.
- If the run-date folder is missing or empty, Hub may read the most recent 1-2 folders.
- Recent-folder fallback must be labeled `recent_context` or `carry_forward`, not fresh signal.
- Root-level files directly under `investment-intelligence-hub/inbox/x_posts/` are temporary / compatibility inputs only and are not formal default input.

## Extracted Signal

Recommended file: `processed/signals/YYYY-MM-DD.jsonl`

```json
{
  "signal_id": "sig_2026-06-17_news_scan_optical_interconnect_001",
  "date": "2026-06-17",
  "claim": "Optical interconnect demand showed a new source-backed signal in today's AI infrastructure news scan.",
  "evidence_summary": "Tier 2A news scan identified a relevant development; still requires company, customer, or Tier 1 confirmation before durable thesis use.",
  "source_ids": ["src_2026-06-17_ai_infrastructure_news_scan_001"],
  "source_type": "ai_infrastructure_news_scan",
  "source_tier": "Tier 2A",
  "tickers": ["AAOI", "CIEN", "COHR"],
  "themes": ["Optical Interconnect", "AI Infrastructure"],
  "direction": "constructive",
  "time_horizon": "short",
  "confidence": 0.70,
  "source_quality_score": 0.78,
  "evidence_strength_score": 0.65,
  "thesis_relevance_score": 0.75,
  "market_impact_score": 0.55,
  "noise_risk_score": 0.30,
  "verification_needed": true,
  "status": "source_backed_needs_primary_confirmation",
  "research_label": "verify"
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
- `source_backed_needs_primary_confirmation`
- `needs_corroboration`
- `watch_only`
- `noise_candidate`
- `rejected`

## Ticker Impact

Recommended file: `processed/ticker_impacts/YYYY-MM-DD.jsonl`

```json
{
  "ticker": "MRVL",
  "date": "2026-06-17",
  "signal_ids": ["sig_2026-06-17_news_scan_networking_001"],
  "watchlist_group": "core_or_watchlist",
  "thesis_impact": "insufficient_evidence",
  "impact_summary": "Relevant to AI networking thesis, but not enough to update durable thesis without company, customer, or earnings evidence.",
  "risk_flags": ["needs_primary_source_verification"],
  "research_label": "verify",
  "follow_up_questions": [
    "Is there company or customer evidence that this signal affects revenue, orders, backlog, margin, or capex exposure?",
    "Does a Tier 1 source confirm or contradict the media signal?"
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

## Research Label

These are research workflow labels only. They are not trading instructions.

Allowed labels:

| Label | Meaning |
|---|---|
| `verify` | Needs source confirmation before it can affect a thesis. |
| `monitor` | Worth tracking but no immediate thesis change. |
| `thesis_review` | May strengthen or weaken a durable thesis after evidence review. |
| `risk_review` | Could indicate elevated business, valuation, dilution, customer, supply-chain, or narrative risk. |
| `ignore_noise` | Low-quality, repetitive, or unsupported item. |
| `weekly_review_candidate` | Not urgent daily, but useful for weekly pattern review. |
| `deep_dive_required` | Requires a separate single-ticker or theme deep dive. |

Forbidden outputs:

- `buy`
- `sell`
- `trim`
- `add`
- `position size change`
- `price target`

## Hub Intelligence Brief

Recommended file: `reports/daily_intelligence/YYYY-MM-DD.md`

```markdown
# Hub Intelligence Brief — YYYY-MM-DD

## 1. Intelligence Verdict

- New Signal Level: None / Low / Medium / High
- Source Quality: Low / Medium / High
- Verification Need: None / Watch / Required
- Deep Dive Required: Yes / No

One-sentence conclusion.

## 2. What Changed

Only real new cross-source changes.

If no material change:

No cross-source material change today.

## 3. Source-Backed Signals

Only signals supported by Tier 1, Tier 2A, or relevant Tier 2B context.

| Signal | Source Tier | Tickers | Impact | Research Label |
|---|---|---|---|---|

If none:

No source-backed signal requiring attention.

## 4. Unverified Leads

Only X posts or speculative ideas.

| Lead | Source | Tickers | Why It Matters | Next Verification |
|---|---|---|---|---|

If none:

No unverified lead requiring attention.

## 5. Chokepoint Intelligence

Only changed chokepoints. Do not repeat long-term rankings without new evidence.

| Chokepoint | Change | Evidence | Related Tickers |
|---|---|---|---|

If none:

No chokepoint change today.

## 6. Verification Queue

- [ ] Verify:
- [ ] Deep dive:
- [ ] Ignore noise:
```

The Hub Intelligence Brief should be concise. It should avoid repeating stock company descriptions, long-term AI infrastructure background, or content already covered in the 8:15 Pre-Market Brief unless it is directly relevant to cross-source triage.
