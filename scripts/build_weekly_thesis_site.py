#!/usr/bin/env python3
"""Build the Vercel weekly-thesis site from the canonical weekly Markdown.

The site renderer is deterministic. HTML Anything's data-report design is the
presentation template; the weekly Markdown remains the content source of truth.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import markdown

from run_weekly_thesis_brief import validate_weekly_markdown
from utils import ROOT

NY = ZoneInfo("America/New_York")
SOURCE_DIR = ROOT / "investment-intelligence-hub" / "memory" / "weekly_reviews"
SITE_DIR = ROOT / "vercel-weekly-thesis"
WEEKLY_DIR = SITE_DIR / "weekly"
LATEST_DIR = SITE_DIR / "latest"
PUBLISHED_DIR = SITE_DIR / ".published"


def friday_on_or_before(day: date) -> date:
    return day - timedelta(days=(day.weekday() - 4) % 7)


def strip_md(value: str) -> str:
    value = re.sub(r"!\[[^]]*]\([^)]*\)", "", value)
    value = re.sub(r"\[([^]]+)]\([^)]*\)", r"\1", value)
    value = re.sub(r"[*_`>#]", "", value)
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", value).strip()


def section(markdown_text: str, number: int) -> str:
    match = re.search(rf"(?ms)^##\s+{number}\..*?(?=^##\s+\d+\.|\Z)", markdown_text)
    return match.group(0) if match else ""


def parse_first_table(text: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    for index in range(len(lines) - 2):
        if not lines[index].lstrip().startswith("|"):
            continue
        if not re.match(r"^\s*\|?\s*:?-{3,}", lines[index + 1]):
            continue
        headers = [strip_md(cell) for cell in lines[index].strip().strip("|").split("|")]
        rows: list[dict[str, str]] = []
        for line in lines[index + 2 :]:
            if not line.lstrip().startswith("|"):
                break
            cells = [strip_md(cell) for cell in line.strip().strip("|").split("|")]
            cells += [""] * (len(headers) - len(cells))
            rows.append(dict(zip(headers, cells)))
        return rows
    return []


def first_value(row: dict[str, str], names: tuple[str, ...]) -> str:
    for name in names:
        for key, value in row.items():
            if name.lower() in key.lower():
                return value
    return ""


def executive_map(markdown_text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in parse_first_table(section(markdown_text, 0)):
        keys = list(row)
        if len(keys) >= 2:
            result[strip_md(row[keys[0]]).lower()] = strip_md(row[keys[1]])
    return result


def executive_value(values: dict[str, str], *needles: str, default: str = "N/A") -> str:
    for key, value in values.items():
        if any(needle.lower() in key for needle in needles):
            return value or default
    return default


def table_status_counts(markdown_text: str) -> tuple[int, int, int]:
    rows = parse_first_table(section(markdown_text, 1))
    green = yellow = damaged = 0
    for row in rows:
        dimension = first_value(row, ("维度", "dimension"))
        if dimension.lower() == "overall" or "overall" in dimension.lower():
            continue
        status = first_value(row, ("状态", "status")).lower()
        if "green" in status or status == "g" or "绿" in status:
            green += 1
        elif "yellow" in status or status == "y" or "watch" in status or "黄" in status:
            yellow += 1
        elif "damaged" in status or "red" in status or status == "r" or "红" in status:
            damaged += 1
    return green, yellow, damaged


def chokepoint_coverage(markdown_text: str) -> tuple[list[str], list[int]]:
    labels: list[str] = []
    counts: list[int] = []
    for row in parse_first_table(section(markdown_text, 2)):
        label = first_value(row, ("Chokepoint", "卡点"))
        tickers = first_value(row, ("Core/watch tickers", "tickers", "标的"))
        if not label:
            continue
        short = label.split("/")[0].strip()
        labels.append(short[:22])
        counts.append(len(re.findall(r"\b[A-Z]{1,5}\b", tickers)))
    return labels[:10], counts[:10]


def remove_header_and_yaml(markdown_text: str) -> str:
    text = re.sub(r"^#\s+.*?\n", "", markdown_text, count=1)
    text = re.sub(r"(?ms)^```yaml\s*\n.*?^```\s*\n?", "", text, count=1)
    return text.strip()


def short_title(markdown_text: str, week_end: str) -> str:
    match = re.search(r"^#\s+(.+)$", markdown_text, re.MULTILINE)
    if not match:
        return f"AI 基建长期论点与卡点周报 — {week_end}"
    return strip_md(match.group(1))


def statement(markdown_text: str) -> str:
    for pattern in (
        r"\*\*一句话周记：\*\*\s*(.+)",
        r"\*\*One-liner:\*\*\s*(.+)",
        r"\*\*One-liner：\*\*\s*(.+)",
    ):
        match = re.search(pattern, markdown_text)
        if match:
            return strip_md(match.group(1))
    return "长线 AI 基建论点、卡点与证伪条件的每周复核。"


def validate_render_inputs(markdown_text: str) -> list[str]:
    """Catch parser/template drift before an incomplete page reaches production."""
    errors: list[str] = []
    values = executive_map(markdown_text)
    for label, needles in (
        ("总体论点", ("overall thesis", "总体论点")),
        ("投资姿态", ("posture", "姿态")),
        ("本周最大事实", ("biggest fact", "最大事实")),
        ("下个证伪信号", ("next falsifier", "下个证伪")),
    ):
        if executive_value(values, *needles) == "N/A":
            errors.append(f"missing KPI source field: {label}")
    green, yellow, damaged = table_status_counts(markdown_text)
    if green + yellow + damaged == 0:
        errors.append("section 1 produced no thesis status chart data")
    labels, coverage = chokepoint_coverage(markdown_text)
    if not labels or not any(coverage):
        errors.append("section 2 produced no chokepoint coverage chart data")
    if len(parse_first_table(section(markdown_text, 5))) < 3:
        errors.append("section 5 produced fewer than 3 active falsifiers")
    return errors


def render_report(markdown_text: str, week_end: str) -> str:
    values = executive_map(markdown_text)
    overall = executive_value(values, "overall thesis", "总体论点")
    overall_label = re.split(r"\s+[—-]\s+", overall, maxsplit=1)[0]
    overall_detail = overall[len(overall_label) :].lstrip(" —-") or "价格波动单独不改变 thesis 状态"
    posture = executive_value(values, "posture", "姿态")
    biggest_fact = executive_value(values, "biggest fact", "最大事实")
    next_falsifier = executive_value(values, "next falsifier", "下个证伪")
    fact_rows = parse_first_table(section(markdown_text, 3))
    falsifier_rows = parse_first_table(section(markdown_text, 5))
    material_count = sum(
        1
        for row in fact_rows
        if any(
            term in " ".join(row.values()).lower()
            for term in ("reinforce", "weaken", "material", "强化", "削弱", "重大")
        )
    )
    green, yellow, damaged = table_status_counts(markdown_text)
    labels, coverage = chokepoint_coverage(markdown_text)

    body_html = markdown.markdown(
        remove_header_and_yaml(markdown_text),
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
        extension_configs={"toc": {"permalink": False}},
    )
    title = short_title(markdown_text, week_end)
    title_html = html.escape(title)
    summary_html = html.escape(statement(markdown_text))
    chart_payload = json.dumps(
        {
            "status": [green, yellow, damaged],
            "coverageLabels": labels,
            "coverage": coverage,
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")

    replacements = {
        "@@TITLE@@": title_html,
        "@@WEEK_END@@": html.escape(week_end),
        "@@SUMMARY@@": summary_html,
        "@@OVERALL@@": html.escape(overall_label),
        "@@OVERALL_DETAIL@@": html.escape(overall_detail),
        "@@POSTURE@@": html.escape(posture),
        "@@MATERIAL_COUNT@@": str(material_count),
        "@@FALSIFIER_COUNT@@": str(len(falsifier_rows)),
        "@@BIGGEST_FACT@@": html.escape(biggest_fact),
        "@@NEXT_FALSIFIER@@": html.escape(next_falsifier),
        "@@REPORT_BODY@@": body_html,
        "@@CHART_DATA@@": chart_payload,
        "@@GENERATED_AT@@": datetime.now(NY).strftime("%Y-%m-%d %H:%M %Z"),
    }
    output = REPORT_TEMPLATE
    for token, value in replacements.items():
        output = output.replace(token, value)
    return output


def retained_dates(cutoff: date) -> list[str]:
    dates: list[str] = []
    if not WEEKLY_DIR.exists():
        return dates
    for path in WEEKLY_DIR.iterdir():
        if not path.is_dir():
            continue
        try:
            report_date = date.fromisoformat(path.name)
        except ValueError:
            continue
        if report_date < cutoff:
            shutil.rmtree(path)
            marker = PUBLISHED_DIR / f"{path.name}.txt"
            if marker.exists():
                marker.unlink()
        elif (path / "index.html").exists():
            dates.append(path.name)
    return sorted(dates, reverse=True)


def render_archive(dates: list[str]) -> str:
    items = "\n".join(
        f'<li><a href="/weekly/{day}/"><span>{day}</span><strong>Weekly Thesis Brief</strong></a></li>'
        for day in dates
    )
    return ARCHIVE_TEMPLATE.replace("@@ITEMS@@", items).replace(
        "@@UPDATED@@", datetime.now(NY).strftime("%Y-%m-%d %H:%M %Z")
    )


def build(week_end: str, retention_days: int) -> tuple[Path, list[str]]:
    report_date = date.fromisoformat(week_end)
    source = SOURCE_DIR / f"{week_end}.md"
    if not source.exists():
        raise SystemExit(f"Missing weekly Markdown: {source}")
    markdown_text = source.read_text(encoding="utf-8")
    if len(markdown_text) < 1200 or "## 0." not in markdown_text:
        raise SystemExit(f"Weekly Markdown is incomplete or still a scaffold: {source}")
    require_chinese = report_date >= date(2026, 7, 31)
    validation_errors = validate_weekly_markdown(markdown_text, require_chinese=require_chinese)
    validation_errors.extend(validate_render_inputs(markdown_text))
    if validation_errors:
        raise SystemExit(
            "Weekly Markdown does not match the v1 render contract: "
            + "; ".join(validation_errors)
        )

    report_html = render_report(markdown_text, week_end)
    report_dir = WEEKLY_DIR / week_end
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "index.html"
    report_path.write_text(report_html, encoding="utf-8")

    LATEST_DIR.mkdir(parents=True, exist_ok=True)
    (LATEST_DIR / "index.html").write_text(report_html, encoding="utf-8")
    (SITE_DIR / "index.html").write_text(report_html, encoding="utf-8")

    cutoff = report_date - timedelta(days=retention_days)
    dates = retained_dates(cutoff)
    (SITE_DIR / "archive.html").write_text(render_archive(dates), encoding="utf-8")
    return report_path, dates


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the weekly thesis Vercel site")
    parser.add_argument("--week-end", default=None, help="Report date YYYY-MM-DD")
    parser.add_argument("--retention-days", type=int, default=365)
    args = parser.parse_args()

    week_end = args.week_end or friday_on_or_before(datetime.now(NY).date()).isoformat()
    path, dates = build(week_end, args.retention_days)
    print(f"Built: {path}")
    print(f"Latest: {LATEST_DIR / 'index.html'}")
    print(f"Archive reports retained: {len(dates)}")
    print(f"Public path: /weekly/{week_end}/")
    return 0


REPORT_TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="AI 基建长期论点、卡点与证伪条件周报。">
  <title>@@TITLE@@</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
  <script src="https://unpkg.com/lucide@0.468.0/dist/umd/lucide.min.js"></script>
  <style>
    :root{--ink:#161814;--muted:#676b63;--faint:#8b8f86;--line:#dfe2da;--paper:#f4f5f1;--surface:#fff;--soft:#eceee8;--green:#217a4b;--green-soft:#dceee3;--yellow:#9a6a12;--red:#a33a32;--blue:#315f9c;--coral:#c6573f;--purple:#6b5a8e}
    *{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,"SF Pro Text","PingFang SC","Noto Sans SC",system-ui,sans-serif;font-size:14px;line-height:1.65;letter-spacing:0;-webkit-font-smoothing:antialiased}a{color:inherit}.topbar{position:sticky;top:0;z-index:20;display:flex;align-items:center;justify-content:space-between;min-height:56px;padding:8px 28px;border-bottom:1px solid var(--line);background:rgba(244,245,241,.94);backdrop-filter:blur(12px)}.brand{display:flex;align-items:center;gap:12px}.mark{display:grid;place-items:center;width:30px;height:30px;border-radius:6px;background:var(--ink);color:#fff;font-size:11px;font-weight:800}.brand strong{display:block;font-size:13px}.brand span{display:block;color:var(--muted);font-size:11px}.tools{display:flex;align-items:center;gap:8px}.tools a,.tools button{display:grid;place-items:center;width:34px;height:34px;padding:0;border:1px solid #c8ccc2;border-radius:6px;background:#fff;cursor:pointer}.tools svg{width:16px;height:16px}.shell{width:min(1180px,100%);margin:auto;padding:32px 28px 64px}.head{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:24px;align-items:end;padding-bottom:24px;border-bottom:1px solid #c8ccc2}.eyebrow{margin:0 0 8px;color:var(--coral);font-size:11px;font-weight:800;text-transform:uppercase}.head h1{max-width:850px;margin:0;font-family:Georgia,"Songti SC",serif;font-size:38px;line-height:1.14}.dek{max-width:850px;margin:12px 0 0;color:var(--muted)}.date{text-align:right}.date strong{display:block;font:700 17px ui-monospace,SFMono-Regular,Menlo,monospace}.date span{color:var(--muted);font-size:11px}.notice{display:flex;gap:8px;align-items:center;margin-top:16px;padding:10px 12px;border:1px solid #ddd4b9;border-radius:6px;background:#faf3df;color:#71531b;font-size:11px}.notice svg{width:15px}.kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:24px 0}.kpi{min-height:138px;padding:16px;border:1px solid var(--line);border-top:3px solid var(--accent);border-radius:8px;background:var(--surface);box-shadow:0 8px 24px rgba(22,24,20,.06)}.kpi label{color:var(--muted);font-size:10px;font-weight:750;text-transform:uppercase}.kpi b{display:block;margin-top:9px;font-size:22px;line-height:1.15}.kpi p{margin:9px 0 0;color:var(--muted);font-size:10px}.charts{display:grid;grid-template-columns:minmax(0,.8fr) minmax(0,1.2fr);gap:12px;margin-bottom:28px}.panel{padding:17px;border:1px solid var(--line);border-radius:8px;background:var(--surface)}.panel h2{margin:0 0 12px;font-size:13px}.chart{position:relative;height:250px}.report{padding:28px clamp(18px,4vw,52px);border:1px solid var(--line);border-radius:8px;background:var(--surface)}.report h2{scroll-margin-top:80px;margin:42px 0 14px;padding-top:10px;border-top:1px solid var(--line);font-size:22px}.report h2:first-of-type{margin-top:8px}.report h3{margin:26px 0 10px;font-size:16px}.report h4{font-size:14px}.report p,.report li{max-width:900px}.report blockquote{margin:16px 0;padding:4px 16px;border-left:3px solid var(--blue);background:#f3f6fa;color:#3f4f61}.report table{display:block;width:100%;overflow-x:auto;border-collapse:collapse;font-size:11px}.report th{padding:9px 10px;background:var(--soft);color:var(--muted);font-size:9px;text-align:left;text-transform:uppercase;white-space:nowrap}.report td{min-width:90px;padding:10px;border-top:1px solid var(--line);vertical-align:top}.report tbody tr:nth-child(even){background:#fafbf8}.report code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.92em}.report pre{overflow:auto;padding:14px;border-radius:6px;background:#1d201c;color:#eef2eb}.report hr{border:0;border-top:1px solid var(--line);margin:28px 0}.footer{display:flex;justify-content:space-between;gap:18px;padding-top:24px;color:var(--muted);font-size:10px}
    @media(max-width:760px){.topbar{padding:8px 16px}.shell{padding:20px 16px 48px}.head{grid-template-columns:1fr}.head h1{font-size:30px}.date{text-align:left}.kpis,.charts{grid-template-columns:1fr}.kpi{min-height:0}.report{padding:18px 14px}.report h2{font-size:19px}.footer{flex-direction:column;gap:4px}}
    @media print{.topbar{display:none}body{background:#fff}.shell{padding:0}.kpi,.panel,.report{box-shadow:none}.report{border:0}}
  </style>
</head>
<body>
  <header class="topbar"><div class="brand"><div class="mark">AI</div><div><strong>AI 基建研究</strong><span>长期论点周报</span></div></div><div class="tools"><a href="/archive.html" title="历史归档" aria-label="历史归档"><i data-lucide="archive"></i></a><button title="打印或保存为 PDF" aria-label="打印或保存为 PDF" onclick="window.print()"><i data-lucide="printer"></i></button></div></header>
  <main class="shell">
    <section class="head"><div><p class="eyebrow">每周论点与卡点复核</p><h1>@@TITLE@@</h1><p class="dek">@@SUMMARY@@</p></div><div class="date"><strong>@@WEEK_END@@</strong><span>周报日期 · 美东时间</span></div></section>
    <div class="notice"><i data-lucide="shield-check"></i>仅供研究。不连接券商，不生成买卖指令，不设目标价。</div>
    <section class="kpis">
      <article class="kpi" style="--accent:var(--green)"><label>总体论点</label><b style="color:var(--green)">@@OVERALL@@</b><p>@@OVERALL_DETAIL@@</p></article>
      <article class="kpi" style="--accent:var(--blue)"><label>投资姿态</label><b style="color:var(--blue)">@@POSTURE@@</b><p>多月到多年研究视角</p></article>
      <article class="kpi" style="--accent:var(--coral)"><label>重大事实</label><b>@@MATERIAL_COUNT@@</b><p>@@BIGGEST_FACT@@</p></article>
      <article class="kpi" style="--accent:var(--red)"><label>有效证伪条件</label><b>@@FALSIFIER_COUNT@@</b><p>@@NEXT_FALSIFIER@@</p></article>
    </section>
    <section class="charts"><article class="panel"><h2>论点状态构成</h2><div class="chart"><canvas id="statusChart"></canvas></div></article><article class="panel"><h2>卡点观察覆盖</h2><div class="chart"><canvas id="coverageChart"></canvas></div></article></section>
    <article class="report">@@REPORT_BODY@@</article>
    <footer class="footer"><span>AI 基建长期论点周报</span><span>生成于 @@GENERATED_AT@@ · 保存一年</span></footer>
  </main>
  <script>
    if(window.lucide)lucide.createIcons();
    const reportData=@@CHART_DATA@@;
    Chart.defaults.color='#676b63';Chart.defaults.font.family='Inter, SF Pro Text, PingFang SC, system-ui, sans-serif';
    new Chart(document.getElementById('statusChart'),{type:'doughnut',data:{labels:['稳固','观察','受损'],datasets:[{data:reportData.status,backgroundColor:['#217a4b','#c79531','#a33a32'],borderColor:'#fff',borderWidth:4}]},options:{responsive:true,maintainAspectRatio:false,cutout:'68%',plugins:{legend:{position:'bottom',labels:{usePointStyle:true,boxWidth:8}}}}});
    new Chart(document.getElementById('coverageChart'),{type:'bar',data:{labels:reportData.coverageLabels,datasets:[{data:reportData.coverage,backgroundColor:['#217a4b','#c79531','#315f9c','#6b5a8e','#c6573f','#3e827f','#53734c'],borderRadius:4}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{display:false}},y:{beginAtZero:true,ticks:{stepSize:1},grid:{color:'#e6e8e1'}}}}});
  </script>
</body>
</html>'''


ARCHIVE_TEMPLATE = r'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Weekly Thesis Archive</title><style>*{box-sizing:border-box}body{margin:0;background:#f4f5f1;color:#161814;font-family:Inter,"PingFang SC",system-ui,sans-serif;letter-spacing:0}.wrap{width:min(820px,100%);margin:auto;padding:48px 20px}a{color:inherit;text-decoration:none}header{padding-bottom:22px;border-bottom:1px solid #c8ccc2}h1{margin:0;font-family:Georgia,"Songti SC",serif;font-size:36px}p{color:#676b63}ul{padding:0;list-style:none}li{border-bottom:1px solid #dfe2da}li a{display:grid;grid-template-columns:140px 1fr;gap:18px;padding:16px 4px}li a:hover{color:#315f9c}span{font-family:ui-monospace,Menlo,monospace;font-size:12px}strong{font-size:14px}.back{display:inline-block;margin-top:24px;color:#315f9c;font-size:13px}@media(max-width:520px){li a{grid-template-columns:1fr;gap:4px}h1{font-size:30px}}</style></head><body><main class="wrap"><header><h1>Weekly Thesis Archive</h1><p>过去一年长期 AI 基建论点复核。更新于 @@UPDATED@@。</p></header><ul>@@ITEMS@@</ul><a class="back" href="/">返回最新报告</a></main></body></html>'''


if __name__ == "__main__":
    raise SystemExit(main())
