# Contrato: feedback de respuestas

**Feature**: `specs/004-experiencia-chat` · **Fecha**: 2026-11-20

## `POST /feedback`

- **Consumo**: `application/x-www-form-urlencoded`:
  - `message_id` (str, obligatorio, UUID del evento `done`)
  - `rating` (`up` | `down`, obligatorio)
  - `comment` (str, opcional, ≤500 caracteres)
- **Respuesta correcta**: `200 application/json`

```json
{"ok": true, "message_id": "m-…", "rating": "up"}
```

- **Validación**: `422 application/json` con `detail` si falta `message_id`, el rating es
  inválido o el comentario excede 500 caracteres.
- **Error de escritura**: `500 application/json` con mensaje genérico y `request_id` en log.
- **No bloquea la UI**: el cliente muestra confirmación optimista y revierte si hay error.

## Persistencia

- Archivo `FEEDBACK_LOG_PATH` (defecto `.cache/feedback.jsonl`), una línea JSON por evento:

```json
{"message_id":"m-…","rating":"up","comment":"","created_at":"2026-11-20T19:00:00+00:00"}
```

- **Sin PII**: no se guarda usuario, correo, IP, user-agent ni la pregunta.
- **Revaloración**: un segundo rating del mismo `message_id` añade otra línea; el reporte
  usa la última (last-wins). El archivo es append-only y no se reescribe.
- **Concurrencia**: escritura con `open(..., "a")` en una sola línea; suficiente para una
  instancia local. El path se crea al primer uso.
- El archivo está en `.cache/` (ignorado por Git); no se versiona feedback.

## Cliente

- Botones “Útil” / “No útil” en cada respuesta terminada; estado seleccionado visible.
- Comentario opcional en un campo que aparece tras elegir un rating.
- Confirmación visual (“Gracias, registrado”) y bloqueo del botón tras enviar.
- El `message_id` se toma del evento `done`; sin `message_id` no se muestra feedback.
