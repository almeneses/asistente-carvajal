# Research: Experiencia de chat con identidad Carvajal

**Feature**: `specs/004-experiencia-chat` · **Fecha**: 2026-11-20

## R1. Transporte SSE con POST y fetch

- **Decisión**: `POST /ask/stream` responde `text/event-stream`; el navegador lo consume con
  `fetch` + `ReadableStream` y un parser SSE propio (~40 líneas). Eventos:
  `start`, `status`, `catalog`, `token`, `sources`, `done`, `error`; comentario de
  heartbeat cada 15 s.
- **Rationale**: `EventSource` solo admite GET y la pregunta viaja en POST (evita límites de
  URL); `fetch` permite abortar con `AbortController` y reintentar. HTMX se mantiene para
  el resto, pero el streaming necesita control fino del parser.
- **Alternativas**: `htmx-ext-sse` (otra dependencia y eventos GET), WebSockets
  (bidireccional innecesario), polling (peor latencia).

## R2. Streaming de LLM y fallback

- **Decisión**: añadir `stream(messages) -> Iterator[str]` a `DeepSeekLLM` (SSE de
  `/chat/completions` con `stream=true`), `OllamaLLM` (NDJSON de `/api/chat` con
  `stream=true`) y `FallbackLLM` (usa el primario; si falla **antes del primer token**
  cambia al respaldo; un fallo a mitad de stream termina con error).
- **Rationale**: evita reescribir la cadena RAG; el primer token llega rápido y el fallback
  no mezcla dos respuestas. `RagService.answer_stream()` reutiliza recuperación y citas.
- **Alternativas**: streaming simulado por palabras (mentira perceptible), solo Ollama
  (peor calidad), WebSocket (más complejo).

## R3. Markdown seguro

- **Decisión**: `markdown-it-py` con preset GFM, `html=False`, `linkify=False` y una regla
  de renderer que fuerza `target="_blank"` y `rel="noopener noreferrer"` en enlaces. Los
  tokens del stream se muestran como **texto plano** (`textContent`); al terminar, el
  evento `done` trae `final_html` ya renderizado y sanitizado por el servidor.
- **Rationale**: evita XSS y el coste de renderizar Markdown en cada token; el usuario ve
  texto legible durante la espera y formato al final.
- **Alternativas**: renderizar Markdown en cliente con `marked`+DOMPurify (dos librerías
  JS y riesgo de divergencia), HTML crudo del LLM (prohibido).

## R4. Feedback JSONL sin PII

- **Decisión**: `POST /feedback` valida `message_id`, `rating` (`up`/`down`) y comentario
  opcional ≤500; escribe una línea JSON en `FEEDBACK_LOG_PATH` (defecto
  `.cache/feedback.jsonl`) con `created_at`. Si se revalora el mismo `message_id`, se
  añade un registro nuevo y el reporte usa el último (last-wins); no se guarda usuario, IP
  ni user-agent.
- **Rationale**: cumple FR-010 y V; el archivo es analizable y no requiere base de datos.
- **Alternativas**: localStorage (no analizable), base de datos (sobreingeniería), sin
  persistencia (no permite mejorar).

## R5. Tokens visuales y fuentes

- **Decisión**: `assistant/static/theme.css` define variables desde `DESIGN.md` (primario
  `#003A5D`, cian `#00B5E5`, kraft `#C89B6A`, tinta `#072B46`, fondo `#F3F6F8`, superficies
  blancas, radios 24/18/16 px, sombras nivel 1/2). DM Sans se vendoriza como woff2 (OFL)
  con `font-display: swap`; el logo ya está en `assistant/static/carvajal-logo.svg`.
- **Rationale**: sin build de Tailwind ni CDN; la app funciona offline y conserva la
  identidad exacta del proyecto de Stitch.
- **Alternativas**: CDN de Google Fonts (dependencia de red), Tailwind (build nuevo),
  fuente del sistema (pierde identidad).

## R6. Accesibilidad AA con objetivo AAA

- **Decisión**: HTML semántico (`header`, `main`, `footer`, `form`), `aria-live="polite"`
  en la conversación, foco visible de 3 px con halo, áreas táctiles ≥64 px, `aria-label`
  en botones de icono, `prefers-reduced-motion` y contraste calculado en pruebas para los
  pares de tokens clave (mínimo AA 4.5:1; objetivo AAA 7:1 en texto normal).
- **Rationale**: el diseño de Stitch está pensado para adultos 60+; la verificación
  automática de contraste evita regresiones y el resto queda como checklist manual.
- **Alternativas**: confiar solo en Lighthouse (no corre en CI), AAA estricto completo
  (coste alto; se aplica donde es viable).

## R7. Controles de conversación

- **Decisión**: estado en DOM; botón “Nueva conversación” limpia `#conversation` y enfoca
  el campo; error muestra “Reintentar” con la pregunta guardada en `data-question`;
  “Copiar” usa `navigator.clipboard` con confirmación; Enter envía, Shift+Enter salto;
  `AbortController` cancela el stream al reiniciar.
- **Rationale**: FR-006..FR-009 sin framework ni persistencia.

## R8. Catálogo y preguntas mixtas en el stream

- **Decisión**: si la intención es comercial, el servidor emite un evento `catalog` con el
  HTML de la sección (determinista, ya renderizado) y termina con `done`; si es mixta se
  mantiene la regla “catálogo primero, corpus solo si el catálogo no cubre”, y en ese caso
  se emiten tokens del corpus.
- **Rationale**: conserva el comportamiento de la fase 3 y la naturaleza determinista del
  catálogo; no se inventan precios.

## R9. Compatibilidad y pruebas

- **Decisión**: se conserva `POST /ask` síncrono para no-JS y pruebas existentes; la UI
  usa `/ask/stream` cuando hay JavaScript. Pruebas unitarias del parser SSE, del render
  Markdown, del feedback y de los tokens; ninguna necesita navegador ni red. CI ejecuta la
  suite completa.
- **Rationale**: evita regresiones en fases 1–3 y permite probar el streaming sin
  navegador.
