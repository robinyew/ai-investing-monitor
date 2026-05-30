# AI Investing Monitor

Cloud-based daily AI investing research monitor. It runs before the US market opens, gathers previous close performance, pre-market market data where available, overnight news metadata, and catalyst notes, generates Markdown and mobile-friendly HTML reports, publishes through GitHub Pages, and creates a GitHub Issue notification.

This is not an auto-trading system. It does not connect to brokerage accounts, generate orders, execute trades, or provide buy/sell instructions. All tickers are watchlist items only.

## Watchlists

Core aggressive AI infrastructure:

```text
DELL, VRT, CIEN, COHR, MRVL, MPWR, AAOI, NVTS
```

Second-stage AI software/cloud/agent:

```text
NOW, ORCL, SNOW, PLTR, MSFT, GOOGL, AMZN
```

Memory/storage:

```text
MU, WDC, STX
```

AI networking/ASIC:

```text
AVGO, ANET, CSCO, ARM
```

AI PC/edge AI:

```text
QCOM, ON, HPQ, TXN
```

ETF/benchmarks:

```text
SMH, SOXX, QQQ, SPY
```

The editable source of truth is `config/watchlists.yaml`.

## What It Creates

- Full pre-market brief: `reports/daily/YYYY-MM-DD.md`
- ChatGPT handoff: `reports/chatgpt_handoff/YYYY-MM-DD.md`
- Web report: `docs/reports/YYYY-MM-DD.html`
- Report index: `docs/index.html`
- Raw data snapshots: `reports/raw_data/`

## Local Folder Setup

Your local project folder on your Mac is:

```text
~/Investment/ai-investing-monitor
```

GitHub Actions runs in GitHub's cloud environment. It cannot write directly to your Mac local folder.

The correct workflow is:

1. The GitHub Actions workflow generates the daily reports in the GitHub repository.
2. The workflow commits the generated report files back to the default branch.
3. On your Mac, keep a local clone of the repository at:

```text
~/Investment/ai-investing-monitor
```

4. Sync reports locally through GitHub Desktop, or run:

```bash
cd ~/Investment/ai-investing-monitor
git pull
```

After syncing, generated report files should appear locally under:

- `~/Investment/ai-investing-monitor/reports/daily/`
- `~/Investment/ai-investing-monitor/reports/chatgpt_handoff/`
- `~/Investment/ai-investing-monitor/docs/reports/`
- `~/Investment/ai-investing-monitor/reports/raw_data/`

## Manual Test

Install dependencies once:

```bash
pip install -r requirements.txt
```

Run the full pre-market process:

```bash
python scripts/run_daily_report.py
```

That single command fetches market data, fetches news metadata, builds the Markdown pre-market brief, builds the ChatGPT handoff, builds the HTML report, and updates `docs/index.html`.

## GitHub Actions

The workflow is in `.github/workflows/daily-report.yml`.

It supports both:

- Scheduled pre-market runs at `12:00 UTC` Monday through Friday, targeting roughly 7:00-8:00 AM Eastern depending on daylight saving time
- Manual runs through `workflow_dispatch` from the GitHub Actions tab

The workflow uses `GITHUB_TOKEN` to create or update one GitHub Issue titled:

```text
AI Investing Pre-Market Brief - YYYY-MM-DD
```

If an issue already exists for the same date, it updates that issue instead of creating a duplicate.

The workflow also commits generated report files back to the repository:

```bash
git add reports docs
git diff --cached --quiet || git commit -m "Add AI investing pre-market brief"
git push
```

If no report files changed, `git diff --cached --quiet` succeeds and the commit is skipped gracefully.

## GitHub Pages

1. Create a GitHub repository named `ai-investing-monitor`.
2. Push this project to the repository.
3. Open GitHub repo Settings -> Pages.
4. Set the source to deploy from the `docs/` folder on the default branch.

Example report URL:

```text
https://YOUR_GITHUB_USERNAME.github.io/ai-investing-monitor/reports/YYYY-MM-DD.html
```

Optional secret:

- `REPORT_BASE_URL`

Example:

```text
https://YOUR_GITHUB_USERNAME.github.io/ai-investing-monitor/reports
```

If `REPORT_BASE_URL` is missing in GitHub Actions, the script falls back to the standard GitHub Pages URL format based on `GITHUB_REPOSITORY`.

## Notifications

Version one uses GitHub Issues as the default notification method because it requires no external email service.

SMTP email support exists in `scripts/send_email.py`, but it is optional future functionality for the first version. To enable it later, add these secrets:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `EMAIL_FROM`
- `EMAIL_TO`
- `REPORT_BASE_URL`

Then set repository variable `AI_MONITOR_SEND_EMAIL` to `true`.

If SMTP secrets are missing, email is skipped and the report process still completes successfully.

## Update Watchlists

Edit `config/watchlists.yaml`. Add or remove tickers under the relevant group. The report treats every symbol as a watchlist item, not as an owned position.

## Data Sources

Version one uses:

- `yfinance` for market data and available fundamentals
- Public RSS/feed metadata for news headlines
- Best-effort earnings dates from the market data provider

Some feeds may be unavailable, delayed, paywalled, or incomplete. The workflow is designed to keep running when individual tickers or sources fail.

## Limitations

- No paid market data feed is included.
- News matching is headline/feed based and may miss important stories.
- Earnings dates depend on data provider availability.
- GitHub Actions schedules are UTC-based and may run slightly later than the target time.
- The report is a research aid only and requires human review.

## Disclaimer

This project is for research only. It does not contain buy/sell instructions and does not execute trades.
