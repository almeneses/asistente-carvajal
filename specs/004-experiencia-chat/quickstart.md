# Quickstart: validar la nueva experiencia de chat

**Feature**: `specs/004-experiencia-chat` · **Fecha**: 2026-11-20

## Prerrequisitos

- Entorno de fases 1–3 funcionando (`make check` en verde, corpus e índice listos).
- Ollama con `bge-m3` y modelo de chat, o `DEEPSEEK_API_KEY`.
- Navegador moderno (Chrome/Firefox/Safari actuales) y, para accesibilidad, axe DevTools
  o Lighthouse.

## Arranque

```bash
uv sync
make run            # http://127.0.0.1:8010
```

Abrir la página: debe mostrar la cabecera con logo Carvajal, el chat con burbujas y el
campo grande (≥64 px).

## Validación manual

| Paso | Acción | Resultado esperado |
|---|---|---|
| 1 | Preguntar “¿Qué es Carvajal y a qué sectores se dedica?” | Estado visible <1 s y respuesta apareciendo token a token; al final, Markdown formateado |
| 2 | Revisar fuentes | Enlaces con título/tipo/URL, abren en pestaña nueva |
| 3 | Preguntar por catálogo (“necesito vasos para café caliente de 12 oz”) | Tarjetas de catálogo con la identidad Carvajal; sin tokens del LLM |
| 4 | Pregunta mixta | Catálogo primero; corpus solo si hace falta |
| 5 | Pulsar “Nueva conversación” | Conversación vacía y foco en el campo |
| 6 | Provocar un error (detener Ollama/Quitar key) y “Reintentar” | Error accionable y reintento con la misma pregunta |
| 7 | Copiar una respuesta | Texto copiado con confirmación |
| 8 | Marcar Útil/No útil y comentar | Confirmación; línea nueva en `.cache/feedback.jsonl` sin PII |
| 9 | Navegar solo con teclado y 360 px | Foco visible, sin scroll horizontal, targets táctiles |
| 10 | Reducir movimiento en el sistema | Sin animaciones no esenciales |

## Streaming por terminal

```bash
curl -N -X POST http://127.0.0.1:8010/ask/stream \
  --data-urlencode "question=¿Qué es Carvajal y a qué sectores se dedica?"
```

Debe verse `event: start`, `status`, varios `token`, `sources` y `done`.

## Feedback

```bash
curl -sS -X POST http://127.0.0.1:8010/feedback \
  -d "message_id=probar-123&rating=up&comment=clara"
cat .cache/feedback.jsonl
```

## Accesibilidad y contraste

- Lighthouse/axe sin errores críticos en escritorio y móvil.
- Contraste AA (≥4.5:1) en textos; objetivo AAA (≥7:1) en texto principal.
- `aria-live="polite"` anuncia respuestas sin interrumpir.
- Foco visible de 3 px y orden de tabulación lógico.
- La suite `tests/test_ui_tokens.py` verifica los pares de color usados.

## Pruebas

```bash
uv run pytest tests/test_ui_markdown.py tests/test_ui_feedback.py \
  tests/test_ui_streaming.py tests/test_ui_tokens.py tests/test_ui_web.py
make check
```

## Evidencia de la fase (2026-11-20)

- **154 pruebas** en verde (`make check`) y **22** de interfaz (`make ui-check`).
- App real: `/healthz` con corpus y catálogo; `POST /ask/stream` emitió
  `start → status → token… → sources → done` con Ollama local.
- Catálogo por SSE: `start → catalog → done` con SKU y tarjetas.
- Feedback: `POST /feedback` escribió `.cache/feedback.jsonl` sin PII.
- Contraste: texto principal 14,55:1 (AAA); pares usados ≥ AA; warning de texto
  oscurecido a `#8A5415` para cumplir AA sobre blanco.
- Identidad: logo extraído de Stitch, DM Sans vendorizada, tema claro/oscuro y
  `prefers-reduced-motion`.

## Problemas frecuentes

- **No hay streaming**: revisar que el navegador no bloquee `text/event-stream`; el
  fallback `POST /ask` sigue disponible.
- **Respuesta sin formato**: el `done` no llegó a renderizar `final_html`; revisar consola.
- **Feedback no escribe**: verificar permisos de `FEEDBACK_LOG_PATH`.
- **Fuente distinta**: DM Sans no cargó; comprobar `assistant/static/fonts/DMSans.woff2`.
