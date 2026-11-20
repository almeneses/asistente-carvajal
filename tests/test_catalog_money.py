"""Pruebas de precios, vigencia y cantidades."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from pathlib import Path

from assistant.catalog.money import format_amount, resolve_quote
from tests.catalog_fixtures import sample_snapshot

TODAY = date(2026, 11, 20)


def test_precio_mx_vigente(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    reference = snapshot.by_sku["MX-VASO-12-PP"]

    # Act
    quote = resolve_quote(reference, snapshot, today=TODAY)

    # Assert
    assert quote is not None
    assert quote.amount == 900
    assert quote.currency == "MXN"
    assert quote.tax_status == "incluido"
    assert quote.validity == "vigente"
    assert quote.valid_until == "2027-12-31"


def test_precio_vencido_se_marca(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    reference = snapshot.by_sku["MX-VASO-12-PP"]

    # Act
    quote = resolve_quote(reference, snapshot, today=date(2030, 1, 1))

    # Assert
    assert quote is not None
    assert quote.validity == "vencido"
    assert any("vencido" in warning for warning in quote.warnings)


def test_precio_sin_vigencia_declarada(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    reference = snapshot.by_sku["CO-VASO-9-PP"]

    # Act
    quote = resolve_quote(reference, snapshot, today=TODAY)

    # Assert
    assert quote is not None
    assert quote.currency == "COP"
    assert quote.validity == "no_declarada"
    assert any("vigencia" in warning for warning in quote.warnings)


def test_sin_precio_devuelve_none(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    reference = replace(snapshot.by_sku["MX-VASO-12-PP"], price=None)

    # Act / Assert
    assert resolve_quote(reference, snapshot, today=TODAY) is None


def test_cajas_y_total(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    reference = snapshot.by_sku["CO-VASO-9-PP"]

    # Act
    quote = resolve_quote(reference, snapshot, today=TODAY, quantity=5000)

    # Assert
    assert quote is not None
    assert quote.boxes == 2
    assert quote.total == 412610.0
    assert quote.units_per_box == 2500


def test_formato_de_montos() -> None:
    # Arrange / Act / Assert
    assert format_amount(206305.0) == "206305"
    assert format_amount(1111.5) == "1111.5"
