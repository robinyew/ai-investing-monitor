# Investment Intelligence Hub Migration Log

## 2026-06-07 - Phase 0 + Phase 1 Setup

Phase 0 baseline and safety check completed.

- Recorded current `ai-investing-monitor/` git status.
- Listed top-level workspace files and folders.
- Listed current report output directories.
- Ran the existing daily report command from `ai-investing-monitor/`.
- Confirmed the existing daily report system generated:
  - `reports/daily/2026-06-07.md`
  - `reports/chatgpt_handoff/2026-06-07.md`
  - `docs/reports/2026-06-07.html`
  - `reports/raw_data/latest_report.json`
  - `reports/raw_data/2026-06-07-news.json`
  - `reports/raw_data/2026-06-07-prices.json`
- Created baseline verification file at `/Users/leimingyu/Investment/investment-intelligence-hub-baseline.md`.

Phase 1 skeleton setup completed.

- Created the `investment-intelligence-hub/` directory skeleton.
- Added architecture, schema, verification, and migration documentation.
- Added placeholder memory files.

Boundary confirmation:

- No production scripts were manually modified.
- Existing `ai-investing-monitor` report generation logic was not changed.
- `watchlists.yaml` and `themes.yaml` were not edited.
- Existing daily reports, ljg-Invest reports, and X converted files were not moved or rewritten.
- Ingestion, extraction, scoring, and brief generation were not implemented.
- No trading automation was created.
- No buy/sell instructions were generated.

## 2026-06-07 - Phase 2 Sample Ingestion Fixtures

Timestamp: 2026-06-07T12:13:27-0400

Selected sample files:

- Daily report sample: `ai-investing-monitor/reports/daily/2026-06-07.md`
- ljg-Invest sample: `20260602T184149==z--投资分析-nok.org`
- X post sample: `x-to-markdown/artofspecuycky/2062623036722049427.md`

Output files created:

- `investment-intelligence-hub/processed/sources/sample.jsonl`
- `investment-intelligence-hub/inbox/sample_manifest.md`

Verification result:

- `sample.jsonl` exists.
- `sample.jsonl` contains exactly 3 JSON lines.
- Each line parses as valid JSON.
- Each `source_id` is unique.
- Each `local_path` exists.
- Each `content_hash` matches the current file content.
- No production scripts were manually modified.

Boundary confirmation:

- Existing daily reports, ljg-Invest reports, and X converted files were not moved or rewritten.
- Signal extraction, scoring, thesis mapping, portfolio mapping, and final brief generation were not implemented.
- No trading automation was created.
- No buy/sell instructions were generated.

## 2026-06-07 - Phase 3 Sample Signal Extraction Prototype

Timestamp: 2026-06-07T12:22:00-0400

Input file used:

- `investment-intelligence-hub/processed/sources/sample.jsonl`

Output files created:

- `investment-intelligence-hub/processed/signals/sample.jsonl`
- `investment-intelligence-hub/processed/signals/sample_extraction_notes.md`

Number of extracted signals: 8.

Validation result:

- `processed/signals/sample.jsonl` exists.
- It contains 8 JSON lines.
- Each line parses as valid JSON.
- Each `signal_id` is unique.
- Each signal references at least one valid `source_id` from `processed/sources/sample.jsonl`.
- All `direction` values are allowed.
- All `status` values are allowed.
- All score fields are numeric between 0 and 1.
- No forbidden trading instruction words appear in `claim` or `evidence_summary`.
- No production scripts were manually modified.

Boundary confirmation:

- Existing production scripts were not modified.
- Existing `ai-investing-monitor` report generation logic was not changed.
- `watchlists.yaml`, `themes.yaml`, and existing report files were not edited.
- Existing daily reports, ljg-Invest reports, and X converted files were not moved or rewritten.
- Scoring pipeline, thesis mapping, portfolio mapping, and final brief generation were not implemented.
- No trading automation was created.
- No trade instructions were generated.

## 2026-06-07 - Phase 7A Implementation Summary

Timestamp: 2026-06-07T18:20:46-0400

Files changed:

- `investment-intelligence-hub/docs/source_policy.md`
- `investment-intelligence-hub/docs/architecture.md`
- `investment-intelligence-hub/docs/schemas.md`
- `investment-intelligence-hub/docs/verification.md`
- `investment-intelligence-hub/docs/PHASE_7_PRECHECK.md`
- `investment-intelligence-hub/scripts/run_hub_pipeline.py`
- `investment-intelligence-hub/inbox/x_posts/2026_06_06/20260606_test_x_post.md`

Source policy created:

- Added four-tier source hierarchy.
- Documented that Primary Source registry is deferred to Phase 8.
- Confirmed `investment-intelligence-hub/memory/primary_sources.yaml` was not created.

x_posts directory status:

- Current target X inbox is `investment-intelligence-hub/inbox/x_posts/`.
- Previous-day archive lookup is implemented as `investment-intelligence-hub/inbox/x_posts/YYYY_MM_DD/`.
- Root-level `investment-intelligence-hub/inbox/x_posts/*.md` and `*.html` files are not read by default.
- Legacy or alternate folder names are not current target inboxes if present; no automatic migration was performed.
- Temporary Phase 7A test fixture created under Hub only: `investment-intelligence-hub/inbox/x_posts/2026_06_06/20260606_test_x_post.md`.

Script changes:

- Added `--x-posts-dir`.
- Added default previous-day `x_posts` archive lookup.
- Preserved explicit-only optional `--ljg-report`.
- Preserved explicit `--x-md`, mapped by extension to `x_markdown` or `x_html`.
- Added `--export-html` local-only output.
- Added per-signal `source_type` and Tier 4 X corroboration checks.
- Added local HTML export notes.

