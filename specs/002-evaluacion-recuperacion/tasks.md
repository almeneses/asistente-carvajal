---
description: "Task list for the retrieval evaluation harness"
---

# Tasks: Evaluación de recuperación y métricas de calidad

**Input**: Design documents from `/specs/002-evaluacion-recuperacion/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/evaluation-cli.md, quickstart.md

**Tests**: Incluidos por política del proyecto (`make check` y CI exigen `pytest`). Las
pruebas usan fixtures y no dependen de red ni servicios.

**Organization**: Tareas agrupadas por historia de usuario (US1–US4).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (archivos distintos, sin dependencias)
- **[Story]**: US1..US4, solo en fases de historia
- Rutas de archivo exactas

## Path Conventions

Proyecto único (ver `plan.md`): `assistant/evaluation/`, `scripts/`, `tests/` y artefactos
en `specs/002-evaluacion-recuperacion/`.

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Añadir `EMBEDDING_DIM` y `EVAL_QDRANT_PATH` a `.env.example`; ignorar `.qdrant-eval/` y `specs/002-evaluacion-recuperacion/reports/*.tmp.json` en `.gitignore` (`data-model.md` `Configuración de la app afectada.EMBEDDING_DIM`, `.EVAL_QDRANT_PATH`)
- [ ] T002 [P] Crear `assistant/evaluation/__init__.py`, `specs/002-evaluacion-recuperacion/evaluation/` y `specs/002-evaluacion-recuperacion/reports/`
- [ ] T003 Añadir `embedding_dim` a `assistant/config.py` (defecto 768, rango 1..4096) y usarlo en `assistant/embeddings.py` y `assistant/index.py` (`data-model.md` `VariantConfig.embedding_dim`)
- [ ] T004 [P] Añadir objetivos `gt-propose`, `eval` y `eval-e2e` en `Makefile`

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: sin esta fase no se ejecuta ninguna historia

- [ ] T005 Implementar el fingerprint en `assistant/evaluation/fingerprint.py` (`data-model.md` `Fingerprint.corpus_fingerprint`, `.index_jsonl_sha256`)
- [ ] T006 [P] Implementar métricas puras en `assistant/evaluation/metrics.py` (`data-model.md` `Metrics.recall_at_1/3/5/10`, `.mrr`, `.citation_precision`, `.expected_citation_coverage`, `.abstention_accuracy`, `.false_abstention_rate`, `.latency_p50_ms`, `.latency_p95_ms`, `.questions_evaluated`)
- [ ] T007 [P] Implementar la matriz de variantes en `assistant/evaluation/variants.py` (`data-model.md` `VariantConfig.id`, `.embedding_model`, `.chunk_size`, `.overlap`, `.cosine_weight`, `.lexical_weight`, `.collection`, `.min_score`)
- [ ] T008 Implementar carga y validación del set en `assistant/evaluation/dataset.py` (`data-model.md` `EvaluationSet.version`, `.corpus_fingerprint`, `.reviewed_by`, `.reviewed_at`, `.questions`; `EvaluationQuestion.id`, `.question`, `.expected_slugs`, `.expected_status`, `.key_facts`, `.notes`)
- [ ] T009 Implementar serialización de reportes en `assistant/evaluation/reports.py` (`data-model.md` `RunReport.schema_version`, `.generated_at`, `.mode`, `.corpus_fingerprint`, `.index_jsonl_sha256`, `.indexed_fragments`, `.provider`, `.variants`, `.winner`; `VariantReport.config`, `.metrics`, `.rows`)
- [ ] T010 Implementar el runner de recuperación en `assistant/evaluation/runner.py` (construye colecciones por variante en `EVAL_QDRANT_PATH`, busca y arma filas; FR-009, no toca el índice de la app)
- [ ] T011 Crear fixtures de evaluación en `tests/eval_fixtures.py` (set sintético de 3 preguntas, corpus de 2 documentos y dobles de embedder/LLM)
- [ ] T012 [P] Pruebas de fingerprint, dataset y métricas en `tests/test_eval_fingerprint.py`, `tests/test_eval_dataset.py` y `tests/test_eval_metrics.py`

**Checkpoint**: métricas y validaciones probadas; runner listo para historias

---

## Phase 3: User Story 1 - Ejecutar la evaluación y leer un reporte (Priority: P1) 🎯 MVP

**Goal**: reporte por pregunta con evidencia esperada/recuperada y agregados

**Independent Test**: correr `--mode retrieval --validate-only` y luego la evaluación sobre el set sintético; totales cuadran con filas

### Tests for User Story 1

- [ ] T013 [P] [US1] Prueba de validación del set en `tests/test_eval_dataset.py` (campo faltante, id duplicado, slug inexistente, estado inválido)
- [ ] T014 [P] [US1] Prueba de filas de recuperación en `tests/test_eval_runner.py` (`data-model.md` `QuestionRow.id`, `.retrieved_slugs`, `.rank_first_expected`, `.latency_ms`)

### Implementation for User Story 1

- [ ] T015 [US1] Implementar `--validate-only` y los errores accionables del set en `scripts/run_evaluation.py`
- [ ] T016 [US1] Implementar `QuestionRow` y agregados de recuperación en `assistant/evaluation/runner.py` (FR-002, FR-003)
- [ ] T017 [US1] Implementar el reporte Markdown en `assistant/evaluation/reports.py` y conectarlo al CLI (FR-006)
- [ ] T018 [US1] Implementar `scripts/propose_ground_truth.py` (propuesta LLM + `evaluation/review.md`, `--limit`) según `contracts/evaluation-cli.md`
- [ ] T019 [P] [US1] Prueba de la propuesta de ground truth en `tests/test_eval_propose.py` (esquema de salida y prompt con LLM falso)

**Checkpoint**: set validable y reporte legible por pregunta

---

## Phase 4: User Story 2 - Comparar configuraciones (Priority: P2)

**Goal**: 8 variantes comparadas en una corrida, con ganadora declarada

**Independent Test**: ejecutar `--mode retrieval --variants all` sobre fixtures y ver 8 filas comparables

### Tests for User Story 2

- [ ] T020 [P] [US2] Prueba de la matriz en `tests/test_eval_variants.py` (8 ids únicos, dims coherentes, colecciones únicas)
- [ ] T021 [P] [US2] Prueba de comparación y desempate en `tests/test_eval_metrics.py` (`data-model.md` `RunReport.winner`)

### Implementation for User Story 2

- [ ] T022 [US2] Implementar indexación por variante con colecciones compartidas por (modelo, fragmentación) y `--recreate` en `assistant/evaluation/runner.py`
- [ ] T023 [US2] Implementar comparación, ganadora por `recall_at_5` y desempate por MRR en `assistant/evaluation/runner.py` (SC-005)
- [ ] T024 [US2] Conectar `--variants`, `--mode retrieval` y `--limit` en `scripts/run_evaluation.py` (FR-013, separación retrieval/e2e)
- [ ] T025 [US2] Implementar progreso por variante, variantes omitidas con causa y exit codes de `contracts/evaluation-cli.md`

**Checkpoint**: matriz completa ejecutable y comparable

---

## Phase 5: User Story 3 - Decidir y registrar (Priority: P3)

**Goal**: e2e de la ganadora, umbrales y decisión registrada

**Independent Test**: ejecutar `--mode e2e --variants <id>` con LLM falso y verificar métricas y exit code

### Tests for User Story 3

- [ ] T026 [P] [US3] Prueba del modo e2e en `tests/test_eval_runner.py` (`data-model.md` `QuestionRow.status`, `.sources`, `.citations_valid`, `.error`; `Metrics.citation_precision`, `.expected_citation_coverage`, `.abstention_accuracy`, `.false_abstention_rate`)
- [ ] T027 [P] [US3] Prueba de umbrales y exit codes en `tests/test_eval_runner.py` (recall@5, citas, abstención)

### Implementation for User Story 3

- [ ] T028 [US3] Implementar `--mode e2e` sobre `RagService` y las métricas de respuesta en `assistant/evaluation/runner.py` (FR-004; `data-model.md` `QuestionRow.error`, `Metrics.questions_evaluated`)
- [ ] T029 [US3] Implementar la evaluación de umbrales y exit code 0/1 en `scripts/run_evaluation.py` (FR-007)
- [ ] T030 [US3] Crear el ADR `docs/adr/0001-embeddings-fase-2.md` con el protocolo de decisión de `research.md` R9 y el umbral de 5 pp (FR-010)
- [ ] T031 [US3] Implementar la verificación de migración condicionada en `assistant/evaluation/runner.py` (detecta si `bge-m3` supera el umbral y lo declara en el reporte)

**Checkpoint**: decisión soportada por evidencia y registrada

---

## Phase 6: User Story 4 - Reproducir y auditar (Priority: P4)

**Goal**: misma corrida, mismos números; fingerprint y revisión trazables

**Independent Test**: dos corridas con el mismo set y corpus dan métricas iguales; fingerprint distinto falla

### Tests for User Story 4

- [ ] T032 [P] [US4] Prueba de fingerprint desactualizado y `--allow-stale-set` en `tests/test_eval_fingerprint.py`
- [ ] T033 [P] [US4] Prueba de determinismo (orden estable de filas/variantes y JSON reproducible) en `tests/test_eval_runner.py`

### Implementation for User Story 4

- [ ] T034 [US4] Ordenar filas y variantes de forma determinista y excluir latencias de la comparación en `assistant/evaluation/reports.py` (SC-006)
- [ ] T035 [US4] Versionar el set congelado en `specs/002-evaluacion-recuperacion/evaluation/questions.json` y `review.md` tras la revisión humana (FR-012)
- [ ] T036 [US4] Versionar `reports/baseline.json/md` y `reports/ganadora.json/md` con fecha y fingerprint (FR-006)

**Checkpoint**: evaluación auditable y repetible

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T037 [P] Añadir `EMBEDDING_DIM`/`EVAL_QDRANT_PATH` a `README.md` y `quickstart.md`; documentar `make eval`
- [ ] T038 Ejecutar `make check` y corregir lint, tipos y pruebas hasta verde
- [ ] T039 Ejecutar la matriz real y el e2e de la ganadora; registrar resultados en `reports/` y `quickstart.md` (SC-001..SC-006)
- [ ] T040 Actualizar `specs/README.md` (✅) y abrir PR con CI `Calidad` en verde
- [ ] T041 [P] Si la migración cumple el umbral: actualizar `CONSTITUTION.md` §3/§9 y proyección, cambiar el defecto de `EMBEDDING_DIM` y reconstruir el índice de la app (condicional a T031; si no aplica, se omite con nota en el ADR)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Fase 1)**: sin dependencias
- **Foundational (Fase 2)**: depende de Setup y bloquea todas las historias
- **US1 (Fase 3)**: depende de Foundational
- **US2 (Fase 4)**: depende de US1 (runner y filas)
- **US3 (Fase 5)**: depende de US1; puede avanzar en paralelo con US2 para las pruebas
- **US4 (Fase 6)**: depende de US1–US3
- **Polish (Fase 7)**: depende de todas

### Within Each User Story

- Pruebas primero (deben fallar antes de implementar)
- Dataset/fingerprint antes de runner; métricas antes de reportes
- Cada historia termina con su checkpoint validado

### Parallel Opportunities

- T002, T004, T006, T007, T012 en paralelo
- T013–T014, T019 en paralelo; T020–T021 en paralelo; T026–T027 en paralelo; T032–T033 en paralelo
- US2 y US3 comparten `runner.py`: coordinar archivos antes de paralelizar

---

## Parallel Example: User Story 1

```bash
Task: "Prueba de validación del set en tests/test_eval_dataset.py"
Task: "Prueba de filas de recuperación en tests/test_eval_runner.py"
Task: "Prueba de la propuesta de ground truth en tests/test_eval_propose.py"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Fase 1 + Fase 2
2. US1: set validable + reporte por pregunta
3. **PARAR y VALIDAR** con el set sintético

### Incremental Delivery

1. US1 → reporte base
2. US2 → matriz comparativa
3. US3 → e2e y decisión
4. US4 → reproducibilidad
5. Polish → `make check`, reportes reales y PR

---

## Notes

- [P] = archivos distintos sin dependencia
- Cada restricción cita `data-model.md` y el campo exacto
- No implementar migración a `bge-m3` antes de que T031 la justifique
- Los reportes reales se versionan solo al cerrar la fase
