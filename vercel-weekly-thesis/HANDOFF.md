# HANDOFF — Weekly Thesis Vercel Publisher

> 写给完全没有上下文的新会话。
> 最后更新：2026-07-31
> 仓库：`robinyew/ai-investing-monitor`
> 本地：`/Users/leimingyu/Investment/ai-investing-monitor`
> 本系统目录：`vercel-weekly-thesis/`

## 1. 系统目标

读取 Weekly Thesis Brief 的权威 Markdown，生成 HTML Anything `data-report` 风格的静态网页，发布到 Vercel，并在公开页面验证成功后发送邮件通知。

本系统是原周报任务的独立下游：

- 不改变周报 Markdown 的研究结论。
- 不改变原来的 Huashu `theme=report` 邮件 HTML。
- 不接券商，不生成买卖指令，不设目标价。
- 网页生成使用固定、可重复的 HTML Anything 设计模板；每周不会调用 AI 重新设计页面。
- 页面布局沿用 `2026-07-18` 第一版，报告内容从 `2026-07-31` 起固定为简体中文。
- 源 Markdown 必须通过 v1 结构校验；不符合时中止部署，不再用 `N/A` 或空图表凑合发布。

## 2. 当前正式地址

| 页面 | 地址 |
|---|---|
| 最新一期 | `https://vercel-weekly-thesis.vercel.app/` |
| Latest alias | `https://vercel-weekly-thesis.vercel.app/latest/` |
| 日期页 | `https://vercel-weekly-thesis.vercel.app/weekly/YYYY-MM-DD/` |
| 一年归档 | `https://vercel-weekly-thesis.vercel.app/archive.html` |
| 已验证样例 | `https://vercel-weekly-thesis.vercel.app/weekly/2026-07-18/` |

`2026-07-18` 是历史样例日期，实际是星期六。未来自动报告必须使用真正的星期五日期。

## 3. 权威输入与输出

### 输入

```text
investment-intelligence-hub/memory/weekly_reviews/YYYY-MM-DD.md
```

源文件必须：

- 存在且非空。
- 长度至少 1200 字符。
- 包含且只包含编号 `0–10` 的固定章节。
- §1 必须是论点状态，§2 必须是卡点表，§3 必须是重大事实，§5 必须从证伪条件表开始。
- 从 `2026-07-31` 起，正文必须以简体中文为主，关键表头不得残留英文。
- 不是空白 scaffold。

### 输出

```text
vercel-weekly-thesis/
├── index.html
├── latest/index.html
├── archive.html
├── weekly/YYYY-MM-DD/index.html
├── .published/YYYY-MM-DD.txt
└── vercel.json
```

- `weekly/YYYY-MM-DD/`：永久日期路径。
- `latest/` 和根路径：最新一期副本。
- `archive.html`：最近 365 天的日期列表。
- `.published/`：成功部署标记，防止双触发重复部署和发信。
- 超过 365 天的网页与成功标记会从站点产物移除；原始 Markdown 不删除。

## 4. 自动化时间线

所有云端 schedule 使用 `America/New_York`，自动处理 DST。

| 时间 | 任务 | 作用 |
|---|---|---|
| 周五 17:00 | `Weekly Thesis Brief` GitHub Action | 云端生成并提交源 MD |
| 周五 17:00 | 原本地 weekly thesis launchd | 本地备份生成，保持原任务不变 |
| 周五 18:30 | 本地 weekly-site launchd | 主触发：调用网页 workflow_dispatch |
| 周五 18:40 | `Publish Weekly Thesis Site` schedule | Mac 关机时的云端补跑 |

双触发共用同一个 GitHub workflow。第一次成功后提交 `.published/YYYY-MM-DD.txt`；第二次看到标记会跳过生成、部署和邮件。

GitHub schedule 可能因平台负载延迟几分钟。18:30 是本地主触发时间，18:40 是兜底时间。

## 5. 关键文件

