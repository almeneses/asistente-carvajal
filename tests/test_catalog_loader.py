"""Pruebas de carga y validación del catálogo."""

from __future__ import annotations

from pathlib import Path

import pytest
from assistant.catalog.loader import load_catalog
from assistant.catalog.models import CatalogError
from tests.catalog_fixtures import sample_snapshot, write_catalog


def test_carga_catalogo_sintetico(tmp_path: Path) -> None:
    # Arrange / Act
    snapshot = sample_snapshot(tmp_path)

    # Assert
    assert snapshot.references_count == 4
    assert snapshot.prices_count == 1
    assert snapshot.distributors_count == 2
    assert len(snapshot.materials) == 3
    assert len(snapshot.fingerprint) == 64


def test_falta_columna(tmp_path: Path) -> None:
    # Arrange
    directory = write_catalog(tmp_path)
    content = (directory / "referencias.csv").read_text(encoding="utf-8")
    lines = [line.replace(",country", "") for line in content.splitlines()]
    (directory / "referencias.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Act / Assert
    with pytest.raises(CatalogError, match="faltan columnas"):
        load_catalog(directory)


def test_sku_duplicado(tmp_path: Path) -> None:
    # Arrange
    directory = write_catalog(tmp_path)
    content = (directory / "referencias.csv").read_text(encoding="utf-8")
    lines = content.splitlines()
    header, row = lines[0], lines[1]
    (directory / "referencias.csv").write_text(
        "\n".join([header, row, row]) + "\n", encoding="utf-8"
    )

    # Act / Assert
    with pytest.raises(CatalogError, match="duplicados"):
        load_catalog(directory)


def test_precio_huerfano(tmp_path: Path) -> None:
    # Arrange
    directory = write_catalog(tmp_path)
    content = (directory / "precios.csv").read_text(encoding="utf-8")
    header, row = content.splitlines()[:2]
    row = row.replace("CO-VASO-9-PP", "CO-NO-EXISTE")
    (directory / "precios.csv").write_text("\n".join([header, row]) + "\n", encoding="utf-8")

    # Act / Assert
    with pytest.raises(CatalogError, match="huérfano"):
        load_catalog(directory)


def test_precio_con_pais_distinto(tmp_path: Path) -> None:
    # Arrange
    directory = write_catalog(tmp_path)
    content = (directory / "precios.csv").read_text(encoding="utf-8")
    header, row = content.splitlines()[:2]
    row = row.replace(",CO,", ",MX,")
    (directory / "precios.csv").write_text("\n".join([header, row]) + "\n", encoding="utf-8")

    # Act / Assert
    with pytest.raises(CatalogError, match="país distinto"):
        load_catalog(directory)


def test_material_sin_regla(tmp_path: Path) -> None:
    # Arrange
    directory = write_catalog(tmp_path)
    content = (directory / "referencias.csv").read_text(encoding="utf-8")
    content = content.replace("MX-VASO-12-PAPEL", "MX-VASO-12-VIDRIO").replace(
        ",PAPEL,", ",VIDRIO,"
    )
    (directory / "referencias.csv").write_text(content, encoding="utf-8")

    # Act / Assert
    with pytest.raises(CatalogError, match="material sin regla"):
        load_catalog(directory)


def test_fingerprint_cambia(tmp_path: Path) -> None:
    # Arrange
    directory = write_catalog(tmp_path)
    first = load_catalog(directory).fingerprint

    # Act
    with (directory / "referencias.csv").open("a", encoding="utf-8") as handle:
        handle.write("")
    (directory / "referencias.csv").write_text(
        (directory / "referencias.csv").read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )
    second = load_catalog(directory).fingerprint

    # Assert
    assert first != second
