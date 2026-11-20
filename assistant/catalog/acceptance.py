"""Aceptación de la rama de catálogo sobre el set de enrutamiento."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from assistant.catalog.models import CatalogSnapshot, ExtractedQuery
from assistant.catalog.money import resolve_quote
from assistant.catalog.query import search_references
from assistant.catalog.router import classify, normalize

ROUTE_MIN_ACCURACY = 0.90
QUOTE_MIN_ACCURACY = 0.90
CAPACITY_TOLERANCE = 1.0


class AcceptanceError(RuntimeError):
    """El set de aceptación no se pudo cargar o ejecutar."""


@dataclass(frozen=True)
class AcceptanceRow:
    id: str
    group: str
    question: str
    expected_route: str
    actual_route: str
    route_ok: bool
    attributes_expected: dict[str, Any]
    attributes_actual: dict[str, Any]
    attributes_ok: bool
    recommended_skus: tuple[str, ...]
    forbidden_materials: tuple[str, ...]
    violations: tuple[str, ...]
    quote_status: str
    quote_ok: bool | None


@dataclass
class AcceptanceReport:
    catalog_fingerprint: str
    generated_at: str
    total: int = 0
    route_ok: int = 0
    route_accuracy: float = 0.0
    attributes_ok: int = 0
    attributes_accuracy: float = 0.0
    forbidden_violations: int = 0
    quote_ok: int = 0
    quote_checked: int = 0
    quote_accuracy: float | None = None
    rows: list[AcceptanceRow] | None = None

    def result_rows(self) -> list[AcceptanceRow]:
        return self.rows or []


def load_routing_set(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AcceptanceError(f"No se pudo leer el set {path}: {error}") from error
    items = payload.get("items") if isinstance(payload, dict) else payload
    if not isinstance(items, list) or not items:
        raise AcceptanceError("El set de enrutamiento debe traer una lista items.")
    return [item for item in items if isinstance(item, dict) and item.get("question")]


def _expected_route(group: str) -> str:
    return "documental" if group == "existente" else "commercial"


def _actual_route(query: ExtractedQuery) -> str:
    if query.intent == "documental":
        return "documental"
    if query.intent in {"commercial", "mixed"}:
        return "commercial"
    return query.intent


def _attributes(query: ExtractedQuery, expected: dict[str, Any]) -> dict[str, Any]:
    return {
        "family": query.family,
        "use": query.use,
        "capacity_oz": query.capacity_oz,
        "quantity": query.quantity,
        "city": query.city,
        "country": query.country,
    }


def _same_value(key: str, expected: Any, actual: Any) -> bool:
    if actual is None:
        return False
    if key == "capacity_oz":
        try:
            return abs(float(actual) - float(expected)) <= CAPACITY_TOLERANCE
        except (TypeError, ValueError):
            return False
    if isinstance(expected, str) and isinstance(actual, str):
        return normalize(expected) == normalize(actual)
    return expected == actual


def _attributes_ok(expected: dict[str, Any], actual: dict[str, Any]) -> bool:
    keys = {"family", "use", "capacity_oz", "quantity", "city", "country"}
    checked = [key for key in expected if key in keys]
    if not checked:
        return True
    return all(_same_value(key, expected[key], actual.get(key)) for key in checked)


def _quote_status(
    snapshot: CatalogSnapshot,
    item: dict[str, Any],
    query: ExtractedQuery,
    *,
    today: date,
) -> tuple[str, bool | None]:
    quote = item.get("quote")
    if not isinstance(quote, dict):
        return "not_applicable", None
    if quote.get("no_price"):
        return "declared_no_price", True
    sku = str(quote.get("sku", ""))
    reference = snapshot.by_sku.get(sku)
    if reference is None or sku.startswith("CO-"):
        return "skipped_unknown_sku", None
    resolved = resolve_quote(reference, snapshot, today=today, quantity=query.quantity)
    if resolved is None:
        return "no_data", False
    expected_total = quote.get("total")
    if expected_total is None:
        return "resolved", None
    try:
        expected_amount = float(
            "".join(char for char in str(expected_total) if char.isdigit() or char == ".")
        )
    except ValueError:
        return "invalid_expected_total", None
    return "checked", resolved.total == expected_amount


def run_acceptance(
    snapshot: CatalogSnapshot,
    items: list[dict[str, Any]],
    *,
    today: date | None = None,
) -> AcceptanceReport:
    """Ejecuta el set y agrega métricas de ruta, atributos y citas."""
    reference_day = today or date.today()
    report = AcceptanceReport(
        catalog_fingerprint=snapshot.fingerprint,
        generated_at=datetime.now(UTC).isoformat(),
        total=len(items),
        rows=[],
    )
    cities = tuple(sorted({distributor.city for distributor in snapshot.distributors}))
    for item in items:
        question = str(item["question"])
        group = str(item.get("group", "comercial"))
        expected_route = _expected_route(group)
        turns = item.get("turns")
        context = None
        if isinstance(turns, list) and turns:
            context = " ".join(
                str(turn.get("question", "")) for turn in turns if isinstance(turn, dict)
            )
        query = classify(question, cities=cities, context=context)
        actual_route = _actual_route(query)
        raw_expected = item.get("expected")
        expected_attributes: dict[str, Any] = raw_expected if isinstance(raw_expected, dict) else {}
        actual_attributes = _attributes(query, expected_attributes)
        attributes_ok = _attributes_ok(expected_attributes, actual_attributes)
        recommendations = (
            search_references(snapshot, query, today=reference_day, limit=5)
            if group != "existente"
            else []
        )
        skus = tuple(recommendation.reference.sku for recommendation in recommendations)
        materials = {recommendation.reference.material for recommendation in recommendations}
        raw_constraints = item.get("constraints")
        constraints: dict[str, Any] = raw_constraints if isinstance(raw_constraints, dict) else {}
        forbidden = tuple(constraints.get("forbidden_materials", ()))
        violations = tuple(material for material in forbidden if material in materials)
        quote_status, quote_ok = _quote_status(snapshot, item, query, today=reference_day)
        row = AcceptanceRow(
            id=str(item.get("id", "")),
            group=group,
            question=question,
            expected_route=expected_route,
            actual_route=actual_route,
            route_ok=actual_route == expected_route,
            attributes_expected=expected_attributes,
            attributes_actual=actual_attributes,
            attributes_ok=attributes_ok,
            recommended_skus=skus,
            forbidden_materials=forbidden,
            violations=violations,
            quote_status=quote_status,
            quote_ok=quote_ok,
        )
        assert report.rows is not None
        report.rows.append(row)
        report.route_ok += int(row.route_ok)
        report.attributes_ok += int(row.attributes_ok)
        report.forbidden_violations += len(violations)
        if quote_ok is not None:
            report.quote_checked += 1
            report.quote_ok += int(quote_ok)

    report.route_accuracy = report.route_ok / report.total if report.total else 0.0
    report.attributes_accuracy = report.attributes_ok / report.total if report.total else 0.0
    report.quote_accuracy = report.quote_ok / report.quote_checked if report.quote_checked else None
    return report


def exit_code(report: AcceptanceReport) -> int:
    """0 si cumple los umbrales; 1 si no; 2 no aplica (sin datos)."""
    if report.total == 0:
        return 2
    if report.route_accuracy < ROUTE_MIN_ACCURACY:
        return 1
    if report.forbidden_violations:
        return 1
    if report.quote_accuracy is not None and report.quote_accuracy < QUOTE_MIN_ACCURACY:
        return 1
    return 0


def report_to_dict(report: AcceptanceReport) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "catalog_fingerprint": report.catalog_fingerprint,
        "total": report.total,
        "route_ok": report.route_ok,
        "route_accuracy": report.route_accuracy,
        "attributes_ok": report.attributes_ok,
        "attributes_accuracy": report.attributes_accuracy,
        "forbidden_violations": report.forbidden_violations,
        "quote_ok": report.quote_ok,
        "quote_checked": report.quote_checked,
        "quote_accuracy": report.quote_accuracy,
        "rows": [
            {
                "id": row.id,
                "group": row.group,
                "question": row.question,
                "expected_route": row.expected_route,
                "actual_route": row.actual_route,
                "route_ok": row.route_ok,
                "attributes_expected": row.attributes_expected,
                "attributes_actual": row.attributes_actual,
                "attributes_ok": row.attributes_ok,
                "recommended_skus": list(row.recommended_skus),
                "forbidden_materials": list(row.forbidden_materials),
                "violations": list(row.violations),
                "quote_status": row.quote_status,
                "quote_ok": row.quote_ok,
            }
            for row in report.result_rows()
        ],
    }


def summary_markdown(report: AcceptanceReport) -> str:
    lines = [
        "# Aceptación del catálogo",
        "",
        f"- Preguntas: {report.total}",
        f"- Ruta: {report.route_ok}/{report.total} ({report.route_accuracy:.1%})",
        f"- Atributos: {report.attributes_ok}/{report.total} ({report.attributes_accuracy:.1%})",
        f"- Materiales prohibidos recomendados: {report.forbidden_violations}",
        f"- Cotizaciones: {report.quote_ok}/{report.quote_checked}"
        + (f" ({report.quote_accuracy:.1%})" if report.quote_accuracy is not None else ""),
        "",
        "| id | grupo | ruta esperada | ruta real | atributos | cotización |",
        "|---|---|---|---|---|---|",
    ]
    for row in report.result_rows():
        lines.append(
            f"| {row.id} | {row.group} | {row.expected_route} | {row.actual_route} | "
            f"{'ok' if row.attributes_ok else 'falla'} | {row.quote_status} |"
        )
    return "\n".join(lines) + "\n"