Tests run:

- Test A dry-run daily only: passed; no files written and migration log not updated by dry-run.
- Test B daily-only real run: passed; warned and continued when previous-day X folder was missing.
- Test C full explicit run with `ljg-report` and `x-md`: passed.
- Test D local HTML export: passed; wrote `investment-intelligence-hub/reports/daily_intelligence/html/2026-06-07.html` and `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_html_notes.md`.
- Test E previous-day `x_posts` default lookup: passed; read `investment-intelligence-hub/inbox/x_posts/2026_06_06/20260606_test_x_post.md` as `x_post` and did not read root-level `x_posts` files.

Validation result:

- `source_policy.md` exists.
- `architecture.md` includes Source Hierarchy.
- `schemas.md` includes required source types.
- `verification.md` includes source-policy and publish-safe checks.
- `investment-intelligence-hub/inbox/x_posts/` exists.
- JSONL outputs parse correctly.
- Signal source references are valid.
- Ticker impact signal references are valid.
- Thesis impact signal references are valid.
- Every signal includes `source_type`.
- Score and confidence fields are numeric between 0 and 1.
- Tier 4 X-only signals are marked `needs_corroboration`.
- Markdown brief contains all 7 sections and uses Watchlist Impact.
- HTML export file and HTML notes file exist.
- Forbidden trading instruction words appear only in disclaimer context.
- No production scripts were modified by Phase 7A work.

Boundary confirmation:

- Existing `ai-investing-monitor` production scripts were not modified.
- Existing `ai-investing-monitor` report generation logic was not changed.
- `watchlists.yaml`, `themes.yaml`, and existing report files were not edited.
- Existing daily reports, `ljg-invest` reports, and `x-to-markdown` files were not moved or rewritten.
- The Hub was not made canonical.
- `ai-investing-monitor/docs/index.html` was not updated.
- Public publishing to `ai-investing-monitor/docs/intelligence` remains deferred to Phase 7B.
- Durable memory thesis files were not updated.
- No public API, Readwise, X Bookmarks, X Timeline, or following-list scraping was added.
- No trading automation was created.
- No trade instructions were generated.

## 2026-06-07 - Phase 7B-1 Manual Publish Workflow

Timestamp: 2026-06-07T19:31:09-0400

Files created / changed:

