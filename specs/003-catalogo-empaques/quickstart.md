# Quickstart: validar la consulta del catálogo

**Feature**: `specs/003-catalogo-empaques` · **Fecha**: 2026-11-20

Guía para levantar el asistente con el catálogo y comprobar recomendaciones, precios,
distribuidores y preguntas mixtas.

## Prerrequisitos

- Catálogo en una ruta local (snapshot del proyecto de corpus):
  ```bash
  ls ../carvajal/data/catalog/empaques/manifest.json
  ```
- Ollama con `bge-m3` y un modelo de chat (para la rama documental).
- Corpus e índice de fases anteriores ya configurados (`.env`).

## Configuración

```bash
cp .env.example .env   # si aún no existe
# Añadir/ajustar:
CATALOG_DIR=/ruta/a/carvajal/data/catalog/empaques
CATALOG_ROUTING_FILE=/ruta/a/carvajal/data/eval/routing_questions.json
```

## Arranque

```bash
make run
# http://127.0.0.1:8010
```

`GET /healthz` debe incluir `catalog.references = 200`, `prices = 29`,
`distributors = 29` y el fingerprint del catálogo.

## Validación manual

| Paso | Pregunta | Resultado esperado |
|---|---|---|
| 1 | “necesito vasos para café caliente de 12 oz” | Recomendaciones sin PET, con SKU, material, presentación y ficha |
| 2 | “¿cuánto cuesta la caja de vasos PET de 12 oz?” | Precio MXN con impuestos, fuente y vigencia; sin inventar |
| 3 | “necesito 5.000 vasos de 9 oz para jugos en Bogotá” | 2 cajas, total 412.610 COP y presentación usada |
| 4 | Misma consulta con `CATALOG_PRICE_TODAY=2030-01-01` | Precio marcado como **vencido**, no como actual |
| 5 | “¿quién distribuye en Medellín?” | Distribuidores con dirección, teléfono y fuente |
| 6 | “¿qué empaques sostenibles ofrece Carvajal y cuánto cuestan?” | Sección Catálogo primero; corpus solo si aporta la parte documental |
| 7 | “vasos de aluminio de 12 oz para café caliente” | Sin coincidencia, restricciones explicadas, sin alternativas inválidas |
| 8 | “¿qué es Carvajal y a qué sectores se dedica?” | Sigue respondiendo con el corpus (sin regresión) |

## Aceptación automatizada

```bash
uv run python scripts/run_catalog_acceptance.py \
  --routing-file ../carvajal/data/eval/routing_questions.json \
  --json-out specs/003-catalogo-empaques/reports/acceptance.json \
  --markdown-out specs/003-catalogo-empaques/reports/acceptance.md
```

Resultado esperado:

- 130 preguntas (49 existentes, 61 comerciales, 20 Colombia).
- `route_accuracy ≥ 0,90`; `forbidden_violations == 0`; `quote_accuracy ≥ 0,90`.
- Exit code `0` si cumple; `1` si no; `2` si catálogo/set no cargan.

## Evidencia de la fase (2026-11-20)

- Catálogo cargado: **200 referencias** (98 MX, 102 CO), 29 precios COP, 5 materiales y
  29 distribuidores; PAPEL/PULPA se validan con el rango de su ficha (materiales sin regla
  declarados en el manifiesto).
- Aceptación de las **130 preguntas**: ruta **130/130 (100 %)**, atributos **130/130
  (100 %)**, materiales prohibidos recomendados **0**, cotizaciones **13/13 (100 %)**;
  exit code 0.
- Respuestas comerciales deterministas, sin LLM; preguntas documentales sin regresión.
- Reportes versionados en `reports/acceptance.json/md`.

## Problemas frecuentes

- **`CATALOG_DIR` ausente o inválido**: el arranque falla con la ruta exacta a corregir.
- **Cabecera de CSV distinta**: el loader enumera la columna faltante; no inventa datos.
- **SKU de precio sin referencia**: el loader falla y reporta el SKU huérfano.
- **Precio vencido en pruebas**: usar `CATALOG_PRICE_TODAY` para fijar la fecha.
- **Pregunta comercial sin atributos**: el asistente pide aclaración en vez de suponer.
