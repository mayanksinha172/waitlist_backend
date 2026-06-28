import os
import threading
import httpx

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
FROM_EMAIL = "webuild6767@gmail.com"
FROM_NAME = "LanceGuardAI"


def _send(to_email: str, name: str, position: int) -> None:
    if not BREVO_API_KEY:
        print("Email skipped: BREVO_API_KEY not set")
        return

    first = name.split()[0] if name else "there"

    html = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#000000;font-family:'Inter',Arial,sans-serif;-webkit-font-smoothing:antialiased">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#000000;padding:40px 20px">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0" style="max-width:520px;width:100%;background:#0a0a0c;border:1px solid rgba(255,255,255,0.1);border-radius:12px">

        <!-- Brand -->
        <tr><td style="padding:40px 40px 32px">
          <span style="font-size:11px;color:#11ff99;font-weight:600;letter-spacing:0.1em;text-transform:uppercase">
            LanceGuardAI
          </span>
        </td></tr>

        <!-- Headline -->
        <tr><td style="padding:0 40px 20px">
          <h1 style="margin:0;font-size:28px;font-weight:400;line-height:1.25;color:#fcfdff">
            You're on the list, <span style="color:#11ff99">{first}.</span>
          </h1>
        </td></tr>

        <!-- Personal note -->
        <tr><td style="padding:0 40px 16px">
          <p style="margin:0;font-size:15px;line-height:1.75;color:rgba(252,253,255,0.7)">
            Thanks for joining early — it means a lot.
          </p>
        </td></tr>

        <tr><td style="padding:0 40px 16px">
          <p style="margin:0;font-size:15px;line-height:1.75;color:rgba(252,253,255,0.7)">
            We're building quietly and will reach out as soon as early access opens.
            As one of our first members, you're locked in for
            <strong style="color:#11ff99">3 months free</strong> at launch.
          </p>
        </td></tr>

        <tr><td style="padding:0 40px 16px">
          <p style="margin:0;font-size:15px;line-height:1.75;color:rgba(252,253,255,0.7)">
            In the meantime — if you have questions, feedback, or just want to share
            how you currently handle proposals and client work, hit reply.
            We're building this for you, and we'd genuinely love to hear from you.
          </p>
        </td></tr>

        <!-- Product line -->
        <tr><td style="padding:0 40px 32px">
          <p style="margin:0;font-size:13px;line-height:1.7;color:rgba(252,253,255,0.35);border-left:2px solid rgba(17,255,153,0.3);padding-left:14px">
            LanceGuardAI writes proposals in under 60 seconds, detects scope creep in real time,
            and auto-generates priced change orders — so every hour of work gets paid.
          </p>
        </td></tr>

        <!-- Sign-off -->
        <tr><td style="padding:0 40px 32px">
          <p style="margin:0;font-size:15px;line-height:1.75;color:rgba(252,253,255,0.7)">
            Thanks for being early.<br><br>
            <span style="color:#fcfdff;font-weight:500">— The LanceGuardAI team</span>
          </p>
        </td></tr>

        <!-- Footer -->
        <tr><td style="padding:0 40px 40px;border-top:1px solid rgba(255,255,255,0.06)">
          <p style="margin:16px 0 0;font-size:11px;color:#464a4d;line-height:1.6">
            You're receiving this because you joined the LanceGuardAI waitlist.<br>
            No spam ever. Reply to unsubscribe.
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""

    try:
        resp = httpx.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "api-key": BREVO_API_KEY,
                "content-type": "application/json",
            },
            json={
                "sender": {"name": FROM_NAME, "email": FROM_EMAIL},
                "to": [{"email": to_email, "name": name}],
                "subject": f"You're in, {first} — LanceGuardAI",
                "htmlContent": html,
            },
            timeout=10,
        )
        if resp.status_code == 201:
            print(f"Welcome email sent to {to_email}")
        else:
            print(f"Email send failed for {to_email}: {resp.status_code} {resp.text}")
    except Exception as exc:
        print(f"Email send failed for {to_email}: {exc}")


def send_welcome_email(to_email: str, name: str, position: int) -> None:
    thread = threading.Thread(target=_send, args=(to_email, name, position), daemon=True)
    thread.start()