- `investment-intelligence-hub/scripts/publish_hub_html.py`
- `ai-investing-monitor/.github/workflows/publish-hub-intelligence.yml`
- `ai-investing-monitor/docs/intelligence/2026-06-07.html`
- `ai-investing-monitor/docs/intelligence/index.html`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_publish_notes.md`
- `investment-intelligence-hub/docs/migration_log.md`

Publish helper script created:

- Added validation-gated local publish helper with `--date`, `--source-html`, `--docs-root`, `--publish`, and `--dry-run`.
- Default source: `investment-intelligence-hub/reports/daily_intelligence/html/YYYY-MM-DD.html`.
- Default target: `ai-investing-monitor/docs/intelligence/YYYY-MM-DD.html`.
- Default index: `ai-investing-monitor/docs/intelligence/index.html`.

Workflow created:

- Added manual `workflow_dispatch` workflow: `Publish Hub Intelligence Brief`.
- Added `publish` input with default `false`.
- Added `contents: write` permission.
- Added dry-run helper step before actual publish.
- Added commit/push steps gated by `publish == "true"`.
- No schedule trigger was added.

Tests run:

- Test 1: `python3 investment-intelligence-hub/scripts/run_hub_pipeline.py --date 2026-06-07 --mode parallel --export-html`
- Test 2: `python3 investment-intelligence-hub/scripts/publish_hub_html.py --date 2026-06-07 --dry-run`
- Test 3: `python3 investment-intelligence-hub/scripts/publish_hub_html.py --date 2026-06-07 --publish true`

Validation result:

- Hub HTML export exists.
- Publish helper dry-run passed validation and did not write public docs files.
- Actual local publish passed validation.
- Published local HTML exists at `ai-investing-monitor/docs/intelligence/2026-06-07.html`.
- Intelligence index exists at `ai-investing-monitor/docs/intelligence/index.html`.
- Publish notes exist at `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_publish_notes.md`.

Local publish test passed:

- Yes.

Public push performed:

- No. No git commit or git push was performed.

Boundary confirmation:

- No production report-generation scripts were modified.
- `ai-investing-monitor/scripts/run_daily_report.py` was not modified.
- `ai-investing-monitor/scripts/build_report.py` was not modified.
- `ai-investing-monitor/scripts/build_html.py` was not modified.
- `watchlists.yaml` and `themes.yaml` were not changed.
- Root `ai-investing-monitor/docs/index.html` was not changed by this phase.
- Existing daily reports were not modified.
- Existing `ljg-invest` reports were not modified.
- Existing `x-to-markdown` files were not modified.
- Cloudflare Worker Cron was not implemented.
- GitHub schedule was not added.
- No API integrations were added.
- Primary Source registry was not created.
- `ljg-invest` baseline automation was not created.
- No trading automation was created.
- No trade instructions were generated.

## 2026-06-07 - Phase 7A Test Fixture Cleanup

Timestamp: 2026-06-07T18:29:04-0400

File moved:

- From: `investment-intelligence-hub/inbox/x_posts/2026_06_06/20260606_test_x_post.md`
- To: `investment-intelligence-hub/test_fixtures/x_posts/2026_06_06/20260606_test_x_post.md`

Reason:

- Prevent the Phase 7A test X fixture from being included in future real Hub runs that default to `investment-intelligence-hub/inbox/x_posts/YYYY_MM_DD/`.

Boundary confirmation:

- Existing `ai-investing-monitor` production scripts were not modified.
- Existing `ai-investing-monitor` report generation logic was not changed.
- `watchlists.yaml`, `themes.yaml`, and existing report files were not edited.
- No public publishing was performed.
- No git commit or git push was performed.
- No trading automation was created.
- No trade instructions were generated.

## 2026-06-07 - Phase 4 Sample Scoring And Mapping Prototype

Timestamp: 2026-06-07T12:34:00-0400

Input files used:

- `investment-intelligence-hub/processed/sources/sample.jsonl`
- `investment-intelligence-hub/processed/signals/sample.jsonl`
- `ai-investing-monitor/config/watchlists.yaml` read only
- `investment-intelligence-hub/memory/portfolio_context.md` read only

Output files created:

- `investment-intelligence-hub/processed/ticker_impacts/sample.jsonl`
- `investment-intelligence-hub/processed/thesis_impacts/sample.jsonl`
- `investment-intelligence-hub/processed/ticker_impacts/sample_mapping_notes.md`

Number of ticker impact records: 5.

Number of thesis impact records: 5.

Validation result:

- `ticker_impacts/sample.jsonl` exists.
- `thesis_impacts/sample.jsonl` exists.
- Both files contain valid JSON lines.
- All referenced `signal_ids` exist in `processed/signals/sample.jsonl`.
- All `thesis_impact` values are allowed.
- All `research_label` values are allowed.
- All `current_thesis_type` values are allowed.
- All `impact_direction` values are allowed.
- All confidence values are numeric between 0 and 1.
- No forbidden trading instruction words appear in mapped summary fields.
- No production scripts were manually modified.

Boundary confirmation:

- Existing production scripts were not modified.
- Existing `ai-investing-monitor` report generation logic was not changed.
- `watchlists.yaml`, `themes.yaml`, and existing report files were not edited.
- Existing daily reports, ljg-Invest reports, and X converted files were not moved or rewritten.
- Final daily intelligence brief generation was not implemented.
- Durable memory thesis files were not updated.
- No trading automation was created.
- No trade instructions were generated.

## 2026-06-07 - Phase 5 Sample Daily Intelligence Brief

Timestamp: 2026-06-07T12:48:00-0400

Input files used:

- `investment-intelligence-hub/processed/sources/sample.jsonl`
- `investment-intelligence-hub/processed/signals/sample.jsonl`
- `investment-intelligence-hub/processed/ticker_impacts/sample.jsonl`
- `investment-intelligence-hub/processed/thesis_impacts/sample.jsonl`
- `investment-intelligence-hub/processed/signals/sample_extraction_notes.md`
- `investment-intelligence-hub/processed/ticker_impacts/sample_mapping_notes.md`

Output files created:

- `investment-intelligence-hub/reports/daily_intelligence/sample.md`
- `investment-intelligence-hub/reports/daily_intelligence/sample_brief_notes.md`

Validation result:

- `reports/daily_intelligence/sample.md` exists.
- All 7 required sections are present.
- The brief references sample signals, ticker impacts, and thesis impacts.
- The brief uses `Watchlist Impact` because holdings are unconfirmed.
- The brief includes a Noise / Hype Filter section.
- The brief includes a Follow-Up Checklist.
- Forbidden trading instruction words appear only in the opening disclaimer context.
- No production scripts were manually modified.

Boundary confirmation:

- Existing production scripts were not modified.
- Existing `ai-investing-monitor` report generation logic was not changed.
- `watchlists.yaml`, `themes.yaml`, and existing report files were not edited.
- Existing daily reports, ljg-Invest reports, and X converted files were not moved or rewritten.
- Durable memory thesis files were not updated.
- No trading automation was created.
- No trade instructions were generated.

## 2026-06-07 - Phase 6 Parallel Hub Run

Timestamp: 2026-06-07T12:57:25-0400

Command run:

- `python3 investment-intelligence-hub/scripts/run_hub_pipeline.py --date 2026-06-07 --mode parallel`

Input files used:

- `ai-investing-monitor/reports/daily/2026-06-07.md`
- `20260602T184149==z--投资分析-nok.org`
- `x-to-markdown/artofspecuycky/2062623036722049427.md`

Output files created:

- `investment-intelligence-hub/processed/sources/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/signals/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/ticker_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/thesis_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_notes.md`

Sources: 3. Signals: 8. Ticker impacts: 5. Thesis impacts: 5.

Validation result:

- Dated source, signal, ticker impact, thesis impact, brief, and notes files were created.
- JSONL files parse successfully and references are internally consistent.
- The brief contains all 7 required sections and uses Watchlist Impact because holdings are unconfirmed.
- Forbidden trading instruction words appear only in the opening disclaimer context.
- No production scripts were manually modified.

Boundary confirmation:

- Existing production scripts were not modified.
- Existing `ai-investing-monitor` report generation logic was not changed.
- `watchlists.yaml`, `themes.yaml`, and existing report files were not edited.
- Existing daily reports, ljg-Invest reports, and X converted files were not moved or rewritten.
- The hub was not made canonical and was not linked from `docs/index.html`.
- Durable memory thesis files were not updated.
- No trading automation was created.
- No trade instructions were generated.

## 2026-06-07 - Phase 7 Precheck Audit

Timestamp: 2026-06-07T17:43:49-0400

Files inspected:

- `investment-intelligence-hub/docs/architecture.md`
- `investment-intelligence-hub/docs/schemas.md`
- `investment-intelligence-hub/docs/verification.md`
- `investment-intelligence-hub/docs/migration_log.md`
- `investment-intelligence-hub/scripts/run_hub_pipeline.py`
- `investment-intelligence-hub/reports/daily_intelligence/*.md`
- `investment-intelligence-hub/processed/**/*.jsonl`
- `IMPLEMENTATION_PLAN.md`
- `ai-investing-monitor` git status

Report created:

- `investment-intelligence-hub/docs/PHASE_7_PRECHECK.md`

Files changed during this audit:

- `investment-intelligence-hub/docs/PHASE_7_PRECHECK.md`
- `investment-intelligence-hub/docs/migration_log.md`

Boundary confirmation:

- No production scripts were modified.
- Existing `ai-investing-monitor` report generation logic was not changed.
- `watchlists.yaml`, `themes.yaml`, and existing report files were not edited.
- Existing daily reports, ljg-Invest reports, and X converted files were not moved or rewritten.
- Publishing was not implemented.
- API integrations were not added.
- Durable memory thesis files were not updated.
- No trading automation was created.
- No trade instructions were generated.

## 2026-06-07 - Phase 6.5 Hub Pipeline Hardening

Timestamp: 2026-06-07T13:07:28-0400

Script changes:

- Added flexible CLI arguments for daily report, ljg-Invest report, and X Markdown input.
- Added dry-run mode that prints selected inputs and output paths without writing files.
- Replaced hardcoded optional-source IDs with date, source type, filename, and stable-hash based IDs.
- Added source-count flexibility for daily-only, daily plus ljg-Invest, daily plus X, and all-source runs.
- Added per-run validation markdown output.

Dry-run command tested:

- `python3 investment-intelligence-hub/scripts/run_hub_pipeline.py --date 2026-06-07 --dry-run`

Full run command tested:

- `python3 investment-intelligence-hub/scripts/run_hub_pipeline.py --date 2026-06-07 --mode parallel --daily-report ai-investing-monitor/reports/daily/2026-06-07.md --ljg-report 20260602T184149==z--投资分析-nok.org --x-md x-to-markdown/artofspecuycky/2062623036722049427.md`

Input files used:

- `ai-investing-monitor/reports/daily/2026-06-07.md`
- `20260602T184149==z--投资分析-nok.org`
- `x-to-markdown/artofspecuycky/2062623036722049427.md`

Missing optional inputs:

- None

Output files created:

- `investment-intelligence-hub/processed/sources/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/signals/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/ticker_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/thesis_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_notes.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_validation.md`

Sources: 3. Signals: 8. Ticker impacts: 5. Thesis impacts: 5.

Validation result:

- All signal source_ids exist in source records.
- All ticker impact signal_ids exist in signals.
- All thesis impact signal_ids exist in signals.
- All score and confidence fields are numeric between 0 and 1.
- Brief contains all 7 sections and uses Watchlist Impact.
- Forbidden trading instruction words appear only in the opening disclaimer context.
- No production scripts were manually modified.

Boundary confirmation:

- Existing production scripts were not modified.
- Existing `ai-investing-monitor` report generation logic was not changed.
- `watchlists.yaml`, `themes.yaml`, and existing report files were not edited.
- Existing daily reports, ljg-Invest reports, and X converted files were not moved or rewritten.
- The hub was not made canonical and was not linked from `docs/index.html`.
- Durable memory thesis files were not updated.
- No trading automation was created.
- No trade instructions were generated.

## 2026-06-07 - Phase 6.5 Hub Pipeline Hardening

Timestamp: 2026-06-07T13:16:07-0400

Script changes:

- Added flexible CLI arguments for daily report, ljg-Invest report, and X Markdown input.
- Added dry-run mode that prints selected inputs and output paths without writing files.
- Replaced hardcoded optional-source IDs with date, source type, filename, and stable-hash based IDs.
- Added source-count flexibility for daily-only, daily plus ljg-Invest, daily plus X, and all-source runs.
- Added per-run validation markdown output.

Dry-run command tested:

- `python3 investment-intelligence-hub/scripts/run_hub_pipeline.py --date 2026-06-07 --dry-run`

Full run command tested:

- `python3 investment-intelligence-hub/scripts/run_hub_pipeline.py --date 2026-06-07 --mode parallel --daily-report ai-investing-monitor/reports/daily/2026-06-07.md`

Input files used:

- `ai-investing-monitor/reports/daily/2026-06-07.md`

Missing optional inputs:

- --ljg-report not provided
- --x-md not provided

Output files created:

- `investment-intelligence-hub/processed/sources/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/signals/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/ticker_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/thesis_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_notes.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_validation.md`

Sources: 1. Signals: 4. Ticker impacts: 5. Thesis impacts: 4.

Validation result:

- All signal source_ids exist in source records.
- All ticker impact signal_ids exist in signals.
- All thesis impact signal_ids exist in signals.
- All score and confidence fields are numeric between 0 and 1.
- Brief contains all 7 sections and uses Watchlist Impact.
- Forbidden trading instruction words appear only in the opening disclaimer context.
- No production scripts were manually modified.

Boundary confirmation:

- Existing production scripts were not modified.
- Existing `ai-investing-monitor` report generation logic was not changed.
- `watchlists.yaml`, `themes.yaml`, and existing report files were not edited.
- Existing daily reports, ljg-Invest reports, and X converted files were not moved or rewritten.
- The hub was not made canonical and was not linked from `docs/index.html`.
- Durable memory thesis files were not updated.
- No trading automation was created.
- No trade instructions were generated.

## 2026-06-07 - Phase 7A Source Policy and Local HTML Export

Timestamp: 2026-06-07T18:19:59-0400

Files changed:

- `investment-intelligence-hub/docs/source_policy.md`
- `investment-intelligence-hub/docs/architecture.md`
- `investment-intelligence-hub/docs/schemas.md`
- `investment-intelligence-hub/docs/verification.md`
- `investment-intelligence-hub/scripts/run_hub_pipeline.py`

Source policy created:

- Added four-tier hierarchy covering Primary Sources, Daily Base / Core Financial News, ljg-invest Deep Research, and User-Captured X Posts.
- Primary Source registry is intentionally deferred to Phase 8; `investment-intelligence-hub/memory/primary_sources.yaml` was not created.

x_posts directory status:

- Current curated X inbox: `investment-intelligence-hub/inbox/x_posts`
- Legacy or alternate folders `x-posts`, `manual_x`, `readwise`, and `x_timeline` are not current target inboxes if present; no automatic migration was performed.

Script changes:

- Added `--x-posts-dir` and default previous-day `x_posts/YYYY_MM_DD/` lookup.
- Kept `--ljg-report` explicit-only and optional.
- Added source-count flexibility for daily-only, daily plus ljg-invest, daily plus X, and all-source runs.
- Added `--export-html` for local-only HTML output.
- Added per-signal `source_type` and Tier 4 X corroboration validation.

Command run:

- `python3 investment-intelligence-hub/scripts/run_hub_pipeline.py --date 2026-06-07 --mode parallel --daily-report ai-investing-monitor/reports/daily/2026-06-07.md`

Input files used:

- `ai-investing-monitor/reports/daily/2026-06-07.md`

Missing optional inputs / warnings:

- --ljg-report not provided
- default previous-day x_posts folder missing: investment-intelligence-hub/inbox/x_posts/2026_06_06

Output files created:

- `investment-intelligence-hub/processed/sources/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/signals/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/ticker_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/thesis_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_notes.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_validation.md`

Sources: 1. Signals: 4. Ticker impacts: 5. Thesis impacts: 4.

Validation result:

- Signal count is between 3 and 12.
- All signal source_ids exist in source records.
- Every signal includes source_type.
- All ticker impact signal_ids exist in signals.
- All thesis impact signal_ids exist in signals.
- All score and confidence fields are numeric between 0 and 1.
- Tier 4 X-only signals are marked needs_corroboration.
- Brief contains all 7 sections and uses Watchlist Impact.
- Forbidden trading instruction words appear only in the opening disclaimer context.
- No production scripts were manually modified.

Boundary confirmation:

- Existing production scripts were not modified.
- Existing `ai-investing-monitor` report generation logic was not changed.
- `watchlists.yaml`, `themes.yaml`, and existing report files were not edited.
- Existing daily reports, ljg-invest reports, and X converted files were not moved or rewritten.
- The hub was not made canonical and was not linked from `docs/index.html`.
- Durable memory thesis files were not updated.
- No public publishing was performed.
- No trading automation was created.
- No trade instructions were generated.

## 2026-06-07 - Phase 7A Source Policy and Local HTML Export

Timestamp: 2026-06-07T18:20:03-0400

Files changed:

- `investment-intelligence-hub/docs/source_policy.md`
- `investment-intelligence-hub/docs/architecture.md`
- `investment-intelligence-hub/docs/schemas.md`
- `investment-intelligence-hub/docs/verification.md`
- `investment-intelligence-hub/scripts/run_hub_pipeline.py`

Source policy created:

- Added four-tier hierarchy covering Primary Sources, Daily Base / Core Financial News, ljg-invest Deep Research, and User-Captured X Posts.
- Primary Source registry is intentionally deferred to Phase 8; `investment-intelligence-hub/memory/primary_sources.yaml` was not created.

x_posts directory status:

- Current curated X inbox: `investment-intelligence-hub/inbox/x_posts`
- Legacy or alternate folders `x-posts`, `manual_x`, `readwise`, and `x_timeline` are not current target inboxes if present; no automatic migration was performed.

Script changes:

- Added `--x-posts-dir` and default previous-day `x_posts/YYYY_MM_DD/` lookup.
- Kept `--ljg-report` explicit-only and optional.
- Added source-count flexibility for daily-only, daily plus ljg-invest, daily plus X, and all-source runs.
- Added `--export-html` for local-only HTML output.
- Added per-signal `source_type` and Tier 4 X corroboration validation.

Command run:

- `python3 investment-intelligence-hub/scripts/run_hub_pipeline.py --date 2026-06-07 --mode parallel --daily-report ai-investing-monitor/reports/daily/2026-06-07.md --ljg-report 20260602T184149==z--投资分析-nok.org --x-md x-to-markdown/artofspecuycky/2062623036722049427.md`

Input files used:

- `ai-investing-monitor/reports/daily/2026-06-07.md`
- `20260602T184149==z--投资分析-nok.org`
- `x-to-markdown/artofspecuycky/2062623036722049427.md`

Missing optional inputs / warnings:

- None

Output files created:

- `investment-intelligence-hub/processed/sources/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/signals/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/ticker_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/thesis_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_notes.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_validation.md`

Sources: 3. Signals: 8. Ticker impacts: 5. Thesis impacts: 6.

Validation result:

- Signal count is between 3 and 12.
- All signal source_ids exist in source records.
- Every signal includes source_type.
- All ticker impact signal_ids exist in signals.
- All thesis impact signal_ids exist in signals.
- All score and confidence fields are numeric between 0 and 1.
- Tier 4 X-only signals are marked needs_corroboration.
- Brief contains all 7 sections and uses Watchlist Impact.
- Forbidden trading instruction words appear only in the opening disclaimer context.
- No production scripts were manually modified.

Boundary confirmation:

- Existing production scripts were not modified.
- Existing `ai-investing-monitor` report generation logic was not changed.
- `watchlists.yaml`, `themes.yaml`, and existing report files were not edited.
- Existing daily reports, ljg-invest reports, and X converted files were not moved or rewritten.
- The hub was not made canonical and was not linked from `docs/index.html`.
- Durable memory thesis files were not updated.
- No public publishing was performed.
- No trading automation was created.
- No trade instructions were generated.

## 2026-06-07 - Phase 7A Source Policy and Local HTML Export

Timestamp: 2026-06-07T18:20:08-0400

Files changed:

- `investment-intelligence-hub/docs/source_policy.md`
- `investment-intelligence-hub/docs/architecture.md`
- `investment-intelligence-hub/docs/schemas.md`
- `investment-intelligence-hub/docs/verification.md`
- `investment-intelligence-hub/scripts/run_hub_pipeline.py`

Source policy created:

- Added four-tier hierarchy covering Primary Sources, Daily Base / Core Financial News, ljg-invest Deep Research, and User-Captured X Posts.
- Primary Source registry is intentionally deferred to Phase 8; `investment-intelligence-hub/memory/primary_sources.yaml` was not created.

x_posts directory status:

- Current curated X inbox: `investment-intelligence-hub/inbox/x_posts`
- Legacy or alternate folders `x-posts`, `manual_x`, `readwise`, and `x_timeline` are not current target inboxes if present; no automatic migration was performed.

Script changes:

- Added `--x-posts-dir` and default previous-day `x_posts/YYYY_MM_DD/` lookup.
- Kept `--ljg-report` explicit-only and optional.
- Added source-count flexibility for daily-only, daily plus ljg-invest, daily plus X, and all-source runs.
- Added `--export-html` for local-only HTML output.
- Added per-signal `source_type` and Tier 4 X corroboration validation.

Command run:

- `python3 investment-intelligence-hub/scripts/run_hub_pipeline.py --date 2026-06-07 --mode parallel --daily-report ai-investing-monitor/reports/daily/2026-06-07.md --export-html`

Input files used:

- `ai-investing-monitor/reports/daily/2026-06-07.md`

Missing optional inputs / warnings:

- --ljg-report not provided
- default previous-day x_posts folder missing: investment-intelligence-hub/inbox/x_posts/2026_06_06

Output files created:

- `investment-intelligence-hub/processed/sources/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/signals/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/ticker_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/thesis_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_notes.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_validation.md`
- `investment-intelligence-hub/reports/daily_intelligence/html/2026-06-07.html`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_html_notes.md`

