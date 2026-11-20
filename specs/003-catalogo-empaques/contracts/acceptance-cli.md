# Contrato: CLI de aceptación del catálogo

**Feature**: `specs/003-catalogo-empaques` · **Fecha**: 2026-11-20

## Ejecución

```bash
uv run python scripts/run_catalog_acceptance.py \
  --routing-file ../carvajal/data/eval/routing_questions.json \
  --json-out specs/003-catalogo-empaques/reports/acceptance.json \
  --markdown-out specs/003-catalogo-empaques/reports/acceptance.md \
  [--limit N] [--today YYYY-MM-DD]
```

- Carga el catálogo desde `CATALOG_DIR` y el set de enrutamiento desde `--routing-file`
  (o `CATALOG_ROUTING_FILE`).
- `--today` permite simular la fecha para precios vencidos (defecto: fecha del sistema).
- **No** requiere el servidor web; usa el router y la rama de catálogo en proceso.

## Qué evalúa

| Grupo | Ruta esperada | Comprobaciones |
|---|---|---|
| `existente` (49) | `rag` | La ruta sigue siendo documental (sin regresión). |
| `comercial` (61) | `commercial` | Atributos esperados (`family`, `use`, `capacity_oz`, `quantity`, `city`, `country`) y materiales prohibidos. |
| `colombia` (20) | `commercial` | Atributos + cajas/total o ausencia de precio declarada. |

- **Atributos**: se comparan los campos presentes en `expected`; tolerancia de capacidad
  ±1 oz.
- **Materiales prohibidos**: ninguna recomendación puede incluir los materiales listados
  en `constraints.forbidden_materials`.
- **Cotización**: si el ítem trae `quote.total`, se calcula cajas×precio y debe coincidir;
  si trae `no_price`, la respuesta debe declarar ausencia de precio (los SKU placeholder
  `CO-*` se tratan como sin precio).
- **Sin coincidencia**: casos propios del set de catálogo (fixtures) deben responder
  `no_match` sin alternativas inválidas.

## Reporte

```json
{
  "generated_at": "…",
  "catalog_fingerprint": "sha256…",
  "total": 130,
  "route_ok": 121,
  "route_accuracy": 0.931,
  "attributes_ok": 108,
  "attributes_accuracy": 0.888,
  "forbidden_violations": 0,
  "quote_ok": 17,
  "quote_accuracy": 0.895,
  "rows": [
    {
      "id": "c-01",
      "question": "necesito vasos para café caliente de 12 oz",
      "expected_route": "commercial",
      "actual_route": "commercial",
      "attributes_expected": {"family": "vaso", "capacity_oz": 12.0},
      "attributes_actual": {"family": "vaso", "capacity_oz": 12.0, "use": "bebida_caliente"},
      "recommended_skus": ["…"],
      "forbidden_materials": ["PET"],
      "violations": [],
      "quote_status": "not_applicable"
    }
  ]
}
```

- **Markdown**: resumen con precisión de ruta/atributos, violaciones y filas fallidas.
- **Exit codes**: `0` si `route_accuracy ≥ 0.90`, `forbidden_violations == 0` y
  `quote_accuracy ≥ 0.90`; `1` si no; `2` si catálogo/set no cargan o falta configuración.

## Invariantes

- El reporte no contiene precios inventados: solo compara con datos del catálogo.
- No modifica el catálogo ni el corpus.
- Las filas fallidas incluyen la causa legible para corregir reglas o datos.
