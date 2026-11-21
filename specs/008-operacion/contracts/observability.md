# Contrato: observabilidad

## `GET /healthz` (liveness)
200 con `status`, `corpus_documents`, `collection`, `provider` y catálogo si existe.
503 si el índice no está listo (comportamiento existente).

## `GET /readyz` (readiness)
200 si índice listo y catálogo cargado; 503 si falta alguno.
```json
{"status":"ok","checks":{"index":true,"catalog":true},"provider":"ollama"}
```

## `GET /metrics`
`text/plain; version=0.0.4` con formato Prometheus. Sin PII. Incluye requests, duración,
SSE, quotes, feedback, uptime y gauges de índice/catálogo.

## Cabeceras
- `X-Request-ID`: eco del válido recibido o UUID generado.
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: microphone=(self)`

## Logs
Una línea JSON por evento; request_id en contexto; sin pregunta/comentario/tokens.