| 作用 | 路径 |
|---|---|
| 本交接 | `vercel-weekly-thesis/HANDOFF.md` |
| 网页生成器 | `scripts/build_weekly_thesis_site.py` |
| 成功邮件 | `scripts/send_weekly_site_email.py` |
| 本地 dispatcher | `scripts/dispatch_weekly_site_publish.sh` |
| 网页 GitHub Action | `.github/workflows/publish-weekly-thesis-site.yml` |
| 源 MD GitHub Action | `.github/workflows/weekly-thesis-brief.yml` |
| launchd 仓库副本 | `launchd/com.robin.ai-investing.weekly-site-publish.plist` |
| launchd 已安装 | `~/Library/LaunchAgents/com.robin.ai-investing.weekly-site-publish.plist` |
| 总周报交接 | `../WEEKLY_THESIS_HANDOFF.md` |

## 6. Vercel 与 GitHub 配置

### Vercel

| 项 | 值 |
|---|---|
| Project | `vercel-weekly-thesis` |
| Scope / Team | `rysbox` / `RYS` |
| Production alias | `vercel-weekly-thesis.vercel.app` |
| Project ID | `prj_PiVcYEKAZJlvEnKaZxkcVeAp3OSD` |
| Org ID | `team_DwShzVTEJs3c0AnzXzNeOYy9` |

### GitHub Secret

- `VERCEL_TOKEN`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `EMAIL_FROM`
- `EMAIL_TO`

### GitHub Repository Variables

- `VERCEL_PROJECT_ID`
- `VERCEL_ORG_ID`

绝对不要把 Token、SMTP 密码或 Secret 实际值写入仓库、日志或交接文件。

Vercel Token 是为该 workflow 单独创建的 team-scoped Token。失效时，在 Vercel Account Tokens 页面创建替代 Token，然后更新 GitHub Secret `VERCEL_TOKEN`。

## 7. 发布流程

`publish-weekly-thesis-site.yml` 的顺序：

1. Checkout 最新 `main`。
2. 解析指定日期或纽约时区最近的星期五。
3. 检查 `.published` 幂等标记。
4. 验证权威 Markdown。
5. 运行网页生成器并保留最近 365 天页面。
6. 检查 HTML 包含日期、Weekly Thesis 和 Research-only。
7. 检查 Vercel Token、Org ID、Project ID。
8. 部署 Vercel Production。
9. 轮询日期 URL，要求 HTTP 200 且页面包含当期日期。
10. 提交网页产物和成功标记。
11. 使用现有 SMTP 发送链接邮件。

邮件只有在第 9 步公开验证成功后才发送。

## 8. 常用操作

### 本地生成，不部署

```bash
cd /Users/leimingyu/Investment/ai-investing-monitor
python3 scripts/build_weekly_thesis_site.py --week-end 2026-07-24 --retention-days 365
python3 -m http.server 4173 --directory vercel-weekly-thesis
```

预览：

```text
http://127.0.0.1:4173/weekly/2026-07-24/
```

### 正常手动触发

```bash
gh workflow run publish-weekly-thesis-site.yml -R robinyew/ai-investing-monitor -f week_end=2026-07-24 -f force=false
```

如果该日期已经成功，workflow 会 skip，不会重复发信。

### 强制重发和重新部署

```bash
gh workflow run publish-weekly-thesis-site.yml -R robinyew/ai-investing-monitor -f week_end=2026-07-24 -f force=true
```

`force=true` 会重新部署并再次发送邮件，只用于明确的补发或测试。

### 查看最近运行

```bash
gh run list -R robinyew/ai-investing-monitor --workflow=publish-weekly-thesis-site.yml --limit 5
```

### 检查本地 launchd

```bash
launchctl print gui/$(id -u)/com.robin.ai-investing.weekly-site-publish
```

### 检查线上页面

```bash
curl -I https://vercel-weekly-thesis.vercel.app/weekly/2026-07-24/
```

## 9. 已验证状态

