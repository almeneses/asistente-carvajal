"""Modelos de datos del catálogo de empaques."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


class CatalogError(RuntimeError):
    """El catálogo no cumple el contrato de datos."""


@dataclass(frozen=True)
class Reference:
    """Referencia del catálogo (producto)."""

    sku: str
    name: str
    family: str
    uses: tuple[str, ...]
    capacity_oz: float | None
    diameter_mm: float | None
    material: str
    brand: str
    units_per_pack: int | None
    packs_per_box: int | None
    units_per_box: int | None
    temp_min_c: float | None
    temp_max_c: float | None
    price: float | None
    currency: str | None
    tax_included: bool | None
    price_valid_until: str | None
    country: str
    source_url: str
    captured_at: str


@dataclass(frozen=True)
class Price:
    """Precio de referencia de un SKU (archivo de precios)."""

    sku: str
    country: str
    amount: float
    currency: str
    tax_status: str
    source_type: str
    source_name: str
    source_city: str
    valid_until: str | None
    source_url: str
    captured_at: str


@dataclass(frozen=True)
class MaterialRule:
    """Regla técnica de un material."""

    material: str
    temp_min_c: float
    temp_max_c: float
    microwave: bool
    refrigeration: bool
    freezing: bool
    hot_content: bool
    recycling_code: str
    applications: dict[str, str]
    source_url: str
    captured_at: str


@dataclass(frozen=True)
class Distributor:
    """Punto de venta o canal de un distribuidor."""

    name: str
    city: str
    address: str
    phone: str
    source_url: str
    captured_at: str


@dataclass(frozen=True)
class CatalogSnapshot:
    """Catálogo cargado y validado, de solo lectura."""

    catalog_dir: Path
    fingerprint: str
    manifest: dict[str, object]
    references: tuple[Reference, ...]
    prices: tuple[Price, ...]
    materials: dict[str, MaterialRule]
    distributors: tuple[Distributor, ...]

    @property
    def references_count(self) -> int:
        return len(self.references)

    @property
    def prices_count(self) -> int:
        return len(self.prices)

    @property
    def distributors_count(self) -> int:
        return len(self.distributors)

    @property
    def by_sku(self) -> dict[str, Reference]:
        return {reference.sku: reference for reference in self.references}

    def price_for(self, sku: str) -> Price | None:
        return next((price for price in self.prices if price.sku == sku), None)


@dataclass(frozen=True)
class ExtractedQuery:
    """Consulta interpretada por el router determinista."""

    intent: str  # documental | commercial | mixed | ambiguous
    family: str | None = None
    capacity_oz: float | None = None
    quantity: int | None = None
    city: str | None = None
    country: str | None = None
    use: str | None = None
    temperature: str | None = None
    material: str | None = None
    prefers_renewable: bool = False
    asks_price: bool = False
    asks_distributor: bool = False
    microwave: bool = False
    freezing: bool = False
    residual_documental: bool = False


@dataclass(frozen=True)
class PriceQuote:
    """Precio resuelto con vigencia y cálculo de cajas."""

    amount: float
    currency: str
    country: str
    tax_status: str
    validity: str  # vigente | vencido | no_declarada
    valid_until: str | None
    source_url: str
    captured_at: str
    warnings: tuple[str, ...] = ()
    boxes: int | None = None
    total: float | None = None
    units_per_box: int | None = None


@dataclass(frozen=True)
class Citation:
    """Fuente citada de una respuesta de catálogo."""

    label: str
    url: str


@dataclass(frozen=True)
class CatalogItem:
    """Elemento mostrado en una sección de catálogo."""

    title: str
    url: str
    details: tuple[str, ...] = ()
    price: PriceQuote | None = None
    sku: str | None = None


@dataclass(frozen=True)
class Recommendation:
    """Referencia recomendada con su precio y citas."""

    reference: Reference
    quote: PriceQuote | None
    citations: tuple[Citation, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class CatalogSection:
    """Sección determinista de la respuesta."""

    kind: str  # recommendations | distributors | no_match | clarification
    title: str
    items: tuple[CatalogItem, ...] = ()
    message: str | None = None
    citations: tuple[Citation, ...] = ()


@dataclass(frozen=True)
class CatalogAnswer:
    """Respuesta de la rama de catálogo."""

    intent: str
    section: CatalogSection | None = None
    citations: tuple[Citation, ...] = ()
    warnings: tuple[str, ...] = field(default_factory=tuple)
