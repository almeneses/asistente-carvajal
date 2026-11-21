# Implementation Plan: Experiencia de chat con identidad Carvajal

**Branch**: `feat/004-experiencia-chat` | **Date**: 2026-11-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-experiencia-chat/spec.md`

## Summary

Rediseñar el chat con el sistema visual de Stitch ([`docs/design/DESIGN.md`](../../docs/design/DESIGN.md)):
paleta azul Carvajal/cian/kraft, DM Sans, tarjetas de 24 px, objetivos de 64 px y
accesibilidad AA con objetivo AAA. Añadir respuesta **token a token por SSE**, Markdown
seguro, estados de progreso/error, reinicio de conversación, reintento, copia, feedback
JSONL sin PII y atajos de teclado. Las ramas documental y de catálogo conservan su
contenido, citas y enrutamiento; solo cambia su presentación.

## Technical Context

**Language/Version**: Python 3.13 (gestionado con `uv`)

**Primary Dependencies**: `markdown-it-py` + `mdit-py-plugins` (Markdown seguro); se
mantienen FastAPI, Jinja2, HTMX vendorizado y `httpx`. JavaScript propio mínimo
(`chat.js`), sin framework ni build de frontend.

**Storage**: conversación solo en el DOM (sin persistencia en servidor); feedback en
JSONL local (`FEEDBACK_LOG_PATH`, por defecto `.cache/feedback.jsonl`, sin PII).
Tokens visuales en CSS variables; fuente DM Sans y logo vendorizados.

**Testing**: `pytest` con LLM de streaming falso y lectura de eventos SSE; pruebas de
Markdown/XSS, feedback, contraste de tokens y estructura de plantillas. Las suites de las
fases 1–3 deben seguir verdes.

**Target Platform**: navegadores modernos; servidor Linux/macOS local; móvil desde 360 px.

**Project Type**: aplicación web existente; se añade una capa de presentación/streaming.

**Performance Goals**: primera señal visual < 1 s; primer token del LLM < 2 s en el camino
normal; catálogo determinista responde de inmediato.

**Constraints**: sin SPA; sin persistencia de conversación; sin voz, avatar animado ni
cotización (fuera de alcance); Markdown sin HTML crudo; feedback sin PII; citas intactas.

**Scale/Scope**: 1 usuario por instancia; 13 pantallas de referencia de Stitch; 5 estados
de respuesta; 2 proveedores LLM con streaming y fallback.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio / restricción | Verificación en el plan | Estado |
|---|---|---|
| I. La constitución manda | La fase solo cambia presentación; no altera stack ni decisiones de §9. | ✅ |
| II. Sin fuentes no hay respuesta | Las citas y el estado de abstención se conservan; el render Markdown no las altera. | ✅ |
| III. El corpus es el contrato | No se toca corpus, catálogo ni índices; solo se leen fuentes. | ✅ |
| IV. Recuperación separada de la generación | El streaming añade una capa de transporte; recuperación y LLM siguen separados. | ✅ |
| V. Cero secretos y cero datos personales | Feedback sin nombre/correo/IP; sin claves nuevas en el repo. | ✅ |
| Python 3.13 + `uv`, modo aplicación | Nuevas dependencias con `uv add`; `main.py` sigue siendo entrypoint. | ✅ |
| FastAPI + HTMX, Qdrant, DeepSeek/Ollama | Se reutilizan; solo se añade SSE y CSS/JS local. | ✅ |
| Ruff, `ty`, pytest, pre-commit, CI | Nuevas pruebas y `make check` como gate. | ✅ |

Sin violaciones; no se requiere *Complexity Tracking*.

## Project Structure

### Documentation (this feature)

```text
specs/004-experiencia-chat/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── chat-stream.md
│   └── feedback-api.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
assistant/ui/
├── __init__.py
├── markdown.py              # Render Markdown seguro (HTML deshabilitado)
├── feedback.py              # Append-only JSONL, dedupe por message_id
├── streaming.py             # Codificación SSE y eventos
└── tokens.py                # Tokens visuales y utilidades de contraste
assistant/templates/
├── index.html               # Nueva estructura visual (cabecera, chat, footer)
├── _exchange.html           # Burbuja de Carva + usuario, fuentes y acciones
├── _catalog_exchange.html   # Tarjetas de catálogo con el nuevo sistema
└── _error.html              # Estado de error con reintento
assistant/static/
├── theme.css                # Variables y componentes desde DESIGN.md
├── chat.js                  # Streaming, reset, retry, copy, feedback, atajos
├── fonts/DMSans.woff2       # DM Sans vendorizada (OFL)
├── htmx.min.js              # existente
└── carvajal-logo.svg        # existente
assistant/llm.py             # stream() en DeepSeek/Ollama/Fallback
assistant/rag.py             # answer_stream() / eventos
assistant/web.py             # POST /ask/stream, POST /feedback, /ask sync conservado
tests/
├── test_ui_markdown.py
├── test_ui_feedback.py
├── test_ui_streaming.py
├── test_ui_tokens.py
├── test_ui_web.py
└── test_ui_llm_stream.py
```

**Structure Decision**: capa `assistant/ui/` para lo transversal (Markdown, feedback,
SSE, tokens) y el resto en los módulos existentes. El endpoint síncrono `POST /ask`
se conserva para no-JS y pruebas; la interfaz usa `POST /ask/stream`.

## Phase 0: Research

Salida en [research.md](research.md): transporte SSE con POST/fetch, streaming de LLM y
fallback, Markdown seguro, feedback JSONL, fuentes/logo, accesibilidad y compatibilidad.

## Phase 1: Design

Salidas: [data-model.md](data-model.md), [contracts/chat-stream.md](contracts/chat-stream.md),
[contracts/feedback-api.md](contracts/feedback-api.md) y [quickstart.md](quickstart.md).

## Re-evaluación del Constitution Check (post-diseño)

| Principio / restricción | Verificación post-diseño | Estado |
|---|---|---|
| II. Sin fuentes no hay respuesta | El evento `sources` y el `done` conservan las citas; el Markdown no las elimina. | ✅ |
| IV. Recuperación separada | `answer_stream()` reutiliza el `RagService`; el streaming es solo transporte. | ✅ |
| V. Sin PII | El feedback guarda `message_id`, rating, comentario y fecha; nunca usuario/IP. | ✅ |
| Accesibilidad | Tokens con contraste verificado y checklist manual AA/AAA. | ✅ |

## Complexity Tracking

> Sin violaciones. La complejidad añadida (SSE, Markdown, feedback) queda aislada en
> `assistant/ui/` y se cubre con pruebas dedicadas.
