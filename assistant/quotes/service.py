"""Servicio de solicitudes: recalcula desde el catálogo y registra."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from assistant.catalog.models import CatalogSnapshot
from assistant.quotes.models import QuoteError, QuoteRecord, QuoteRequest
from assistant.quotes.store import append_quote, generate_code, read_quotes


def create_quote(
    snapshot: CatalogSnapshot,
    path: Path,
    request: QuoteRequest,
    *,
    now: datetime | None = None,
) -> QuoteRecord:
    """Valida contra el catálogo, calcula el total y persiste la solicitud."""
    request.validate()
    reference = snapshot.by_sku.get(request.sku.strip())
    if reference is None:
        raise QuoteError("La referencia solicitada no existe en el catálogo.")
    if reference.units_per_box is None:
        raise QuoteError("La referencia no tiene unidades por caja configuradas.")
    price = snapshot.price_for(reference.sku)
    if price is not None and price.amount > 0:
        unit_price = price.amount
        currency = price.currency or reference.currency or ""
    elif reference.price is not None and reference.price > 0:
        unit_price = reference.price
        currency = reference.currency or ""
    else:
        raise QuoteError("La referencia no tiene un precio de referencia disponible.")

    boxes = int(request.boxes)
    units = boxes * reference.units_per_box
    total = round(boxes * unit_price, 2)
    existing = {record.code for record in read_quotes(path)}
    code = generate_code(now)
    while code in existing:
        code = generate_code(now)
    record = QuoteRecord(
        code=code,
        sku=reference.sku,
        reference=reference.name,
        boxes=boxes,
        units=units,
        unit_price=unit_price,
        total=total,
        currency=currency,
        city=request.city.strip(),
        business=request.business.strip(),
        created_at=(now or datetime.now(UTC)).isoformat(),
    )
    append_quote(path, record)
    return record
