# config.py
import os

from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "alerts@webshieldai.com")
FROM_NAME = os.getenv("FROM_NAME", "Web Shield AI Alerts")

SCREENSHOTONE_ACCESS_KEY = os.getenv("SCREENSHOTONE_ACCESS_KEY", "")
# Signs session cookies; set a long random value in production.
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "")
