"""
Service d'envoi d'emails — partagé entre le cron et le endpoint withdraw.
"""
from __future__ import annotations

import asyncio
import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger("uvicorn")


def send_pdf_email_sync(
    *,
    from_addr: str,
    from_name: str,
    to_addr: str,
    to_name: str,
    subject: str,
    body: str,
    pdf_bytes: bytes,
    pdf_filename: str,
    extra_attachments: list[tuple[bytes, str]] = (),
) -> None:
    """
    Envoie un email avec un PDF en pièce jointe (synchrone).
    extra_attachments : liste de (contenu, nom_fichier) pour les PJ supplémentaires.
    À utiliser dans un BackgroundTask FastAPI ou via run_in_executor.
    """
    smtp_host = settings.SMTP_HOST
    smtp_port = settings.SMTP_PORT
    smtp_user = settings.SMTP_USER or None
    smtp_password = settings.SMTP_PASSWORD or None

    msg = MIMEMultipart()
    msg["From"] = f"{from_name} <{from_addr}>"
    msg["To"] = f"{to_name} <{to_addr}>"
    msg["Cc"] = from_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename=pdf_filename)
    msg.attach(attachment)

    for extra_bytes, extra_name in extra_attachments:
        ext = extra_name.rsplit(".", 1)[-1].lower() if "." in extra_name else "bin"
        part = MIMEApplication(extra_bytes, _subtype=ext)
        part.add_header("Content-Disposition", "attachment", filename=extra_name)
        msg.attach(part)

    recipients = list({to_addr, from_addr})  # deduplicate (owner sends to himself in test)

    if smtp_port == 465:
        import ssl as _ssl
        ctx = _ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=ctx) as smtp:
            if smtp_user and smtp_password:
                smtp.login(smtp_user, smtp_password)
            smtp.sendmail(from_addr, recipients, msg.as_string())
    else:
        with smtplib.SMTP(smtp_host, smtp_port) as smtp:
            if smtp_port == 587:
                smtp.starttls()
            if smtp_user and smtp_password:
                smtp.login(smtp_user, smtp_password)
            smtp.sendmail(from_addr, recipients, msg.as_string())


async def send_pdf_email_async(
    *,
    from_addr: str,
    from_name: str,
    to_addr: str,
    to_name: str,
    subject: str,
    body: str,
    pdf_bytes: bytes,
    pdf_filename: str,
    extra_attachments: list[tuple[bytes, str]] = (),
) -> None:
    """
    Wrapper async — exécute send_pdf_email_sync dans le thread executor.
    À utiliser depuis les coroutines (ex : cron).
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: send_pdf_email_sync(
            from_addr=from_addr,
            from_name=from_name,
            to_addr=to_addr,
            to_name=to_name,
            subject=subject,
            body=body,
            pdf_bytes=pdf_bytes,
            pdf_filename=pdf_filename,
            extra_attachments=extra_attachments,
        ),
    )
