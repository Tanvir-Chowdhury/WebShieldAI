# config.py
import os

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465")) 
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "tanvir.chowdhury.us@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "jyot hetw szhl lruy")
FROM_EMAIL = os.getenv("FROM_EMAIL", "alerts@webshieldai.com")
FROM_NAME = os.getenv("FROM_NAME", "Web Shield AI Alerts")
