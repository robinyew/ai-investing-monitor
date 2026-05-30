from __future__ import annotations

import os

from build_html import build_html
from send_email import send_email
from utils import ROOT, report_base_url, write_json


def main() -> None:
    result = build_html()
    report_date = result["date"]
    base_url = report_base_url()
    report_url = f"{base_url}/{report_date}.html" if base_url else f"docs/reports/{report_date}.html"
    handoff_path = f"reports/chatgpt_handoff/{report_date}.md"
    status = {
        "date": report_date,
        "html_path": f"docs/reports/{report_date}.html",
        "markdown_path": f"reports/daily/{report_date}.md",
        "handoff_path": handoff_path,
        "report_url": report_url,
        "status_summary": "Pre-market brief generated successfully. Individual data-source gaps, if any, are marked inside the report.",
    }
    write_json(ROOT / "reports/raw_data/latest_report.json", status)

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as handle:
            for key, value in status.items():
                handle.write(f"{key}={value}\n")

    if os.environ.get("AI_MONITOR_SEND_EMAIL", "").lower() in {"1", "true", "yes"}:
        send_email(report_date)
    else:
        print("SMTP email is optional in version one; skipping email.")

    print(f"Brief date: {report_date}")
    print(f"HTML brief: {status['html_path']}")
    print(f"ChatGPT handoff: {handoff_path}")
    print(f"Report URL: {report_url}")


if __name__ == "__main__":
    main()
