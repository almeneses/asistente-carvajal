# Plan: catálogo enriquecido y streaming

- **Pipeline**: `scripts/enrich_catalog.py` lee `referencias.csv`, cachea fichas en
  `.cache/catalog_pages`, extrae `og:image`, descripción/dimensiones/peso/color y
  convierte a WebP 600×600 con `ffmpeg`; escribe `assistant/catalog/product_assets.json`
  y `assistant/static/products/{sku}.webp`.
- **Runtime**: `assistant/catalog/assets.py` carga el JSON; filtro Jinja `product_image`.
- **SSE**: en la rama comercial, `quote_best` (HTML de la mejor) y `quote_alternatives`
  (hasta 2) antes de `done`; el cliente los inserta en orden.
- **UI**: `_quote_best.html` y `_quote_alternatives.html`; `<details>`; CTA con
  `data-image`; revisión/confirmación con imagen.
- **Pruebas**: fallback, orden de eventos, máximo de alternativas, estructura.
