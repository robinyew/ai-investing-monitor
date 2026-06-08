# Investment Report Dispatcher

Cloudflare Worker for dispatching existing GitHub Actions workflows for the AI Investing report system.

The Worker only triggers GitHub workflows. It does not generate reports, modify investment data, commit code, push changes, run investment logic, create trading automation, or generate trade instructions.

## Schedule

- 08:15 America/Toronto: dispatch `daily-report.yml`
- 08:30 America/Toronto: dispatch `publish-hub-intelligence.yml` with `publish=true`

Cloudflare cron expressions are UTC-based. Toronto shifts between EST and EDT, so this Worker registers both possible UTC times and checks the actual local Toronto time before dispatching.

Configured weekday cron triggers:

```text
15 12 * * 1-5
15 13 * * 1-5
30 12 * * 1-5
30 13 * * 1-5
```

The Worker computes `America/Toronto` local date and time with `Intl.DateTimeFormat`. If the local day is Saturday or Sunday, scheduled dispatch is skipped.

## Required Secrets

Set these with Wrangler. Do not commit real values.

```bash
npx wrangler secret put GITHUB_WORKFLOW_TOKEN
npx wrangler secret put DISPATCH_SECRET
```

`GITHUB_WORKFLOW_TOKEN` needs permission to dispatch workflows in `robinyew/ai-investing-monitor`.

## Non-Secret Vars

Configured in `wrangler.toml`:

```text
GITHUB_OWNER = robinyew
GITHUB_REPO = ai-investing-monitor
GITHUB_REF = main
DAILY_WORKFLOW_ID = daily-report.yml
HUB_WORKFLOW_ID = publish-hub-intelligence.yml
```

## Local Testing

Run local Worker dev:

```bash
npx wrangler dev --test-scheduled
```

Health endpoint:

```bash
curl http://127.0.0.1:8787/health
```

Dry-run manual dispatch:

```bash
curl "http://127.0.0.1:8787/dispatch?target=daily&date=2026-06-07&dry_run=true"
curl "http://127.0.0.1:8787/dispatch?target=hub&date=2026-06-07&dry_run=true"
```

Manual dispatch without `dry_run=true` requires:

```text
X-Dispatch-Secret: <secret>
```

## Deploy

Do not deploy until secrets are configured and manual dry-runs are reviewed.

```bash
npx wrangler deploy
```

## Workflow Payloads

`daily-report.yml` currently has no `workflow_dispatch` inputs, so the Worker dispatches it with an empty `inputs` object.

`publish-hub-intelligence.yml` receives:

```json
{
  "date": "YYYY-MM-DD",
  "mode": "parallel",
  "publish": "true"
}
```

## Idempotency Note

The current protection is time-gating: the Worker only dispatches when the computed Toronto local time exactly matches `08:15` or `08:30`. A future enhancement can add Cloudflare KV to record dispatched `(target, date)` keys and prevent duplicate dispatches across retries or redeploys.

## Boundaries

- No report generation in Worker
- No investment logic in Worker
- No trading automation
- No trade instructions
- No Readwise, X API, bookmark, or timeline integrations
- No Cloudflare Worker changes to existing `cloudflare-x-extractor`
