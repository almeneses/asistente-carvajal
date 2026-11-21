"""Solicitudes de cotización: modelos y validación."""

from __future__ import annotations

from dataclasses import dataclass


class QuoteError(ValueError):
    """Solicitud inválida o no registrable."""


MAX_TEXT = 80


@dataclass(frozen=True)
class QuoteRequest:
    """Datos mínimos que envía la persona."""

    sku: str
    boxes: int
    city: str = ""
    business: str = ""

    def validate(self) -> None:
        if not self.sku.strip():
            raise QuoteError("El SKU es obligatorio.")
        if self.boxes < 1:
            raise QuoteError("Debes solicitar al menos una caja.")
        for label, value in (("ciudad", self.city), ("negocio", self.business)):
            if len(value) > MAX_TEXT:
                raise QuoteError(f"El campo {label} no puede superar {MAX_TEXT} caracteres.")


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
