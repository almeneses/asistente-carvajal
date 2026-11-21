---
description: "Task list for the accessible chat experience"
---

# Tasks: Experiencia de chat con identidad Carvajal

**Input**: Design documents from `/specs/004-experiencia-chat/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/chat-stream.md, contracts/feedback-api.md, quickstart.md

**Tests**: Incluidos por política del proyecto (`make check` y CI exigen `pytest`). Las
pruebas no dependen de navegador ni red.

**Organization**: Tareas agrupadas por historia de usuario (US1–US5).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (archivos distintos, sin dependencias)
- **[Story]**: US1..US5, solo en fases de historia
- Rutas de archivo exactas

## Path Conventions

Proyecto único (ver `plan.md`): `assistant/ui/`, `assistant/templates/`,
`assistant/static/`, `tests/` y artefactos en `specs/004-experiencia-chat/`.

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Añadir `FEEDBACK_LOG_PATH` a `.env.example` y usar `.cache/feedback.jsonl` por defecto (`data-model.md` `Configuración añadida.FEEDBACK_LOG_PATH`)
- [X] T002 Instalar con `uv add markdown-it-py mdit-py-plugins` y actualizar `uv.lock`
- [X] T003 [P] Vendorizar DM Sans variable woff2 y su licencia OFL en `assistant/static/fonts/`
- [X] T004 [P] Crear `assistant/ui/__init__.py` y la estructura de pruebas `tests/test_ui_*.py`
- [X] T005 [P] Añadir objetivo `make ui-check` (pruebas de UI) en `Makefile`

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: sin esta fase no se implementa ninguna historia

- [X] T006 Implementar `assistant/ui/tokens.py` con los tokens de `docs/design/DESIGN.md` (`DesignTokens.primary`, `.secondary`, `.tertiary`, `.ink`, `.background`, `.surface`, `.border`, `.radii`, `.spacing`) y la fórmula de contraste WCAG
- [X] T007 Implementar `assistant/ui/markdown.py` (MarkdownIt GFM, `html=False`, `.render_safe()` con enlaces `target="_blank"` y `rel="noopener noreferrer"`) según `research.md` R3
- [X] T008 Implementar `assistant/ui/feedback.py` (validación y append JSONL, last-wins por `message_id`) según `data-model.md` `FeedbackEntry`
- [X] T009 Implementar `assistant/ui/streaming.py` (codificación SSE `event:`/`data:`, heartbeat y `StreamEvent` de `data-model.md` `StreamEvent`)
- [X] T010 Implementar el estado de conversación del cliente en `assistant/static/chat.js` (`ChatMessage.message_id`, `.status`, `.provider`, `.feedback`) según `data-model.md` `ChatMessage`
- [X] T011 Extender `assistant/llm.py` con `stream()` en DeepSeek, Ollama y `FallbackLLM` (`research.md` R2)
- [X] T012 Implementar `RagService.answer_stream()` en `assistant/rag.py` reutilizando recuperación y citas
- [X] T013 Implementar los fixtures de streaming en `tests/streaming_fixtures.py` (LLM falso, eventos, HTML esperado)
- [X] T014 [P] Pruebas de tokens y contraste en `tests/test_ui_tokens.py` (AA ≥4.5:1; objetivo AAA ≥7:1)
- [X] T015 [P] Pruebas de Markdown/XSS en `tests/test_ui_markdown.py` (HTML crudo, `javascript:`, enlaces seguros)

**Checkpoint**: base de tokens, Markdown, SSE, feedback y streaming de LLM probada

---

## Phase 3: User Story 1 - Respuesta progresiva por SSE (Priority: P1) 🎯 MVP

**Goal**: la respuesta aparece token a token con estados visibles

**Independent Test**: `POST /ask/stream` emite `start`, `token` y `done`; el navegador
muestra texto mientras llega

### Tests for User Story 1

- [X] T016 [P] [US1] Prueba del endpoint SSE en `tests/test_ui_streaming.py` (orden de eventos, `done` único, heartbeat)
- [X] T017 [P] [US1] Prueba de pregunta inválida (422 antes del stream) y error a mitad de stream

### Implementation for User Story 1

- [X] T018 [US1] Implementar `POST /ask/stream` en `assistant/web.py` con `StreamingResponse` y cancelación al desconectar
- [X] T019 [US1] Implementar el parser SSE y el render incremental en `assistant/static/chat.js` (`fetch` + `ReadableStream`; tokens con `textContent`)
- [X] T020 [US1] Implementar los estados `retrieving`/`generating` visibles en `assistant/templates/index.html`
- [X] T021 [US1] Implementar el evento `error` con `retryable` y `request_id` en servidor y cliente
- [X] T022 [US1] Conservar `POST /ask` síncrono como fallback y mantener sus pruebas verdes

**Checkpoint**: streaming funcional y con fallback; tests de fases 1–3 verdes

---

## Phase 4: User Story 2 - Formato legible y fuentes (Priority: P1)

**Goal**: Markdown seguro, secciones de catálogo/corpus separadas y citas legibles

**Independent Test**: una respuesta con listas/tablas se ve formateada y no ejecuta HTML

### Tests for User Story 2

- [X] T023 [P] [US2] Prueba de `final_html` en el evento `done` y de que los `token` son texto plano
- [X] T024 [P] [US2] Prueba de render de secciones mixtas y fuentes en `tests/test_ui_web.py`

### Implementation for User Story 2

- [X] T025 [US2] Enviar `final_html` renderizado de forma segura en el evento `done` (`assistant/web.py` + `markdown.py`)
- [X] T026 [US2] Renderizar las fuentes como HTML seguro en el evento `sources` y en el parcial `_exchange.html`
- [X] T027 [US2] Actualizar `_catalog_exchange.html` a las tarjetas del sistema visual (precio/vigencia/fuente)
- [X] T028 [US2] Reemplazar el texto plano por `final_html` al terminar el stream en `chat.js`

**Checkpoint**: Markdown seguro y secciones separadas en la UI

---

## Phase 5: User Story 3 - Control y recuperación (Priority: P2)

**Goal**: reiniciar, reintentar, copiar y atajos de teclado

**Independent Test**: error → reintentar conserva la pregunta; reiniciar deja la
conversación vacía; copiar confirma

### Tests for User Story 3

- [X] T029 [P] [US3] Pruebas de los controles en `tests/test_ui_web.py` (estructura de botones y `data-question`)
- [X] T030 [P] [US3] Prueba unitaria del helper de reintento/copia en `tests/test_ui_streaming.py`

### Implementation for User Story 3

- [X] T031 [US3] Implementar “Nueva conversación” con `AbortController` y foco en el campo
- [X] T032 [US3] Implementar “Reintentar” con la pregunta guardada en `data-question`
- [X] T033 [US3] Implementar “Copiar” con `navigator.clipboard` y confirmación; Enter/Shift+Enter

**Checkpoint**: controles operativos sin recargar

---

## Phase 6: User Story 4 - Feedback (Priority: P3)

**Goal**: rating útil/no útil con comentario, persistido sin PII

**Independent Test**: valorar una respuesta escribe una línea JSON sin datos personales

### Tests for User Story 4

- [X] T034 [P] [US4] Prueba del endpoint y validaciones en `tests/test_ui_feedback.py` (422, comentario largo)
- [X] T035 [P] [US4] Prueba de append/last-wins y ausencia de PII en el archivo

### Implementation for User Story 4

- [X] T036 [US4] Implementar `POST /feedback` en `assistant/web.py` y conectar `feedback.py`
- [X] T037 [US4] Implementar los botones y el comentario en `_exchange.html` y `chat.js`
- [X] T038 [US4] Mostrar confirmación y bloquear doble envío; revertir si falla

**Checkpoint**: feedback registrado y visible

---

## Phase 7: User Story 5 - Identidad y accesibilidad (Priority: P2)

**Goal**: aplicar el sistema visual de Stitch y WCAG AA/AAA

**Independent Test**: la página se ve Carvajal, responde a 360 px y pasa axe/contraste

### Tests for User Story 5

- [X] T039 [P] [US5] Prueba de estructura accesible en `tests/test_ui_web.py` (landmarks, `aria-live`, labels, foco)
- [X] T040 [P] [US5] Prueba de contraste de los pares de tokens en `tests/test_ui_tokens.py`

### Implementation for User Story 5

- [X] T041 [US5] Crear `assistant/static/theme.css` con variables, tipografía, tarjetas, botones, inputs y estados desde `DESIGN.md`
- [X] T042 [US5] Rediseñar `index.html` (cabecera con logo, chat, footer de accesibilidad) y `_exchange.html` (burbujas Carva/usuario + acciones)
- [X] T043 [US5] Cargar DM Sans vendorizada, logo y `prefers-color-scheme`/`prefers-reduced-motion`
- [X] T044 [US5] Aplicar foco visible, targets ≥64 px, `aria-live="polite"` y navegación por teclado; verificar 360/768/1280 px

**Checkpoint**: identidad aplicada y accesibilidad verificada

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T045 [P] Actualizar `README.md` (nueva UI, feedback y variables) y `CONSTITUTION.md` §9 si aplica
- [X] T046 Ejecutar `make check` y `make ui-check`; corregir hasta verde
- [X] T047 Ejecutar la validación de `quickstart.md` (streaming, catálogo, feedback, teclado, móvil) y registrar evidencia
- [X] T048 Actualizar `specs/README.md` (✅) y abrir PR con CI `Calidad` en verde

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup**: sin dependencias
- **Foundational**: depende de Setup y bloquea las historias
- **US1 y US2**: dependen de Foundational; US2 puede ir tras US1
- **US3 y US4**: dependen de US1 (DOM y `message_id`)
- **US5**: depende de US2 (plantillas) y puede solaparse con US3/US4
- **Polish**: depende de todas

### Within Each User Story

- Pruebas primero, deben fallar antes de implementar
- Tokens/Markdown/SSE antes de plantillas y JS
- Cada historia termina con su checkpoint validado

### Parallel Opportunities

- T003–T005, T014–T015, T016–T017, T023–T024, T029–T030, T034–T035, T039–T040 en paralelo
- US3 y US4 comparten `chat.js`: coordinar antes de paralelizar

---

## Parallel Example: User Story 1

```bash
Task: "Prueba del endpoint SSE en tests/test_ui_streaming.py"
Task: "Prueba de pregunta inválida en tests/test_ui_streaming.py"
Task: "Prueba de tokens y contraste en tests/test_ui_tokens.py"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Setup + Foundational
2. US1: streaming SSE con estados
3. **PARAR y VALIDAR** con el navegador

### Incremental Delivery

1. US1 → streaming
2. US2 → Markdown y fuentes
3. US5 → identidad y accesibilidad
4. US3 → controles
5. US4 → feedback
6. Polish → docs, evidencia y PR

---

## Notes

- [P] = archivos distintos sin dependencia
- Cada restricción cita `data-model.md` y el campo exacto
- El diseño de referencia está en `docs/design/DESIGN.md`; voz/avatar/cotización quedan fuera
- No romper `/ask` síncrono ni las suites de fases 1–3
