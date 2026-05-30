from __future__ import annotations

import smtplib
from email.message import EmailMessage

from utils import env, today_est


REQUIRED = ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "EMAIL_FROM", "EMAIL_TO", "REPORT_BASE_URL"]


def send_email(report_date: str | None = None) -> bool:
    report_date = report_date or today_est()
    missing = [name for name in REQUIRED if not env(name)]
    if missing:
        print(f"Email skipped: missing secrets/env vars: {', '.join(missing)}")
        return False

    base_url = env("REPORT_BASE_URL").rstrip("/")
    report_url = f"{base_url}/{report_date}.html"
    msg = EmailMessage()
    msg["Subject"] = f"AI Investing Pre-Market Brief - {report_date}"
    msg["From"] = env("EMAIL_FROM")
    msg["To"] = env("EMAIL_TO")
    msg.set_content(
        f"""AI Investing Pre-Market Brief {report_date} is ready.

Report link:
{report_url}

ChatGPT Handoff:
The handoff is included at the top of the report.

No trading actions were taken.
"""
    )

    port = int(env("SMTP_PORT", "587"))
    try:
        with smtplib.SMTP(env("SMTP_HOST"), port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(env("SMTP_USERNAME"), env("SMTP_PASSWORD"))
            smtp.send_message(msg)
        print(f"Email sent to {env('EMAIL_TO')}")
        return True
    except Exception as exc:
        print(f"Email failed but report generation is complete: {exc}")
        return False


if __name__ == "__main__":
    send_email()
