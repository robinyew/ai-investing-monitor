# ljg-invest 报告生成规则

本文件是 ljg-invest 深度研究报告的标准操作规则。**生成任何 ljg-invest 报告前，必须先读取本文件并严格遵守。**

参考样本（已通过验收，作为风格基准）：
`investment-intelligence-hub/reports/ljg_invest/ANET/2026-06-07.md`

---

## 职责范围

只做两件事：
1. 生成 ljg-invest 深度研究报告
2. 更新 `investment-intelligence-hub/memory/ljg_invest_index.yaml`

---

## 禁止修改的内容

- Hub pipeline scripts（`scripts/run_hub_pipeline.py` 等）
- GitHub Actions workflows
- daily report scripts
- `watchlists.yaml`
- `themes.yaml`
- `docs/index.html`
- `docs/intelligence/`
- publish scripts
- Cloudflare Worker
- 任何生产环境自动化
- `memory/portfolio_context.md`
- `processed/` 下的内容
- 当前未在处理的其他 ticker 报告文件

禁止行为：
- 不要 publish
- 不要 commit / push
- 不要生成买入/卖出指令

---

## 输出路径

每个 ticker 的报告必须输出到：

```
investment-intelligence-hub/reports/ljg_invest/{TICKER}/{YYYY-MM-DD}.md
```

---

## 报告顶部 YAML metadata（必须）

```yaml
---
ticker: {TICKER}
company: {COMPANY_NAME}
report_type: ljg_invest
source_tier: 3
date: {YYYY-MM-DD}
thesis_classification: {investment_thesis_candidate | speculation_thesis | watch_only | rejected}
status: needs_primary_source_verification
next_review: {YYYY-MM-DD}
---
```

---

## 报告风格要求

- 使用 ljg-invest 风格（"秩序创造机器"分析框架），不要写成普通公司介绍
- 可以自由组织结构，不需要机械套模板
- 重点分析以下问题：
  - 这家公司到底是什么（穿透表面标签，给出自定义赛道定义）
  - 是否是一台"秩序创造机器"（飞轮 / 冲击反应 / 资源引力综合判定）
  - 飞轮是否存在、转不转得起来
  - S-curve 在哪里（积累期/拐点/加速期/平台期，触发拐点的条件是什么）
  - 瓶颈在哪里
  - 反身性是否存在（市场信念与基本面之间的正向/负向循环）
  - 市场看见什么，我们看见什么（认知折价信号检测）
  - 风险与证伪条件（必须是具体可观测的信号，不能是"既可能好也可能坏"式的废话）
  - 一手信源验证清单

## 报告必须明确声明

- 这是 Tier 3 二手研究（与 `SOURCE_QUALITY["ljg_invest_report"]` 一致）
- 不是一手信源验证结论
- 不构成、也不包含买入/卖出指令
- durable investment thesis 未经一手信源验证不能确认

---

## 更新 index.yaml

每次生成报告后，必须更新 `investment-intelligence-hub/memory/ljg_invest_index.yaml`：

```yaml
{TICKER}:
  latest_report: investment-intelligence-hub/reports/ljg_invest/{TICKER}/{YYYY-MM-DD}.md
  last_run: {YYYY-MM-DD}
  thesis_type: {investment_thesis_candidate | speculation_thesis | watch_only | rejected}
  status: needs_primary_source_verification
  next_review: {YYYY-MM-DD}
  report_count: {COUNT}
```

### 已存在旧报告的 ticker 处理规则

- 不要覆盖旧报告文件
- 新报告使用新的日期文件名
- `latest_report` 指向最新报告
- `report_count` 在原有基础上 +1
- `last_run` 和 `next_review` 更新为本次值

---

## 完成后报告格式

每次生成完成后，只报告以下五项：

1. 报告路径
2. index 是否更新
3. thesis_type
4. next_review
5. 修改了哪些文件
