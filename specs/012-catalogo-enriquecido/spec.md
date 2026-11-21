# Feature Specification: Catálogo enriquecido y cotizador streaming

**Branch**: `feat/012-catalogo-enriquecido` · **Fase**: 12

## Objetivo

Enriquecer las 200 referencias con imágenes y especificaciones desde las fichas oficiales,
y convertir la respuesta comercial en un flujo streaming: mejor opción primero, hasta dos
alternativas desplegables, con imágenes en tarjetas, revisión y confirmación.

## User Scenarios

### US1 · Catálogo enriquecido (P1)
- **Given** una referencia, **Then** la app conoce su imagen local optimizada y especificaciones adicionales (descripción, dimensiones, peso, color).
- **Given** una ficha sin imagen, **Then** se usa un placeholder local y no se rompe.

### US2 · Mejor opción primero (P1)
- **Given** una consulta comercial, **When** el stream avanza, **Then** aparece primero la mejor recomendación con imagen y specs.
- **Given** más opciones, **Then** aparecen hasta 2 en un `<details>` “Ver alternativas”.

### US3 · Cotizador con imagen (P2)
- **Given** una opción, **When** abro la revisión, **Then** veo su imagen y specs; la confirmación conserva la imagen.
- **Given** elijo una alternativa, **Then** esa pasa a ser la opción principal.

## Requirements

- **FR-001**: Script reproducible que lea `referencias.csv` y genere `product_assets.json` + imágenes WebP 600×600 locales.
- **FR-002**: Guardar `source_url`, `captured_at` y atribución; no modificar los datos de `carvajal`.
- **FR-003**: Caché de fichas y manejo de fallos/404 sin abortar el lote.
- **FR-004**: Operar desde el catálogo CSV: imagen por SKU, placeholder si falta.
- **FR-005**: SSE comercial: `status`, `quote_best`, `quote_alternatives` (0–2), `done`.
- **FR-006**: Mejor opción primero; alternativas dentro de `<details>`.
- **FR-007**: Las tarjetas muestran imagen, nombre, material, unidades, cajas y total.
- **FR-008**: Seleccionar alternativa actualiza la opción principal.
- **FR-009**: Revisión y confirmación muestran imagen y specs.
- **FR-010**: Fallback accesible con `alt`, `loading="lazy"` y placeholder.
- **FR-011**: Tests de assets, orden SSE, límite de alternativas y render.
- **FR-012**: Sin regresiones.

## Success Criteria

- **SC-001**: ≥95% de referencias con imagen local; el resto con placeholder.
- **SC-002**: 0 peticiones a dominios externos en runtime.
- **SC-003**: Mejor opción visible antes que alternativas; máximo 2.
- **SC-004**: Cotización conserva imagen/specs.
- **SC-005**: CI, gates y 198+ pruebas verdes.
