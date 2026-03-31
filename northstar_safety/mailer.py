from __future__ import annotations

import smtplib
from email.message import EmailMessage

from .config import settings


def smtp_snapshot() -> dict[str, object]:
    configured = bool(
        settings.smtp_mode == "smtp"
        and settings.smtp_host
        and settings.smtp_username
        and settings.smtp_password
        and settings.smtp_from_email
    )
    return {
        "mode": settings.smtp_mode,
        "configured": configured,
        "host": settings.smtp_host,
        "port": settings.smtp_port,
        "from_email": settings.smtp_from_email,
        "reply_to": settings.smtp_reply_to or settings.public_support_email,
        "starttls": settings.smtp_starttls,
        "ssl": settings.smtp_ssl,
    }


def smtp_ready() -> bool:
    return bool(smtp_snapshot()["configured"])


def send_plain_email(*, to_email: str, subject: str, body: str, reply_to: str = "") -> None:
    if not smtp_ready():
        raise RuntimeError("SMTP is not configured.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from_email
    message["To"] = to_email
    message["Reply-To"] = reply_to or settings.smtp_reply_to or settings.public_support_email
    message.set_content(body)

    if settings.smtp_ssl:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        if settings.smtp_starttls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
