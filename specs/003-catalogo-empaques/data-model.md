# Data Model: Consulta del catálogo de empaques

**Feature**: `specs/003-catalogo-empaques` · **Fecha**: 2026-11-20

Define los datos cargados, la consulta extraída, las respuestas y las validaciones. Es la
fuente para `contracts/` y `tasks.md`.

## Snapshot del catálogo

### CatalogSnapshot

| Campo | Tipo | Regla |
|---|---|---|
| `catalog_dir` | Path | directorio con los CSV y `manifest.json`; solo lectura |
| `fingerprint` | str | sha256 de los cuatro CSV ordenados por nombre |
| `references_count` | int | 200 en el snapshot actual |
| `prices_count` | int | 29 en el snapshot actual |
| `materials_count` | int | 5 |
| `distributors_count` | int | 29 |
| `captured_at` | str ISO | del manifiesto o del CSV más reciente |

- **Validación**: los cuatro archivos existen, cabeceras exactas, SKUs únicos y
  `units_per_box > 0` cuando hay presentación.

### Reference

| Campo | Tipo | Regla |
|---|---|---|
| `sku` | str | único, no vacío |
| `name` | str | no vacío |
| `family` | str | `vaso`, `contenedor`, `plato`, `tapa`, `charola`, `cubierto`, `envase`… |
| `uses` | tuple[str] | valores separados por `\|` en el CSV |
| `capacity_oz` | float \| None | ≥ 0 si existe |
| `diameter_mm` | float \| None | ≥ 0 si existe |
| `material` | str | debe existir en `materiales.csv` |
| `brand` | str | — |
| `units_per_pack` / `packs_per_box` / `units_per_box` | int | ≥ 1 si existen; `units_per_box` obligatorio para calcular cajas |
| `temp_min_c` / `temp_max_c` | float \| None | rango de la ficha |
| `price` / `currency` / `tax_included` / `price_valid_until` | — | solo México (precio en la referencia) |
| `country` | enum | `MX` \| `CO` |
| `source_url` | str | http(s) |
| `captured_at` | str ISO | obligatorio |

### Price

| Campo | Tipo | Regla |
|---|---|---|
| `sku` | str | debe existir en referencias |
| `country` | enum | `MX` \| `CO` |
| `amount` | float | > 0 |
| `currency` | enum | `MXN` \| `COP` (coherente con país) |
| `tax_status` | str | `incluido` \| `no_incluido` \| desconocido |
| `source_type` / `source_name` / `source_city` | str | fuente de la captura |
| `valid_until` | str ISO \| None | vacío = vigencia no declarada |
| `source_url` | str | http(s) |
| `captured_at` | str ISO | obligatorio |

- **Invariante**: un SKU de un país no puede recibir precio de otro país.

### MaterialRule

| Campo | Tipo | Regla |
|---|---|---|
| `material` | str | único (`PP`, `EPS`, `PS`, `PET`, `PAPEL`, `PULPA`, `ALUMINIO`…) |
| `temp_min_c` / `temp_max_c` | float | rango declarado |
| `microwave` / `refrigeration` / `freezing` / `hot_content` | bool | del CSV (`true`/`false`) |
| `recycling_code` | str | — |
| `applications` | dict[str, str] | uso → `recomendable` \| `aplicable` \| `no_apto` |
| `source_url` / `captured_at` | str | obligatorios |

### Distributor

| Campo | Tipo | Regla |
|---|---|---|
| `name` | str | no vacío |
| `city` | str | ciudad del catálogo (Colombia en el snapshot) |
| `address` / `phone` | str | pueden faltar; si faltan se omite el campo |
| `source_url` / `captured_at` | str | obligatorios |

## Consulta extraída

### QueryIntent

`documental` \| `commercial` \| `mixed` \| `ambiguous`.

### ExtractedQuery

| Campo | Tipo | Regla |
|---|---|---|
| `intent` | QueryIntent | del router determinista |
| `family` | str \| None | familia detectada |
| `capacity_oz` | float \| None | regex `N oz` |
| `quantity` | int \| None | `5.000`, `3000`, `2.000` |
| `city` / `country` | str \| None | ciudades del catálogo; `CO`/`MX` |
| `use` | str \| None | `bebida_caliente`, `bebida_fria`, `sopas`, `microondas`, `congelacion` |
| `temperature` | str \| None | `caliente`, `fria` |
| `material` | str \| None | PET/PP/EPS/PS/PAPEL/PULPA/ALUMINIO |
| `prefers_renewable` | bool | papel/pulpa/fibra/sostenible |
| `asks_price` / `asks_distributor` | bool | señales léxicas |
| `residual_documental` | bool | parte documental detectada en pregunta mixta |

- **Validación**: si `intent="commercial"` y falta `family` o un criterio de uso, la
  respuesta pide aclaración (no adivina).

## Resultados

### PriceQuote

| Campo | Tipo | Regla |
|---|---|---|
| `amount` / `currency` / `country` | — | del precio resuelto |
| `tax_status` | str | del dato |
| `validity` | enum | `vigente` \| `vencido` \| `no_declarada` |
| `valid_until` | str \| None | — |
| `boxes` / `total` | int \| None / float \| None | solo si hay cantidad y precio |
| `units_per_box` | int \| None | presentación usada |
| `source_url` / `captured_at` | str | — |
| `warnings` | tuple[str] | vencido / no declarada / sin precio |

### Recommendation

| Campo | Tipo | Regla |
|---|---|---|
| `reference` | Reference | validada por material/temperatura |
| `quote` | PriceQuote \| None | None si no hay precio |
| `citations` | tuple[str] | ficha + fuente de precio |
| `warnings` | tuple[str] | regla faltante, precio vencido, etc. |

### CatalogAnswer

| Campo | Tipo | Regla |
|---|---|---|
| `intent` | QueryIntent | del router |
| `sections` | tuple[Section] | `catalog` y/o `corpus`; catálogo primero en mixtas |
| `catalog` | CatalogSection \| None | recomendaciones/precios/distribuidores/no-match |
| `corpus_answer` | Answer \| None | solo si se invocó RAG documental |
| `clarification` | str \| None | si falta un dato o la intención es ambigua |
| `citations` | tuple[str] | unión de citas de las secciones |

## Configuración añadida

| Variable | Obligatoria | Defecto | Validación |
|---|---|---|---|
| `CATALOG_DIR` | sí | — | directorio con los cuatro CSV + `manifest.json` |
| `CATALOG_ROUTING_FILE` | no | — | JSON del set de aceptación |
| `CATALOG_PRICE_TODAY` | no | fecha actual | ISO `YYYY-MM-DD` para pruebas de vigencia |

- `CATALOG_PRICE_TODAY` permite tests deterministas de precios vencidos.

## Reporte de aceptación

`CatalogAcceptanceReport`: `generated_at`, `catalog_fingerprint`, `total`, `route_ok`,
`route_accuracy`, `attributes_ok`, `attributes_accuracy`, `forbidden_violations`,
`quote_ok`, `quote_accuracy`, `rows[]`. Cada fila: `id`, `question`, `expected_route`,
`actual_route`, `attributes_expected`, `attributes_actual`, `recommended_skus`,
`forbidden_materials`, `violations`, `quote_status`.

- **Exit codes**: `0` si `route_accuracy ≥ 0.90` y `forbidden_violations == 0` y
  `quote_accuracy ≥ 0.90`; `1` si no; `2` si el catálogo o el set no cargan.
