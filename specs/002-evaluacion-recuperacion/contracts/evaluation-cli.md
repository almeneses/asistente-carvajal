# Contrato: CLI de evaluación y reporte

**Feature**: `specs/002-evaluacion-recuperacion` · **Fecha**: 2026-11-20

Dos scripts, un reporte JSON (esquema en `data-model.md` §Reporte) y una tabla Markdown.

## 1. `scripts/propose_ground_truth.py`

Propone evidencia y estado esperado para revisión humana.

```bash
uv run python scripts/propose_ground_truth.py \
  --questions ../carvajal/data/questions.json \
  --output specs/002-evaluacion-recuperacion/evaluation/questions.candidate.json \
  --review specs/002-evaluacion-recuperacion/evaluation/review.md \
  [--limit N] [--provider deepseek|ollama]
```

- **Entrada**: JSON con lista de preguntas (strings u objetos `{question}`).
- **Proceso**: recupera los 5 fragmentos más similares por pregunta con el índice actual y
  pide al LLM una propuesta de `expected_slugs`, `expected_status` y `key_facts`.
- **Salida**: `questions.candidate.json` (esquema `EvaluationSet` sin firma) y `review.md`
  con una tabla `id | pregunta | propuesta | decisión | cambios`.
- **No** firma el set: `reviewed_by`/`reviewed_at` quedan vacíos hasta la revisión humana.
- **Exit codes**: `0` propuesta generada; `2` configuración, corpus o LLM no disponible.

## 2. `scripts/run_evaluation.py`

```bash
uv run python scripts/run_evaluation.py \
  --set specs/002-evaluacion-recuperacion/evaluation/questions.json \
  --mode retrieval \
  --variants all \
  --json-out specs/002-evaluacion-recuperacion/reports/baseline.json \
  --markdown-out specs/002-evaluacion-recuperacion/reports/baseline.md \
  [--qdrant-path .qdrant-eval] [--qdrant-url URL] \
  [--recreate] [--allow-stale-set] [--limit N]

# Ganadora end-to-end
uv run python scripts/run_evaluation.py \
  --set specs/002-evaluacion-recuperacion/evaluation/questions.json \
  --mode e2e --variants bge-m3-500-hybrid \
  --json-out specs/002-evaluacion-recuperacion/reports/ganadora.json
```

| Opción | Defecto | Regla |
|---|---|---|
| `--mode` | `retrieval` | `retrieval` no usa LLM; `e2e` exige una sola variante |
| `--variants` | `all` | `all` (8) o lista separada por comas de ids |
| `--qdrant-path` | `EVAL_QDRANT_PATH` o `.qdrant-eval` | nunca `.qdrant/` de la app |
| `--qdrant-url` | `QDRANT_URL` | si existe, tiene prioridad |
| `--recreate` | `false` | recrea las colecciones de las variantes |
| `--allow-stale-set` | `false` | permite fingerprint distinto (marca advertencia) |
| `--limit` | sin límite | primeras N preguntas (para humo) |
| `--validate-only` | `false` | valida el set y sale sin indexar |
| `--json-out` / `--markdown-out` | — | rutas de salida |

- **Progreso**: logs por variante a `stderr`; rutas de reporte y ganadora a `stdout`.
- **Exit codes**: `0` reporte generado (retrieval) o umbrales cumplidos (e2e); `1`
  umbrales incumplidos o fingerprint inválido; `2` error de configuración, corpus, modelo
  o índice.
- **Variantes omitidas**: si un modelo o índice no está disponible, la variante se
  registra en `omitted` con su causa y la corrida continúa.
- **Recomendación**: el reporte de retrieval incluye `migration_recommendation` con el
  delta de `recall@5` entre `bge-m3` y `nomic-embed-text` y el umbral de 5 pp.
- **Umbrales** (solo `e2e` para las métricas de respuesta):
  - `hit_at_5 ≥ 0.95` en sustentables (al menos una evidencia esperada en el top 5);
  - `citation_precision == 1.0` y `0` citas inválidas;
  - `abstention_accuracy ≥ 0.90`.

### Reporte JSON (resumen)

```json
{
  "schema_version": 1,
  "generated_at": "2026-11-20T15:00:00+00:00",
  "mode": "retrieval",
  "corpus_fingerprint": "sha256…",
  "index_jsonl_sha256": "sha256…",
  "indexed_fragments": {"nomic-1000": 123, "bge-m3-500": 251},
  "provider": null,
  "variants": [
    {
      "config": {"id": "nomic-1000-hybrid", "embedding_model": "nomic-embed-text", "…": "…"},
      "metrics": {"recall_at_5": 0.9, "mrr": 0.78, "latency_p50_ms": 35, "…": "…"},
      "rows": [{"id": "q01", "retrieved_slugs": ["…"], "rank_first_expected": 1, "…": "…"}]
    }
  ],
  "winner": "bge-m3-500-hybrid"
}
```

- **Markdown**: tabla `variante | recall@1 | recall@5 | MRR | p50 | p95` y, en `e2e`,
  columnas de citas y abstención; una sección final con la ganadora y los umbrales.
- **No comparable**: si el fingerprint difiere de `corpus_fingerprint`, el reporte se
  marca con `not_comparable_with` y la corrida falla salvo `--allow-stale-set`.
