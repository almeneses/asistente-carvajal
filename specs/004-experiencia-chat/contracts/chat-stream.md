# Contrato: streaming del chat

**Feature**: `specs/004-experiencia-chat` · **Fecha**: 2026-11-20

## `POST /ask/stream`

- **Consumo**: `application/x-www-form-urlencoded`, campo `question` (1..2000 caracteres).
- **Respuesta válida**: `200 text/event-stream; charset=utf-8` con
  `Cache-Control: no-cache`, `X-Accel-Buffering: no`.
- **Pregunta inválida**: `422 application/json` **antes** de abrir el stream, con el mismo
  mensaje que hoy.
- **Cancelación**: si el cliente aborta (`AbortController` o cierra la pestaña), el servidor
  cancela la generación y no escribe fuentes.

### Secuencia de eventos

```text
event: start
data: {"request_id":"a1b2…","intent":"documental"}

event: status
data: {"phase":"retrieving"}

event: status
data: {"phase":"generating"}

event: token
data: {"text":"Carvajal "}

event: token
data: {"text":"nació en 1904…"}

event: sources
data: {"count":2,"html":"<ul class=\"sources\">…</ul>"}

event: done
data: {"message_id":"m-…","status":"answered","provider":"deepseek",
       "latency_ms":1234,"final_html":"<p>Carvajal…</p>"}
```

- **Catálogo**: `start` → `catalog` (HTML determinista) → `done`; sin `token`.
- **Mixta**: si el catálogo responde, se emite `catalog` y termina; si no cubre la parte
  documental, se emiten `token` del corpus.
- **Sin evidencia**: `start` → `status(generating)` → `done` con `final_html` de abstención
  y sin `sources`.
- **Error**: `event: error` con `message`, `request_id`, `retryable` y fin del stream.
- **Heartbeat**: comentario `: keep-alive` cada 15 s si no hay eventos.
- **Orden**: `start` primero; `done`/`error` último; máximo un `sources`.

### HTML permitido

- `catalog` y `sources.html` se renderizan en el servidor con el mismo motor seguro del
  resto de la app; `final_html` es Markdown renderizado sin HTML crudo.
- Enlaces: `target="_blank"` y `rel="noopener noreferrer"`.
- El cliente inserta `final_html`/`catalog` como HTML **solo** porque vienen del servidor;
  los `token` se insertan con `textContent`.

## Cliente

- Envía con `fetch` y lee el cuerpo con `ReadableStream`, parseando bloques SSE.
- Mientras llegan `token`, muestra texto plano en la burbuja con cursor de escritura.
- Al `done`: reemplaza el texto por `final_html`, muestra `sources`, guarda
  `message_id` (para feedback) y `provider`.
- Error: muestra el mensaje, botón **Reintentar** con la pregunta original y `request_id`.
- Reiniciar: `AbortController.abort()`, limpia el DOM y enfoca el input.
- Sin JavaScript: el formulario sigue haciendo `POST /ask` (respuesta completa HTML).

## Compatibilidad

- `POST /ask` se mantiene sin cambios de contrato para la suite de pruebas y no-JS.
- `GET /` conserva la página; el nuevo diseño es el mismo endpoint.
- `GET /healthz` no cambia.
