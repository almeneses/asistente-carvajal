# Data Model: Experiencia de chat con identidad Carvajal

**Feature**: `specs/004-experiencia-chat` · **Fecha**: 2026-11-20

## Eventos del stream

### StreamEvent

| Campo | Tipo | Regla |
|---|---|---|
| `event` | enum | `start` \| `status` \| `catalog` \| `token` \| `sources` \| `done` \| `error` |
| `data` | dict | JSON de la carga del evento |

| Evento | Carga | Semántica |
|---|---|---|
| `start` | `request_id`, `intent` | La petición fue aceptada (`intent` = documental/commercial/mixed/ambiguous) |
| `status` | `phase` (`retrieving`/`generating`) | Progreso visible |
| `catalog` | `html` | Sección de catálogo ya renderizada (sin LLM) |
| `token` | `text` | Fragmento de texto plano de la respuesta documental |
| `sources` | `html`, `count` | Lista de fuentes citadas con enlaces seguros |
| `done` | `message_id`, `status`, `provider`, `latency_ms`, `final_html` | Fin correcto; `final_html` es el Markdown seguro renderizado |
| `error` | `message`, `request_id`, `retryable` | Error accionable; el cliente ofrece reintento |

- **Invariantes**: `token` solo antes de `done`; `done` o `error` cierra el stream; `sources`
  aparece una vez como máximo; `final_html` nunca contiene HTML crudo del LLM.
- **Codificación**: `event: <tipo>\ndata: <json>\n\n`; comentario `: keep-alive` cada 15 s.

## Conversación (solo cliente)

### ChatMessage

| Campo | Tipo | Regla |
|---|---|---|
| `message_id` | str | UUID generado por el servidor en `done` |
| `question` | str | 1..2000 caracteres |
| `status` | enum | `streaming` \| `answered` \| `no_evidence` \| `error` \| `cancelled` |
| `provider` | str \| null | `deepseek`/`ollama` |
| `latency_ms` | int | del servidor |
| `sources` | list[str] | URLs citadas |
| `feedback` | enum \| null | `up` \| `down` |

- Vive en el DOM; no se persiste ni se envía al servidor al recargar.

## Feedback

### FeedbackEntry

| Campo | Tipo | Regla |
|---|---|---|
| `message_id` | str | UUID del `done`; obligatorio |
| `rating` | enum | `up` \| `down`; obligatorio |
| `comment` | str | ≤500; opcional; sin PII |
| `created_at` | str ISO-8601 | UTC generado por el servidor |

- **Almacenamiento**: una línea JSON por evento en `FEEDBACK_LOG_PATH`
  (`.cache/feedback.jsonl` por defecto).
- **Deduplicación**: si llega otro rating para el mismo `message_id`, se añade un registro
  nuevo; el reporte usa el último. El archivo no se reescribe (append-only).
- **Prohibido**: nombre, correo, IP, user-agent, contenido de la pregunta.

## Tokens de diseño

### DesignTokens

| Grupo | Campos | Fuente |
|---|---|---|
| Color | `primary`, `secondary`, `tertiary`, `ink`, `background`, `surface`, `border`, `success`, `warning` | `designTheme.designMd` |
| Tipografía | `headline-xl/lg/md/sm`, `body-xl/lg/md`, `label-lg/md/sm` (DM Sans) | igual |
| Radios | tarjeta 24 px, botón 18 px, input 16 px, chip pill | igual |
| Espaciado | `space-xs/sm/md/lg/xl`, gutter, margin | igual |
| Elevación | nivel 1 y nivel 2 (sombras) | igual |
| Contraste | pares texto/fondo usados en la UI | calculado en pruebas |

- **Validación**: el contraste de cada par texto/fondo usado en componentes ≥4.5:1 (AA);
  el texto principal sobre superficies claras ≥7:1 (AAA objetivo).

## Configuración añadida

| Variable | Obligatoria | Defecto | Validación |
|---|---|---|---|
| `FEEDBACK_LOG_PATH` | no | `.cache/feedback.jsonl` | ruta escribible; archivo ignorado por Git |

## Estados de la interfaz

```text
idle → enviando → (retrieving) → (generating) → completada
                                      ├→ abstención (sin fuentes)
                                      ├→ error → reintento
                                      └→ cancelada (nueva conversación/abort)
```

- Reiniciar cancela cualquier stream en curso y vuelve a `idle` con 0 intercambios.
- Reintentar reutiliza la pregunta y vuelve a `enviando`.
