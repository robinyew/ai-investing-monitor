# Phase 7B Publish Plan

Date: 2026-06-07

Status: planning only. Do not implement in Phase 7B planning.

## Goal

Publish a local Investment Intelligence Hub HTML report into the existing `ai-investing-monitor` GitHub Pages docs tree so it becomes available as a public URL.

Source HTML:

```text
investment-intelligence-hub/reports/daily_intelligence/html/YYYY-MM-DD.html
```

Publish target:

```text
ai-investing-monitor/docs/intelligence/YYYY-MM-DD.html
```

## Boundaries

- Do not modify production report-generation scripts during planning.
- Do not change `watchlists.yaml` or `themes.yaml`.
- Do not publish yet.
- Do not update `ai-investing-monitor/docs/index.html` yet.
- Do not commit or push yet.
- Do not create trading automation.
- Do not generate buy/sell instructions.

## 1. GitHub Actions `workflow_dispatch` Design

Create a future manually triggered workflow in `ai-investing-monitor/.github/workflows/`.

Proposed workflow name:

```text
publish-hub-intelligence.yml
```

Inputs:

| Input | Required | Default | Purpose |
|---|---:|---|---|
| `date` | yes | none | Report date in `YYYY-MM-DD` format. |
| `mode` | no | `parallel` | Hub run mode. |
| `publish` | no | `false` | Safety gate; must be true before copy/commit/push. |

High-level jobs:

1. Checkout repository.
2. Set up Python.
3. Run Hub pipeline with `--export-html`.
4. Run publish-safe validation.
5. Copy generated HTML into `ai-investing-monitor/docs/intelligence/`.
6. Update `ai-investing-monitor/docs/intelligence/index.html`.
7. Commit and push only if `publish=true` and validation passes.

The workflow should fail closed: if validation fails, do not copy, commit, or push.

## 2. CLI Command

Future local or CI command:

```bash
python3 investment-intelligence-hub/scripts/run_hub_pipeline.py \
  --date YYYY-MM-DD \
  --mode parallel \
  --daily-report ai-investing-monitor/reports/daily/YYYY-MM-DD.md \
  --export-html
```

Optional explicit inputs remain available:

```bash
--ljg-report PATH
--x-md PATH
--x-posts-dir PATH
```

Default X behavior should remain:

```text
investment-intelligence-hub/inbox/x_posts/YYYY_MM_DD_OF_PREVIOUS_DAY/
```

## 3. Copy HTML To Public Docs

After validation passes, copy:

```text
investment-intelligence-hub/reports/daily_intelligence/html/YYYY-MM-DD.html
```

to:

```text
ai-investing-monitor/docs/intelligence/YYYY-MM-DD.html
```

Create this folder if missing:

```text
ai-investing-monitor/docs/intelligence/
```

Do not copy Markdown, JSONL, notes, validation files, raw inputs, or memory files into public docs.

## 4. Update Intelligence Index

Create or update:

```text
ai-investing-monitor/docs/intelligence/index.html
```

Index requirements:

- List published intelligence briefs by date.
- Link each date to `YYYY-MM-DD.html`.
- Keep the page minimal and static.
- Include research-only disclaimer.
- Do not expose private notes, account details, holdings quantities, cost basis, tax details, or internal validation logs.

Do not update root `ai-investing-monitor/docs/index.html` until a later explicit approval step.

## 5. Publish-Safe Validation

Before copying to public docs, validate the local HTML and source Markdown.

Required checks:

- HTML file exists.
- HTML includes all seven report sections.
- HTML includes the public disclaimer:

```text
Research-only. No trading automation. No buy/sell instructions. Watchlist labels are not confirmed holdings.
```

- Report uses `Watchlist Impact` when holdings are unconfirmed.
- No forbidden trading instruction words appear outside disclaimer or forbidden-output context.
- No account amount, holding quantity, cost basis, exact trading plan, tax detail, banking/company sensitive information, or private personal notes are detected.
- Source JSONL files parse correctly.
- Signal references and impact references are valid.
- X-only signals remain `needs_corroboration`.

If validation fails:

- Do not copy into public docs.
- Do not update index.
- Do not commit.
- Write a failure note to the workflow log or Hub validation markdown.

## 6. Commit And Push Behavior

Future commit behavior should be explicit and gated.

Only commit if all are true:

- Workflow input `publish=true`.
- Hub pipeline completed.
- Publish-safe validation passed.
- Target HTML and index update were generated.
- Git diff contains only allowed public docs files.

Allowed commit paths:

```text
ai-investing-monitor/docs/intelligence/YYYY-MM-DD.html
ai-investing-monitor/docs/intelligence/index.html
```

Commit message format:

```text
Publish intelligence brief YYYY-MM-DD
```

Do not include Hub processed JSONL, source registries, memory files, private notes, or test fixtures in the publish commit.

## 7. Output URL Format

Expected GitHub Pages URL pattern:

```text
https://<github-user-or-org>.github.io/<repo>/intelligence/YYYY-MM-DD.html
```

For this project, confirm the exact Pages base URL from the existing `ai-investing-monitor` Pages setup before implementation.

Index URL pattern:

```text
https://<github-user-or-org>.github.io/<repo>/intelligence/
```

## 8. Required GitHub Secrets Or Permissions

Preferred permission model:

- Use built-in `GITHUB_TOKEN`.
- Workflow permissions:

```yaml
permissions:
  contents: write
```

Only add a personal access token if the repository or branch protection rules require it.

No brokerage secrets, trading credentials, X API keys, Readwise keys, or Cloudflare secrets are required for Phase 7B publishing.

## 9. Later Cloudflare Worker Cron Trigger Design

Later phase only.

Possible flow:

```text
Cloudflare Worker Cron
  -> GitHub Actions workflow_dispatch
  -> run hub pipeline with --export-html
  -> publish-safe validation
  -> copy HTML into docs/intelligence/
  -> commit and push
  -> public GitHub Pages URL
```

Worker responsibilities:

- Trigger the GitHub workflow with date input.
- Pass a publish flag only when scheduled publishing is explicitly approved.
- Record trigger status.

Worker non-goals:

- Do not generate the Hub report itself.
- Do not hold investment data.
- Do not bypass publish-safe validation.
- Do not trigger trading automation.

## 10. Rollback / Failure Handling

Failure cases:

| Failure | Handling |
|---|---|
| Hub pipeline fails | Stop workflow; do not copy or commit. |
| HTML export missing | Stop workflow; write validation failure. |
| Publish-safe validation fails | Stop workflow; do not copy or commit. |
| Git diff includes disallowed files | Stop workflow; do not commit. |
| Push fails | Leave local workflow logs; retry manually after inspecting branch state. |
| Published page has bad content | Revert the publish commit or replace with a corrected HTML file after validation. |

Rollback options:

1. Revert the publish commit.
2. Remove the dated HTML file and update `docs/intelligence/index.html`.
3. Republish the last known-good dated HTML file.

Every rollback should preserve the rule that only public-safe files under `ai-investing-monitor/docs/intelligence/` are modified.

## Implementation Readiness Checklist

- [ ] Confirm GitHub Pages base URL.
- [ ] Confirm allowed public docs paths.
- [ ] Add publish-safe validator or reuse Hub validation output.
- [ ] Add manual workflow with `publish=false` default.
- [ ] Test workflow without publishing.
- [ ] Test workflow with local copy only.
- [ ] Enable commit/push only after validation is proven.
- [ ] Keep Phase 7B separate from later Cloudflare Cron automation.
