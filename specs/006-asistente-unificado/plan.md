# Implementation Plan: Asistente único

**Branch**: `feat/006-asistente-unificado`

## Technical Context

Python 3.13/uv, FastAPI + Jinja2, Tailwind local (fase 5), JS vanilla. Se sustituyen
`welcome.html` y `chat.html`; `/chat/empaques` pasa a redirección. CSS: fondo Carvajal
con gradientes + SVG inline (montañas, cuadrícula, cuadrados del logo). JS: contraer
`#carva-presence` al primer envío; compactar tarjetas de catálogo al siguiente mensaje.
Se conservan SSE, `/quotes`, feedback y confirmación.

## Constitution Check

| Principio | Verificación | Estado |
|---|---|---|
| II/IV | SSE y RAG sin cambios; citas y abstención intactas. | ✅ |
| V | Sin PII nueva; solicitudes siguen en JSONL sin datos personales. | ✅ |
| Accesibilidad | Transición con movimiento reducido, contraste y foco. | ✅ |
| Stack | Sin dependencias nuevas; activos locales. | ✅ |

## Structure

```text
assistant/templates/welcome.html     # inicio unificado
assistant/templates/chat.html        # panel 70%, presencia Carva, compositor
assistant/static/stitch/stitch.css   # fondo Carvajal, panel 70%, compactación
assistant/static/chat.js             # transición, compactación, streaming
assistant/web.py                     # /chat/empaques -> /chat
tests/test_stitch_templates.py       # inicio/chat/redirección
tests/test_ui_web.py                 # estructura y panel
```

## Verification

`make check`, capturas headless de inicio y chat, prueba manual de transición y de
compactación, y revisión de que no queden modos separados.
