# Investment Intelligence Hub Verification Checklist

Date: 2026-06-07

Copied from `IMPLEMENTATION_PLAN.md` for Phase 1 documentation.

Before Codex claims implementation completion in a future build step, it must verify:

| Check | Required verification |
|---|---|
| Existing report generation still works | Run current `ai-investing-monitor/scripts/run_daily_report.py` and confirm generated Markdown, handoff, HTML, raw snapshots, and `latest_report.json`. |
| No existing files were overwritten unexpectedly | Compare pre/post file list and modification times; inspect `git status --short` inside `ai-investing-monitor/`. |
| New directories were created correctly | List `investment-intelligence-hub/` and confirm `inbox/`, `processed/`, `memory/`, `reports/`, `prompts/`, `skills/`, `docs/`. |
| Sample input can produce sample extracted signals | Run sample ingestion/extraction and verify non-empty `processed/signals/sample.jsonl`. |
| Final brief can be generated from sample data | Verify `reports/daily_intelligence/sample.md` exists and contains all required sections. |
| Source provenance is present | Every signal references valid `source_id`; every source has local path or URL. |
| Source type is present | Every signal includes `source_type` derived from its source records. |
| Source quality scoring is present | Every signal has `source_quality_score` and every source has quality rationale. |
| Five-pillar signal evaluation is present | Every signal has source quality, evidence strength, thesis relevance, market impact, and noise risk scores. |
| Investment vs speculation thesis is separated | Thesis impact output explicitly labels durable investment thesis vs speculation thesis. |
| Tier 4 X signals are constrained | X-only signals are marked `needs_corroboration` unless confirmed by Tier 1 or Tier 2. |
| X cannot update memory alone | No X signal can update durable memory without higher-quality confirmation. |
| Durable thesis update gate is enforced | Durable thesis updates require Tier 1 confirmation or explicit human approval. |
| No trading automation was added | No brokerage API, order file, trading endpoint, or execution script exists. |
| No buy/sell instructions are generated | Search generated hub files for forbidden action terms in instruction context; allowed terms only appear in disclaimers or forbidden-output definitions. |
| Memory update is controlled | Run ledger is append-only; durable thesis files are updated only by explicit approval or a documented memory proposal workflow. |
| HTML export uses watchlist boundary | HTML export uses Watchlist Impact when holdings are unconfirmed. |
| HTML export is publish-safe | HTML export fails or warns if it detects account amount, holding quantity, cost basis, exact trading plan, tax detail, banking/company sensitive information, or private personal notes. |
