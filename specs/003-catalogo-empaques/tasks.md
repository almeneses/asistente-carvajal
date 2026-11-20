---
description: "Task list for the packaging catalog branch"
---

# Tasks: Consulta del catálogo de empaques con precios y validación técnica

**Input**: Design documents from `/specs/003-catalogo-empaques/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/chat-catalog.md, contracts/acceptance-cli.md, quickstart.md

**Tests**: Incluidos por política del proyecto (`make check` y CI exigen `pytest`). Las
pruebas usan CSVs sintéticos y no dependen de red.

**Organization**: Tareas agrupadas por historia de usuario (US1–US4).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (archivos distintos, sin dependencias)
- **[Story]**: US1..US4, solo en fases de historia
- Rutas de archivo exactas

## Path Conventions

Proyecto único (ver `plan.md`): `assistant/catalog/`, `scripts/`, `tests/` y artefactos en
`specs/003-catalogo-empaques/`.

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Añadir `CATALOG_DIR`, `CATALOG_ROUTING_FILE` y `CATALOG_PRICE_TODAY` a `.env.example` e ignorar `specs/003-catalogo-empaques/reports/*.tmp.json` en `.gitignore` (`data-model.md` `Configuración añadida.CATALOG_DIR`, `.CATALOG_ROUTING_FILE`, `.CATALOG_PRICE_TODAY`)
- [ ] T002 [P] Crear `assistant/catalog/__init__.py`, `tests/catalog_fixtures.py` y `specs/003-catalogo-empaques/reports/`
- [ ] T003 Añadir `catalog_dir`, `catalog_routing_file` y `catalog_price_today` a `assistant/config.py` con validación accionable (`data-model.md` `Configuración añadida`)
- [ ] T004 [P] Añadir objetivo `catalog-acceptance` en `Makefile`

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: sin esta fase no se implementa ninguna historia

- [ ] T005 Implementar los modelos en `assistant/catalog/models.py` (`data-model.md` `CatalogSnapshot.catalog_dir`, `.fingerprint`, `.references_count`; `Reference.sku`, `.family`, `.uses`, `.capacity_oz`, `.material`, `.units_per_box`, `.country`, `.source_url`; `Price.sku`, `.amount`, `.currency`, `.tax_status`, `.valid_until`; `MaterialRule.material`, `.applications`, `.microwave`; `Distributor.name`, `.city`, `.address`, `.phone`, `.source_url`)
- [ ] T006 Implementar carga y validación en `assistant/catalog/loader.py` (cabeceras, SKUs únicos, precios huérfanos, país/moneda coherentes, fingerprint) según `data-model.md` `Snapshot del catálogo`
- [ ] T007 [P] Implementar validación de material en `assistant/catalog/materials.py` (`MaterialRule.applications`, `.microwave`, `.refrigeration`, `.freezing`, `.hot_content`, `.temp_min_c`, `.temp_max_c`)
- [ ] T008 [P] Implementar precios y cantidades en `assistant/catalog/money.py` (`PriceQuote.amount`, `.currency`, `.tax_status`, `.validity`, `.valid_until`, `.boxes`, `.total`, `.units_per_box`, `.warnings`)
- [ ] T009 Implementar router y extracción en `assistant/catalog/router.py` (`ExtractedQuery.intent`, `.family`, `.capacity_oz`, `.quantity`, `.city`, `.country`, `.use`, `.temperature`, `.material`, `.prefers_renewable`, `.asks_price`, `.asks_distributor`) según `research.md` R6/R7
- [ ] T010 Implementar búsqueda en `assistant/catalog/query.py` (filtro por familia/uso/material/capacidad/país, orden y límite de 5)
- [ ] T011 Implementar plantillas de respuesta en `assistant/catalog/answers.py` (`CatalogAnswer.intent`, `.sections`, `.catalog`, `.clarification`, `.citations`; `Recommendation.reference`, `.quote`, `.citations`, `.warnings`) según `contracts/chat-catalog.md`
- [ ] T012 Crear CSVs sintéticos y helpers en `tests/catalog_fixtures.py` (2 referencias MX/CO, 1 precio, 2 materiales, 1 distribuidor)
- [ ] T013 [P] Pruebas del loader en `tests/test_catalog_loader.py` (cabecera faltante, SKU duplicado, precio huérfano, fingerprint)
- [ ] T014 [P] Pruebas de materiales y dinero en `tests/test_catalog_materials.py` y `tests/test_catalog_money.py`
- [ ] T015 [P] Pruebas del router en `tests/test_catalog_router.py` (intenciones y atributos)
- [ ] T016 [P] Pruebas de búsqueda y plantillas en `tests/test_catalog_query.py` y `tests/test_catalog_answers.py`

**Checkpoint**: catálogo cargado y validado; router y plantillas probados

---

## Phase 3: User Story 1 - Referencias técnicamente válidas (Priority: P1) 🎯 MVP

**Goal**: recomendaciones que respetan material/temperatura y citan su ficha

**Independent Test**: pedir vasos para café caliente y comprobar que ninguna referencia es PET y que todas citan su ficha

### Tests for User Story 1

- [ ] T017 [P] [US1] Prueba de recomendación y materiales prohibidos en `tests/test_catalog_query.py` (FR-003, SC-003)
- [ ] T018 [P] [US1] Prueba de aclaración cuando falta uso/temperatura en `tests/test_catalog_answers.py` (US1 escenario 3)

### Implementation for User Story 1

- [ ] T019 [US1] Implementar `recommend()` en `assistant/catalog/query.py` con validación de material/temperatura y preferencia renovable (`recommendation` + `MaterialRule`)
- [ ] T020 [US1] Implementar la respuesta de recomendación en `assistant/catalog/answers.py` (SKU, material, presentación, ficha y captura)
- [ ] T021 [US1] Implementar la aclaración por atributos faltantes en `assistant/catalog/router.py` y `answers.py`

**Checkpoint**: recomendaciones válidas y citadas, con aclaración cuando falta información

---

## Phase 4: User Story 2 - Precio con vigencia y cantidad (Priority: P2)

**Goal**: precios correctos por país/moneda, con vigencia y cálculo de cajas/total

**Independent Test**: consultar un precio MX y uno CO con cantidad; verificar moneda, impuestos, vigencia y total

### Tests for User Story 2

- [ ] T022 [P] [US2] Prueba de resolución MX/CO en `tests/test_catalog_money.py` (FR-005, FR-015)
- [ ] T023 [P] [US2] Prueba de precio vencido, no declarado y ausente en `tests/test_catalog_money.py` (FR-006, FR-017, SC-005)
- [ ] T024 [P] [US2] Prueba de cajas y total en `tests/test_catalog_money.py` (FR-016, SC-009)

### Implementation for User Story 2

- [ ] T025 [US2] Implementar `price_quote()` en `assistant/catalog/money.py` con MX inline y CO desde `precios.csv`
- [ ] T026 [US2] Implementar `PriceQuote.validity` y los avisos de vencido/no declarado en la plantilla de `answers.py`
- [ ] T027 [US2] Implementar cajas/total y presentación usada cuando hay cantidad
- [ ] T028 [US2] Integrar precio y cantidad en la respuesta comercial (`CatalogSection`)

**Checkpoint**: precios y totales correctos, con vigencia y advertencias

---

## Phase 5: User Story 3 - Canal de compra (Priority: P3)

**Goal**: distribuidores por ciudad con contacto y fuente

**Independent Test**: preguntar por distribuidores en Medellín y verificar nombre, dirección, teléfono y fuente

### Tests for User Story 3

- [ ] T029 [P] [US3] Prueba de distribuidores y ciudad sin resultados en `tests/test_catalog_query.py` (FR-009)

### Implementation for User Story 3

- [ ] T030 [US3] Implementar `find_distributors()` en `assistant/catalog/query.py` por ciudad/país
- [ ] T031 [US3] Implementar la plantilla de distribuidores en `answers.py` sin afirmar inventario/entrega

**Checkpoint**: consultas de canal de compra resueltas con citas

---

## Phase 6: User Story 4 - Enrutamiento y preguntas mixtas (Priority: P4)

**Goal**: rutas correctas y composición catálogo→corpus sin regresión documental

**Independent Test**: enviar preguntas documentales, comerciales y mixtas y verificar ruta, secciones y citas

### Tests for User Story 4

- [ ] T032 [P] [US4] Prueba de rutas sobre el set de enrutamiento en `tests/test_catalog_router.py` (SC-004, FR-001)
- [ ] T033 [P] [US4] Prueba de pregunta mixta y no regresión documental en `tests/test_catalog_web.py` (FR-010, FR-013)

### Implementation for User Story 4

- [ ] T034 [US4] Integrar el catálogo en el contexto de `assistant/web.py` (carga al arrancar, `healthz.catalog`) y resolver la rama comercial
- [ ] T035 [US4] Implementar preguntas mixtas: catálogo primero; corpus solo si el catálogo no cubre la parte documental
- [ ] T036 [US4] Actualizar el parcial HTMX y estilos para secciones Catálogo/Corpus y avisos de vigencia (`contracts/chat-catalog.md`)
- [ ] T037 [US4] Implementar aclaración y no coincidencia en la web (`data-status="clarification"` y `"no_match"`)

**Checkpoint**: rutas y secciones correctas; corpus sin regresiones

---

## Phase 7: Acceptance & Polish

- [ ] T038 Implementar `assistant/catalog/acceptance.py` (grupos existing/commercial/colombia, ruta, atributos, materiales prohibidos, cotizaciones y métricas) según `contracts/acceptance-cli.md`
- [ ] T039 [P] Pruebas del reporte de aceptación en `tests/test_catalog_acceptance.py`
- [ ] T040 Implementar `scripts/run_catalog_acceptance.py` (CLI, `--today`, JSON/Markdown y exit codes)
- [ ] T041 Ejecutar la aceptación real de 130 preguntas; ajustar reglas si `route_accuracy < 0,90`; versionar reportes en `reports/`
- [ ] T042 [P] Actualizar `README.md`, `CONSTITUTION.md` §9 (rama determinista, `CATALOG_DIR`) y proyección si cambia una decisión
- [ ] T043 Ejecutar `make check` y la validación de `quickstart.md` con el catálogo real; registrar evidencia
- [ ] T044 Actualizar `specs/README.md` (✅) y abrir PR con CI `Calidad` en verde

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Fase 1)**: sin dependencias
- **Foundational (Fase 2)**: depende de Setup y bloquea todas las historias
- **US1 (Fase 3)**: depende de Foundational
- **US2 (Fase 4)**: depende de Foundational (puede ir tras US1)
- **US3 (Fase 5)**: depende de Foundational
- **US4 (Fase 6)**: depende de US1–US3 (usa las plantillas y consultas)
- **Acceptance & Polish (Fase 7)**: depende de todas

### Within Each User Story

- Pruebas primero, deben fallar antes de implementar
- Modelos/loader antes de consultas; consultas antes de plantillas
- Cada historia termina con su checkpoint validado

### Parallel Opportunities

- T002, T004, T007, T008, T013–T016 en paralelo
- T017–T018, T022–T024, T029, T032–T033, T039 en paralelo
- US1, US2 y US3 comparten `query.py` y `answers.py`: coordinar archivos antes de paralelizar

---

## Parallel Example: User Story 1

```bash
Task: "Prueba de recomendación y materiales prohibidos en tests/test_catalog_query.py"
Task: "Prueba de aclaración en tests/test_catalog_answers.py"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Fase 1 + Fase 2
2. US1: recomendaciones válidas y citadas
3. **PARAR y VALIDAR** con el catálogo real

### Incremental Delivery

1. US1 → recomendaciones
2. US2 → precios y cantidades
3. US3 → distribuidores
4. US4 → router, mixtas y web
5. Acceptance → métricas, reportes y PR

---

## Notes

- [P] = archivos distintos sin dependencia
- Cada restricción cita `data-model.md` y el campo exacto
- Si el router no alcanza el 90 % en T041, se ajustan reglas (no se cambia el set)
- Los reportes reales se versionan al cerrar la fase
