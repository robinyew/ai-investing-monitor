from __future__ import annotations

from pathlib import Path

import markdown

from build_report import build_reports
from utils import ROOT, ensure_dirs, load_yaml


STYLE = """
:root { color-scheme: light; --bg:#f6f7f9; --panel:#fff; --text:#17202a; --muted:#5d6b7a; --line:#d9dee5; --accent:#0f766e; --warn:#b45309; }
* { box-sizing: border-box; }
body { margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif; background:var(--bg); color:var(--text); line-height:1.5; }
main { width:min(1060px,100%); margin:0 auto; padding:18px; }
header { padding:20px 0 10px; }
h1 { font-size:1.7rem; margin:0 0 8px; letter-spacing:0; }
h2 { font-size:1.25rem; margin:28px 0 10px; border-bottom:1px solid var(--line); padding-bottom:6px; }
h3 { font-size:1rem; margin:18px 0 6px; }
a { color:var(--accent); overflow-wrap:anywhere; }
.panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; margin:14px 0; box-shadow:0 1px 2px rgba(0,0,0,.04); }
.alert { border-left:4px solid var(--warn); }
table { width:100%; border-collapse:collapse; margin:10px 0; font-size:.92rem; }
th, td { border:1px solid var(--line); padding:8px; text-align:left; vertical-align:top; }
th { background:#eef2f5; }
pre, code { white-space:pre-wrap; overflow-wrap:anywhere; }
@media (max-width: 760px) {
  main { padding:12px; }
  table { display:block; overflow-x:auto; white-space:nowrap; }
  h1 { font-size:1.35rem; }
}
"""


def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>{STYLE}</style>
</head>
<body>
<main>{body}</main>
</body>
</html>
"""


def build_html() -> dict:
    ensure_dirs()
    result = build_reports()
    date = result["date"]
    md_text = Path(result["markdown"]).read_text(encoding="utf-8")
    handoff_text = Path(result["handoff"]).read_text(encoding="utf-8")
    html = markdown.markdown(md_text, extensions=["tables", "toc"])
    handoff_html = markdown.markdown(handoff_text, extensions=["tables"])
    alerts = "<p>No major automated risk flags.</p>"
    if "Needs ChatGPT review: Yes" in md_text:
        alerts = "<p>Automated flags were detected. Review the handoff and risk flags before drawing conclusions.</p>"
    body = f"""
<header>
  <h1>AI Investing Pre-Market Brief - {date}</h1>
  <p>Research only. No brokerage connection, no trade execution, no buy/sell instructions.</p>
</header>
<section class="panel alert">
  <h2>Important Alerts</h2>
  {alerts}
</section>
<section class="panel">
  <h2>ChatGPT Handoff Summary</h2>
  {handoff_html}
</section>
<section class="panel">
  {html}
</section>
"""
    report_path = ROOT / f"docs/reports/{date}.html"
    report_path.write_text(_page(f"AI Investing Pre-Market Brief - {date}", body), encoding="utf-8")
    update_index()
    return {**result, "html": str(report_path)}


def update_index() -> None:
    settings = load_yaml("config/report_settings.yaml")
    limit = int(settings.get("recent_reports_on_index", 20))
    reports = sorted((ROOT / "docs/reports").glob("*.html"), reverse=True)[:limit]
    links = "\n".join([f'<li><a href="reports/{path.name}">{path.stem}</a></li>' for path in reports]) or "<li>No reports yet.</li>"
    body = f"""
<header>
  <h1>AI Investing Monitor</h1>
  <p>Pre-market AI investing research briefs for human review only.</p>
</header>
<section class="panel">
  <h2>Recent Reports</h2>
  <ul>{links}</ul>
</section>
"""
    (ROOT / "docs/index.html").write_text(_page("AI Investing Monitor", body), encoding="utf-8")


if __name__ == "__main__":
    result = build_html()
    print(f"Wrote {result['html']}")
