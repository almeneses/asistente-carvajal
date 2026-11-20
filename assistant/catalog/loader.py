"""Carga y validación del catálogo de empaques (solo lectura)."""

from __future__ import annotations

import csv
import json
from hashlib import sha256
from pathlib import Path

from assistant.catalog.models import (
    CatalogError,
    CatalogSnapshot,
    Distributor,
    MaterialRule,
    Price,
    Reference,
)

REFERENCE_HEADERS = (
    "sku",
    "name",
    "family",
    "use",
    "capacity_oz",
    "diameter_mm",
    "material",
    "brand",
    "units_per_pack",
    "packs_per_box",
    "units_per_box",
    "temp_min_c",
    "temp_max_c",
    "price",
    "currency",
    "tax_included",
    "price_valid_until",
    "country",
    "source_url",
    "captured_at",
)
PRICE_HEADERS = (
    "sku",
    "country",
    "amount",
    "currency",
    "tax_status",
    "source_type",
    "source_name",
    "source_city",
    "valid_until",
    "source_url",
    "captured_at",
)
MATERIAL_HEADERS = (
    "material",
    "temp_min_c",
    "temp_max_c",
    "microwave",
    "refrigeration",
    "freezing",
    "hot_content",
    "recycling_code",
    "applications",
    "source_url",
    "captured_at",
)
DISTRIBUTOR_HEADERS = (
    "name",
    "city",
    "address",
    "phone",
    "source_url",
    "captured_at",
)
_FILES = (
    ("referencias.csv", REFERENCE_HEADERS),
    ("precios.csv", PRICE_HEADERS),
    ("materiales.csv", MATERIAL_HEADERS),
    ("distribuidores.csv", DISTRIBUTOR_HEADERS),
)
_APPLICATION_VALUES = {"recomendable", "aplicable", "no_apto"}
_COUNTRIES = {"MX", "CO"}


def _text(row: dict[str, str], key: str) -> str:
    return (row.get(key) or "").strip()


def _number(row: dict[str, str], key: str, *, required: bool = False) -> float | None:
    raw = _text(row, key).replace(",", ".")
    if not raw:
        if required:
            raise ValueError(f"falta {key}")
        return None
    return float(raw)


def _integer(row: dict[str, str], key: str) -> int | None:
    value = _number(row, key)
    if value is None:
        return None
    return int(value)


def _boolean(row: dict[str, str], key: str) -> bool | None:
    raw = _text(row, key).lower()
    if not raw:
        return None
    return raw in {"true", "1", "si", "sí"}


def _read_rows(path: Path, headers: tuple[str, ...]) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise CatalogError(f"{path.name}: archivo vacío.")
            missing = [header for header in headers if header not in reader.fieldnames]
            if missing:
                raise CatalogError(f"{path.name}: faltan columnas: {', '.join(missing)}")
            return list(reader)
    except OSError as error:
        raise CatalogError(f"No se pudo leer {path}: {error}") from error


def _reference(row: dict[str, str]) -> Reference:
    sku = _text(row, "sku")
    if not sku:
        raise CatalogError("referencias.csv: hay una fila sin sku.")
    material = _text(row, "material")
    if not material:
        raise CatalogError(f"referencias.csv: {sku} sin material.")
    return Reference(
        sku=sku,
        name=_text(row, "name"),
        family=_text(row, "family"),
        uses=tuple(part.strip() for part in _text(row, "use").split("|") if part.strip()),
        capacity_oz=_number(row, "capacity_oz"),
        diameter_mm=_number(row, "diameter_mm"),
        material=material,
        brand=_text(row, "brand"),
        units_per_pack=_integer(row, "units_per_pack"),
        packs_per_box=_integer(row, "packs_per_box"),
        units_per_box=_integer(row, "units_per_box"),
        temp_min_c=_number(row, "temp_min_c"),
        temp_max_c=_number(row, "temp_max_c"),
        price=_number(row, "price"),
        currency=_text(row, "currency") or None,
        tax_included=_boolean(row, "tax_included"),
        price_valid_until=_text(row, "price_valid_until") or None,
        country=_text(row, "country"),
        source_url=_text(row, "source_url"),
        captured_at=_text(row, "captured_at"),
    )


def _price(row: dict[str, str]) -> Price:
    sku = _text(row, "sku")
    amount = _number(row, "amount", required=True)
    if amount is None or amount <= 0:
        raise CatalogError(f"precios.csv: {sku} con monto inválido.")
    return Price(
        sku=sku,
        country=_text(row, "country"),
        amount=amount,
        currency=_text(row, "currency"),
        tax_status=_text(row, "tax_status"),
        source_type=_text(row, "source_type"),
        source_name=_text(row, "source_name"),
        source_city=_text(row, "source_city"),
        valid_until=_text(row, "valid_until") or None,
        source_url=_text(row, "source_url"),
        captured_at=_text(row, "captured_at"),
    )


