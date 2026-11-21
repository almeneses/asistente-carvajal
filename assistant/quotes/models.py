"""Solicitudes de cotización: modelos y validación."""

from __future__ import annotations

import re
from dataclasses import dataclass


class QuoteError(ValueError):
    """Solicitud inválida o no registrable."""


MAX_TEXT = 80
MAX_CONTACT = 120
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class QuoteRequest:
    """Datos mínimos que envía la persona."""

    sku: str
    boxes: int
    city: str = ""
    business: str = ""
    contact_name: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    consent: bool = False

    def validate(self) -> None:
        if not self.sku.strip():
            raise QuoteError("El SKU es obligatorio.")
        if self.boxes < 1:
            raise QuoteError("Debes solicitar al menos una caja.")
        for label, value in (("ciudad", self.city), ("negocio", self.business)):
            if len(value) > MAX_TEXT:
                raise QuoteError(f"El campo {label} no puede superar {MAX_TEXT} caracteres.")
        for label, value in (
            ("nombre", self.contact_name),
            ("correo", self.contact_email),
            ("teléfono", self.contact_phone),
        ):
            if len(value) > MAX_CONTACT:
                raise QuoteError(f"El campo {label} no puede superar {MAX_CONTACT} caracteres.")
        has_contact = bool(
            self.contact_name.strip() or self.contact_email.strip() or self.contact_phone.strip()
        )
        if has_contact:
            if not self.consent:
                raise QuoteError(
                    "Debes aceptar el aviso de privacidad para dejar tus datos de contacto."
                )
            if not self.contact_email.strip() and not self.contact_phone.strip():
                raise QuoteError("Deja un correo o un teléfono para que podamos contactarte.")
            if self.contact_email.strip() and not _EMAIL_RE.match(self.contact_email.strip()):
                raise QuoteError("El correo no tiene un formato válido.")


@dataclass(frozen=True)
class QuoteRecord:
    """Solicitud registrada (sin PII)."""

    code: str
    sku: str
    reference: str
    boxes: int
    units: int
    unit_price: float
    total: float
    currency: str
    city: str
    business: str
    created_at: str
    contact_name: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    consent_at: str = ""
