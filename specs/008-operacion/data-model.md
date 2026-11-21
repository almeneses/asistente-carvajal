# Data Model: observabilidad

## LogEntry (JSON)
| Campo | Tipo | Regla |
|---|---|---|
| `ts` | ISO-8601 UTC | Generado por el formatter |
| `level` | str | INFO/WARNING/ERROR |
| `logger` | str | `asistente` o submódulo |
| `message` | str | Evento, sin PII |
| `request_id` | str | Del contexto o `-` |
| `method`, `path`, `status`, `latency_ms` | varios | Cuando aplica |
| `extra` | dict | Campos del evento (sin contenido de pregunta) |

## MetricSample
- `asistente_http_requests_total{method,path,status}` (counter)
- `asistente_http_request_duration_seconds_sum{method,path}` / `_count`
- `asistente_sse_streams_total{status}` (counter)
- `asistente_quotes_total` / `asistente_feedback_total`
- `asistente_uptime_seconds` (gauge)
- `asistente_index_ready` / `asistente_catalog_loaded` (gauge 0/1)
- `asistente_catalog_references` (gauge)

## Readiness
```json
{"status":"ok","checks":{"index":true,"catalog":true},"provider":"ollama"}
```

## Configuración
| Variable | Defecto | Regla |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Nivel de logging |
| `LOG_FORMAT` | `json` | `json` o `text` |
