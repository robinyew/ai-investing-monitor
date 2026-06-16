"""Send Hub Intelligence Brief email notification.

Sends a link-only email when the Hub Intelligence Brief is published.

Usage:
  python scripts/send_hub_email.py [YYYY-MM-DD]
  (date defaults to today in Toronto time)

Required env vars:
  SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM, EMAIL_TO
"""

from __future__ import annotations

import smtplib
import sys
from email.message import EmailMessage

from utils import env, today_est

REQUIRED = ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "EMAIL_FROM", "EMAIL_TO"]
HUB_BASE_URL = "https://robinyew.github.io/ai-investing-monitor/intelligence"


def send_hub_email(report_date: str | None = None) -> bool:
    report_date = report_date or today_est()

    missing = [k for k in REQUIRED if not env(k)]
    if missing:
        print(f"Email skipped: missing env vars: {', '.join(missing)}")
        return False

    report_url = f"{HUB_BASE_URL}/{report_date}.html"

    msg = EmailMessage()
    msg["Subject"] = f"Hub Intelligence Brief — {report_date}"
    msg["From"] = env("EMAIL_FROM")
    msg["To"] = env("EMAIL_TO")
    msg.set_content(
        f"Hub Intelligence Brief for {report_date} is ready.\n\n"
        f"Report link:\n{report_url}\n\n"
        "Research-only. No buy/sell instructions. No trading automation.\n"
    )

    port = int(env("SMTP_PORT", "587"))
    try:
        with smtplib.SMTP(env("SMTP_HOST"), port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(env("SMTP_USERNAME"), env("SMTP_PASSWORD"))
            smtp.send_message(msg)
        print(f"Hub Intelligence email sent to {env('EMAIL_TO')} for {report_date}")
        return True
    except Exception as exc:
        print(f"Hub Intelligence email failed: {exc}")
        return False


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    ok = send_hub_email(date_arg)
    sys.exit(0 if ok else 1)
