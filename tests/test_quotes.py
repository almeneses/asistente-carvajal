"""Pruebas de solicitudes: modelos, store y servicio."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from assistant.quotes.models import QuoteError, QuoteRequest
from assistant.quotes.service import create_quote
from assistant.quotes.store import generate_code, read_quotes
from tests.catalog_fixtures import sample_snapshot


def test_genera_codigo_legible() -> None:
    # Arrange
    moment = datetime(2026, 11, 21, tzinfo=UTC)

    # Act
    code = generate_code(moment)

    # Assert
    assert code.startswith("OC-2026-1121-")
    assert len(code) == len("OC-2026-1121-XXXX")


def test_crea_solicitud_y_persiste(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path / "catalog")
    path = tmp_path / "solicitudes.jsonl"
    request = QuoteRequest(
        sku="MX-VASO-12-PP", boxes=5, city="Ciudad de México", business="Café Origen"
    )

    # Act
    record = create_quote(snapshot, path, request)

    # Assert
    assert record.sku == "MX-VASO-12-PP"
    assert record.units == 5000
    assert record.total == 4500
    assert record.currency == "MXN"
    assert record.code.startswith("OC-")
    stored = read_quotes(path)
    assert len(stored) == 1
    assert stored[0].code == record.code


def test_rechaza_sku_inexistente(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path / "catalog")
    path = tmp_path / "solicitudes.jsonl"

    # Act / Assert
    with pytest.raises(QuoteError, match="no existe"):
        create_quote(snapshot, path, QuoteRequest(sku="NO-EXISTE", boxes=1))


def test_rechaza_cajas_invalidas(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path / "catalog")
    path = tmp_path / "solicitudes.jsonl"

    # Act / Assert
    with pytest.raises(QuoteError, match="al menos una caja"):
        create_quote(snapshot, path, QuoteRequest(sku="MX-VASO-12-PP", boxes=0))


def test_rechaza_ciudad_larga(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path / "catalog")

    # Act / Assert
    with pytest.raises(QuoteError, match="80"):
        create_quote(
            snapshot,
            tmp_path / "solicitudes.jsonl",
            QuoteRequest(sku="MX-VASO-12-PP", boxes=1, city="x" * 81),
        )


def test_rechaza_sin_precio(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path / "catalog")
    sin_precios = replace(
        snapshot,
        prices=(),
        references=tuple(
            replace(reference, price=None, currency=None)
            if reference.sku == "MX-VASO-12-PP"
            else reference
            for reference in snapshot.references
        ),
    )

    # Act / Assert
    with pytest.raises(QuoteError, match="precio"):
        create_quote(
            sin_precios, tmp_path / "solicitudes.jsonl", QuoteRequest(sku="MX-VASO-12-PP", boxes=1)
        )


def test_jsonl_sin_contacto_no_guarda_datos_personales(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path / "catalog")
    path = tmp_path / "solicitudes.jsonl"

    # Act
    create_quote(
        snapshot,
        path,
        QuoteRequest(sku="MX-VASO-12-PP", boxes=1, city="Bogotá", business="Mi negocio"),
    )

    # Assert
    raw = path.read_text(encoding="utf-8").lower()
    assert '"contact_email": ""' in raw
    assert '"contact_phone": ""' in raw
    assert "user-agent" not in raw


def test_contacto_requiere_consentimiento(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path / "catalog")

    # Act / Assert
    with pytest.raises(QuoteError, match="aviso de privacidad"):
        create_quote(
            snapshot,
            tmp_path / "solicitudes.jsonl",
            QuoteRequest(sku="MX-VASO-12-PP", boxes=1, contact_email="ana@example.com"),
        )


def test_contacto_requiere_canal_y_correo_valido(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path / "catalog")

    # Act / Assert
    with pytest.raises(QuoteError, match="correo o un teléfono"):
        create_quote(
            snapshot,
            tmp_path / "solicitudes.jsonl",
            QuoteRequest(sku="MX-VASO-12-PP", boxes=1, contact_name="Ana", consent=True),
        )
    with pytest.raises(QuoteError, match="formato válido"):
        create_quote(
            snapshot,
            tmp_path / "solicitudes.jsonl",
            QuoteRequest(
                sku="MX-VASO-12-PP",
                boxes=1,
                contact_email="no-es-correo",
                consent=True,
            ),
        )
