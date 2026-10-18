import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

def send_email(to, subject, body):
    """Send an email using SMTP"""
    load_dotenv()
    
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_username = os.getenv("SMTP_USERNAME", smtp_email)  # Default to email if username not set
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    
    if not all([smtp_server, smtp_email, smtp_password]):
        return "Error: SMTP configuration incomplete. Please set SMTP_SERVER, SMTP_EMAIL, and SMTP_PASSWORD in .env file."
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to SMTP server
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if smtp_use_tls:
                server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        return f"Email sent to {to}"
    except Exception as e:
        return f"Error sending email: {str(e)}"

tool = {
    "type": "function",
    "function": {
        "name": "send_email",
        "description": "Send an email using SMTP",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line"
                },
                "body": {
                    "type": "string",
                    "description": "Email body content"
                }
            },
            "required": ["to", "subject", "body"]
        },
        "implementation": send_email
    },
    "critical": True,
    "confirmation_template": "send an email to {to}"
}
