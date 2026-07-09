# Investment Intelligence Hub Architecture

Date: 2026-06-17

## Purpose

The Investment Intelligence Hub is a cross-source intelligence triage layer for the AI infrastructure investing research workflow.

It is not another pre-market report. The 8:15 Pre-Market Brief is now the daily decision-discipline report: market regime score, AI infrastructure score, portfolio action score, material changes, chokepoint snapshot, portfolio alerts, and today's action. Hub Intelligence uses that brief as context only.

The Hub should answer:

- What changed across sources?
- Which signals are source-backed?
- Which signals are unverified leads?
- Which chokepoints changed?
- What needs verification or deep dive?

## Division Of Labor

| Output | Primary Job | Typical Use |
|---|---|---|
| Pre-Market Brief | Daily decision discipline | Today score, alerts, action posture, no-change logic |
| Hub Intelligence Brief | Cross-source signal triage | Source-backed signals, unverified leads, chokepoint changes, verification queue |
| Deep Dive | Single ticker or theme research | Serenity / TradingAgents / valuation / portfolio-fit research |

## Source Hierarchy

The Hub uses a tiered source policy so evidence, news, context, deep research, and social leads do not get mixed together.

| Tier | Source Class | Examples / Path | Default Source Quality | Allowed Use | Boundary |
|---|---|---|---:|---|---|
| Tier 1 | Primary Sources | Company IR, earnings releases, earnings call transcripts, SEC filings, investor presentations, official guidance / backlog / orders / capex disclosures | 0.85-0.95 | Confirm or reject claims; durable thesis review; highest-priority verification | Highest priority. Durable thesis changes require Tier 1 evidence or explicit human approval. |
| Tier 2A | AI Infrastructure News Scan | `investment-intelligence-hub/inbox/news/YYYY-MM-DD_ai_infrastructure_news.md` | 0.70-0.85 | Fresh AI infrastructure signal detection, `monitor`, `risk_review`, verification queue, chokepoint intelligence | Can trigger a Hub source-backed signal, but cannot alone confirm a durable investment thesis. |
| Tier 2B | Core Market / Financial Context | Pre-Market Brief, Yahoo Finance, CNBC, price / volume / macro context | 0.55-0.75 | Market regime context, AI infrastructure score context, portfolio alert context, daily risk discipline | Pre-Market Brief is context-only. It must not be used as independent thesis-confirming evidence. |
| Tier 3 | ljg_invest Deep Research | `investment-intelligence-hub/reports/ljg_invest/` and any explicitly approved current project path | 0.60-0.75 | Periodic thesis baseline, `thesis_review`, verification tasks, deep-dive context | Not a daily required input. Cannot alone confirm durable thesis. |
| Tier 4 | User-Captured X Posts | `investment-intelligence-hub/inbox/x_posts/YYYY_MM_DD/` | 0.40-0.60 | Discovery, narrative awareness, idea generation | Default `needs_corroboration`. Must not support durable thesis alone or trigger trading advice. |

## Current Inbox Structure

### AI Infrastructure News Scan

The independent news scan writes daily Markdown files here:

```text
investment-intelligence-hub/inbox/news/YYYY-MM-DD_ai_infrastructure_news.md
```

These files are Tier 2A sources. They can create source-backed Hub signals, risk review items, and chokepoint intelligence, but they still require Tier 1 confirmation for durable thesis changes.

### User-Captured X Posts

The curated Hub X inbox uses date folders:

```text
investment-intelligence-hub/inbox/x_posts/YYYY_MM_DD/
```

Examples:

```text
investment-intelligence-hub/inbox/x_posts/2026_06_17/20260617_smh-4.md
investment-intelligence-hub/inbox/x_posts/2026_06_17/20260616_citrini-research-smh-ai.md
```

Rules:

- `YYYY_MM_DD` folder date is the user archive / processing date.
- The first 8 filename characters, `YYYYMMDD`, represent the post date, capture date, or file generation date.
- If the filename date differs from the folder date, do not move the file and do not fail the run.
- Hub ingestion should record `folder_date`, `source_date`, and `file_path`.
- Default Hub input is the run-date folder.
- If the run-date folder is missing or empty, Hub may read the most recent 1-2 folders as recent context / carry-forward, and must label them as such.
- Root-level files directly under `x_posts/` are temporary / compatibility inputs only and are not formal default inputs.

X content is treated as discovery and narrative awareness, not final truth.

## Production Workflow Boundary

The existing `ai-investing-monitor/` production workflow remains preserved.

The Hub does not replace or rewrite:

- `scripts/run_daily_report.py`
- `scripts/build_report.py`
- `scripts/build_html.py`
- `config/watchlists.yaml`
- `config/themes.yaml`
- Existing daily reports
- Existing news scan reports
- Existing ljg_invest reports
- Existing X converted Markdown / HTML files

During migration, the Hub reads or references existing outputs only after they are already generated by the current workflow.

## Non-Goals

The Hub is not a trading system.

It must not:

- Connect to brokerage accounts
- Create orders
- Execute trades
- Add trading automation
- Generate buy / sell instructions
- Generate position-size changes
- Generate price targets
- Treat X posts as confirmed facts without corroboration

## Target Output

The target output is a concise, research-only Hub Intelligence Brief:

```markdown
# Hub Intelligence Brief — YYYY-MM-DD

## 1. Intelligence Verdict

- New Signal Level: None / Low / Medium / High
- Source Quality: Low / Medium / High
- Verification Need: None / Watch / Required
- Deep Dive Required: Yes / No

One-sentence conclusion.

## 2. What Changed

Only real new changes.

If no change:

No cross-source material change today.

## 3. Source-Backed Signals

| Signal | Source Tier | Tickers | Impact | Research Label |
|---|---|---|---|---|

## 4. Unverified Leads

| Lead | Source | Tickers | Why It Matters | Next Verification |
|---|---|---|---|---|

If none:

No unverified lead requiring attention.

## 5. Chokepoint Intelligence

| Chokepoint | Change | Evidence | Related Tickers |
|---|---|---|---|

If no change:

No chokepoint change today.

## 6. Verification Queue

- [ ] Verify:
- [ ] Deep dive:
- [ ] Ignore noise:
```

Allowed research labels are `verify`, `monitor`, `thesis_review`, `risk_review`, `ignore_noise`, `weekly_review_candidate`, and `deep_dive_required`.