Sources: 1. Signals: 4. Ticker impacts: 5. Thesis impacts: 4.

Validation result:

- Signal count is between 3 and 12.
- All signal source_ids exist in source records.
- Every signal includes source_type.
- All ticker impact signal_ids exist in signals.
- All thesis impact signal_ids exist in signals.
- All score and confidence fields are numeric between 0 and 1.
- Tier 4 X-only signals are marked needs_corroboration.
- Brief contains all 7 sections and uses Watchlist Impact.
- Forbidden trading instruction words appear only in the opening disclaimer context.
- HTML export publish-safe validation passed.
- No production scripts were manually modified.

Boundary confirmation:

- Existing production scripts were not modified.
- Existing `ai-investing-monitor` report generation logic was not changed.
- `watchlists.yaml`, `themes.yaml`, and existing report files were not edited.
- Existing daily reports, ljg-invest reports, and X converted files were not moved or rewritten.
- The hub was not made canonical and was not linked from `docs/index.html`.
- Durable memory thesis files were not updated.
- No public publishing was performed.
- No trading automation was created.
- No trade instructions were generated.

## 2026-06-07 - Phase 7A Source Policy and Local HTML Export

Timestamp: 2026-06-07T18:20:21-0400

Files changed:

- `investment-intelligence-hub/docs/source_policy.md`
- `investment-intelligence-hub/docs/architecture.md`
- `investment-intelligence-hub/docs/schemas.md`
- `investment-intelligence-hub/docs/verification.md`
- `investment-intelligence-hub/scripts/run_hub_pipeline.py`

