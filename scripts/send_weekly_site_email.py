#!/usr/bin/env python3
"""Send a link-only notification after a verified Vercel publication."""

from __future__ import annotations

import argparse
import smtplib
from email.message import EmailMessage

from utils import env

REQUIRED = ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "EMAIL_FROM", "EMAIL_TO"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Send weekly thesis site notification")
    parser.add_argument("--week-end", required=True)
    parser.add_argument("--base-url", default="https://vercel-weekly-thesis.vercel.app")
    args = parser.parse_args()

    missing = [key for key in REQUIRED if not env(key)]
    if missing:
        print(f"Email failed: missing {', '.join(missing)}")
        return 1

    url = f"{args.base_url.rstrip('/')}/weekly/{args.week_end}/"
    msg = EmailMessage()
    msg["Subject"] = f"Weekly Thesis webpage published — {args.week_end}"
    msg["From"] = env("EMAIL_FROM")
    msg["To"] = env("EMAIL_TO")
    msg.set_content(
        f"Weekly Thesis webpage for {args.week_end} was published and verified.\n\n"
        f"Report:\n{url}\n\n"
        "Archive:\n"
        f"{args.base_url.rstrip('/')}/archive.html\n\n"
        "Research-only. No buy/sell instructions. No trading automation.\n"
    )

    try:
        with smtplib.SMTP(env("SMTP_HOST"), int(env("SMTP_PORT", "587")), timeout=30) as smtp:
            smtp.starttls()
            smtp.login(env("SMTP_USERNAME"), env("SMTP_PASSWORD"))
            smtp.send_message(msg)
        print(f"Publication email sent to {env('EMAIL_TO')}")
        return 0
    except Exception as exc:
        print(f"Publication email failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
