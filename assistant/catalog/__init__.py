"""Rama determinista del catálogo de empaques."""

from assistant.catalog.loader import load_catalog
from assistant.catalog.models import CatalogSnapshot

__all__ = ["CatalogSnapshot", "load_catalog"]
