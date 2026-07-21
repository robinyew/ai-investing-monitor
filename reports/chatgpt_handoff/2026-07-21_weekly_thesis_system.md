# Handoff — Weekly Thesis Brief System

- **Date:** 2026-07-21
- **Status:** Deployed + email test OK (report theme)
- **Horizon:** multi-month / multi-year AI infra investor (not short-term trading)
- **Research-only:** no brokerage, no buy/sell, no price targets

---

## 1. What shipped

Long-horizon **Weekly Thesis & Chokepoint Brief**:

1. Markdown memory (source of truth)
2. **Huashu md-html `theme=report`** polished HTML
3. Email full HTML via existing GitHub SMTP secrets
4. Local **Friday 17:00** launchd + GitHub Actions `workflow_dispatch`

User confirmed: **email received** for test send of week `2026-07-18`.

---

## 2. Product decisions (locked)

| Decision | Choice | Why |
|---|---|---|
| Investor mode | Long-term only | User does not do short-term; open-checklist is optional/secondary |
| Primary product | Weekly thesis brief | Thesis / chokepoints / falsifiers — not daily tape |
| HTML theme | **report** (not article/reading) | Best for dense tables |
| Default thesis | **Intact + Hold** | Price alone never sets Damaged |
| Daily digests | Keep as “night watch” | Escalate only on fundamental change |
| Open checklist | Built earlier, not primary | Short-term tool; do not put in weekly email |

---

## 3. Paths (absolute + repo-relative)

| Artifact | Path |
|---|---|
| Template | `templates/weekly_thesis_brief.md` |
| Markdown instances | `investment-intelligence-hub/memory/weekly_reviews/YYYY-MM-DD.md` |
| Example filled | `investment-intelligence-hub/memory/weekly_reviews/2026-07-18.md` |
| Next blank scaffold | `investment-intelligence-hub/memory/weekly_reviews/2026-07-25.md` |
| HTML (canonical report) | `docs/weekly/YYYY-MM-DD.html` |
| HTML mirror | `reports/weekly/YYYY-MM-DD.html` |
| HTML index | `docs/weekly/index.html` |
| Pipeline | `scripts/run_weekly_thesis_brief.py` |
| Local dispatcher | `scripts/dispatch_weekly_thesis.sh` |
| launchd (repo) | `launchd/com.robin.ai-investing.weekly-thesis.plist` |
| launchd (installed) | `~/Library/LaunchAgents/com.robin.ai-investing.weekly-thesis.plist` |
| GHA workflow | `.github/workflows/weekly-thesis-brief.yml` |
| Huashu vendor | `vendor/huashu-md-html/` |
| Memory README | `investment-intelligence-hub/memory/weekly_reviews/README.md` |

**Preview (local):**
```bash
open /Users/leimingyu/Investment/ai-investing-monitor/docs/weekly/2026-07-18.html
```

**Pages (after publish):**  
`https://robinyew.github.io/ai-investing-monitor/weekly/YYYY-MM-DD.html`  
(requires `docs/` GitHub Pages; weekly folder is under `docs/weekly/`)

---

## 4. Automation map

### A) Local launchd (Mac must be on)

| Item | Value |
|---|---|
| Label | `com.robin.ai-investing.weekly-thesis` |
| When | **Friday 17:00 local system timezone** |
| Command | `bash scripts/dispatch_weekly_thesis.sh` |
| Logs | `logs/weekly-thesis.log`, `logs/weekly-thesis-error.log` |
| Env | sources `.env.local` and `~/.config/ai-investing-monitor/env` |

**Note:** Local machine currently has **no SMTP in `.env.local`**.  
Local Friday run will still **generate MD+HTML**; email will skip unless SMTP is added locally.  
**Email that works today = GitHub Actions secrets.**

### B) GitHub Actions (SMTP works)

| Item | Value |
|---|---|
| Workflow | `Weekly Thesis Brief` |
| Trigger | `workflow_dispatch` (manual; can also be scheduled later) |
| Secrets used | `SMTP_*`, `EMAIL_FROM`, `EMAIL_TO`, optional `ANTHROPIC_API_KEY`, `REPORT_BASE_URL` |
| Test run | `29873496342` — **success, Email: sent** |
| Subject | `Weekly Thesis Brief — {week_end}` |

Manual re-send:
```bash
gh workflow run weekly-thesis-brief.yml \
  -R robinyew/ai-investing-monitor \
  -f week_end=2026-07-18 \
  -f html_only=true \
  -f dry_run=false
```

### C) Pipeline logic (`run_weekly_thesis_brief.py`)

