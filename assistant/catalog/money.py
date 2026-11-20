"""Precios, vigencia y cálculo de cajas."""

from __future__ import annotations

import math
from datetime import date

from assistant.catalog.models import CatalogSnapshot, PriceQuote, Reference


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _tax_status(reference: Reference) -> str:
    if reference.tax_included is True:
        return "incluido"
    if reference.tax_included is False:
        return "no_incluido"
    return "desconocido"


def _quote(
    *,
    amount: float,
    currency: str,
    country: str,
    tax_status: str,
    valid_until: str | None,
    source_url: str,
    captured_at: str,
    today: date,
    quantity: int | None,
    units_per_box: int | None,
) -> PriceQuote:
    warnings: list[str] = []
    if not valid_until:
        validity = "no_declarada"
        warnings.append("el precio no declara vigencia")
    else:
        expiry = _parse_date(valid_until)
        if expiry is None:
            validity = "no_declarada"
            warnings.append(f"vigencia ilegible ({valid_until})")
        elif expiry < today:
            validity = "vencido"
            warnings.append(f"precio de referencia vencido el {valid_until}")
        else:
            validity = "vigente"
    boxes: int | None = None
    total: float | None = None
    if quantity is not None and quantity > 0 and units_per_box:
        boxes = math.ceil(quantity / units_per_box)
        total = round(boxes * amount, 2)
    return PriceQuote(
        amount=amount,
        currency=currency,
        country=country,
        tax_status=tax_status,
        validity=validity,
        valid_until=valid_until,
        source_url=source_url,
        captured_at=captured_at,
        warnings=tuple(warnings),
        boxes=boxes,
        total=total,
        units_per_box=units_per_box,
    )


def resolve_quote(
    reference: Reference,
    snapshot: CatalogSnapshot,
    *,
    today: date,
    quantity: int | None = None,
) -> PriceQuote | None:
    """Resuelve el precio de la referencia o devuelve None si no existe."""
    if reference.country == "MX":
        if reference.price is None:
            return None
        return _quote(
            amount=reference.price,
            currency=reference.currency or "MXN",
            country=reference.country,
            tax_status=_tax_status(reference),
            valid_until=reference.price_valid_until,
            source_url=reference.source_url,
            captured_at=reference.captured_at,
            today=today,
            quantity=quantity,
            units_per_box=reference.units_per_box,
        )
    price = snapshot.price_for(reference.sku)
    if price is None:
        return None
    return _quote(
        amount=price.amount,
        currency=price.currency,
        country=price.country,
        tax_status=price.tax_status,
        valid_until=price.valid_until,
        source_url=price.source_url,
        captured_at=price.captured_at,
        today=today,
        quantity=quantity,
        units_per_box=reference.units_per_box,
    )


def format_amount(amount: float) -> str:
    """Formatea sin decimales si el monto es entero."""
    if float(amount).is_integer():
        return str(int(amount))
    return f"{amount:.2f}".rstrip("0").rstrip(".")
