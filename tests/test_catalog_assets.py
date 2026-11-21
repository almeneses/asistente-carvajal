"""Pruebas de imágenes y especificaciones enriquecidas del catálogo."""

from __future__ import annotations

import json
from pathlib import Path

from assistant.catalog.assets import ASSETS_PATH, PLACEHOLDER, product_image, product_specs

ROOT = Path(__file__).resolve().parents[1]


def test_placeholder_para_sku_desconocido() -> None:
    # Arrange / Act / Assert
    assert product_image(None) == PLACEHOLDER
    assert product_image("NO-EXISTE") == PLACEHOLDER


def test_assets_versionados() -> None:
    # Arrange
    payload = json.loads(ASSETS_PATH.read_text(encoding="utf-8"))

    # Act
    sku = "2864108000"
    image = product_image(sku)
    specs = product_specs(sku)

    # Assert
    assert len(payload) == 200
    assert image.startswith("/static/products/")
    assert (ROOT / "assistant" / image.lstrip("/")).is_file()
    assert str(specs.get("source_url", "")).startswith("https://mexico.carvajalempaques.com/")
    assert specs.get("captured_at")


def test_assets_incluye_especificaciones() -> None:
    # Arrange
    specs = product_specs("2864108000")

    # Assert
    assert specs.get("description")
    assert specs.get("length_cm")
    assert specs.get("weight_kg")
