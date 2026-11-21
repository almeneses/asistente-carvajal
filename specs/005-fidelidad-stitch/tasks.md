# Tasks: Fidelidad visual del flujo Stitch y solicitud de cotización

**Feature**: `specs/005-fidelidad-stitch/`

**Tests**: Incluidos (contrato de plantillas, animación, store y endpoint).

## Phase 1: Setup

- [ ] T001 Vendorizar `tailwindcss` y su configuración en `assistant/static/stitch/tailwind.js`
- [ ] T002 [P] Descargar Material Symbols woff2 y DM Sans faltante a `assistant/static/stitch/`
- [ ] T003 [P] Descargar activos del prototipo (Carva, producto, logo) a `assistant/static/stitch/assets/`
- [ ] T004 [P] Extraer `@keyframes`, estilos y funciones JS de los HTML de Stitch a `stitch.css` y `stitch.js`
- [ ] T005 Añadir `QUOTES_LOG_PATH` a `.env.example` y `Settings` (`data-model.md`, `Configuración añadida`)

## Phase 2: Foundational

- [ ] T006 Implementar `assistant/quotes/models.py` (`QuoteRequest`, `QuoteRecord`, validación)
- [ ] T007 Implementar `assistant/quotes/store.py` (JSONL append, lectura, código `OC-AAAA-MMDD-XXXX` único)
- [ ] T008 Implementar `assistant/quotes/service.py` (recalcular total desde catálogo y registrar)
- [ ] T009 [P] Pruebas de modelos/store/código en `tests/test_quotes.py`
- [ ] T010 Implementar `stitch.js` con `minimizeToChat`, `expandFullCard`, `startCountdown`, `toggleFullCard` y `prefers-reduced-motion`
- [ ] T011 Crear la plantilla base Stitch (`base_stitch.html`) con cabecera, footer y carga local de Tailwind/fuentes/iconos
- [ ] T012 [P] Pruebas de contrato de animación en `tests/test_stitch_animation.py` (IDs, funciones, reduced motion)

**Checkpoint**: store, endpoint base y JS de animación listos.

## Phase 3: US1 - Bienvenida (P1)

- [ ] T013 Portar la bienvenida de Stitch a `assistant/templates/welcome.html` con Carva y dos tarjetas
- [ ] T014 Conectar “Conversar” → `/chat` y “Empaques” → `/chat/empaques`
- [ ] T015 Implementar “Escuchar la bienvenida” como aviso de voz próximamente
- [ ] T016 [P] Prueba de estructura/composición de la bienvenida
- [ ] T017 Revisión visual contra la captura `17b56113…` en 1280 y 390 px

## Phase 4: US2 - Conversación (P1)

- [ ] T018 Portar cabecera, barra de micrófono, burbujas y quick replies a `chat.html`
- [ ] T019 Integrar el streaming SSE existente en la nueva burbuja y estado
- [ ] T020 Portar el campo de entrada con micrófono (visual) y botón Enviar
- [ ] T021 Mantener citas, Markdown y feedback dentro del nuevo diseño
- [ ] T022 [P] Pruebas de estructura y de que los tokens SSE siguen renderizando
- [ ] T023 Revisión visual contra `20ebe791…` en 1280 y 390 px

## Phase 5: US3 - Empaques (P2)

- [ ] T024 Portar `_catalog_stitch.html` con resumen de atributos y recomendación
- [ ] T025 Conectar la rama de catálogo del backend a la nueva plantilla
- [ ] T026 Añadir CTA “Solicitar cotización” con datos de la recomendación
- [ ] T027 [P] Pruebas de render de recomendación y CTA
- [ ] T028 Revisión visual contra `cb7848c9…`

## Phase 6: US4 - Confirmación animada (P1)

- [ ] T029 Portar `_confirmation.html` (tarjeta completa) y `_compact_quote.html` (compacta)
- [ ] T030 Implementar `POST /quotes` en `assistant/web.py` conectado al servicio
- [ ] T031 Conectar “Solicitar cotización” al endpoint y al estado `submitting`
- [ ] T032 Implementar la transición completa → minimizada con countdown de 10 s
- [ ] T033 Implementar expandir desde la tarjeta compacta y el foco accesible
- [ ] T034 Implementar `prefers-reduced-motion` y estados de error/reintento
- [ ] T035 [P] Pruebas de estructura de confirmación, IDs y flujo sin código falso
- [ ] T036 Revisión visual contra `8045cfc2…` y `194f22dc…`

## Phase 7: US5 - Registro real (P2)

- [ ] T037 Implementar validación del SKU/cajas contra el catálogo y recálculo de total
- [ ] T038 Verificar ausencia de PII y append-only en el JSONL
- [ ] T039 [P] Pruebas del endpoint (éxito, 422, colisión de código, error de escritura)
- [ ] T040 Documentar `QUOTES_LOG_PATH` y el contrato en README

## Phase 8: Polish

- [ ] T041 Checklist de fidelidad de las 4 pantallas contra capturas (≥20 puntos por pantalla)
- [ ] T042 Verificar 0 peticiones a CDN y assets locales
- [ ] T043 axe/Lighthouse, teclado, foco y contraste en las 4 pantallas
- [ ] T044 Ejecutar `make check` y suites 1–4; corregir regresiones
- [ ] T045 Actualizar README/AGENTS/CONSTITUTION (0.8.0) y `specs/README.md`
- [ ] T046 Ejecutar quickstart y registrar evidencia; abrir PR y merge con CI verde

## Dependencies

- Setup → Foundational → US1/US2 → US3 → US4 → US5 → Polish.
- T030 depende de T006–T008; T031–T034 dependen de T030.
- Las revisiones visuales (T017, T023, T028, T036) requieren servidor local y capturas.