| 测试 | Run ID | 结果 |
|---|---:|---|
| 首次完整云端发布 | `29970538552` | Success；部署、公开验证、邮件全部成功 |
| 幂等补跑 | `29970627900` | Success；部署和邮件正确 skip |
| 用户要求的测试邮件 | `29970868126` | Success；SMTP accepted，用户确认收到 |

当前 launchd：

- Label：`com.robin.ai-investing.weekly-site-publish`
- 已加载。
- 时间：周五 18:30，Mac 系统时区为 ET。
- `runs=0`、`last exit code=(never exited)` 在第一个正式周五之前属于正常状态。

下一次正式自动日期：`2026-07-24`。

## 10. 故障排查

### 顶部出现 N/A、重大事实为 0、图表为空

原因：源 Markdown 偏离第一版结构。常见情况是把重大事实从 §3 移到 §2、把卡点从 §2 移到 §3，或把证伪条件从 §5 移到其他章节。

当前保护：`run_weekly_thesis_brief.py` 与 `build_weekly_thesis_site.py` 都会校验 v1 契约并阻止发布。不要放宽校验；应使用 `templates/weekly_thesis_brief.md` 重新生成源 Markdown。

### Missing weekly Markdown

原因：17:00 的源周报 workflow 没有成功提交当周 MD。

处理：

1. 查看 `Weekly Thesis Brief` 最近运行。
2. 确认 `weekly_reviews/YYYY-MM-DD.md` 已进入 `main`。
3. 修复后用 `force=true` 补发网页。

### Missing VERCEL_TOKEN

处理：

1. 在 Vercel Account Tokens 创建 team-scoped Token。
2. 更新 GitHub Secret `VERCEL_TOKEN`。
3. 不要把 Token 粘贴进 workflow 或提交记录。

### Vercel 部署成功但公开验证失败

通常是 Production alias 传播延迟。Workflow 会每 15 秒重试，最多 10 次。

检查：

- Vercel deployment 是否 `Ready`。
- 日期 URL 是否 HTTP 200。
- 页面是否确实包含当期日期。
- `vercel.json` 是否仍使用静态输出目录。

### 重复邮件

正常情况下成功标记会阻止重复邮件。检查：

- 是否有人使用了 `force=true`。
- `.published/YYYY-MM-DD.txt` 是否被删除。
- 两次运行是否在成功标记提交前发生并发；workflow 已配置 concurrency 串行化。

### 本地 18:30 没触发

检查 launchd、日志和 GitHub CLI 登录：

```bash
launchctl print gui/$(id -u)/com.robin.ai-investing.weekly-site-publish
tail -100 logs/weekly-site-publish.log
tail -100 logs/weekly-site-publish-error.log
gh auth status
```

即使本地失败，18:40 云端 schedule 仍会补跑。

## 11. 不要做

1. 不要修改原周报 MD 的研究逻辑来适配网页。
2. 不要把 open checklist 或短线工具混入网页发布系统。
3. 不要删除 `.published/`，除非明确要重发。
4. 不要用股价 alone 把 thesis 标为 Damaged。
5. 不要把 Secret 实际值写入文件或命令日志。
6. 不要让本地和云端使用两套不同的网页生成逻辑。
7. 不要把历史样例 `2026-07-18` 当作“星期五日期”模板。
8. 不要声称邮件送达，除非 SMTP 成功且用户确认；自动化只能确认 SMTP accepted。
9. 不要改变 v1 章节职责来适配新的模型写作偏好；模型必须适配模板。

## 12. 新会话开场

```text
继续 Weekly Thesis Vercel Publisher。
先读 vercel-weekly-thesis/HANDOFF.md 和仓库根 WEEKLY_THESIS_HANDOFF.md。
保持原周报任务不变；网页双触发为本地周五 18:30 主触发、GitHub 18:40 补跑。
操作前检查源 MD、.published 标记、最近 GitHub run、Vercel Production 和 launchd。
```