Source policy created:

- Added four-tier hierarchy covering Primary Sources, Daily Base / Core Financial News, ljg-invest Deep Research, and User-Captured X Posts.
- Primary Source registry is intentionally deferred to Phase 8; `investment-intelligence-hub/memory/primary_sources.yaml` was not created.

x_posts directory status:

- Current curated X inbox: `investment-intelligence-hub/inbox/x_posts`
- Legacy or alternate folders `x-posts`, `manual_x`, `readwise`, and `x_timeline` are not current target inboxes if present; no automatic migration was performed.

Script changes:

- Added `--x-posts-dir` and default previous-day `x_posts/YYYY_MM_DD/` lookup.
- Kept `--ljg-report` explicit-only and optional.
- Added source-count flexibility for daily-only, daily plus ljg-invest, daily plus X, and all-source runs.
- Added `--export-html` for local-only HTML output.
- Added per-signal `source_type` and Tier 4 X corroboration validation.

Command run:

- `python3 investment-intelligence-hub/scripts/run_hub_pipeline.py --date 2026-06-07 --mode parallel --daily-report ai-investing-monitor/reports/daily/2026-06-07.md`

Input files used:

- `ai-investing-monitor/reports/daily/2026-06-07.md`
- `investment-intelligence-hub/inbox/x_posts/2026_06_06/20260606_test_x_post.md`

