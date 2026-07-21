# Weekly Thesis Reviews

Long-horizon (not short-term) weekly memory for AI infrastructure investing.

| Item | Path |
|---|---|
| Template | `templates/weekly_thesis_brief.md` |
| Markdown instances | `investment-intelligence-hub/memory/weekly_reviews/YYYY-MM-DD.md` |
| HTML (Huashu report theme) | `docs/weekly/YYYY-MM-DD.html` |
| HTML mirror | `reports/weekly/YYYY-MM-DD.html` |
| Pipeline | `python3 scripts/run_weekly_thesis_brief.py` |
| Scaffold only | `python3 scripts/scaffold_weekly_thesis_brief.py` |
| Example | `2026-07-18.md` |

**Cadence:** Friday **17:00 local** via launchd `com.robin.ai-investing.weekly-thesis`.

**Pipeline**
1. Build/fill weekly markdown (existing filled file preferred; else LLM if `ANTHROPIC_API_KEY`, else rules summary from digests)
2. Render with **huashu-md-html** `--theme report` (pandoc)
3. Email full HTML if SMTP env is set

**Manual**
```bash
# Preview HTML only (no email)
python3 scripts/run_weekly_thesis_brief.py --week-end 2026-07-18 --preview-only
open docs/weekly/2026-07-18.html

# Full run including email
python3 scripts/run_weekly_thesis_brief.py --week-end 2026-07-18
```

**SMTP env** (same as other project emails):  
`SMTP_HOST SMTP_PORT SMTP_USERNAME SMTP_PASSWORD EMAIL_FROM EMAIL_TO`  
Put them in `.env.local` or `~/.config/ai-investing-monitor/env` for launchd.

**Rules of thumb**
- Default: Intact + Hold thesis
- Price alone never sets Damaged
- Max 5 material facts
- No buy/sell, no price targets
