# AI 基建长期论点与卡点周报 — 2026-07-31

```yaml
week_start: 2026-07-27
week_end: 2026-07-31
generation: claude_code_cli
auto_trade: false
```

<!-- TEMPLATE_VERSION: weekly-v1-zh -->

```yaml
report_type: weekly_thesis_brief
week_start: 2026-07-27
week_end: 2026-07-31
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

**Inputs（本周实际引用）**
- Daily digests: `reports/digest/2026-07-27_opus.md` … `2026-07-30_opus.md`
- News scans: `investment-intelligence-hub/inbox/news/2026-07-27` … `2026-07-31_ai_infrastructure_news.md`
- Pre-market briefs: `reports/daily/2026-07-27.md` … `2026-07-31.md`
- Hub intelligence: 2026-07-29 / 2026-07-30 两日缺失（Missing Sources）
- Prior weekly: `investment-intelligence-hub/memory/weekly_reviews/`

---

## 0. 执行摘要

| 字段 | 本周结论 |
|---|---|
| **总体论点** | Intact — Amazon 与 Alphabet 本周均上修 2026 年 AI 支出，物理卡点（封装、HBM、电力长约）反而更紧；Microsoft 与 Meta 的一手口径仍待补齐，没有一手事实削弱主线 |
| **投资姿态** | 保持论点 + 对单一标的（VRT）深入研究 |
| **本周最大事实** | Amazon 将 2026 年 capex 上调至 $220B（同比 +69%），AWS 收入增速 37% 超预期，并明确点名「更高的存储器成本」为支出驱动之一 |
| **本周最大风险** | Nvidia 对 OpenAI 数据中心的约 $250B 背书（相关交易被报道合计 >$750B）引发循环融资质疑，NVDA CDS 创单日最大升幅，需求质量而非需求数量成为争议核心 |
| **组合逻辑影响** | 局部 — 仅 VRT 因「令人失望的季度」需要重新核对一手财报；其余持仓逻辑未变，周内剧烈涨跌属价格层面 |
| **下个证伪信号** | Microsoft 与 Meta 的 capex 指引一手文件（10-Q / IR），以及 VRT 季报原文中的订单、backlog 与毛利结构 |

**一句话周记：** 本周市场先用价格惩罚了 capex，再用 Amazon/Alphabet 的实际指引把 capex 抬得更高，论点的分歧点已经从「还买不买」转成「谁在出钱、钱从哪来」。

---

## 1. 论点状态

### 1.1 主论点（你在赌什么）

> 默认主线：全球 hyperscaler / neocloud **持续把 capex 转化为 AI 集群**；约束从「有没有 GPU」转向 **电力、冷却、光互连、网络、HBM、先进封装** 等物理卡点；持有/研究的是 **卡点上的秩序机器**，不是主题情绪票。

| 维度 | 状态 | 说明（事实，非股价） |
|---|---|---|
| Demand: hyperscaler / AI capex | Green | Amazon 2026 capex 上调至 $220B（+69% YoY），AWS +37%；Alphabet 上调 2026 AI capex（07-26 口径 $205B，07-30 二手口径约 $195B，需一手核对）；Google Cloud 收入 +82% 至 $24.8B |
| Supply: accelerators & platforms | Green | Nebius 在芬兰完成首台 Nvidia Vera Rubin NVL72 机架现场部署并披露 $40B 已签约 GPU 收入；AMD 以 $14B 锁定 530MW、15 年数据中心容量，形成第二供给源 |
| Chokepoints still binding | Green | CoWoS 交期 52–78 周、ABF 基板膜约 95% 由 Ajinomoto 供应；Amazon 在财报中直接点名存储器成本上升；Apacer CEO 预计 2027 年模组厂 DRAM 供给同比降幅可能 >70% |
| Competition / substitution risk | Yellow | AMD 拿到 530MW 专属容量并保留扩至 2.5GW 的权利；TSMC 与 Kinsus 开发 EMIB-like 封装对标 Intel，CoWoS 产能年扩张 >80% —— 长期可能缓解封装稀缺并改变份额格局 |
| Financing / macro / geo overlay | Yellow | Nvidia 对 OpenAI 俄亥俄 Pike County 园区约 $250B 债务背书；NVDA CDS 单日创纪录上行；Alphabet 出现上市以来首个自由现金流为负的季度，Meta 因 FCF 被 capex 吞噬单日 -10% |
| **Overall** | **Intact** | 需求上修由付款方自身指引确认；本周唯一的一手负面是 VRT 单季度经营表现，属公司层面而非卡点层面 |

**状态定义**
- **Intact：** 无一级事实削弱主线；价格波动单独不构成 Damaged。
- **Watch：** 出现需验证的软信号（二手 capex 传言、竞争叙事升温、指引措辞变软）。
- **Damaged：** 一级来源确认 capex 下修、关键客户砍单、卡点被替代且份额/利润结构破坏，或核心公司商业模式受损。

**相对上周变化：** Improved — 从「等待 Amazon/Microsoft 验证」变成「付款方已用自身指引上修支出」，同时融资结构风险从背景升为显性议题。

---

## 2. 卡点仪表盘

对每个卡点只评 **逻辑与证据**，不评「这周好不好炒」。

| 卡点 | 状态 | 与上周相比 | 证据（最多 2 条） | 核心/观察标的 | 翻转条件 |
|---|---|---|---|---|---|
| Power / cooling / grid | G | → | ① AMD 与 Core Scientific 签 $14B、529–530MW、15 年租约，可扩至 2.5GW；② SK Telecom 分拆 AI 基建公司，目标 15GW 数据中心容量 | VRT, ETN, GEV, PWR, FIX, MPWR, NVTS | 出现电力/冷却交期缩短、产能明显过剩，或 VRT 一手财报显示订单与 backlog 同步走弱 |
| Optical interconnect / 800G–1.6T | G | → | ① Nebius NVL72 现场部署带动机架级光互连拉动；② 07-29 光模块普跌的触发点是 Corning 指引「符合预期」，无任何砍单或价格崩塌的一手证据 | AAOI, COHR, CIEN, LITE, CRDO, ALAB | 出现光模块客户明确砍单、库存天数跳升或长期价格战证据 |
| AI networking / DSP / Ethernet | G | ↑ | ① Amazon 与 Alphabet 上修 capex，机架级部署直接带动网络端口需求；② 日更卡点评分 07-31 由 85 升至 86（improved） | ANET, AVGO, MRVL, NOK | 云厂商披露网络架构自研替代并体现在供应商订单下滑 |
| ASIC / custom silicon | G | → | ① Alphabet 上修 capex，TPU 路线由 AVGO 承接；② Amazon capex 上修中包含 Trainium 体系投入 | AVGO, MRVL, MSFT, GOOGL | 自研 ASIC 出货份额与利润结构同时验证对 merchant GPU 的实质替代 |
| Memory / HBM | G | ↑ | ① Amazon 财报明确将「更高的存储器成本」列为 capex 上升原因；② Apacer CEO 称 2027 年流向模组厂的 DRAM 供给同比可能下降 70%+ | MU | HBM/DRAM 价格与交期同时松动，或云厂商指引存储器成本回落 |
| AI server / rack / EMS | G | → | ① Nebius 完成首台 Vera Rubin NVL72 现场验证，平台从路线图进入部署；② $40B 已签约 GPU 收入指向机架级持续出货 | DELL, SMCI, HPE, CLS, JBL | 机架集成商披露订单推迟或 NVL72 量产节奏落后 |
| Cloud platform demand（付款方） | G | ↑ | ① AWS 收入 +37%，高于约 31% 的一致预期；② Google Cloud 收入 +82% 至 $24.8B | MSFT, GOOGL, (AMZN if tracked) | 任一大型云在一手文件中下修 capex 或明确表述部署放缓 |
| Advanced packaging / CoWoS / 基板 | G | ↑ | ① AT&S CEO 称瓶颈已从晶圆制造上移到先进封装，CoWoS 交期 52–78 周，ABF 膜约 95% 集中于 Ajinomoto；② TSMC 与 Kinsus 开发 EMIB-like 桥接封装，CoWoS 产能年扩张 >80% | TSM, NVDA, AVGO（观察） | CoWoS 交期回落至 26 周以内，或基板供给多元化后加速器出货不再受封装限制 |

**本周卡点迁移（若有）：**
从 `GPU 可得性 / 加速器供给` 转向 `先进封装 + HBM/DRAM + 长周期电力合约`，因为：本周三条独立证据（CoWoS 52–78 周交期、Amazon 点名存储器成本、AMD 15 年 530MW 租约）都指向「芯片之外的物理与合约约束」才是决定出货节奏的变量。

---

## 3. 本周重大事实（最多 5 条）

> 只写 **可能改变 3–12 个月预期** 的事实。股价大跌、分析师调目标价、社媒热帖 → 默认进 §8 噪声。

| # | 日期 | 事实（单行） | 来源等级 | 卡点 | 论点影响 | 标的 |
|---|---|---|---|---|---|---|
| 1 | 2026-07-30 | Amazon 将 2026 年 capex 上调至 $220B（同比 +69%），AWS 收入 +37% 超一致预期，并点名存储器成本上升 | Tier-1（CNBC 转述财报） | Hyperscaler capex / Memory | Reinforce | AMZN, MU, NVDA, AVGO |
| 2 | 2026-07-26 | Alphabet 上调 2026 年 AI 资本支出（07-26 报道口径 $205B），同时出现上市以来首个自由现金流为负的季度；07-30 另有约 $195B 的二手口径，Google Cloud 收入 +82% 至 $24.8B | Tier-1（口径待一手核对） | Hyperscaler capex / ASIC | Reinforce | GOOGL, AVGO, ANET |
| 3 | 2026-07-29 | Vertiv CEO 公开回应 17% 股价下跌与「令人失望的季度」，称其为暂时性 | Tier-1（CEO 表态，季报原文待核） | Power / cooling | Weaken（公司层面） | VRT |
| 4 | 2026-07-27 → 07-29 | Nvidia 与 OpenAI 就俄亥俄 Pike County 园区最高约 $250B 债务背书洽谈（相关交易被报道合计 >$750B），NVDA CDS 创单日最大升幅 | Tier-1（Bloomberg / CNBC / LAT，均引述转述） | Data center / 融资结构 | Neutral（需求量增加，需求质量存疑） | NVDA, MU, TSM |
| 5 | 2026-07-28 → 07-30 | 先进封装成为绑定约束：CoWoS 交期 52–78 周、ABF 膜约 95% 由 Ajinomoto 供应；同期 TSMC 与 Kinsus 开发 EMIB-like 封装，CoWoS 产能年扩张 >80% | Tier-1 / Secondary（高管口径 + The Information） | Advanced packaging | Reinforce（近端），长期为翻转候选 | TSM, NVDA, AVGO |

**Source tier**
- **Primary：** 公司 IR/SEC/官方博客、监管文件、交易所公告
- **Tier-1：** 高质量一手转述仍待核对（主流社/供应链调研需标注）
- **Secondary：** 媒体综合、分析师意见 — 不得单独把 thesis 打成 Damaged

**本周无 Material fact？** No

---

## 4. 组合映射（逻辑层，不是交易层）

本周所有映射均为逻辑层判断，不含任何仓位、买卖或价格建议。

### 4.1 核心计划 / 持仓视角

| 标的 | 产业链角色 | 本周逻辑 | 确信度 | 说明（仅事实） |
|---|---|---|---|---|
| DELL | Server / rack | Stronger | High | Vera Rubin NVL72 进入现场部署，机架级集成需求被确认；周内无公司特定新闻 |
| VRT | Power / cooling | Weaker | Med | 唯一出现公司层面负面一手线索：CEO 承认季度表现令人失望；需读季报原文中的订单/backlog/毛利 |
| AAOI | Optics | Unchanged | Med | 周内暴跌的直接触发是 Corning 指引符合预期与 capex 情绪，非自身订单事件 |
| NVTS | Power semi (higher risk) | Unchanged | Low | 无公司特定事实；周内价格双向剧烈波动，仍属高风险观察类 |
| MPWR | Power mgmt | Unchanged | Med | 无新增一手事实；受益逻辑仍绑定机架供电密度上升 |
| MRVL | Networking / custom | Unchanged | Med | Amazon 与 Alphabet 的 capex 上修间接支持定制硅与互连，但无公司层面新披露 |
| ANET | AI networking | Stronger | High | AWS/GCP 增速与 capex 同步上修，直接对应以太网集群端口需求 |
| AVGO | Networking / ASIC | Stronger | High | Alphabet TPU 与 Amazon Trainium 两条自研线同时受 capex 上修支撑 |
| ETN | Electrical infra | Unchanged | Med | 无公司特定事实；AMD 530MW 长约与 SKT 15GW 计划支持中期电力设备需求 |
| MSFT | Capex payer / platform | Unclear | High | 语料中仅有「与 Amazon 合计约 $400B」的预期与二手提及，未见其自身 capex 指引原文，待一手确认 |
| GOOGL | Capex payer / platform | Stronger | High | capex 上修 + Google Cloud +82%，但首个负 FCF 季度是需要持续跟踪的结构性变量 |

### 4.2 仅观察（本周事实触及时才填写）

| 标的 | 提及原因 | 逻辑影响 | 后续跟踪 |
|---|---|---|---|
| AMD | $14B / 530MW / 15 年 Core Scientific 容量长约 | 强化「电力是绑定约束」的论点，同时抬升加速器端竞争强度 | 等待 AMD 一手文件确认租约条款与容量爬坡节奏 |
| NBIS | 首台 Vera Rubin NVL72 现场投产，$40B 已签约 GPU 收入 | 验证机架级平台从路线图进入部署阶段 | 跟踪 8/12 财报中的交付与 backlog 口径 |
| MU | Amazon 点名存储器成本；2027 年模组端 DRAM 供给或降 70%+ | 支持 HBM/DRAM 紧缺的结构性判断 | 用后续价格与产能公告核对，而非亚洲同业股价 |
| TSM | CoWoS 年扩产 >80%，EMIB-like 封装立项 | 近端封装仍紧，中期可能松动 | 跟踪 CoWoS 交期是否从 52–78 周回落 |
| META | FCF 被 capex 吞噬，管理层暗示云业务 | 付款方支出未减，但投资者容忍度成为新变量 | 核对其 capex 指引一手文件 |

### 4.3 分类变化（本周是否改标签）

| 标的 | 原分类 | 新分类 | 原因（可证伪） | 下次复核 |
|---|---|---|---|---|
| VRT | investment_thesis_candidate | investment_thesis_candidate（pending review） | 仅凭 CEO 口头「暂时性」不足以下调；若季报原文显示订单与 backlog 同时走弱则下调至 watch_only | 2026-08-07 |

其余：`No classification changes.`

---

## 5. 证伪条件与验证队列

### 5.1 有效证伪条件（什么会让你改主意）

| ID | 证伪条件（可观察） | 状态 | 本周证据 | 触发后的动作 |
|---|---|---|---|---|
| F1 | Hyperscaler 集体下修 AI-related capex 或明确放缓部署 | Armed | 反向证据：Amazon 上调至 $220B（+69% YoY），Alphabet 上调 2026 capex，AWS +37%、GCP +82% | Reduce conviction / re-underwrite |
| F2 | 电力/冷却不再是绑定约束（产能明显过剩信号） | Armed | 反向证据：AMD 签 530MW / 15 年长约并保留扩至 2.5GW 权利；SKT 目标 15GW | Revisit power overweight logic |
| F3 | 光互连需求证伪（库存/砍单/价格崩且非短期） | Armed | 本周下跌由 Corning 符合预期指引与情绪驱动，无砍单或库存一手证据 | Optics from candidate → watch/reject |
| F4 | ASIC 替代 merchant GPU **已体现在** 份额与利润（非口头） | Armed | 无份额/利润数据；TPU 与 Trainium 目前与 GPU 采购并行扩张 | Rebalance networking/ASIC map |
| F5 | 核心公司商业模式受损（客户、毛利、产品路线） | Armed | VRT 出现单季度经营不及预期的 CEO 表态，尚无客户流失或毛利结构破坏的一手证据 | Ticker-level deep dive |
| F6 | 先进封装不再是绑定约束（CoWoS 交期显著回落 / 基板供给多元化） | Armed | CoWoS 交期仍为 52–78 周；但 TSMC 年扩产 >80% 与 EMIB-like 路线为潜在松动来源 | 下调封装稀缺溢价假设，重估加速器出货上限 |
| F7 | 供应商融资（vendor financing）结构收缩，导致已宣布的数据中心承诺被撤回或缩量 | Armed | Nvidia 约 $250B 背书仍在洽谈中；NVDA CDS 单日创纪录升幅为早期预警 | 对 neocloud/OpenAI 关联需求做折价，重算需求基数 |

### 5.2 未来 2–4 周验证队列

| 时间 | 待验证事项 | 重要性 | 优先一手来源 |
|---|---|---|---|
| 2026-08-03 起一周内 | MSFT 与 META 的 2026 capex 指引与云增速原文 | 本周唯一未用一手材料验证的两个付款方，决定需求上限判断 | Earnings release / 10-Q / call transcript |
| 2026-08-03 起一周内 | VRT 季报原文：订单、backlog、毛利率、指引口径 | 判定 F5 是公司执行问题还是电力/冷却卡点松动 | 公司 IR / 8-K |
| 2026-08-07 前 | Alphabet capex 数字的一手口径（$205B vs 约 $195B） | 两个媒体口径不一致，直接影响需求规模测算 | Alphabet IR / 10-Q |
| 2026-08-12 | Nebius 财报：Vera Rubin 交付节奏与 $40B 签约收入结构 | 验证机架级平台是否从单机验证进入量产部署 | 公司公告 / 财报 |
| 未来 2–4 周 | Nvidia–OpenAI 背书是否落地为正式文件，以及 CDS 走向 | 决定 F7 是否从 Armed 转向 Triggered | 8-K / 债务发行文件 / 公司公告 |

---

## 6. 价格背景（附录 · 可选 · 非决策主轴）

> 仅用于判断「要不要重读基本面」，**不得**单独改变 thesis。

| 基准 / 组合 | 约 1 周 | 约 1 月 | 解读 |
|---|---:|---:|---|
| SMH | n/a（本周语料未提供指数报价） | n/a（本周语料未提供指数报价） | Volatility only |
| Core equal-weight (qualitative) | 周中显著回撤后于 07-31 大幅反弹（DELL 单日 +9.51%，MSFT +15.51%） | 定性：区间震荡加剧 | Volatility only |
| High-beta optics sleeve | 07-29/30 AAOI 连续 -9.90%、-13.18%，07-31 +17.76%；CIEN -7.09%、MRVL -7.77%/-6.34% 后 +12.18% | 定性：波动放大，方向未定 | Warrants re-read（已完成，见 §3/§4，无一手事实缺口） |

**异常波动触发规则：**
单票或 sleeve 大幅偏离基准 → 打开 §3/§4 重查是否有被忽略的一手事实；若无 → 记为 **pricing noise**。
本周执行结果：VRT -17.26% 对应真实公司事实（季度不及预期），已升入 §3；DELL / AAOI / NVTS / MRVL / CIEN / ETN / ANET 的双位数波动均无公司特定新闻，记为 **pricing noise**。

---

## 7. 下周研究任务

| # | 任务 | 产出 | 完成？ |
|---|---|---|---|
| 1 | 读 MSFT 与 META 财报原文，抽取 2026 capex 指引与云增速 | 更新 capex 付款方汇总表（四家口径统一） | ☐ |
| 2 | 读 VRT 季报原文，拆解订单、backlog、毛利率与指引措辞 | VRT 单票判定备忘：执行问题 vs 需求问题 | ☐ |
| 3 | 用 Alphabet IR 文件核对 2026 capex 是 $205B 还是约 $195B | 修正需求规模测算并标注来源等级 | ☐ |
| 4 | 建立先进封装跟踪表：CoWoS 交期、ABF 基板供给、EMIB-like 进展 | 封装卡点跟踪表 v1 | ☐ |
| 5 | 梳理 vendor financing 敞口清单（NVDA–OpenAI、NVDA–NBIS 持股、AMD–Core Scientific） | 需求质量折价框架草稿 | ☐ |

**Deep dive needed？** Ticker list: VRT
若需要 → 走 `ljg-invest` 规则：`investment-intelligence-hub/docs/ljg_invest_report_rules.md`

---

## 8. 明确忽略的噪声

- VRT -17.26%、AAOI -13.18%/+17.76%、NVTS -12.27%/+13.10%、MRVL、DELL、CIEN、ETN、ANET 的单日双位数波动本身（除 VRT 外均无公司特定新闻）。
- MSFT 单日 +15.51% 的价格记录——在拿到其 capex 指引原文之前不作为基本面结论。
- SK Hynix -14.7%、Samsung -13% 的亚洲存储器抛售：情绪与估值传导，非订单或产能事实。
- 07-31 pre-market brief 中把 Sprouts Farmers Market、Banc of California、General Dynamics、Hayward、IDEX、Littelfuse 等财报映射到 MSFT/NOK 的条目：ticker 匹配噪声，不构成任何信息。
- Pre-market brief 中反复出现的 GOOGL/MSFT 产品与开发者博客条目（BigQuery IAM 标签、llm-d 时间片、Foundry 可用性等）：产品公告，不改变 3–12 个月预期。
- 「Marvell vs Nvidia」「值得买的顶级股票」类无新增事实的媒体聚合文章；Penguin Solutions 自述「内存才是瓶颈」的公司口径（YTD +123%，存在推广偏差，仅作方向参考）。
- 分析师目标价、日线支撑阻力、开盘清单。

---

## 9. 下周延续记忆

| 项目 | 内容 |
|---|---|
| Open questions | ① Alphabet 2026 capex 究竟是 $205B 还是约 $195B？② Nvidia 对 OpenAI 的背书是否会落成正式债务文件？③ VRT 的差季度是执行问题还是订单问题？④ 在大型云厂商 FCF 承压后，capex 上修还能持续几个季度？ |
| Pending primary confirms | MSFT capex 指引、META capex 指引、Alphabet 10-Q capex 口径、VRT 季报原文、AMD–Core Scientific 租约条款；另需补齐 07-29 与 07-30 缺失的 Hub Intelligence Brief |
| Thesis one-liner for next week | 需求端已由付款方自身指引确认上修，主线争议点转移到「融资结构的可持续性」与「封装/存储器的物理上限」，不在股价波动上。 |
| Do not forget | 07-31 的普涨与 07-29/30 的普跌是同一批标的、同一批缺乏公司新闻的价格事件；不要把任何一端当成论点变化。VRT 是本周唯一需要一手复核的持仓级事实。 |

---

## 10. 签署

| 字段 | 内容 |
|---|---|
| Author | AI 基建研究助理（Claude Agent，research-only） |
| Time spent | ~50 min |
| Sources checked | digests（4 份）/ news scans（5 份）/ pre-market briefs（5 份）；Hub intelligence 2 日缺失 |
| Confidence in this week’s grade | Med（需求端高置信，VRT 与 MSFT 口径待一手确认） |
| Next brief due | 2026-08-07 |