Missing optional inputs / warnings:

- --ljg-report not provided

Output files created:

- `investment-intelligence-hub/processed/sources/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/signals/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/ticker_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/thesis_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_notes.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_validation.md`

Sources: 2. Signals: 5. Ticker impacts: 5. Thesis impacts: 5.

Validation result:

- Signal count is between 3 and 12.
- All signal source_ids exist in source records.
- Every signal includes source_type.
- All ticker impact signal_ids exist in signals.
- All thesis impact signal_ids exist in signals.
- All score and confidence fields are numeric between 0 and 1.
- Tier 4 X-only signals are marked needs_corroboration.
- Brief contains all 7 sections and uses Watchlist Impact.
- Forbidden trading instruction words appear only in the opening disclaimer context.
- No production scripts were manually modified.

Boundary confirmation:

- Existing production scripts were not modified.
- Existing `ai-investing-monitor` report generation logic was not changed.
- `watchlists.yaml`, `themes.yaml`, and existing report files were not edited.
- Existing daily reports, ljg-invest reports, and X converted files were not moved or rewritten.
- The hub was not made canonical and was not linked from `docs/index.html`.
- Durable memory thesis files were not updated.
- No public publishing was performed.
- No trading automation was created.
- No trade instructions were generated.

## 2026-06-07 - Phase 7A Source Policy and Local HTML Export

