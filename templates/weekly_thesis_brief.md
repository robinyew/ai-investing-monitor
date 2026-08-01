# AI 基建长期论点与卡点周报 — {{WEEK_END}}

<!-- TEMPLATE_VERSION: weekly-v1-zh -->
<!-- 固定要求：正文使用简体中文；保留 0–10 章节编号、章节职责和首张表字段，不得自由改版。 -->

```yaml
report_type: weekly_thesis_brief
week_start: {{WEEK_START}}
week_end: {{WEEK_END}}
timezone: America/New_York
horizon: multi_month_to_multi_year
audience: long_term_AI_infra_investor
default_posture: Hold thesis unless falsified
auto_trade: false
price_targets: false
buy_sell_instructions: false
```

**Research-only.** 不连接券商，不生成买卖指令，不设目标价。  
**用途：** 用 10–15 分钟更新「主线还在不在 / 逻辑有没有被证伪 / 下阶段盯什么」。  
**不是：** 下周涨跌预测、开盘策略、短线观察清单。

**Inputs（可选引用）**
- Daily digests: `reports/digest/{{WEEK_START}}` … `{{WEEK_END}}`
- News scans: `investment-intelligence-hub/inbox/news/`
- Pre-market briefs: `reports/daily/`
- Hub intelligence: `investment-intelligence-hub/reports/daily_intelligence/`
- Prior weekly: `investment-intelligence-hub/memory/weekly_reviews/`
- Deep dives: `investment-intelligence-hub/reports/ljg_invest/`

---

## 0. 执行摘要

| 字段 | 本周结论 |
|---|---|
| **总体论点** | Intact / Watch / Damaged — {{THESIS_ONE_LINER}} |
| **投资姿态** | 保持论点 / 深入研究 / 降低确信度 / 重新评估 |
| **本周最大事实** | {{BIGGEST_FACT}} |
| **本周最大风险** | {{BIGGEST_RISK}} |
| **组合逻辑影响** | 无 / 局部 / 广泛 — {{PORTFOLIO_IMPACT}} |
| **下个证伪信号** | {{NEXT_FALSIFIER}} |

**一句话周记：** {{WEEK_SUMMARY_1_SENTENCE}}

---

## 1. 论点状态

### 1.1 主论点（你在赌什么）

> 默认主线（可改）：全球 hyperscaler / neocloud **持续把 capex 转化为 AI 集群**；约束从「有没有 GPU」转向 **电力、冷却、光互连、网络、HBM** 等物理卡点；持有/研究的是 **卡点上的秩序机器**，不是主题情绪票。

| 维度 | 状态 | 说明（事实，非股价） |
|---|---|---|
| Demand: hyperscaler / AI capex | Green / Yellow / Red | |
| Supply: accelerators & platforms | Green / Yellow / Red | |
| Chokepoints still binding | Green / Yellow / Red | |
| Competition / substitution risk | Green / Yellow / Red | |
| Financing / macro / geo overlay | Green / Yellow / Red | |
| **Overall** | **Intact / Watch / Damaged** | |

**状态定义**
- **Intact：** 无一级事实削弱主线；价格波动单独不构成 Damaged。
- **Watch：** 出现需验证的软信号（二手 capex 传言、竞争叙事升温、指引措辞变软）。
- **Damaged：** 一级来源确认 capex 下修、关键客户砍单、卡点被替代且份额/利润结构破坏，或核心公司商业模式受损。

**相对上周变化：** Unchanged / Improved / Deteriorated — {{THESIS_DELTA}}

---

## 2. 卡点仪表盘

对每个卡点只评 **逻辑与证据**，不评「这周好不好炒」。

| 卡点 | 状态 | 与上周相比 | 证据（最多 2 条） | 核心/观察标的 | 翻转条件 |
|---|---|---|---|---|---|
| Power / cooling / grid | G / Y / R | ↑ → ↓ | | VRT, ETN, GEV, PWR, FIX, MPWR, NVTS | |
| Optical interconnect / 800G–1.6T | G / Y / R | ↑ → ↓ | | AAOI, COHR, CIEN, LITE, CRDO, ALAB | |
| AI networking / DSP / Ethernet | G / Y / R | ↑ → ↓ | | ANET, AVGO, MRVL, NOK | |
| ASIC / custom silicon | G / Y / R | ↑ → ↓ | | AVGO, MRVL, MSFT, GOOGL | |
| Memory / HBM | G / Y / R | ↑ → ↓ | | MU | |
| AI server / rack / EMS | G / Y / R | ↑ → ↓ | | DELL, SMCI, HPE, CLS, JBL | |
| Cloud platform demand (payer) | G / Y / R | ↑ → ↓ | | MSFT, GOOGL, (AMZN if tracked) | |

**本周卡点迁移（若有）：**  
从 `____` 转向 `____`，因为：____

---

## 3. 本周重大事实（最多 5 条）

> 只写 **可能改变 3–12 个月预期** 的事实。股价大跌、分析师调目标价、社媒热帖 → 默认进 §8 噪声。

| # | 日期 | 事实（单行） | 来源等级 | 卡点 | 论点影响 | 标的 |
|---|---|---|---|---|---|---|
| 1 | | | Primary / Tier-1 / Secondary | | Reinforce / Neutral / Weaken | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |

**Source tier**
- **Primary：** 公司 IR/SEC/官方博客、监管文件、交易所公告
- **Tier-1：** 高质量一手转述仍待核对（主流社/供应链调研需标注）
- **Secondary：** 媒体综合、分析师意见 — 不得单独把 thesis 打成 Damaged

**本周无 Material fact？** Yes / No  
若 No：写「No material fundamental change; thesis carry-forward.」然后可跳到 §5–§7 精简填写。

