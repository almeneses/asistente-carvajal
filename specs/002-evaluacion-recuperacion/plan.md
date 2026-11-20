# Implementation Plan: Evaluación de recuperación y métricas de calidad

**Branch**: `feat/002-evaluacion-recuperacion` | **Date**: 2026-11-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-evaluacion-recuperacion/spec.md`

## Summary

Construir un harness de evaluación reproducible que: (1) propone y registra el ground truth
de las 30 preguntas (evidencia esperada y estado sustentable/no sustentable) con revisión
humana; (2) mide la recuperación en modo *retrieval-only* (sin generación) para una matriz
de variantes —embeddings `nomic-embed-text` vs. `bge-m3`, fragmentación 1000/200 vs.
500/100 y pesos del híbrido—; (3) ejecuta end-to-end solo la variante ganadora para medir
citas, abstención y latencia; y (4) emite un reporte con fingerprint del corpus y registra
la decisión (mantener `nomic` o migrar a `bge-m3` si mejora ≥5 pp en `recall@5`).

El harness vive fuera de la ruta de la aplicación: no modifica corpus ni índice de la app,
usa un directorio Qdrant propio (`EVAL_QDRANT_PATH`, por defecto `.qdrant-eval`) y solo
depende de las dependencias existentes (`httpx`, `qdrant-client`).

## Technical Context

**Language/Version**: Python 3.13 (gestionado con `uv`)

**Primary Dependencies**: sin dependencias nuevas; se reutilizan `httpx` (Ollama/DeepSeek),
`qdrant-client` y la librería estándar (estadística y percentiles).

**Storage**: colecciones Qdrant por variante (`eval_<variante>`) en `EVAL_QDRANT_PATH`
(embebido) o en `QDRANT_URL`; corpus gold en solo lectura; reportes versionados en
`specs/002-evaluacion-recuperacion/reports/` y reportes ad-hoc en `.cache/`.

**Testing**: `pytest` con fixtures sintéticas, sin red ni servicios; CI ejecuta solo esas
pruebas. La evaluación real es una ejecución manual documentada en `quickstart.md`.

**Target Platform**: Linux/macOS de desarrollo; ejecución local de una instancia.

**Project Type**: aplicación web existente + scripts de evaluación; `main.py` sigue siendo
el entrypoint de la app.

**Performance Goals**: la matriz de recuperación (8 variantes × 30 preguntas) se ejecuta en
una sola corrida; el end-to-end de la ganadora tarda menos de 3 minutos con DeepSeek.

**Constraints**: corpus y app de solo lectura; el modo retrieval no invoca LLM; las
métricas agregadas son deterministas salvo latencia; cambiar la dimensión del embedding
exige recrear el índice; la migración a `bge-m3` está condicionada a ≥5 pp de mejora.

**Scale/Scope**: 30 preguntas, 24 documentos, 123 fragmentos, 8 variantes, 1 ganadora.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio / restricción | Verificación en el plan | Estado |
|---|---|---|
| I. La constitución manda | El plan no contradice la constitución; una migración a `bge-m3` solo ocurre si se cumple el umbral y se enmienda §3/§9 en el mismo commit. | ✅ |
| II. Sin fuentes no hay respuesta | El ground truth incluye evidencia esperada; la evaluación mide citas y abstención; el reporte conserva slugs y enlaces. | ✅ |
| III. El corpus es el contrato | La evaluación abre el corpus en solo lectura y usa un Qdrant separado; no toca el índice de la app. | ✅ |
| IV. Recuperación separada de la generación | El modo *retrieval-only* no usa LLM; el end-to-end se ejecuta solo para la ganadora. | ✅ |
| V. Cero secretos y cero datos personales | El ground truth usa preguntas y documentos públicos; sin claves en reportes ni fixtures. | ✅ |
| Python 3.13 + `uv`, modo aplicación | Sin paquete instalable; scripts ejecutables con `uv run python scripts/...`. | ✅ |
| FastAPI + HTMX, Qdrant, DeepSeek + Ollama | Se reutiliza el stack; no se añade infraestructura. | ✅ |
| Ruff, `ty`, pytest, pre-commit, CI, `make check` | Se añaden pruebas unitarias del harness y se amplía la cobertura de tipos; `make check` sigue siendo el gate. | ✅ |

**Nota condicional**: la única enmienda constitucional posible (cambio de `nomic-embed-text`
a `bge-m3` y de 768 a 1024 dims) queda bloqueada por el umbral de FR-010; si no se cumple,
no hay cambio de stack y la constitución permanece en 0.4.0.

## Project Structure

### Documentation (this feature)

```text
specs/002-evaluacion-recuperacion/
├── plan.md                  # Este archivo
├── research.md              # Fase 0: decisiones y alternativas
├── data-model.md            # Fase 1: entidades, ground truth y reporte
├── quickstart.md            # Fase 1: cómo anotar, ejecutar y comparar
├── contracts/
│   └── evaluation-cli.md    # Fase 1: CLI, JSON del reporte y exit codes
├── evaluation/
│   ├── questions.json       # Ground truth revisado (versionado)
│   └── review.md            # Registro de revisión humana
├── reports/                 # Baseline y comparación (versionados al cerrar)
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 (/speckit.tasks)
```

### Source Code (repository root)

```text
assistant/evaluation/
├── __init__.py
├── dataset.py               # Carga y valida el ground truth
├── fingerprint.py           # Fingerprint del corpus y comparabilidad
├── metrics.py               # recall@k, MRR, precisión, abstención, percentiles
├── variants.py              # Matriz de variantes y nombres de colección
├── ground_truth.py          # Propuesta asistida del ground truth
├── runner.py                # Indexa variantes, ejecuta retrieval/e2e y agrega
└── reports.py               # Serializa JSON y Markdown
scripts/
├── propose_ground_truth.py  # Propuesta asistida por LLM para revisión humana
├── run_evaluation.py        # Ejecuta variantes y escribe el reporte
└── index_corpus.py          # (existente) indexación de la app
tests/
├── test_eval_dataset.py
├── test_eval_fingerprint.py
├── test_eval_metrics.py
├── test_eval_runner.py
└── test_eval_variants.py
```

**Structure Decision**: se añade el subpaquete `assistant/evaluation/` (importable con
`pythonpath = ["."]`) y scripts en `scripts/`; la app no cambia de estructura salvo
`assistant/config.py` (dimensión configurable) y `assistant/index.py` (usar la dimensión de
configuración). El ground truth y los reportes viven en `specs/`, versionados.

## Phase 0: Research

Salida en [research.md](research.md): modelo `bge-m3` en Ollama, matriz de variantes,
modo retrieval vs. end-to-end, definición de métricas, fingerprint, colecciones por
variante y protocolo de migración condicionada.

## Phase 1: Design

Salidas: [data-model.md](data-model.md), [contracts/evaluation-cli.md](contracts/evaluation-cli.md)
y [quickstart.md](quickstart.md).

## Re-evaluación del Constitution Check (post-diseño)

| Principio / restricción | Verificación post-diseño | Estado |
|---|---|---|
| II. Sin fuentes no hay respuesta | El reporte conserva `expected_slugs`, `retrieved` y citas; la abstención se evalúa con estado esperado. | ✅ |
| III. Corpus de solo lectura | El runner abre el corpus con `load_corpus` y escribe solo en Qdrant/`reports/`. | ✅ |
| IV. Recuperación separada | `--mode retrieval` no construye LLM; `--mode e2e` es explícito. | ✅ |
| Dimensión configurable | `EMBEDDING_DIM` con defecto 768; la variante `bge-m3` usa 1024 y colección propia. | ✅ |
| CI sin servicios | Pruebas con fixtures y vectores sintéticos; sin red. | ✅ |

## Complexity Tracking

> No hay violaciones de la constitución. La complejidad adicional (matriz de variantes y
> ground truth revisado) está justificada por SC-002 y SC-005 y se limita al árbol de
> evaluación.
