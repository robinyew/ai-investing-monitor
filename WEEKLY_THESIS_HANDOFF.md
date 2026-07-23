# HANDOFF — Weekly Thesis Brief（周报专用）

> 写给**完全没有上下文**的新会话。
> 最后更新：2026-07-22
> 仓库：`robinyew/ai-investing-monitor`
> 本地：`/Users/leimingyu/Investment/ai-investing-monitor`

**不要和这些搞混：**

| 文档 | 内容 |
|------|------|
| **本文** `WEEKLY_THESIS_HANDOFF.md` | **周五长线周报**（Thesis / Chokepoint） |
| `../HANDOFF.md`（Investment 根） | **每日** Pre-Market / Hub / Digest |
| `~/.grok/portfolio-reports/HANDOFF.md` | **每日盘前** AI 持仓简报（Grok launchd） |
| `reports/chatgpt_handoff/2026-07-21_weekly_thesis_system.md` | 建系统当日的会话交接原稿（历史） |

---

## 1. 任务是什么

为 Robin 做 **多月～多年视角的 AI 基建投资周报**：

1. Markdown 记忆（真相源）
2. **华叔 md-html `theme=report`** 精排 HTML
3. 邮件发完整 HTML（可靠路径 = **GitHub Actions SMTP secrets**）
4. 本地 **周五 17:00** launchd + GHA `workflow_dispatch`

**研究向 only：** 不荐股、不买卖、不给目标价；默认 thesis **Intact + Hold**，**价格 alone 不能把 thesis 判成 Damaged**。

用户确认过：测试周 `2026-07-18` **邮件已收到**。

---

## 2. 产品决策（已锁定，勿擅自改）

| 决策 | 选择 |
|------|------|
| 投资者模式 | **长线 only**（不做短线） |
| 主产品 | Weekly Thesis Brief（论点 / 卡点 / 证伪条件） |
| HTML 主题 | **`report`**（不要用 article/reading 发邮件） |
| 默认论点 | Intact + Hold |
| 日更 Digest | 保留作「夜班哨兵」；只有基本面变化才升级 |
| Open checklist | 已有、**次要**；**不要塞进周报邮件** |

---

## 3. 路径清单

| 产物 | 路径 |
|------|------|
| **本交接** | `WEEKLY_THESIS_HANDOFF.md`（仓库根） |
| 模板 | `templates/weekly_thesis_brief.md` |
| 周 MD | `investment-intelligence-hub/memory/weekly_reviews/YYYY-MM-DD.md` |
| 样例（已填） | `.../weekly_reviews/2026-07-18.md` |
| 下一空白脚手架 | `.../weekly_reviews/2026-07-25.md` |
| HTML 正式 | `docs/weekly/YYYY-MM-DD.html` |
| HTML 镜像 | `reports/weekly/YYYY-MM-DD.html` |
| 索引 | `docs/weekly/index.html` |
| 流水线 | `scripts/run_weekly_thesis_brief.py` |
| 本地调度 shell | `scripts/dispatch_weekly_thesis.sh` |
| launchd（仓库副本） | `launchd/com.robin.ai-investing.weekly-thesis.plist` |
| launchd（已安装） | `~/Library/LaunchAgents/com.robin.ai-investing.weekly-thesis.plist` |
| GHA | `.github/workflows/weekly-thesis-brief.yml` |
| 网页生成器 | `scripts/build_weekly_thesis_site.py` |
| 网页发布 GHA | `.github/workflows/publish-weekly-thesis-site.yml` |
| 网页本地触发 | `scripts/dispatch_weekly_site_publish.sh` |
| 网页 launchd | `launchd/com.robin.ai-investing.weekly-site-publish.plist` |
| Vercel 静态站 | `vercel-weekly-thesis/` |
| 网页发布专用交接 | `vercel-weekly-thesis/HANDOFF.md` |
| Huashu | `vendor/huashu-md-html/` |
| Memory 说明 | `investment-intelligence-hub/memory/weekly_reviews/README.md` |

**本地预览：**

```bash
open /Users/leimingyu/Investment/ai-investing-monitor/docs/weekly/2026-07-18.html
```

**线上（Pages）：**
`https://robinyew.github.io/ai-investing-monitor/weekly/YYYY-MM-DD.html`