---

## 4. 组合映射（逻辑层，不是交易层）

对照 `config/watchlists.yaml` 核心组 / 观察组。

### 4.1 核心计划 / 持仓视角

| 标的 | 产业链角色 | 本周逻辑 | 确信度 | 说明（仅事实） |
|---|---|---|---|---|
| DELL | Server / rack | Stronger / Unchanged / Weaker / Unclear | High / Med / Low | |
| VRT | Power / cooling | | | |
| AAOI | Optics | | | |
| NVTS | Power semi (higher risk) | | | |
| MPWR | Power mgmt | | | |
| MRVL | Networking / custom | | | |
| ANET | AI networking | | | |
| AVGO | Networking / ASIC | | | |
| ETN | Electrical infra | | | |
| MSFT | Capex payer / platform | | | |
| GOOGL | Capex payer / platform | | | |

### 4.2 仅观察（本周事实触及时才填写）

| 标的 | 提及原因 | 逻辑影响 | 后续跟踪 |
|---|---|---|---|
| | | | |

### 4.3 分类变化（本周是否改标签）

| 标的 | 原分类 | 新分类 | 原因（可证伪） | 下次复核 |
|---|---|---|---|---|
| — | investment_thesis_candidate / speculation_thesis / watch_only / rejected | | | |

无变更则写：`No classification changes.`

---

## 5. 证伪条件与验证队列

### 5.1 有效证伪条件（什么会让你改主意）

| ID | 证伪条件（可观察） | 状态 | 本周证据 | 触发后的动作 |
|---|---|---|---|---|
| F1 | Hyperscaler 集体下修 AI-related capex 或明确放缓部署 | Armed / Triggered / Retired | | Reduce conviction / re-underwrite |
| F2 | 电力/冷却不再是绑定约束（产能明显过剩信号） | Armed / Triggered / Retired | | Revisit power overweight logic |
| F3 | 光互连需求证伪（库存/砍单/价格崩且非短期） | Armed / Triggered / Retired | | Optics from candidate → watch/reject |
| F4 | ASIC 替代 merchant GPU **已体现在** 份额与利润（非口头） | Armed / Triggered / Retired | | Rebalance networking/ASIC map |
| F5 | 核心公司商业模式受损（客户、毛利、产品路线） | Armed / Triggered / Retired | | Ticker-level deep dive |

可增删，但必须 **可观察**，禁止「可能好也可能坏」。

### 5.2 未来 2–4 周验证队列

| 时间 | 待验证事项 | 重要性 | 优先一手来源 |
|---|---|---|---|
| | e.g. GOOGL/META/MSFT/AMZN earnings + capex guide | Demand ceiling | Earnings release / 10-Q / call |
| | | | |
| | | | |

---

## 6. 价格背景（附录 · 可选 · 非决策主轴）

> 仅用于判断「要不要重读基本面」，**不得**单独改变 thesis。

| 基准 / 组合 | 约 1 周 | 约 1 月 | 解读 |
|---|---:|---:|---|
| SMH | | | Volatility only / Warrants re-read / Ignore |
| Core equal-weight (qualitative) | | | |
| High-beta optics sleeve | | | |

**异常波动触发规则：**  
单票或 sleeve 大幅偏离基准 → 打开 §3/§4 重查是否有被忽略的一手事实；若无 → 记为 **pricing noise**。

---

## 7. 下周研究任务

最多 5 项。每项必须可完成。

| # | 任务 | 产出 | 完成？ |
|---|---|---|---|
| 1 | | e.g. 更新 GOOGL capex note | ☐ |
| 2 | | | ☐ |
| 3 | | | ☐ |
| 4 | | | ☐ |
| 5 | | | ☐ |

**Deep dive needed？** None / Ticker list: ____  
若需要 → 走 `ljg-invest` 规则：`investment-intelligence-hub/docs/ljg_invest_report_rules.md`

---

## 8. 明确忽略的噪声

列出本周看到但 **明确忽略** 的东西，防止注意力泄漏：

- 
- 
- 

常见默认忽略：日线支撑阻力、开盘清单、分析师 PT、无一级来源的「要翻倍」、单一社媒线程。

---

## 9. 下周延续记忆

| 项目 | 内容 |
|---|---|
| Open questions | |
| Pending primary confirms | |
| Thesis one-liner for next week | |
| Do not forget | |

---

## 10. 签署

| 字段 | 内容 |
|---|---|
| Author | |
| Time spent | ~___ min |
| Sources checked | digests / news / primary / other |
| Confidence in this week’s grade | High / Med / Low |
| Next brief due | {{NEXT_WEEK_END}} |

---

## Writing rules（固定纪律）

1. **默认 Intact + Hold thesis**；升级 Watch/Damaged 需要事实，不需要收盘价。  
2. **§3 最多 5 条**；写不满是好事。  
3. **禁止** 买卖点、仓位比例指令、目标价、明日/本周涨跌预测。  
4. 一手与媒体冲突 → **一手优先**。  
5. 价格只进 §6 附录。  
6. 与日更 digest 关系：digest = 守夜人；weekly = 记忆与仪表盘。  
7. 单票深度不写进周报正文 → 链到 `ljg_invest/{TICKER}/`。

---

## Path conventions

| Kind | Path |
|---|---|
| Template | `templates/weekly_thesis_brief.md` |
| Instance (memory) | `investment-intelligence-hub/memory/weekly_reviews/{{WEEK_END}}.md` |
| Optional digest copy | `reports/digest/{{WEEK_END}}_weekly_thesis.md` |
| Scaffold | `python3 scripts/scaffold_weekly_thesis_brief.py` |

_Week_end = 该周周五（美东）日期，ISO `YYYY-MM-DD`._
