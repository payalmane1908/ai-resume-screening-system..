import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

logger = logging.getLogger(__name__)


def send_email_alert(to_email, candidate_name, score, job_title):
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        logger.info("Email credentials not configured — skipping email alert.")
        return False

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = f"Top Candidate Alert: {candidate_name} for {job_title}"

    body = f"""
    Hello HR Team,

    A high-fit candidate has been screened:
    - Name: {candidate_name}
    - Fit Score: {score}%
    - Role: {job_title}

    Check the dashboard for full details.
    """
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        logger.info("Email alert sent to %s for candidate %s", to_email, candidate_name)
        return True
    except Exception:
        logger.exception("Failed to send email alert to %s", to_email)
        return False


def send_slack_alert(candidate_name, score, job_title):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.info("Slack webhook not configured — skipping Slack alert.")
        return False

    payload = {
        "text": f"🚀 *New High-Fit Candidate!*\n*Name:* {candidate_name}\n*Score:* {score}%\n*Job:* {job_title}"
    }

    try:
        requests.post(webhook_url, json=payload, timeout=10)
        logger.info("Slack alert sent for candidate %s", candidate_name)
        return True
    except Exception:
        logger.exception("Failed to send Slack alert")
        return False
