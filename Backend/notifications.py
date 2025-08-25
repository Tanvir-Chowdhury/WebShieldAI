# notifications.py
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USERNAME = "tanvir.chowdhury.us@gmail.com"
SMTP_PASSWORD = "jyothetwszhllruy"
FROM_EMAIL = "alerts@webshieldai.com"
FROM_NAME = "Web Shield AI"

def send_email_now(to_email: str, subject: str, html: str) -> None:
    msg = MIMEText(html, "html")
    msg["Subject"] = subject
    msg["From"] = formataddr((FROM_NAME, FROM_EMAIL))
    msg["To"] = to_email
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=8) as s:
        s.login(SMTP_USERNAME, SMTP_PASSWORD)
        s.sendmail(FROM_EMAIL, [to_email], msg.as_string())

def build_threat_email_html(
    *, website_name: str, website_url: str, log_type: str,
    occurred_at, ip_address: str | None = None,
    query: str | None = None, prediction: str | None = None,
    score: float | None = None,
) -> str:
    ip = f"<p><b>IP:</b> {ip_address}</p>" if ip_address else ""
    qry = f"<p><b>Query:</b> {query}</p>" if query else ""
    pred = f"<p><b>Prediction:</b> {prediction}</p>" if prediction else ""
    scr = f"<p><b>Score:</b> {score}</p>" if score is not None else ""
    return f"""
      <h2>Threat detected on {website_name}</h2>
      <p><b>Type:</b> {log_type}</p>
      <p><b>When:</b> {occurred_at}</p>
      <p><b>Site:</b> <a href="{website_url}">{website_url}</a></p>
      {ip}{qry}{pred}{scr}
      <p>Please review in your dashboard.</p>
    """
