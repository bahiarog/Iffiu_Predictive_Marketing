"""Email notifications"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def send_email(to: str, subject: str, html_body: str):
    """Send email via SMTP"""
    if not settings.SMTP_HOST:
        logger.warning(f"SMTP not configured. Would send to {to}: {subject}")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.SMTP_USER or "noreply@iffiu.com"
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASS:
                server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.send_message(msg)
        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Email failed to {to}: {e}")
        return False

def notify_admin_new_registration(user_email: str, user_name: str, company: str):
    """Notify admin when a new user registers"""
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
        <h2 style="color:#6366f1;">🆕 New IFFIU Registration</h2>
        <table style="width:100%;border-collapse:collapse;">
            <tr><td style="padding:8px;font-weight:bold;">Email:</td><td style="padding:8px;">{user_email}</td></tr>
            <tr><td style="padding:8px;font-weight:bold;">Name:</td><td style="padding:8px;">{user_name or 'N/A'}</td></tr>
            <tr><td style="padding:8px;font-weight:bold;">Company:</td><td style="padding:8px;">{company or 'N/A'}</td></tr>
        </table>
        <p style="color:#64748b;font-size:13px;margin-top:20px;">— IFFIU System</p>
    </div>
    """
    send_email(settings.ADMIN_EMAIL, f"New IFFIU Registration: {user_email}", html)

def send_welcome_email(user_email: str, user_name: str):
    """Welcome email to new user"""
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
        <h2 style="color:#6366f1;">Welcome to IFFIU! 🚀</h2>
        <p>Hi {user_name or 'there'},</p>
        <p>Your account is ready. You have <strong>3 free analyses</strong> to get started.</p>
        <p>Upload any creative (video or image) and our AI will predict how 10 audience segments will react.</p>
        <a href="https://iffiu.com/dashboard" style="display:inline-block;padding:12px 28px;background:#6366f1;color:white;text-decoration:none;border-radius:8px;font-weight:bold;">Go to Dashboard →</a>
        <p style="color:#64748b;font-size:13px;margin-top:20px;">Need help? Reply to this email or contact info@pimentagroup.de</p>
    </div>
    """
    send_email(user_email, "Welcome to IFFIU — Your AI Marketing Intelligence", html)
