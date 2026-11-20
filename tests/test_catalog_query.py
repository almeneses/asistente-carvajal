"""Pruebas de consultas y plantillas de respuesta del catálogo."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from assistant.catalog.answers import build_catalog_answer
from assistant.catalog.models import ExtractedQuery
from assistant.catalog.query import find_distributors, search_references
from assistant.catalog.router import classify
from tests.catalog_fixtures import sample_snapshot

TODAY = date(2026, 11, 20)
CITIES = ("Bogotá", "Medellín")


def test_recomendacion_caliente_excluye_pet(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    query = classify("necesito vasos para café caliente de 12 oz", cities=CITIES)

    # Act
    recommendations = search_references(snapshot, query, today=TODAY)

    # Assert
    materials = {recommendation.reference.material for recommendation in recommendations}
    assert recommendations
    assert "PET" not in materials
    assert {item.reference.sku for item in recommendations} >= {"MX-VASO-12-PP"}


def test_preferencia_renovable_prioriza_papel(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    query = classify("necesito vasos de papel para café de 12 oz", cities=CITIES)

    # Act
    recommendations = search_references(snapshot, query, today=TODAY)

    # Assert
    assert recommendations
    assert recommendations[0].reference.material == "PAPEL"


def test_sin_coincidencias(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    query = classify("necesito vasos de 20 oz", cities=CITIES)

    # Act / Assert
    assert search_references(snapshot, query, today=TODAY) == []


def test_distribuidores_por_ciudad(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)

    # Act
    distributors = find_distributors(snapshot, "Medellín")

    # Assert
    assert [distributor.name for distributor in distributors] == ["Distribuidora Medellín"]


def test_respuesta_de_recomendacion(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    query = classify("necesito vasos para café caliente de 12 oz", cities=CITIES)

    # Act
    answer = build_catalog_answer(query, snapshot=snapshot, today=TODAY)

    # Assert
    assert answer.section is not None
    assert answer.section.kind == "recommendations"
    assert answer.section.items
    assert any("unidades por caja" in detail for detail in answer.section.items[0].details)
    assert any("MXN" in detail for detail in answer.section.items[0].details)
    assert answer.citations


def test_respuesta_sin_coincidencia(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    query = classify("necesito vasos de 20 oz", cities=CITIES)

    # Act
    answer = build_catalog_answer(query, snapshot=snapshot, today=TODAY)

    # Assert
    assert answer.section is not None
    assert answer.section.kind == "no_match"
    assert "No encontré" in (answer.section.message or "")


def test_aclaracion_sin_familia(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    query = ExtractedQuery(intent="commercial", asks_price=True)

    # Act
    answer = build_catalog_answer(query, snapshot=snapshot, today=TODAY)

    # Assert
    assert answer.section is not None
    assert answer.section.kind == "clarification"


def test_respuesta_de_distribuidores(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    query = classify("¿quién distribuye en Medellín?", cities=CITIES)

    # Act
    answer = build_catalog_answer(query, snapshot=snapshot, today=TODAY)

    # Assert
    assert answer.section is not None
    assert answer.section.kind == "distributors"
    assert len(answer.section.items) == 1


def test_aviso_de_precio_vencido(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    query = classify("necesito vasos de papel para café de 12 oz", cities=CITIES)

    # Act
    answer = build_catalog_answer(query, snapshot=snapshot, today=date(2030, 1, 1))

    # Assert
    assert answer.warnings
    assert any("vencido" in warning for warning in answer.warnings)
    item = answer.section.items[0] if answer.section else None
    assert item is not None
    assert item.price is not None
    assert item.price.validity == "vencido"
