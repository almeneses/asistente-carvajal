# Plan: Operación, observabilidad y despliegue

## Technical Context

Python 3.13 + `uv`; stdlib (`logging`, `contextvars`, `threading`, `time`) y FastAPI.
Sin dependencias nuevas. Middleware ASGI/HTTP para request_id, latencia, cabeceras y
métricas. Métricas en memoria (contadores/duraciones) expuestas en texto Prometheus.
Docker multi-stage con `ghcr.io/astral-sh/uv`, usuario no root y healthcheck.

## Constitution Check

| Principio | Verificación | Estado |
|---|---|---|
| V. Sin secretos/PII | Logs sin preguntas/comentarios; métricas sin contenido; `.env` fuera del repo. | ✅ |
| II/IV | No se toca RAG; SSE conserva citas/abstención. | ✅ |
| Stack | Sin dependencias nuevas; FastAPI/uv. | ✅ |
| Calidad | Pruebas y `make check`. | ✅ |

## Structure

```text
assistant/observability.py     # logging JSON, request_id, métricas, middleware
assistant/config.py            # LOG_LEVEL, versión
assistant/web.py               # /readyz, /metrics, middlewares, logs SSE
Dockerfile / docker-compose.yml / .dockerignore
docs/operacion.md
tests/test_observability.py
```

## Enfoque

1. `JsonFormatter` + `ContextVar` de request_id.
2. `RequestContextMiddleware`: saneo de `X-Request-ID`, latencia, estado, cabeceras.
3. `Metrics`: contadores por método/ruta/estado y sumas de duración; render Prometheus.
4. `/readyz` y `/metrics`; gauges de índice/catálogo.
5. Logs específicos de SSE, solicitudes y feedback (sin contenido).
6. Artefactos Docker + runbook + pruebas.
