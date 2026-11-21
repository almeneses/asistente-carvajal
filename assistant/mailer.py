"""Envío de cotizaciones por correo (SMTP opcional)."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from assistant.config import Settings
from assistant.quotes.models import QuoteRecord

logger = logging.getLogger("asistente")


def send_quote_email(record: QuoteRecord, settings: Settings) -> str:
    """Devuelve sent | not_configured | no_email | failed. Nunca loguea PII."""
    if not record.contact_email:
        return "no_email"
    if not settings.smtp_host or not settings.smtp_from:
        return "not_configured"
    message = EmailMessage()
    message["Subject"] = f"Cotización {record.code} — Carvajal"
    message["From"] = settings.smtp_from
    message["To"] = record.contact_email
    message.set_content(
        "\n".join(
            [
                f"Hola {record.contact_name or ''}".strip(),
                "",
                f"Tu solicitud quedó registrada con el código {record.code}.",
                "",
                f"Producto: {record.reference}",
                f"Cajas: {record.boxes}",
                f"Unidades: {record.units}",
                f"Precio unitario: {record.unit_price} {record.currency}",
                f"Total de referencia: {record.total} {record.currency}",
                f"Ciudad: {record.city or 'por coordinar'}",
                f"Negocio: {record.business or 'por coordinar'}",
                "",
                "Un asesor de Carvajal te contactará para coordinar la entrega. Sin cobro previo.",
                "Esta cotización es de referencia y no constituye una orden de compra.",
            ]
        )
    )
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.ehlo()
            if settings.smtp_tls:
                smtp.starttls()
                smtp.ehlo()
            if settings.smtp_user and settings.smtp_password:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
        return "sent"
    except Exception:
        logger.warning("quote_email_failed", extra={"count": 1})
        return "failed"