def _material(row: dict[str, str]) -> MaterialRule:
    material = _text(row, "material")
    applications: dict[str, str] = {}
    for part in _text(row, "applications").split("|"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value not in _APPLICATION_VALUES:
            raise CatalogError(f"materiales.csv: {material} con aplicación inválida ({value!r}).")
        applications[key] = value
    return MaterialRule(
        material=material,
        temp_min_c=_number(row, "temp_min_c", required=True) or 0.0,
        temp_max_c=_number(row, "temp_max_c", required=True) or 0.0,
        microwave=bool(_boolean(row, "microwave")),
        refrigeration=bool(_boolean(row, "refrigeration")),
        freezing=bool(_boolean(row, "freezing")),
        hot_content=bool(_boolean(row, "hot_content")),
        recycling_code=_text(row, "recycling_code"),
        applications=applications,
        source_url=_text(row, "source_url"),
        captured_at=_text(row, "captured_at"),
    )


def _distributor(row: dict[str, str]) -> Distributor:
    name = _text(row, "name")
    city = _text(row, "city")
    if not name or not city:
        raise CatalogError("distribuidores.csv: hay una fila sin nombre o ciudad.")
    return Distributor(
        name=name,
        city=city,
        address=_text(row, "address"),
        phone=_text(row, "phone"),
        source_url=_text(row, "source_url"),
        captured_at=_text(row, "captured_at"),
    )


def _fingerprint(catalog_dir: Path) -> str:
    digest = sha256()
    for name in ("referencias.csv", "precios.csv", "materiales.csv", "distribuidores.csv"):
        digest.update((catalog_dir / name).read_bytes())
    return digest.hexdigest()


def load_catalog(catalog_dir: Path) -> CatalogSnapshot:
    """Carga y valida el snapshot del catálogo; falla con mensaje accionable."""
    if not catalog_dir.is_dir():
        raise CatalogError(f"CATALOG_DIR no existe: {catalog_dir}")
    for name, headers in _FILES:
        path = catalog_dir / name
        if not path.is_file():
            raise CatalogError(f"Falta {name} en {catalog_dir}.")
        try:
            _read_rows(path, headers)
        except CatalogError:
            raise
    try:
        manifest = json.loads((catalog_dir / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CatalogError(f"manifest.json inválido: {error}") from error

    references = tuple(
        _reference(row) for row in _read_rows(catalog_dir / "referencias.csv", REFERENCE_HEADERS)
    )
    prices = tuple(_price(row) for row in _read_rows(catalog_dir / "precios.csv", PRICE_HEADERS))
    materials = tuple(
        _material(row) for row in _read_rows(catalog_dir / "materiales.csv", MATERIAL_HEADERS)
    )
    distributors = tuple(
        _distributor(row)
        for row in _read_rows(catalog_dir / "distribuidores.csv", DISTRIBUTOR_HEADERS)
    )

    skus = {reference.sku for reference in references}
    if len(skus) != len(references):
        raise CatalogError("referencias.csv: hay SKU duplicados.")
    for reference in references:
        if reference.country not in _COUNTRIES:
            raise CatalogError(
                f"referencias.csv: {reference.sku} con país inválido ({reference.country!r})."
            )
        if not reference.source_url.startswith(("http://", "https://")):
            raise CatalogError(f"referencias.csv: {reference.sku} sin ficha válida.")
        if reference.currency not in (None, "MXN", "COP"):
            raise CatalogError(f"referencias.csv: {reference.sku} con moneda inválida.")
    for price in prices:
        if price.sku not in skus:
            raise CatalogError(f"precios.csv: SKU huérfano {price.sku}.")
        reference = next(item for item in references if item.sku == price.sku)
        if price.country != reference.country:
            raise CatalogError(f"precios.csv: {price.sku} con país distinto al de la referencia.")
        if price.currency not in ("MXN", "COP"):
            raise CatalogError(f"precios.csv: {price.sku} con moneda inválida.")
    material_names = {material.material for material in materials}
    if len(material_names) != len(materials):
        raise CatalogError("materiales.csv: materiales duplicados.")
    without_rule = set(manifest.get("materials_without_rule", []))
    for reference in references:
        if reference.material not in material_names and reference.material not in without_rule:
            raise CatalogError(
                f"referencias.csv: {reference.sku} usa material sin regla ({reference.material})."
            )
    if not references:
        raise CatalogError("El catálogo no tiene referencias.")
    return CatalogSnapshot(
        catalog_dir=catalog_dir,
        fingerprint=_fingerprint(catalog_dir),
        manifest=manifest,
        references=references,
        prices=prices,
        materials={material.material: material for material in materials},
        distributors=distributors,
    )