Timestamp: 2026-06-07T19:30:41-0400

Files changed:

- `investment-intelligence-hub/docs/source_policy.md`
- `investment-intelligence-hub/docs/architecture.md`
- `investment-intelligence-hub/docs/schemas.md`
- `investment-intelligence-hub/docs/verification.md`
- `investment-intelligence-hub/scripts/run_hub_pipeline.py`

Source policy created:

- Added four-tier hierarchy covering Primary Sources, Daily Base / Core Financial News, ljg-invest Deep Research, and User-Captured X Posts.
- Primary Source registry is intentionally deferred to Phase 8; `investment-intelligence-hub/memory/primary_sources.yaml` was not created.

x_posts directory status:

- Current curated X inbox: `investment-intelligence-hub/inbox/x_posts`
- Legacy or alternate folders `x-posts`, `manual_x`, `readwise`, and `x_timeline` are not current target inboxes if present; no automatic migration was performed.

Script changes:

- Added `--x-posts-dir` and default previous-day `x_posts/YYYY_MM_DD/` lookup.
- Kept `--ljg-report` explicit-only and optional.
- Added source-count flexibility for daily-only, daily plus ljg-invest, daily plus X, and all-source runs.
- Added `--export-html` for local-only HTML output.
- Added per-signal `source_type` and Tier 4 X corroboration validation.

Command run:

- `python3 investment-intelligence-hub/scripts/run_hub_pipeline.py --date 2026-06-07 --mode parallel --export-html`

Input files used:

- `ai-investing-monitor/reports/daily/2026-06-07.md`

Missing optional inputs / warnings:

- --ljg-report not provided
- default previous-day x_posts folder has no .md/.html files: investment-intelligence-hub/inbox/x_posts/2026_06_06

Output files created:

- `investment-intelligence-hub/processed/sources/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/signals/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/ticker_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/thesis_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_notes.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_validation.md`
- `investment-intelligence-hub/reports/daily_intelligence/html/2026-06-07.html`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_html_notes.md`

Sources: 1. Signals: 4. Ticker impacts: 5. Thesis impacts: 4.

Validation result:

- Signal count is between 3 and 12.
- All signal source_ids exist in source records.
- Every signal includes source_type.
- All ticker impact signal_ids exist in signals.
- All thesis impact signal_ids exist in signals.
- All score and confidence fields are numeric between 0 and 1.
- Tier 4 X-only signals are marked needs_corroboration.
- Brief contains all 7 sections and uses Watchlist Impact.
- Forbidden trading instruction words appear only in the opening disclaimer context.
- HTML export publish-safe validation passed.
- No production scripts were manually modified.

Boundary confirmation:

- Existing production scripts were not modified.
- Existing `ai-investing-monitor` report generation logic was not changed.
- `watchlists.yaml`, `themes.yaml`, and existing report files were not edited.
- Existing daily reports, ljg-invest reports, and X converted files were not moved or rewritten.
- The hub was not made canonical and was not linked from `docs/index.html`.
- Durable memory thesis files were not updated.
- No public publishing was performed.
- No trading automation was created.
- No trade instructions were generated.

## 2026-06-07 - Phase 7A Source Policy and Local HTML Export

Timestamp: 2026-06-07T23:12:05-0400

Files changed:

- `investment-intelligence-hub/docs/source_policy.md`
- `investment-intelligence-hub/docs/architecture.md`
- `investment-intelligence-hub/docs/schemas.md`
- `investment-intelligence-hub/docs/verification.md`
- `investment-intelligence-hub/scripts/run_hub_pipeline.py`

Source policy created:

- Added four-tier hierarchy covering Primary Sources, Daily Base / Core Financial News, ljg-invest Deep Research, and User-Captured X Posts.
- Primary Source registry is intentionally deferred to Phase 8; `investment-intelligence-hub/memory/primary_sources.yaml` was not created.

x_posts directory status:

- Current curated X inbox: `investment-intelligence-hub/inbox/x_posts`
- Legacy or alternate folders `x-posts`, `manual_x`, `readwise`, and `x_timeline` are not current target inboxes if present; no automatic migration was performed.

Script changes:

- Added `--x-posts-dir` and default previous-day `x_posts/YYYY_MM_DD/` lookup.
- Kept `--ljg-report` explicit-only and optional.
- Added source-count flexibility for daily-only, daily plus ljg-invest, daily plus X, and all-source runs.
- Added `--export-html` for local-only HTML output.
- Added per-signal `source_type` and Tier 4 X corroboration validation.

Command run:

- `python3 investment-intelligence-hub/scripts/run_hub_pipeline.py --date 2026-06-07 --mode parallel --export-html`

Input files used:

- `reports/daily/2026-06-07.md`

Missing optional inputs / warnings:

- --ljg-report not provided
- default previous-day x_posts folder missing: investment-intelligence-hub/inbox/x_posts/2026_06_06

Output files created:

- `investment-intelligence-hub/processed/sources/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/signals/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/ticker_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/thesis_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_notes.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_validation.md`
- `investment-intelligence-hub/reports/daily_intelligence/html/2026-06-07.html`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_html_notes.md`

