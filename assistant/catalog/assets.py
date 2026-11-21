"""Assets locales de producto (imágenes y specs derivadas de las fichas)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ASSETS_PATH = Path(__file__).with_name("product_assets.json")
PLACEHOLDER = "/static/stitch/assets/producto-placeholder.svg"


@lru_cache(maxsize=1)
def _assets() -> dict[str, dict[str, object]]:
    if not ASSETS_PATH.is_file():
        return {}
    try:
        payload = json.loads(ASSETS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def product_image(sku: str | None) -> str:
    """Ruta local de la imagen o placeholder."""
    if not sku:
        return PLACEHOLDER
    image = _assets().get(sku, {}).get("image")
    return str(image) if image else PLACEHOLDER


def product_specs(sku: str | None) -> dict[str, object]:
    if not sku:
        return {}
    return dict(_assets().get(sku, {}))
