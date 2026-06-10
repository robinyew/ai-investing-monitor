"""Send AI Infrastructure News Scan email.

Reads the Markdown report for the given date, renders it to styled HTML,
and sends it as a full-content email via SMTP.

Usage:
  python scripts/send_news_scan_email.py [YYYY-MM-DD]
  (date defaults to today in Toronto time)

Required env vars (same SMTP secrets used by send_email.py):
  SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM, EMAIL_TO
"""

from __future__ import annotations

import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import markdown as md_lib

from utils import ROOT, env, today_est

REQUIRED = ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "EMAIL_FROM", "EMAIL_TO"]

EMAIL_CSS = """
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
    max-width: 860px;
    margin: 0 auto;
    padding: 24px 20px;
    color: #1a1a1a;
    background: #ffffff;
  }
  h1 {
    color: #111;
    font-size: 1.5em;
    border-bottom: 2px solid #0055cc;
    padding-bottom: 8px;
    margin-bottom: 20px;
  }
  h2 {
    color: #222;
    font-size: 1.15em;
    border-bottom: 1px solid #e0e0e0;
    padding-bottom: 4px;
    margin-top: 32px;
  }
  h3 {
    color: #333;
    font-size: 1em;
    margin-top: 20px;
    margin-bottom: 6px;
  }
  p { line-height: 1.65; margin: 8px 0; }
  ul, ol { padding-left: 20px; margin: 8px 0; }
  li { line-height: 1.65; margin-bottom: 4px; }
  table {
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0 20px;
    font-size: 0.92em;
  }
  th {
    background: #f0f4f8;
    color: #333;
    padding: 7px 12px;
    text-align: left;
    border: 1px solid #d0d8e4;
    font-weight: 600;
  }
  td {
    padding: 7px 12px;
    border: 1px solid #d0d8e4;
    vertical-align: top;
  }
  tr:nth-child(even) td { background: #f8fafc; }
  a { color: #0055cc; text-decoration: none; }
  a:hover { text-decoration: underline; }
  hr {
    border: none;
    border-top: 1px solid #e8e8e8;
    margin: 28px 0;
  }
  code {
    background: #f4f4f4;
    border-radius: 3px;
    padding: 2px 5px;
    font-size: 0.88em;
    font-family: 'SF Mono', 'Fira Mono', monospace;
  }
  blockquote {
    border-left: 3px solid #0055cc;
    margin: 0 0 12px;
    padding: 4px 0 4px 14px;
    color: #555;
  }
  strong { color: #111; }
  em { color: #555; }
"""


def render_html(md_text: str) -> str:
    body = md_lib.markdown(
        md_text,
        extensions=["tables", "fenced_code", "nl2br"],
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
{EMAIL_CSS}
</style>
</head>
<body>
{body}
</body>
</html>"""


def send_news_scan_email(report_date: str | None = None) -> bool:
    report_date = report_date or today_est()

    missing = [k for k in REQUIRED if not env(k)]
    if missing:
        print(f"Email skipped: missing env vars: {', '.join(missing)}")
        return False

    report_path = ROOT / "news" / f"{report_date}_ai_infrastructure_news.md"
    if not report_path.exists():
        print(f"Email skipped: report not found at {report_path}")
        return False

    md_text = report_path.read_text(encoding="utf-8")
    html_content = render_html(md_text)

    # Plain-text fallback: first 4 000 chars of the raw Markdown
    plain_text = (
        f"AI Infrastructure News Scan — {report_date}\n\n"
        + md_text[:4000]
        + ("\n\n[... truncated — see HTML version above ...]" if len(md_text) > 4000 else "")
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"AI Infrastructure News Scan — {report_date}"
    msg["From"] = env("EMAIL_FROM")
    msg["To"] = env("EMAIL_TO")
    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    port = int(env("SMTP_PORT", "587"))
    try:
        with smtplib.SMTP(env("SMTP_HOST"), port, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(env("SMTP_USERNAME"), env("SMTP_PASSWORD"))
            smtp.send_message(msg)
        print(f"News scan email sent to {env('EMAIL_TO')} for {report_date}")
        return True
    except Exception as exc:
        print(f"News scan email failed: {exc}")
        return False


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    ok = send_news_scan_email(date_arg)
    sys.exit(0 if ok else 1)
