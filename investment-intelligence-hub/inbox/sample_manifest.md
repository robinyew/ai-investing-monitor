# Phase 2 Sample Ingestion Manifest

Timestamp: 2026-06-07T12:13:27-0400

This manifest registers exactly three sample inputs for source-record fixtures only. No source contents were copied into `sample.jsonl`, and no extraction, scoring, thesis mapping, portfolio mapping, or brief generation was implemented.

## Daily Report Sample

| Field | Value |
|---|---|
| Local path | `ai-investing-monitor/reports/daily/2026-06-07.md` |
| File size | 17,619 bytes |
| Content hash | `sha256:fedfb21d3e789ab3f1ffb54a652405f5a4a210e8cad8434a30eb36f443c27ca6` |
| Why selected | Required Phase 2 daily report sample. |
| Registered in `sample.jsonl` | Yes, `src_sample_daily_20260607` |

## ljg-Invest Sample

| Field | Value |
|---|---|
| Local path | `20260602T184149==z--投资分析-nok.org` |
| File size | 17,840 bytes |
| Content hash | `sha256:6ce69191987f565b1bdd717f1ee17f5622c4569f30c0e71d098e5b1d8c8dfcee` |
| Why selected | Required Phase 2 ljg-Invest sample file existed. |
| Registered in `sample.jsonl` | Yes, `src_sample_ljg_invest_nok_20260602` |

## X Post Sample

| Field | Value |
|---|---|
| Local path | `x-to-markdown/artofspecuycky/2062623036722049427.md` |
| File size | 2,530 bytes |
| Content hash | `sha256:db9d668fda4dcd1084ebf70fba72fee10435d643a85f015e8760078250b4ee5c` |
| Why selected | Most recent existing `.md` file under `x-to-markdown/` by filesystem modification time. |
| Registered in `sample.jsonl` | Yes, `src_sample_x_artofspecuycky_2062623036722049427` |

