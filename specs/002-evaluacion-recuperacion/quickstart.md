# Quickstart: evaluar recuperación y decidir el modelo

**Feature**: `specs/002-evaluacion-recuperacion` · **Fecha**: 2026-11-20

Guía para construir el ground truth, correr la matriz de recuperación y ejecutar la
evaluación end-to-end de la variante ganadora.

## Prerrequisitos

- Ollama con `nomic-embed-text` y, para la matriz, `bge-m3`:
  ```bash
  ollama list
  ollama pull bge-m3        # ~1.2 GB, solo la primera vez
  ```
- Corpus gold en `CORPUS_GOLD_DIR` (el mismo de la app).
- Clave de DeepSeek para el modo `e2e` (opcional en `retrieval`).
- App en `main` y entorno sincronizado (`uv sync`).

## 1. Generar el ground truth propuesto

```bash
uv run python scripts/propose_ground_truth.py \
  --questions ../carvajal/data/questions.json \
  --output specs/002-evaluacion-recuperacion/evaluation/questions.candidate.json \
  --review specs/002-evaluacion-recuperacion/evaluation/review.md \
  --limit 3
```

Resultado esperado: `questions.candidate.json` y `review.md` con 3 filas. Repetir sin
`--limit` para las 30.

## 2. Revisar y congelar

1. Abrir `evaluation/review.md` y corregir `decisión` y `cambios` por pregunta.
2. Editar `questions.candidate.json`: fijar `expected_slugs`, `expected_status`,
   `key_facts`, y completar `reviewed_by` y `reviewed_at`.
3. Guardar como `evaluation/questions.json` y validar:
   ```bash
   uv run python scripts/run_evaluation.py \
     --set specs/002-evaluacion-recuperacion/evaluation/questions.json \
     --validate-only
   ```
4. Commit del set congelado (y de `review.md`) antes de correr reportes.

## 3. Matriz de recuperación (sin LLM)

```bash
uv run python scripts/run_evaluation.py \
  --mode retrieval --variants all --recreate \
  --json-out specs/002-evaluacion-recuperacion/reports/baseline.json \
  --markdown-out specs/002-evaluacion-recuperacion/reports/baseline.md
```

Resultado esperado: 8 variantes indexadas en `.qdrant-eval/`, tabla con `recall@1/3/5/10`,
MRR y latencias; `winner` declarada por `recall@5` (desempate MRR).

## 4. End-to-end de la ganadora

```bash
uv run python scripts/run_evaluation.py \
  --mode e2e --variants <id-ganadora> \
  --json-out specs/002-evaluacion-recuperacion/reports/ganadora.json \
  --markdown-out specs/002-evaluacion-recuperacion/reports/ganadora.md
```

Resultado esperado: umbrales `recall@5 ≥ 0.95`, `citation_precision == 1.0`,
`abstention_accuracy ≥ 0.90`; exit code `0` si se cumplen.

## 5. Decidir y registrar

- Si `bge-m3` gana por **≥5 pp** en `recall@5`: aplicar el protocolo de `research.md` R9
  (constitución §3/§9 + proyección, `EMBEDDING_DIM=1024`, reconstruir índice de la app) y
  escribir el ADR.
- Si no: ADR con “mantener `nomic`” y evidencia del reporte.

## Evidencia de la fase (2026-11-20)

- Set congelado: **30 preguntas + 3 controles de abstención** (33), revisado en sesión
  asistida; fingerprint `9952ecc5…`.
- Matriz de 8 variantes: ganadora **`bge-m3-500-hybrid`** con `hit@5 = 0,966`
  (`nomic` mejor: 0,862 → **+10,3 pp**); `recall@5` secundario 0,764.
- E2E de la ganadora: citas **1,0**, abstención **1,0**, cobertura esperada 0,962,
  latencia p50 1,57 s / p95 2,37 s; **umbrales cumplidos**.
- Decisión: migrar a `bge-m3` (ADR 0001); `EMBEDDING_DIM=1024` y reconstrucción del
  índice de la app.
- Reportes versionados: `reports/baseline.json/md` y `reports/ganadora.json/md`.

## Problemas frecuentes

- **`model "bge-m3" not found`**: `ollama pull bge-m3`.
- **Dimensión incompatible** (`768` vs `1024`): recrear la colección con `--recreate` o
  borrar `.qdrant-eval/`.
- **Set desactualizado**: el reporte falla si el fingerprint no coincide; regenerar el set
  o usar `--allow-stale-set` solo para diagnóstico.
- **Índice bloqueado**: la evaluación usa `.qdrant-eval/`, distinto del `.qdrant/` de la
  app; si persiste, revisar que `EVAL_QDRANT_PATH` no apunte al índice de la app.
- **`e2e` sin clave**: `LLM_PROVIDER=ollama` para operar sin DeepSeek (más lento).
