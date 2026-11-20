"""Pruebas de validación de materiales."""

from __future__ import annotations

from pathlib import Path

from assistant.catalog.materials import check_compatibility
from tests.catalog_fixtures import sample_snapshot


def test_pet_no_apto_para_caliente(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    reference = snapshot.by_sku["MX-VASO-12-PET"]

    # Act
    compatible, _ = check_compatibility(
        reference,
        snapshot.materials["PET"],
        use="bebida_caliente",
        temperature="caliente",
    )

    # Assert
    assert compatible is False


def test_pp_apto_para_caliente(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    reference = snapshot.by_sku["MX-VASO-12-PP"]

    # Act
    compatible, warnings = check_compatibility(
        reference,
        snapshot.materials["PP"],
        use="bebida_caliente",
        temperature="caliente",
    )

    # Assert
    assert compatible is True
    assert warnings == ()


def test_microondas_solo_si_la_regla_lo_permite(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    reference = snapshot.by_sku["MX-VASO-12-PET"]

    # Act
    compatible, _ = check_compatibility(
        reference,
        snapshot.materials["PET"],
        use="microondas",
        temperature=None,
        needs_microwave=True,
    )

    # Assert
    assert compatible is False


def test_temperatura_fuera_de_rango(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path)
    reference = snapshot.by_sku["MX-VASO-12-PET"]

    # Act
    compatible, _ = check_compatibility(
        reference,
        snapshot.materials["PET"],
        use=None,
        temperature="caliente",
    )

    # Assert
    assert compatible is False