---

## 4. 自动化地图

### A) 本地 launchd（Mac 要开机）

| 项 | 值 |
|----|-----|
| Label | `com.robin.ai-investing.weekly-thesis` |
| 时间 | **周五 17:00**（**系统本地时区**；机子在 ET 即美东） |
| 命令 | `bash scripts/dispatch_weekly_thesis.sh` |
| 日志 | `logs/weekly-thesis.log` / `logs/weekly-thesis-error.log` |
| 环境 | source `.env.local` 与 `~/.config/ai-investing-monitor/env` |

**关键限制：** 本机 `.env.local` **通常没有 SMTP** → launchd 仍会 **生成 MD+HTML**，但 **邮件会 skip**。
**今天能稳定发信的路径 = GitHub Actions secrets。**

### B) GitHub Actions（发信可靠）

| 项 | 值 |
|----|-----|
| Workflow 名 | `Weekly Thesis Brief` |
| 触发 | `workflow_dispatch`（可选手动；日后可加 cron） |
| Secrets | `SMTP_*`, `EMAIL_FROM`, `EMAIL_TO`，可选 `ANTHROPIC_API_KEY`, `REPORT_BASE_URL` |
| 测试 run | `29873496342` — success, Email: sent |
| 主题 | `Weekly Thesis Brief — {week_end}` |

手动重发 / 补发：

```bash
gh workflow run weekly-thesis-brief.yml \
  -R robinyew/ai-investing-monitor \
  -f week_end=2026-07-18 \
  -f html_only=true \
  -f dry_run=false
```

### C) 流水线逻辑（`run_weekly_thesis_brief.py`）

1. `week_end` = 当天或之前最近的 **周五（NY）**
2. 准备 markdown：优先已填 brief → 有 key 则 LLM → 否则 rules_auto（digest/news）
3. 渲染 HTML：`huashu --theme report`
4. 写 `docs/weekly/` + `reports/weekly/` + index
5. 有 SMTP 才发 HTML multipart

常用 flag：

```bash
--week-end YYYY-MM-DD
--force-regen
--html-only
--no-email / --preview-only
```

### D) 周报网页发布（双触发）

网页是原任务的独立下游，不改变周报 MD、`report` 邮件 HTML 或邮件逻辑。

| 项 | 值 |
|----|-----|
| 正式域名 | `https://vercel-weekly-thesis.vercel.app` |
| 日期页 | `/weekly/YYYY-MM-DD/` |
| 最新页 | `/latest/` 与 `/` |
| 归档 | `/archive.html`，保留最近 365 天 |
| 主触发 | Mac launchd 周五 **18:30 ET** → `workflow_dispatch` |
| 云端补跑 | GitHub Actions 周五 **18:40 America/New_York** |
| 幂等 | `.published/YYYY-MM-DD.txt`；同周成功后补跑自动 skip |
| 成功通知 | Vercel Ready + 日期页 HTTP 200 + 日期内容校验后，使用现有 SMTP 发信 |

为了保证云端能读取 MD，`weekly-thesis-brief.yml` 同时在周五 **17:00 America/New_York** 云端生成并提交源文件；原来的本地 17:00 launchd 保留。

手动补发网页：

```bash
gh workflow run publish-weekly-thesis-site.yml -R robinyew/ai-investing-monitor -f week_end=2026-07-24 -f force=true
```

Vercel CI 配置：GitHub Secret `VERCEL_TOKEN`；Repository Variables `VERCEL_ORG_ID`、`VERCEL_PROJECT_ID`。不要把 token 写进仓库或日志。

---

## 5. 报告结构（用户实际读到的）

Executive strip → Thesis status → Chokepoint dashboard → ≤5 material facts → Portfolio logic mapping → Falsifiers → Price appendix（非决策）→ Research agenda → Noise list → Carry-forward。

**默认证伪条件（falsifiers）：**
hyperscaler capex 砍单；电力不再是约束；光模块需求证伪；ASIC 替代被量化；核心商业模式受损。

---

## 6. 已完成 vs 待办

### 已完成