Sources: 1. Signals: 4. Ticker impacts: 5. Thesis impacts: 4.

Validation result:

- Signal count is between 3 and 12.
- All signal source_ids exist in source records.
- Every signal includes source_type.
- All ticker impact signal_ids exist in signals.
- All thesis impact signal_ids exist in signals.
- All score and confidence fields are numeric between 0 and 1.
- Tier 4 X-only signals are marked needs_corroboration.
- Brief contains all 7 sections and uses Watchlist Impact.
- Forbidden trading instruction words appear only in the opening disclaimer context.
- HTML export publish-safe validation passed.
- No production scripts were manually modified.

Boundary confirmation:

- Existing production scripts were not modified.
- Existing `ai-investing-monitor` report generation logic was not changed.
- `watchlists.yaml`, `themes.yaml`, and existing report files were not edited.
- Existing daily reports, ljg-invest reports, and X converted files were not moved or rewritten.
- The hub was not made canonical and was not linked from `docs/index.html`.
- Durable memory thesis files were not updated.
- No public publishing was performed.
- No trading automation was created.
- No trade instructions were generated.

## 2026-06-07 - Phase 7A Source Policy and Local HTML Export

Timestamp: 2026-06-07T23:14:34-0400

Files changed:

- `investment-intelligence-hub/docs/source_policy.md`
- `investment-intelligence-hub/docs/architecture.md`
- `investment-intelligence-hub/docs/schemas.md`
- `investment-intelligence-hub/docs/verification.md`
- `investment-intelligence-hub/scripts/run_hub_pipeline.py`

Source policy created:

- Added four-tier hierarchy covering Primary Sources, Daily Base / Core Financial News, ljg-invest Deep Research, and User-Captured X Posts.
- Primary Source registry is intentionally deferred to Phase 8; `investment-intelligence-hub/memory/primary_sources.yaml` was not created.

x_posts directory status:

- Current curated X inbox: `investment-intelligence-hub/inbox/x_posts`
- Legacy or alternate folders `x-posts`, `manual_x`, `readwise`, and `x_timeline` are not current target inboxes if present; no automatic migration was performed.

Script changes:

- Added `--x-posts-dir` and default previous-day `x_posts/YYYY_MM_DD/` lookup.
- Kept `--ljg-report` explicit-only and optional.
- Added source-count flexibility for daily-only, daily plus ljg-invest, daily plus X, and all-source runs.
- Added `--export-html` for local-only HTML output.
- Added per-signal `source_type` and Tier 4 X corroboration validation.

Command run:

- `python3 investment-intelligence-hub/scripts/run_hub_pipeline.py --date 2026-06-07 --mode parallel --export-html`

Input files used:

- `reports/daily/2026-06-07.md`

Missing optional inputs / warnings:

- --ljg-report not provided
- default previous-day x_posts folder missing: investment-intelligence-hub/inbox/x_posts/2026_06_06

Output files created:

- `investment-intelligence-hub/processed/sources/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/signals/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/ticker_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/processed/thesis_impacts/2026-06-07.jsonl`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_notes.md`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_validation.md`
- `investment-intelligence-hub/reports/daily_intelligence/html/2026-06-07.html`
- `investment-intelligence-hub/reports/daily_intelligence/2026-06-07_html_notes.md`

Sources: 1. Signals: 4. Ticker impacts: 5. Thesis impacts: 4.

Validation result:

- Signal count is between 3 and 12.
- All signal source_ids exist in source records.
- Every signal includes source_type.
- All ticker impact signal_ids exist in signals.
- All thesis impact signal_ids exist in signals.
- All score and confidence fields are numeric between 0 and 1.
- Tier 4 X-only signals are marked needs_corroboration.
- Brief contains all 7 sections and uses Watchlist Impact.
- Forbidden trading instruction words appear only in the opening disclaimer context.
- HTML export publish-safe validation passed.
- No production scripts were manually modified.

Boundary confirmation:

- Existing production scripts were not modified.
- Existing `ai-investing-monitor` report generation logic was not changed.
- `watchlists.yaml`, `themes.yaml`, and existing report files were not edited.
- Existing daily reports, ljg-invest reports, and X converted files were not moved or rewritten.
- The hub was not made canonical and was not linked from `docs/index.html`.
- Durable memory thesis files were not updated.
- No public publishing was performed.
- No trading automation was created.
- No trade instructions were generated.
