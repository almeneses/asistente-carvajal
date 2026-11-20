# Data Model: Evaluación de recuperación y métricas de calidad

**Feature**: `specs/002-evaluacion-recuperacion` · **Fecha**: 2026-11-20

Define el ground truth versionado, la configuración de variantes, el reporte y las
validaciones. Es la fuente para `contracts/`, `tasks.md` y las pruebas.

## Ground truth (`specs/002-evaluacion-recuperacion/evaluation/questions.json`)

### EvaluationSet

| Campo | Tipo | Regla |
|---|---|---|
| `version` | int | `1` |
| `corpus_fingerprint` | str | sha256 del corpus anotado |
| `reviewed_by` | str | obligatorio, no vacío |
| `reviewed_at` | str ISO-8601 | obligatorio |
| `questions` | list[EvaluationQuestion] | exactamente 30, ids únicos |

- **Validación**: si el fingerprint no coincide con el corpus cargado, el set se marca
  como desactualizado (advertencia) y la corrida falla salvo `--allow-stale-set`.
- **Inmutabilidad**: una vez congelado, cualquier cambio exige revisión humana y sube
  `version`.

### EvaluationQuestion

| Campo | Tipo | Regla |
|---|---|---|
| `id` | str | `qNN`, único |
| `question` | str | 1..2000 caracteres |
| `expected_slugs` | list[str] | ≥1 si `sustainable`; vacío si `not_sustainable` |
| `expected_status` | enum | `sustainable` \| `not_sustainable` |
| `key_facts` | list[str] | ≥1, hechos que una respuesta correcta debe cubrir |
| `notes` | str | opcional; dudas de la revisión |

- **Validación**: cada `slug` existe en el corpus; `id` único; `question` no vacía.
- **Ciclo de vida**: `candidate` (propuesta LLM) → `reviewed` (persona firma) →
  `frozen` (congelado en el commit). El reporte solo usa el estado `frozen`.

## Variantes (`assistant/evaluation/variants.py`)

### VariantConfig

| Campo | Tipo | Regla |
|---|---|---|
| `id` | str | `^[a-z0-9][a-z0-9-]*$`; p. ej. `bge-m3-500-hybrid` |
| `embedding_model` | str | `nomic-embed-text` \| `bge-m3` |
| `embedding_dim` | int | 768 \| 1024, coherente con el modelo |
| `chunk_size` | int | 1000 \| 500 |
| `overlap` | int | 200 \| 100; `< chunk_size` |
| `cosine_weight` | float | 0.6 \| 1.0 |
| `lexical_weight` | float | `1 - cosine_weight` |
| `collection` | str | `eval_<id>` con guiones bajos; única |
| `min_score` | float | 0.2 (umbral de la cadena) |

- **Matriz**: 8 configuraciones = 2 modelos × 2 fragmentaciones × 2 mezclas.
- **Restricción**: dos variantes no pueden compartir `(embedding_model, embedding_dim,
  chunk_size, overlap)` salvo que cambie solo la mezcla; en ese caso comparten colección.

## Reporte (`specs/002-evaluacion-recuperacion/reports/*.json`)

### RunReport

| Campo | Tipo | Regla |
|---|---|---|
| `schema_version` | int | `1` |
| `generated_at` | str ISO-8601 | UTC |
| `mode` | enum | `retrieval` \| `e2e` |
| `corpus_fingerprint` | str | sha256 del corpus |
| `index_jsonl_sha256` | str | sha256 del índice JSONL |
| `indexed_fragments` | int | fragmentos por variante |
| `provider` | str \| null | `deepseek`/`ollama` solo en `e2e` |
| `variants` | list[VariantReport] | ≥1 |
| `winner` | str \| null | id ganadora por `recall@5` (desempate MRR) |
| `omitted` | list[dict[id, reason]] | variantes no ejecutables (modelo o índice no disponible) |
| `migration_recommendation` | str \| null | “migrar a bge-m3 (X pp)” o “mantener nomic (X pp)” |

- **Comparabilidad**: dos reportes solo se comparan si `corpus_fingerprint` y
  `index_jsonl_sha256` coinciden; si no, el reporte lo declara en `not_comparable_with`.

### VariantReport

| Campo | Tipo | Regla |
|---|---|---|
| `config` | VariantConfig | — |
| `metrics` | Metrics | agregados |
| `rows` | list[QuestionRow] | una por pregunta |

### Metrics

| Campo | Tipo | Regla |
|---|---|---|
| `recall_at_1/3/5/10` | float 0..1 | macro sobre sustentables |
| `mrr` | float 0..1 | macro sobre sustentables |
| `citation_precision` | float 0..1 | solo `e2e`; 1.0 esperado |
| `expected_citation_coverage` | float 0..1 | respuestas que citan un slug esperado |
| `abstention_accuracy` | float 0..1 | sobre `not_sustainable` |
| `false_abstention_rate` | float 0..1 | sobre sustentables |
| `latency_p50_ms` | int | percentil 50 |
| `latency_p95_ms` | int | percentil 95 |
| `questions_evaluated` | int | 30 |

### QuestionRow

| Campo | Tipo | Regla |
|---|---|---|
| `id` / `question` | str | del set |
| `expected_slugs` | list[str] | del set |
| `expected_status` | enum | del set |
| `retrieved_slugs` | list[str] | orden de ranking, sin duplicados |
| `rank_first_expected` | int \| null | 1-based; null si no aparece |
| `status` | enum | `answered` \| `no_evidence` \| `error` (solo `e2e`) |
| `sources` | list[str] | URLs citadas (`e2e`) |
| `source_slugs` | list[str] | slugs citados (`e2e`), para cobertura |
| `citations_valid` | bool | todas las citas coinciden con el corpus |
| `citations_invalid` | int | número de citas que no coinciden |
| `latency_ms` | int | por pregunta |
| `error` | str \| null | causa si `status="error"` |

- **Invariante**: `mode="retrieval"` ⇒ `status`, `sources` y `citations_valid` son null/false
  y no se calcula `citation_precision` (se reporta `null`).

## Fingerprint

```text
corpus_fingerprint = sha256( "\n".join(f"{slug}:{hash}" for slug, hash en orden de slug) )
index_jsonl_sha256 = sha256( bytes de index.jsonl )
```

- Se calcula en `assistant/evaluation/fingerprint.py`; se guarda en el set y en cada
  reporte.

## Configuración de la app afectada

| Variable | Obligatoria | Defecto | Validación |
|---|---|---|---|
| `EMBEDDING_DIM` | no | `768` | entero 1..4096; debe coincidir con el modelo |
| `EVAL_QDRANT_PATH` | no | `.qdrant-eval` | ruta escribible, ignorada por Git |

- `OllamaEmbedder` valida cada vector contra `EMBEDDING_DIM`.
- `QdrantIndex` crea la colección con `EMBEDDING_DIM`; si la colección existente difiere,
  falla con mensaje que ordena recrearla.

## Transiciones de una corrida

```text
cargar set → validar fingerprint → construir/abrir colecciones por variante
  → retrieval (sin LLM) → métricas de recuperación → reporte parcial
  → [e2e opcional] → métricas de respuesta → reporte final → decidir ganadora
```

- Un error en una variante se registra en `rows`/`variants` y no invalida las demás,
  salvo que falle la carga del set o el fingerprint.