1. Resolve `week_end` = Friday (NY) on/before today  
2. Ensure markdown:
   - prefer existing **filled** brief
   - else LLM if `ANTHROPIC_API_KEY`
   - else **rules_auto** summary from digests/news  
3. Render HTML: **huashu `--theme report`**  
4. Write `docs/weekly/` + `reports/weekly/` + index  
5. Email HTML multipart (if SMTP present)

Flags:
```bash
--week-end YYYY-MM-DD
--force-regen
--html-only
--no-email / --preview-only
```

---

## 5. Report structure (what the user actually reads)

Executive strip → Thesis status → Chokepoint dashboard → ≤5 material facts → Portfolio logic mapping → Falsifiers → Price appendix (non-decision) → Research agenda → Noise list → Carry-forward.

**Falsifiers (armed defaults):** hyperscaler capex cut; power not binding; optics demand falsified; ASIC substitution quantified; core business model damage.

---

## 6. Related systems (do not confuse)

| System | Role vs weekly |
|---|---|
| Daily Decision Digest (09:00 ET launchd → GHA) | Overnight triage; default No Action |
| Pre-market brief / news scan | Daily inputs for weekly §3 |
| Open checklist (`templates/open_checklist.md`) | Short-term open observation — **not** weekly product |
| ljg-invest deep dives | On-demand ticker underwrite; link from weekly when needed |
| global-stock-data skill | Installed for quotes/fundamentals when agents need data |

---

## 7. Deploy checklist (done)

- [x] Template + example week `2026-07-18`
- [x] Pipeline script + dispatch shell
- [x] Huashu report HTML render (pandoc installed locally)
- [x] Vendor huashu into repo for CI
- [x] GHA workflow on `main`
- [x] Test email **received** by user
- [x] launchd installed Friday 17:00
- [x] Theme locked to **report**
- [ ] Optional: add local SMTP to `.env.local` so launchd also emails without GHA
- [ ] Optional: GHA `schedule: cron` Friday 21:00 UTC (≈17:00 ET) as dual path if Mac off
- [ ] Optional: wire launchd → `gh workflow run` for email-only reliability

---

## 8. How to operate next Friday (2026-07-25)

**Preferred (email reliable):**
```bash
# After week digests exist, either let a human lightly edit:
#   investment-intelligence-hub/memory/weekly_reviews/2026-07-25.md
# Then:
gh workflow run weekly-thesis-brief.yml \
  -R robinyew/ai-investing-monitor \
  -f week_end=2026-07-25 \
  -f html_only=false \
  -f force_regen=false
```

**Local generate only:**
```bash
cd ~/Investment/ai-investing-monitor
python3 scripts/run_weekly_thesis_brief.py --week-end 2026-07-25 --preview-only
open docs/weekly/2026-07-25.html
```

**If Mac is on at 17:00 Friday:** launchd runs automatically (HTML always; email only if SMTP local).

---

## 9. Known issues / nits

1. **Local SMTP missing** — launchd path does not email until secrets are in env file.  
2. GHA commit step once warned on rebase with unstaged files; workflow commit step tightened in follow-up.  
3. `article`/`reading` HTML previews remain on disk as optional comparisons; **do not email those**.  
4. Auto LLM fill quality depends on digest coverage that week; human 10-min pass recommended before trusting executive strip.  
5. GitHub Pages may need a few minutes after push for `docs/weekly/` to appear online.

---

## 10. Session recap (this conversation arc)

1. User asked if AI infra bounce would continue → framed as long-term: thesis intact, bounce not confirmed trend.  
2. Rebound quality scorecard + open checklist built (short-term) → user later clarified **not short-term**.  
3. Recommended report stack → user chose **Weekly Thesis Brief (A)**.  
4. Template + example + scaffold created.  
5. User requested Friday 17:00 auto + Huashu HTML + email; preview first.  
6. Compared article/reading/report → user chose **report**.  
7. Test push via GHA → **email received**.  
8. This handoff + deploy verification.

---

## 11. Next agent: start here

```text
1. Read this handoff.
2. Read templates/weekly_thesis_brief.md
3. Read investment-intelligence-hub/memory/weekly_reviews/2026-07-18.md (style sample)
4. For ops: scripts/run_weekly_thesis_brief.py --help
5. Do NOT reintroduce short-term open-checklist into the weekly email.
6. Do NOT change theme away from report without user ask.
7. Do NOT invent thesis damage from price alone.
```

**Quick health check:**
```bash
launchctl print gui/$(id -u)/com.robin.ai-investing.weekly-thesis | head -50
gh run list -R robinyew/ai-investing-monitor --workflow=weekly-thesis-brief.yml --limit 3
ls docs/weekly/
```

---

_Handoff file: `reports/chatgpt_handoff/2026-07-21_weekly_thesis_system.md`_
