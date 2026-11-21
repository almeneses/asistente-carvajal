# Analyze: catálogo enriquecido

- FR 12/12 cubiertos; SC 5/5.
- Datos: 200/200 referencias con imagen WebP local; `product_assets.json` con specs.
- SSE: `quote_best` antes de `quote_alternatives`; máximo 2 alternativas.
- Fallback: placeholder local cuando falta imagen.
- Sin dependencias nuevas (httpx/ffmpeg ya disponibles).
- Riesgo documentado: imágenes de la tienda oficial con atribución; no se modifican datos
  de `carvajal`.
