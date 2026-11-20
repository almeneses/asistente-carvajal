"""CSVs sintéticos del catálogo para pruebas (sin red)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from assistant.catalog.loader import (
    DISTRIBUTOR_HEADERS,
    MATERIAL_HEADERS,
    PRICE_HEADERS,
    REFERENCE_HEADERS,
    load_catalog,
)
from assistant.catalog.models import CatalogSnapshot

_REFERENCES = [
    {
        "sku": "MX-VASO-12-PP",
        "name": "Vaso PP 12 oz",
        "family": "vaso",
        "use": "comida_caliente|bebida_caliente",
        "capacity_oz": "12",
        "diameter_mm": "98",
        "material": "PP",
        "brand": "Converpro",
        "units_per_pack": "50",
        "packs_per_box": "20",
        "units_per_box": "1000",
        "temp_min_c": "0",
        "temp_max_c": "100",
        "price": "900",
        "currency": "MXN",
        "tax_included": "true",
        "price_valid_until": "2027-12-31",
        "country": "MX",
        "source_url": "https://example.com/mx-vaso-pp",
        "captured_at": "2026-11-01",
    },
    {
        "sku": "MX-VASO-12-PET",
        "name": "Vaso PET 12 oz",
        "family": "vaso",
        "use": "bebida_fria",
        "capacity_oz": "12",
        "diameter_mm": "98",
        "material": "PET",
        "brand": "Converpro",
        "units_per_pack": "50",
        "packs_per_box": "16",
        "units_per_box": "800",
        "temp_min_c": "-20",
        "temp_max_c": "40",
        "price": "1111",
        "currency": "MXN",
        "tax_included": "true",
        "price_valid_until": "2027-12-31",
        "country": "MX",
        "source_url": "https://example.com/mx-vaso-pet",
        "captured_at": "2026-11-01",
    },
    {
        "sku": "MX-VASO-12-PAPEL",
        "name": "Vaso papel 12 oz",
        "family": "vaso",
        "use": "comida_caliente",
        "capacity_oz": "12",
        "diameter_mm": "90",
        "material": "PAPEL",
        "brand": "Converpro Bio",
        "units_per_pack": "50",
        "packs_per_box": "20",
        "units_per_box": "1000",
        "temp_min_c": "0",
        "temp_max_c": "90",
        "price": "800",
        "currency": "MXN",
        "tax_included": "true",
        "price_valid_until": "2027-12-31",
        "country": "MX",
        "source_url": "https://example.com/mx-vaso-papel",
        "captured_at": "2026-11-01",
    },
    {
        "sku": "CO-VASO-9-PP",
        "name": "Vaso PP 9 oz",
        "family": "vaso",
        "use": "bebida_fria",
        "capacity_oz": "9",
        "diameter_mm": "80",
        "material": "PP",
        "brand": "Converpro",
        "units_per_pack": "50",
        "packs_per_box": "50",
        "units_per_box": "2500",
        "temp_min_c": "0",
        "temp_max_c": "100",
        "price": "",
        "currency": "",
        "tax_included": "",
        "price_valid_until": "",
        "country": "CO",
        "source_url": "https://example.com/co-vaso-pp",
        "captured_at": "2026-11-18",
    },
]

_PRICES = [
    {
        "sku": "CO-VASO-9-PP",
        "country": "CO",
        "amount": "206305",
        "currency": "COP",
        "tax_status": "incluido",
        "source_type": "tercero",
        "source_name": "EDEXA",
        "source_city": "Bogotá",
        "valid_until": "",
        "source_url": "https://example.com/co-precio",
        "captured_at": "2026-11-18",
    }
]

_MATERIALS = [
    {
        "material": "PP",
        "temp_min_c": "0",
        "temp_max_c": "100",
        "microwave": "true",
        "refrigeration": "false",
        "freezing": "false",
        "hot_content": "true",
        "recycling_code": "5",
        "applications": "comida_caliente=recomendable|comida_fria=aplicable",
        "source_url": "https://example.com/materiales",
        "captured_at": "2026-11-18",
    },
    {
        "material": "PET",
        "temp_min_c": "-20",
        "temp_max_c": "40",
        "microwave": "false",
        "refrigeration": "true",
        "freezing": "true",
        "hot_content": "false",
        "recycling_code": "1",
        "applications": "comida_caliente=no_apto|comida_fria=recomendable",
        "source_url": "https://example.com/materiales",
        "captured_at": "2026-11-18",
    },
    {
        "material": "PAPEL",
        "temp_min_c": "0",
        "temp_max_c": "90",
        "microwave": "false",
        "refrigeration": "false",
        "freezing": "false",
        "hot_content": "true",
        "recycling_code": "20",
        "applications": "comida_caliente=recomendable",
        "source_url": "https://example.com/materiales",
        "captured_at": "2026-11-18",
    },
]

_DISTRIBUTORS = [
    {
        "name": "Distribuidora Bogotá",
        "city": "Bogotá",
        "address": "Calle 1 # 2-3",
        "phone": "601 000 0000",
        "source_url": "https://example.com/dist-bogota",
        "captured_at": "2026-11-18",
    },
    {
        "name": "Distribuidora Medellín",
        "city": "Medellín",
        "address": "Carrera 4 # 5-6",
        "phone": "604 000 0000",
        "source_url": "https://example.com/dist-medellin",
        "captured_at": "2026-11-18",
    },
]


def _write(path: Path, headers: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def write_catalog(directory: Path) -> Path:
    """Escribe el catálogo sintético y devuelve su directorio."""
    directory.mkdir(parents=True, exist_ok=True)
    _write(directory / "referencias.csv", REFERENCE_HEADERS, _REFERENCES)
    _write(directory / "precios.csv", PRICE_HEADERS, _PRICES)
    _write(directory / "materiales.csv", MATERIAL_HEADERS, _MATERIALS)
    _write(directory / "distribuidores.csv", DISTRIBUTOR_HEADERS, _DISTRIBUTORS)
    (directory / "manifest.json").write_text(
        json.dumps({"spec": "test", "sources": {}}), encoding="utf-8"
    )
    return directory


def sample_snapshot(tmp_path: Path) -> CatalogSnapshot:
    return load_catalog(write_catalog(tmp_path))
