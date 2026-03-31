import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import os

def send_email_alert(to_email, candidate_name, score, job_title):
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    if not smtp_user or not smtp_password:
        print("Email credentials not configured")
        return False
        
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = f"Top Candidate Alert: {candidate_name} for {job_title}"
    
    body = f"""
    Hello HR Team,
    
    A high-fit candidate has been screened:
    - Name: {candidate_name}
    - Fit Score: {score}%
    - Role: {job_title}
    
    Check the dashboard for full details.
    """
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_slack_alert(candidate_name, score, job_title):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("Slack webhook not configured")
        return False
        
    payload = {
        "text": f"🚀 *New High-Fit Candidate!*\n*Name:* {candidate_name}\n*Score:* {score}%\n*Job:* {job_title}"
    }
    
    try:
        requests.post(webhook_url, json=payload)
        return True
    except Exception as e:
        print(f"Failed to send Slack alert: {e}")
        return False
