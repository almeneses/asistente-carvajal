# Implementation Plan: Fidelidad visual del flujo Stitch y solicitud de cotización

**Branch**: `feat/005-fidelidad-stitch` | **Date**: 2026-11-20 | **Spec**: [spec.md](spec.md)

## Summary

Portar el flujo completo del prototipo Stitch —Bienvenida, Conversación, Asistente de
Empaques y Confirmación animada— copiando su HTML/CSS/JS y vendorizando Tailwind, DM Sans,
Material Symbols y los activos visuales. Añadir el registro real de solicitudes de
cotización (JSONL, código `OC-AAAA-MMDD-XXXX`, sin PII) y conectar la animación de
minimización/expansión de la confirmación. Se conserva el backend de fases 1–4.

## Technical Context

**Language/Version**: Python 3.13 + `uv`; JavaScript vanilla (sin framework) + Tailwind
Play CDN vendorizado.

**Primary Dependencies**: FastAPI, Jinja2; se añaden `tailwindcss` (script local),
DM Sans (ya vendorizada), Material Symbols (woff2 local) y los activos del prototipo
(Carva, producto, logo). Sin dependencias Python nuevas.

**Storage**: solicitudes en JSONL (`QUOTES_LOG_PATH`, por defecto
`.cache/solicitudes.jsonl`), append-only, sin PII. Conversación sin persistencia.

**Testing**: `pytest` para modelos, store, endpoint y estructura de plantillas; pruebas de
contrato de la animación (IDs/clases/funciones y respeto a `prefers-reduced-motion`);
suites 1–4 sin regresiones.

**Target Platform**: navegadores modernos; 390/768/1280 px.

**Project Type**: aplicación web existente; se sustituye la capa visual y se añade la rama
de solicitudes.

**Constraints**: sin CDN en runtime; sin SPA; sin voz funcional; sin PII; sin inventar
precios; una sola página con vistas/estados; fidelidad al prototipo.

**Scale/Scope**: 4 pantallas/estados, 1 flujo de solicitud, 2 idiomas no (solo español).

## Constitution Check

| Principio / restricción | Verificación | Estado |
|---|---|---|
| II. Sin fuentes no hay respuesta | Las citas y abstención se conservan; la UI copiada las muestra. | ✅ |
| III. El corpus es el contrato | No se modifican corpus ni catálogo; solo se leen. | ✅ |
| IV. Recuperación separada | SSE y RAG no cambian; la UI consume los mismos eventos. | ✅ |
| V. Cero secretos y cero PII | Solicitudes sin nombre/correo/teléfono/IP; JSONL ignorado. | ✅ |
| Stack FastAPI + HTMX/Jinja | Se mantiene; Tailwind es solo presentación local. | ✅ |
| Ruff, `ty`, pytest, CI | Nuevas pruebas y `make check`. | ✅ |

Sin violaciones.

## Project Structure

```text
assistant/quotes/
├── __init__.py
├── models.py          # QuoteRequest, QuoteRecord, validación
├── store.py           # JSONL append + lectura + código único
└── service.py         # recalcula total desde catálogo y registra
assistant/static/stitch/
├── tailwind.js        # Play CDN vendorizado
├── stitch.css         # keyframes y estilos del prototipo
├── stitch.js          # navegación, minimizar/expandir, countdown
├── material-symbols.woff2
└── assets/            # Carva, producto, logo del prototipo
assistant/templates/
├── welcome.html       # pantalla de bienvenida copiada
├── chat.html          # conversación fiel + SSE
├── _catalog_stitch.html
├── _confirmation.html
└── _compact_quote.html
assistant/web.py       # rutas /, /chat, /chat/empaques, POST /quotes
assistant/config.py    # QUOTES_LOG_PATH
tests/
├── test_quotes.py
├── test_quotes_web.py
├── test_stitch_templates.py
└── test_stitch_animation.py
```

## Phase 0: Research

Ver [research.md](research.md): portado del HTML, dependencias locales, animación,
registro de solicitudes y accesibilidad.

## Phase 1: Design

Ver [data-model.md](data-model.md), [contracts/quote-api.md](contracts/quote-api.md) y
[quickstart.md](quickstart.md).

## Re-evaluación post-diseño

| Principio | Verificación | Estado |
|---|---|---|
| II / IV | El endpoint de solicitud no toca RAG; el chat conserva SSE y fuentes. | ✅ |
| V | Solo se persisten datos comerciales del catálogo y ciudad; 0 PII. | ✅ |
| Accesibilidad | Transición con `prefers-reduced-motion`, foco y contraste. | ✅ |
