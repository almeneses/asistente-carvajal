"""Plantillas deterministas de respuesta del catálogo."""

from __future__ import annotations

from datetime import date

from assistant.catalog.models import (
    CatalogAnswer,
    CatalogItem,
    CatalogSection,
    CatalogSnapshot,
    Citation,
    ExtractedQuery,
    PriceQuote,
    Recommendation,
)
from assistant.catalog.money import format_amount
from assistant.catalog.query import find_distributors, search_references
from assistant.catalog.router import normalize


def _price_details(quote: PriceQuote) -> str:
    parts = [f"Precio: {format_amount(quote.amount)} {quote.currency}"]
    parts.append(f"impuestos: {quote.tax_status}")
    parts.append(f"país: {quote.country}")
    if quote.validity == "vigente" and quote.valid_until:
        parts.append(f"vigente hasta {quote.valid_until}")
    elif quote.validity == "vencido":
        parts.append(f"VENCIDO el {quote.valid_until}; no es un precio actual")
    else:
        parts.append("vigencia no declarada")
    if quote.boxes is not None and quote.total is not None:
        parts.append(
            f"{quote.boxes} cajas x {quote.units_per_box} unidades = "
            f"{format_amount(quote.total)} {quote.currency}"
        )
    return " · ".join(parts)


def _recommendation_items(
    recommendations: list[Recommendation],
) -> tuple[CatalogItem, ...]:
    items: list[CatalogItem] = []
    for recommendation in recommendations:
        reference = recommendation.reference
        details = [
            f"Material: {reference.material}",
            f"País: {reference.country}",
        ]
        if reference.units_per_box:
            details.append(f"Presentación: {reference.units_per_box} unidades por caja")
        if recommendation.quote is not None:
            details.append(_price_details(recommendation.quote))
        items.append(
            CatalogItem(
                title=reference.name,
                url=reference.source_url,
                details=tuple(details),
                price=recommendation.quote,
                sku=reference.sku,
            )
        )
    return tuple(items)


def _constraints(query: ExtractedQuery) -> str:
    parts: list[str] = []
    if query.family:
        parts.append(query.family)
    if query.capacity_oz is not None:
        parts.append(f"{query.capacity_oz:g} oz")
    if query.use:
        parts.append(query.use.replace("_", " "))
    if query.material:
        parts.append(query.material)
    if query.city:
        parts.append(query.city)
    return ", ".join(parts) or "los criterios indicados"


def _citations(recommendations: list[Recommendation]) -> tuple[Citation, ...]:
    seen: set[str] = set()
    citations: list[Citation] = []
    for recommendation in recommendations:
        for citation in recommendation.citations:
            if citation.url in seen:
                continue
            seen.add(citation.url)
            citations.append(citation)
    return tuple(citations)


def build_catalog_answer(
    query: ExtractedQuery,
    *,
    snapshot: CatalogSnapshot,
    today: date,
    limit: int = 5,
) -> CatalogAnswer:
    """Construye la respuesta determinista para una consulta comercial."""
    if query.intent == "ambiguous":
        return CatalogAnswer(
            intent=query.intent,
            section=CatalogSection(
                kind="clarification",
                title="Aclaración",
                message=(
                    "¿Buscas información documental de Carvajal o referencias, "
                    "precios o distribuidores del catálogo de empaques?"
                ),
            ),
        )

    if query.asks_distributor:
        distributors = find_distributors(snapshot, query.city)
        if not distributors:
            city = query.city or "esa ciudad"
            return CatalogAnswer(
                intent=query.intent,
                section=CatalogSection(
                    kind="no_match",
                    title="Sin distribuidores",
                    message=f"No encontré distribuidores para {city} en el catálogo.",
                ),
            )
        items = tuple(
            CatalogItem(
                title=distributor.name,
                url=distributor.source_url,
                details=tuple(
                    detail
                    for detail in (
                        distributor.city,
                        distributor.address,
                        distributor.phone,
                    )
                    if detail
                ),
            )
            for distributor in distributors
        )
        citations = tuple(
            Citation(label=f"Distribuidor {distributor.name}", url=distributor.source_url)
            for distributor in distributors
        )
        return CatalogAnswer(
            intent=query.intent,
            section=CatalogSection(
                kind="distributors",
                title="Distribuidores",
                items=items,
                citations=citations,
            ),
            citations=citations,
        )

    if query.family is None and query.material is None:
        return CatalogAnswer(
            intent=query.intent,
            section=CatalogSection(
                kind="clarification",
                title="Aclaración",
                message=(
                    "¿Qué tipo de empaque necesitas (vaso, contenedor, plato…), "
                    "para qué uso y en qué ciudad?"
                ),
            ),
        )

    recommendations = search_references(snapshot, query, today=today, limit=limit)
    if not recommendations:
        return CatalogAnswer(
            intent=query.intent,
            section=CatalogSection(
                kind="no_match",
                title="Sin coincidencias",
                message=(
                    "No encontré una referencia que cumpla: "
                    f"{_constraints(query)}. Puedes ajustar la capacidad, el uso o el material."
                ),
            ),
        )

    warnings: list[str] = []
    for recommendation in recommendations:
        warnings.extend(recommendation.warnings)
    citations = _citations(recommendations)
    return CatalogAnswer(
        intent=query.intent,
        section=CatalogSection(
            kind="recommendations",
            title="Catálogo",
            items=_recommendation_items(recommendations),
            citations=citations,
        ),
        citations=citations,
        warnings=tuple(dict.fromkeys(warnings)),
    )


def city_names(snapshot: CatalogSnapshot) -> tuple[str, ...]:
    """Ciudades del catálogo, para la extracción del router."""
    distributors = getattr(snapshot, "distributors", ())
    return tuple(sorted({distributor.city for distributor in distributors}))


def normalized_city_map(snapshot: CatalogSnapshot) -> dict[str, str]:
    """Mapa de ciudad normalizada a nombre canónico."""
    return {normalize(city): city for city in city_names(snapshot)}