- [x] 模板 + 样例周 `2026-07-18`
- [x] 流水线 + dispatch shell
- [x] Huashu report HTML（本地有 pandoc）
- [x] vendor huashu 进仓供 CI
- [x] GHA workflow 在 main
- [x] 测试邮件用户确认收到
- [x] launchd 周五 17:00 已装
- [x] 主题锁定 **report**
- [x] 专用交接 `WEEKLY_THESIS_HANDOFF.md`（本文件）
- [x] HTML Anything data-report 风格网页生成器
- [x] Vercel Production + 日期路径 + latest + 一年归档
- [x] 网页双触发：本地 18:30 + GitHub 18:40 补跑
- [x] 网页发布成功后 SMTP 通知

### 可选 / 未做

- [ ] 本机 `.env.local` 加 SMTP → launchd 也能直接发信
- [x] GHA 周五 17:00 `America/New_York` 云端生成，作为 Mac 关机双保险
- [x] 网页 launchd → `gh workflow run`，周五 18:30 主触发

---

## 7. 下周五怎么操作（例：2026-07-24）

**推荐（发信可靠）：** 先轻改 MD，再 GHA：

```bash
# 可选编辑
#   investment-intelligence-hub/memory/weekly_reviews/2026-07-24.md

gh workflow run weekly-thesis-brief.yml \
  -R robinyew/ai-investing-monitor \
  -f week_end=2026-07-24 \
  -f html_only=false \
  -f force_regen=false
```

**只本地生成预览：**

```bash
cd ~/Investment/ai-investing-monitor
python3 scripts/run_weekly_thesis_brief.py --week-end 2026-07-24 --preview-only
open docs/weekly/2026-07-24.html
```

**Mac 周五 17:00 开着：** launchd 自动跑（HTML 一定有；邮件看本机 SMTP）。

---

## 8. 踩坑 / 绝对不要

1. **不要把 open-checklist / 短线清单塞进周报邮件。**
2. **不要把 HTML 主题从 `report` 改成 article/reading 去发邮件**（磁盘上可有对比稿，勿发）。
3. **不要因股价 alone 把 thesis 标 Damaged。**
4. **本地 launchd ≠ 一定有邮件** — 没 SMTP 只出 HTML；要邮件优先 GHA。
5. **日更系统与周报分离** — 改 Digest 别误伤周报路径；见 Investment 根 `HANDOFF.md` 的 git/沙盒铁律同样适用。
6. **Pages 推送后可能延迟几分钟** 才刷新。
7. **LLM 自动填质量依赖当周 digest 覆盖** — 建议人眼 10 分钟过 executive strip。
8. 给用户的 shell 命令块：**不要夹中文注释行**（整段粘贴会炸 zsh）。
9. **不要删除 `.published/` 成功标记**，否则双触发会重复部署和发信。
10. GitHub schedule 可能因平台负载延迟几分钟；18:30 本地 dispatch 是主触发，18:40 是补跑。

---

## 9. 健康检查

```bash
launchctl print gui/$(id -u)/com.robin.ai-investing.weekly-thesis | head -50
gh run list -R robinyew/ai-investing-monitor --workflow=weekly-thesis-brief.yml --limit 5
ls -la /Users/leimingyu/Investment/ai-investing-monitor/docs/weekly/
ls -la /Users/leimingyu/Investment/ai-investing-monitor/investment-intelligence-hub/memory/weekly_reviews/
```

---

## 10. 新会话开场（可复制）

```
继续 Weekly Thesis Brief（见 ai-investing-monitor/WEEKLY_THESIS_HANDOFF.md）。
长线 only，theme=report，默认 Intact+Hold。
操作前先确认 launchd 与最近 GHA run；发信优先 gh workflow run weekly-thesis-brief.yml。
```

---

## 11. 相关系统（边界）

| 系统 | 相对周报 |
|------|----------|
| Daily Decision Digest（09:00） | 隔夜分诊；默认 No Action |
| Pre-market / News scan | 周报 § 事实输入 |
| Open checklist | 短线观察，**非周报产品** |
| Grok portfolio premarket | 个人持仓盘前，**另一套** |

---

_原稿会话交接：`reports/chatgpt_handoff/2026-07-21_weekly_thesis_system.md`_
_固定入口：本文件 `WEEKLY_THESIS_HANDOFF.md`_
