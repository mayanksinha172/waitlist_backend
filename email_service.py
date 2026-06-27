import asyncio
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")


async def _send(to_email: str, name: str, position: int) -> None:
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("Email skipped: GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set")
        return

    first = name.split()[0] if name else "there"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"You're in, {first} — FreelanceGuard AI"
    msg["From"] = f"FreelanceGuard AI <{GMAIL_ADDRESS}>"
    msg["To"] = to_email

    html = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#000000;font-family:'Inter',Arial,sans-serif;-webkit-font-smoothing:antialiased">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#000000;padding:40px 20px">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0" style="max-width:520px;width:100%">

        <!-- Brand -->
        <tr><td style="padding-bottom:32px">
          <span style="font-size:11px;color:#11ff99;font-weight:600;letter-spacing:0.1em;text-transform:uppercase">
            FreelanceGuard AI
          </span>
        </td></tr>

        <!-- Headline -->
        <tr><td style="padding-bottom:16px">
          <h1 style="margin:0;font-size:30px;font-weight:400;line-height:1.2;color:#fcfdff">
            You're #<span style="color:#11ff99">{position}</span> on the list, {first}.
          </h1>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding-bottom:16px">
          <p style="margin:0;font-size:16px;line-height:1.7;color:rgba(252,253,255,0.65)">
            We got you. When we launch, you'll be among the first to know — and as an early member,
            you're locked in for <strong style="color:#11ff99">3 months free</strong>.
          </p>
        </td></tr>

        <tr><td style="padding-bottom:32px">
          <p style="margin:0;font-size:15px;line-height:1.7;color:rgba(252,253,255,0.55)">
            FreelanceGuard AI writes proposals in under 60 seconds, detects scope creep in real time,
            and auto-generates priced change orders — so every hour of work gets paid.
          </p>
        </td></tr>

        <!-- Divider -->
        <tr><td style="border-top:1px solid rgba(255,255,255,0.08);padding-top:24px">
          <p style="margin:0;font-size:11px;color:#464a4d;line-height:1.6">
            You're receiving this because you joined the FreelanceGuard AI waitlist.<br>
            No spam ever. Reply to unsubscribe.
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""

    msg.attach(MIMEText(html, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname="smtp.gmail.com",
            port=465,
            use_tls=True,
            username=GMAIL_ADDRESS,
            password=GMAIL_APP_PASSWORD,
        )
        print(f"Welcome email sent to {to_email}")
    except Exception as exc:
        print(f"Email send failed for {to_email}: {exc}")


def send_welcome_email(to_email: str, name: str, position: int) -> None:
    asyncio.create_task(_send(to_email, name, position))
