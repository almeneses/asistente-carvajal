---
description: "Task list for the corpus-cited vertical slice"
---

# Tasks: Corte vertical del asistente con citas del corpus

**Input**: Design documents from `/specs/001-corte-vertical-citas/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/http-api.md, quickstart.md

**Tests**: Incluidos por política del proyecto (`make check` y CI exigen `pytest`; ver
`CONSTITUTION.md`). Las pruebas unitarias usan dobles de prueba y no dependen de red.

**Organization**: Tareas agrupadas por historia de usuario para implementación y prueba
independientes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (archivos distintos, sin dependencia de tareas incompletas)
- **[Story]**: US1..US4, solo en fases de historia de usuario
- Rutas de archivo exactas en cada tarea

## Path Conventions

Proyecto único de aplicación (ver `plan.md`): `main.py`, `assistant/`, `scripts/`, `tests/`
en la raíz del repositorio.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: dependencias, estructura y recursos compartidos

- [X] T001 Añadir dependencias de runtime con `uv add fastapi uvicorn jinja2 httpx qdrant-client` y actualizar `pyproject.toml` (`[tool.ruff] src = ["assistant", "tests", "scripts"]`)
- [X] T002 [P] Crear la estructura `assistant/` (con `__init__.py`), `assistant/templates/`, `assistant/static/`, `scripts/` y `tests/`
- [X] T003 [P] Crear `.env.example` con las variables de `data-model.md` `Configuración` (sin valores reales) y añadir `.qdrant/`, `.env` a `.gitignore` (FR-011)
- [X] T004 [P] Vendorizar HTMX en `assistant/static/htmx.min.js` (descarga única, sin CDN en runtime)
- [X] T005 [P] Añadir objetivos `make run`, `make index` y `make acceptance` en `Makefile`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: núcleo compartido por todas las historias; ninguna historia comienza antes

**⚠️ CRITICAL**: sin esta fase no se puede implementar ninguna historia

- [X] T006 Implementar la carga y validación de configuración en `assistant/config.py` según `data-model.md` `Configuración` (fallo con variable/ruta exacta; sin registrar secretos; FR-007, FR-008)
- [X] T007 Implementar la carga del corpus en `assistant/corpus.py` en modo solo lectura (sin escrituras en el directorio) con validación de `data-model.md` `Documento del corpus` (`Documento.slug`, `Documento.url`, `Documento.title`, `Documento.section`, `Documento.source_type`, `Documento.captured_at`, `Documento.hash`, `Documento.chars`, `Documento.body`) contra `index.jsonl` (FR-009)
- [X] T008 [P] Implementar la fragmentación 1000/200 en `assistant/chunking.py` según `data-model.md` `Fragmento` (`Fragmento.slug`, `Fragmento.url`, `Fragmento.title`, `Fragmento.source_type`, `Fragmento.section`, `Fragmento.chunk_index`, `Fragmento.text` 1..1000, `Fragmento.char_start`)
- [X] T009 [P] Implementar el embedder Ollama en `assistant/embeddings.py` (`/api/embed`, 768 dims, lote)
- [X] T010 Implementar el índice Qdrant en `assistant/index.py` (crear colección, upsert idempotente, búsqueda coseno) según el esquema de `data-model.md` `Esquema del índice Qdrant` (`slug`, `url`, `title`, `source_type`, `section`, `chunk_index`, `text`, `char_start`, `doc_hash`; 768 dims, coseno)
- [X] T011 Implementar los adaptadores LLM en `assistant/llm.py` (DeepSeek `/chat/completions`, Ollama `/api/chat`, timeouts y fallback de `research.md` R4)
- [X] T012 Implementar el prompt de sistema/usuario y el formato `[n]` en `assistant/prompting.py` (contexto delimitado como datos, prohibido conocimiento externo; FR-002, FR-012)
- [X] T013 Implementar la cadena RAG en `assistant/rag.py` con los protocolos de `data-model.md` `Protocolos internos` (`Embedder.embed`, `Retriever.search`, `LLM.generate`; recuperar → generar → citar/abstenerse; FR-002)
- [X] T014 Implementar la app FastAPI en `assistant/web.py` (`GET /`, `POST /ask`, `GET /healthz`) y el entrypoint `main.py` (Uvicorn), con página y parcial HTMX en `assistant/templates/`
- [X] T015 Implementar `scripts/index_corpus.py` (carga corpus, fragmenta, embebe e indexa; `--recreate`)
- [X] T016 Crear fixtures y dobles de prueba en `tests/conftest.py` (documentos sintéticos, `FakeEmbedder`, `FakeLLM`, `FakeRetriever`)

**Checkpoint**: app arrancable con configuración válida; índice construible

---

## Phase 3: User Story 1 - Preguntar y recibir una respuesta citada (Priority: P1) 🎯 MVP

**Goal**: pregunta en el chat → respuesta en español con fuentes válidas (título, tipo, enlace)

**Independent Test**: preguntar algo cubierto por el corpus y verificar que la respuesta cita un documento con metadatos coincidentes (FR-003, FR-015)

### Tests for User Story 1

- [X] T017 [P] [US1] Prueba del prompt y citas en `tests/test_prompting.py` (referencias `[n]`, fuentes desde metadatos, sin extractos)
- [X] T018 [P] [US1] Prueba de la cadena respondida en `tests/test_rag.py` (usa `FakeEmbedder`/`FakeLLM`; `status="answered"`, `sources` no vacía y válida)
- [X] T019 [P] [US1] Prueba del contrato web en `tests/test_web.py` (`GET /` 200 con formulario, `POST /ask` 200 parcial con `data-status="answered"` y enlaces)

### Implementation for User Story 1

- [X] T020 [US1] Construir las fuentes citadas desde los fragmentos recuperados en `assistant/rag.py` (FR-003, FR-015; `data-model.md` `Cita.title`, `Cita.source_type`, `Cita.url`, `Cita.slug`)
- [X] T021 [US1] Renderizar la respuesta y las fuentes en `assistant/templates/index.html` y `assistant/templates/_exchange.html` (escapado de HTML)
- [X] T022 [US1] Conectar `POST /ask` al flujo respondido en `assistant/web.py` y mostrar el historial en el DOM con `hx-swap="beforeend"` (FR-001, FR-016; `data-model.md` `Pregunta.text` 1..2000, `Respuesta.text`, `Respuesta.request_id`)

**Checkpoint**: pregunta cubierta → respuesta citada visible en el navegador

---

## Phase 4: User Story 2 - No inventar cuando no hay evidencia (Priority: P2)

**Goal**: abstención explícita cuando no hay evidencia (FR-004, FR-005, FR-013; SC-002/SC-003)

**Independent Test**: preguntar por precios o temas fuera del corpus y verificar abstención sin cifras ni fuentes inventadas

### Tests for User Story 2

- [X] T023 [P] [US2] Prueba de abstención en `tests/test_rag.py` (sin fragmentos sobre umbral → `status="no_evidence"`, `sources=[]`)
- [X] T024 [P] [US2] Prueba del parcial de abstención en `tests/test_web.py` (`data-status="no_evidence"`, sin cifras)
- [X] T025 [P] [US2] Prueba de contradicción de fuentes en `tests/test_rag.py` (el prompt incluye ambas y la respuesta las menciona)

### Implementation for User Story 2

- [X] T026 [US2] Implementar la política de abstención y el umbral de relevancia en `assistant/rag.py` (FR-004; `data-model.md` `Respuesta.status`, `Respuesta.text`, `Respuesta.sources`, `Respuesta.provider`, `Respuesta.latency_ms`)
- [X] T027 [US2] Implementar la instrucción de contradicciones y de alcance (catálogo fuera) en `assistant/prompting.py` (FR-005, FR-013)
- [X] T028 [US2] Renderizar el parcial de abstención en `assistant/templates/_exchange.html`

**Checkpoint**: preguntas sin evidencia se rechazan de forma explícita

---

## Phase 5: User Story 3 - Configuración explícita y degradación (Priority: P3)

**Goal**: arranque con errores accionables y fallback de proveedor (FR-006..FR-008; SC-004, SC-006)

**Independent Test**: arrancar con variables/rutas inválidas y con el proveedor primario caído

### Tests for User Story 3

- [X] T029 [P] [US3] Pruebas de configuración en `tests/test_config.py` (variable faltante, ruta inexistente, mensaje con el nombre exacto)
- [X] T030 [P] [US3] Prueba de fallback en `tests/test_llm.py` (primario falla → respaldo responde; ambos fallan → error controlado)
- [X] T031 [P] [US3] Prueba de arranque en `tests/test_web.py` (`/healthz` 200 con corpus y colección; 503 cuando el índice no responde)

### Implementation for User Story 3

- [X] T032 [US3] Validar corpus, colección Qdrant y proveedor al arrancar en `assistant/web.py` (FR-008; `data-model.md` `Configuración.CORPUS_GOLD_DIR`, `Configuración.QDRANT_PATH`, `Configuración.QDRANT_URL`, `Configuración.LLM_PROVIDER`)
- [X] T033 [US3] Implementar la degradación y el error accionable en `assistant/llm.py` y `assistant/rag.py` (FR-006; `data-model.md` `Respuesta.status`, `Respuesta.provider`, `Respuesta.latency_ms`, `Respuesta.request_id`)
- [X] T034 [US3] Implementar `GET /healthz` y la traza `request_id` en `assistant/web.py` según `contracts/http-api.md` (FR-010; `data-model.md` `Pregunta.request_id`, `Respuesta.request_id`)

**Checkpoint**: configuración incorrecta falla temprano; proveedor caído no rompe la respuesta

---

## Phase 6: User Story 4 - Evaluar el corte con un set de preguntas (Priority: P4)

**Goal**: reporte de aceptación con 40 preguntas y validación de citas (FR-014; SC-001, SC-002, SC-007)

**Independent Test**: ejecutar el script sobre el corpus real y verificar 40 filas y `invalid_citations == 0`

### Tests for User Story 4

- [X] T035 [P] [US4] Prueba del reporte en `tests/test_acceptance.py` (esquema `data-model.md` `Reporte de aceptación.generated_at`, `.questions_total`, `.answered_with_valid_citation`, `.no_evidence`, `.invalid_citations`, `.rows`; exit codes 0/1/2)
- [X] T036 [P] [US4] Prueba de validación de citas en `tests/test_acceptance.py` (`Cita` válida solo con metadatos coincidentes)

### Implementation for User Story 4

- [X] T037 [US4] Implementar `scripts/run_acceptance.py` (entrada JSON, cadena en proceso, reporte JSON + resumen, exit codes de `contracts/http-api.md`; `data-model.md` `Row.question`, `.status`, `.provider`, `.latency_ms`, `.sources`, `.citations_valid`, `.expected_out_of_scope`)
- [X] T038 [US4] Implementar la validación de citas contra metadatos del corpus en `scripts/run_acceptance.py` (FR-015)
- [X] T039 [US4] Documentar el uso en `quickstart.md` y `README.md` (sección de aceptación)

**Checkpoint**: aceptación ejecutable y reproducible

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: calidad, documentación y cierre

- [X] T040 [P] Añadir `.qdrant/` y artefactos de reporte a `.gitignore` y revisar `.env.example`
- [X] T041 [P] Actualizar `README.md` (estado del corte, comandos nuevos) y `CONSTITUTION.md` §9 si la implementación revela decisiones nuevas
- [X] T042 Ejecutar `make check` y corregir lint/tipos/pruebas hasta verde
- [ ] T043 Ejecutar la validación de `quickstart.md` con el corpus real y Ollama; registrar evidencia en `specs/001-corte-vertical-citas/quickstart.md` (SC-005, SC-006)
- [ ] T044 Actualizar `specs/README.md` (estado ✅) y abrir PR con CI `Calidad` en verde

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias
- **Foundational (Phase 2)**: depende de Setup y bloquea todas las historias
- **US1 (Phase 3)**: depende de Foundational
- **US2 (Phase 4)**: depende de Foundational y reutiliza la cadena de US1 (no puede ir en paralelo estricto)
- **US3 (Phase 5)**: depende de Foundational; sus pruebas pueden avanzar con dobles
- **US4 (Phase 6)**: depende de US1 (cadena respondida) y US2 (abstención)
- **Polish (Phase 7)**: depende de todas las historias

### Within Each User Story

- Pruebas primero, deben fallar antes de implementar
- Modelos/validaciones antes de servicios; servicios antes de rutas
- Cada historia termina con su checkpoint validado

### Parallel Opportunities

- T002–T005 y T008–T009 en paralelo
- T017–T019 en paralelo; T023–T025 en paralelo; T029–T031 en paralelo; T035–T036 en paralelo
- US1 y US3 pueden avanzar en paralelo tras Foundational si se respetan archivos distintos (US1 en `rag.py`/plantillas; US3 en `config.py`/`llm.py`/`healthz`)

---

## Parallel Example: User Story 1

```bash
# Pruebas de la historia
Task: "Prueba del prompt y citas en tests/test_prompting.py"
Task: "Prueba de la cadena respondida en tests/test_rag.py"
Task: "Prueba del contrato web en tests/test_web.py"

# Implementación
Task: "Construir fuentes citadas en assistant/rag.py"
Task: "Plantillas assistant/templates/index.html y _exchange.html"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Completar Fase 1 y Fase 2
2. Completar Fase 3 (US1)
3. **PARAR y VALIDAR**: pregunta cubierta → respuesta con cita válida
4. Demostrar con `quickstart.md`

### Incremental Delivery

1. Setup + Foundational → base lista
2. US1 → MVP con citas
3. US2 → abstención
4. US3 → operación robusta
5. US4 → aceptación medible
6. Polish → `make check`, documentación, PR

---

## Notes

- [P] = archivos distintos y sin dependencia de tareas incompletas
- Cada tarea cita la fuente canónica de sus restricciones (`data-model.md`, contratos)
- No duplicar restricciones ya definidas; la tarea solo añade lo específico
- Commit convencional por grupo lógico; no mezclar refactors ajenos
