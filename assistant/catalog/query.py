"""Consultas de referencias y distribuidores sobre el catálogo."""

from __future__ import annotations

from datetime import date

from assistant.catalog.materials import (
    check_compatibility,
    is_freezing_use,
    is_microwave_use,
)
from assistant.catalog.models import (
    CatalogSnapshot,
    Citation,
    Distributor,
    ExtractedQuery,
    Recommendation,
    Reference,
)
from assistant.catalog.money import resolve_quote

RENEWABLE_MATERIALS = {"PAPEL", "PULPA", "FIBRA"}
USE_TO_REFERENCE = {
    "bebida_caliente": ("comida_caliente", "bebida_caliente"),
    "bebida_fria": ("bebida_fria", "comida_fria"),
    "sopas": ("sopas",),
}


def _matches_use(reference: Reference, use: str) -> bool:
    wanted = USE_TO_REFERENCE.get(use, (use,))
    return any(candidate in reference.uses for candidate in wanted)


def search_references(
    snapshot: CatalogSnapshot,
    query: ExtractedQuery,
    *,
    today: date,
    limit: int = 5,
) -> list[Recommendation]:
    """Filtra y valida referencias; devuelve hasta `limit` recomendaciones."""
    candidates = list(snapshot.references)
    if query.country:
        candidates = [item for item in candidates if item.country == query.country]
    if query.family:
        candidates = [item for item in candidates if item.family == query.family]
    if query.material:
        candidates = [item for item in candidates if item.material == query.material]
    if query.capacity_oz is not None:
        candidates = [
            item
            for item in candidates
            if item.capacity_oz is not None and abs(item.capacity_oz - query.capacity_oz) <= 1.0
        ]
    if query.prefers_renewable:
        renewable = [item for item in candidates if item.material in RENEWABLE_MATERIALS]
        if renewable:
            candidates = renewable
    if query.use:
        by_use = [item for item in candidates if _matches_use(item, query.use)]
        if by_use:
            candidates = by_use

    recommendations: list[Recommendation] = []
    for reference in candidates:
        rule = snapshot.materials.get(reference.material)
        compatible, warnings = check_compatibility(
            reference,
            rule,
            use=query.use,
            temperature=query.temperature,
            needs_microwave=query.microwave or is_microwave_use(query.use),
            needs_freezing=query.freezing or is_freezing_use(query.use),
        )
        if not compatible:
            continue
        quote = resolve_quote(reference, snapshot, today=today, quantity=query.quantity)
        citations = [Citation(label=f"Ficha {reference.name}", url=reference.source_url)]
        if quote is not None:
            citations.append(Citation(label=f"Precio {reference.sku}", url=quote.source_url))
        all_warnings = warnings + (quote.warnings if quote is not None else ())
        recommendations.append(
            Recommendation(
                reference=reference,
                quote=quote,
                citations=tuple(citations),
                warnings=all_warnings,
            )
        )

    recommendations.sort(
        key=lambda item: (
            0 if item.reference.material in RENEWABLE_MATERIALS else 1,
            0 if item.quote is not None and item.quote.validity == "vigente" else 1,
            item.reference.sku,
        )
    )
    return recommendations[:limit]


def find_distributors(snapshot: CatalogSnapshot, city: str | None) -> list[Distributor]:
    """Distribuidores de la ciudad indicada (o todos si no se indica)."""
    if not city:
        return list(snapshot.distributors)
    needle = city.strip().lower()
    return [
        distributor
        for distributor in snapshot.distributors
        if distributor.city.strip().lower() == needle
    ]
