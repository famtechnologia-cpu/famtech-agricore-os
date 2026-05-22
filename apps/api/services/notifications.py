from __future__ import annotations
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from twilio.rest import Client
from ..core.config import settings
import asyncio

log = logging.getLogger("notifications")

async def send_sms(to_phone: str, message: str) -> bool:
    """Send an SMS via Twilio. If no credentials, log the mock SMS."""
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN or not settings.TWILIO_FROM_NUMBER:
        log.info(f"[MOCK SMS] To: {to_phone} | Message: {message}")
        return True

    try:
        def _send():
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            message_obj = client.messages.create(
                body=message,
                from_=settings.TWILIO_FROM_NUMBER,
                to=to_phone
            )
            return message_obj.sid

        sid = await asyncio.to_thread(_send)
        log.info(f"SMS sent successfully. SID: {sid}")
        return True
    except Exception as e:
        log.error(f"Failed to send SMS to {to_phone}: {e}")
        return False

async def send_email(to_email: str, subject: str, message: str) -> bool:
    """Send an email via SendGrid. If no credentials, log the mock email."""
    if not settings.SENDGRID_API_KEY or not settings.SENDGRID_FROM_EMAIL:
        log.info(f"[MOCK EMAIL] To: {to_email} | Subject: {subject} | Message: {message}")
        return True

    try:
        def _send():
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            mail = Mail(
                from_email=settings.SENDGRID_FROM_EMAIL,
                to_emails=to_email,
                subject=subject,
                html_content=f"<p>{message}</p>"
            )
            response = sg.send(mail)
            return response.status_code

        status_code = await asyncio.to_thread(_send)
        log.info(f"Email sent successfully to {to_email}. Status code: {status_code}")
        return True
    except Exception as e:
        log.error(f"Failed to send Email to {to_email}: {e}")
        return False
