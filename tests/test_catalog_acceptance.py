"""Pruebas del reporte de aceptación del catálogo."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from assistant.catalog.acceptance import (
    AcceptanceError,
    exit_code,
    load_routing_set,
    report_to_dict,
    run_acceptance,
    summary_markdown,
)
from tests.catalog_fixtures import sample_snapshot

TODAY = date(2026, 11, 20)


def _items() -> list[dict[str, object]]:
    return [
        {
            "id": "e-01",
            "group": "existente",
            "question": "¿Qué es Carvajal y a qué sectores se dedica?",
            "route": "rag",
        },
        {
            "id": "c-01",
            "group": "comercial",
            "question": "necesito vasos para café caliente de 12 oz",
            "expected": {"family": "vaso", "capacity_oz": 12.0, "use": "bebida_caliente"},
            "constraints": {"forbidden_materials": ["PET"]},
        },
        {
            "id": "co-01",
            "group": "colombia",
            "question": "necesito 5.000 vasos de 9 oz para jugos en Bogotá",
            "expected": {"family": "vaso", "quantity": 5000, "city": "Bogotá", "country": "CO"},
            "quote": {"sku": "CO-VASO-9-PP", "total": "412610 COP"},
        },
        {
            "id": "co-02",
            "group": "colombia",
            "question": "vasos de 8 oz para café en Medellín, 3000 unidades",
            "expected": {"family": "vaso", "quantity": 3000, "city": "Medellín"},
            "quote": {"sku": "CO-NO-EXISTE", "no_price": True},
        },
    ]


def test_ejecuta_y_agrega_metricas(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)

    # Act
    report = run_acceptance(snapshot, _items(), today=TODAY)

    # Assert
    assert report.total == 4
    assert report.route_accuracy == 1.0
    assert report.forbidden_violations == 0
    assert report.quote_checked == 1
    assert report.quote_ok == 1
    assert report.quote_accuracy == 1.0
    assert exit_code(report) == 0


def test_material_prohibido_falla(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    items = [
        {
            "id": "x-01",
            "group": "comercial",
            "question": "necesito vasos PET de 12 oz para café caliente",
            "constraints": {"forbidden_materials": ["PET"]},
        }
    ]

    # Act
    report = run_acceptance(snapshot, items, today=TODAY)

    # Assert
    assert report.forbidden_violations == 0  # PET se descarta por validación
    assert exit_code(report) == 0


def test_ruta_incorrecta_falla(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    items = [{"id": "x-01", "group": "existente", "question": "necesito vasos de 12 oz"}]

    # Act
    report = run_acceptance(snapshot, items, today=TODAY)

    # Assert
    assert report.route_ok == 0
    assert exit_code(report) == 1


def test_reporte_json_y_markdown(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    report = run_acceptance(snapshot, _items(), today=TODAY)

    # Act
    payload = report_to_dict(report)
    markdown = summary_markdown(report)

    # Assert
    assert payload["total"] == 4
    assert len(payload["rows"]) == 4
    assert "Aceptación del catálogo" in markdown


def test_load_routing_set(tmp_path: Path) -> None:
    # Arrange
    path = tmp_path / "routing.json"
    path.write_text(
        '{"items": [{"id": "a", "group": "existente", "question": "¿Qué es Carvajal?"}]}',
        encoding="utf-8",
    )

    # Act
    items = load_routing_set(path)

    # Assert
    assert len(items) == 1


def test_load_routing_set_invalido(tmp_path: Path) -> None:
    # Arrange
    path = tmp_path / "routing.json"
    path.write_text("{}", encoding="utf-8")

    # Act / Assert
    with pytest.raises(AcceptanceError, match="items"):
        load_routing_set(path)
