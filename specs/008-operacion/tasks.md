# Tasks: Operación, observabilidad y despliegue

## Setup y base

- [X] T001 Añadir `LOG_LEVEL`/`LOG_FORMAT` a `Settings` y `.env.example`.
- [X] T002 Implementar `assistant/observability.py`: formatter JSON, request_id, métricas y middleware.
- [X] T003 Conectar logging y middleware en `assistant/web.py`.
- [X] T004 Exponer `/readyz` y `/metrics`; gauges de índice/catálogo.
- [X] T005 Instrumentar SSE, `/quotes` y `/feedback` (sin contenido).
- [X] T006 Cabeceras de seguridad y saneo de `X-Request-ID`.

## Pruebas

- [X] T007 Pruebas de formatter JSON y request_id en `tests/test_observability.py`.
- [X] T008 Pruebas de `/readyz` (200/503), `/metrics` y cabeceras.
- [X] T009 Prueba de que logs/métricas no contienen la pregunta ni comentarios.

## Despliegue y documentación

- [X] T010 `Dockerfile` multi-stage, no root y healthcheck.
- [X] T011 `.dockerignore` y `docker-compose.yml` (app + Ollama + volúmenes).
- [X] T012 `docs/operacion.md` (arranque, health, logs, backup, rollback, troubleshooting).
- [X] T013 `make smoke` y comandos de operación en README/AGENTS.
- [X] T014 Actualizar `CONSTITUTION.md`/proyección y `specs/README.md`.

## Converge (añadidas tras analyze)

- [X] T015 Validar `docker compose config` y documentar variables de compose.
- [X] T016 Prueba explícita de no-PII en logs y métricas.
- [X] T017 Target `make smoke` con health/ready/metrics.
- [X] T018 Cerrar docs (README/AGENTS/constitución) y abrir PR.
