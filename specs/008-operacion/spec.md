# Feature Specification: Operación, observabilidad y despliegue

**Branch**: `feat/008-operacion-observabilidad` · **Fase**: 7

## Objetivo

Dejar el asistente listo para operar: trazabilidad por petición, salud y readiness,
métricas, cabeceras de seguridad, empaquetado reproducible y runbook. Sin nuevas
funcionalidades de negocio ni datos personales.

## User Scenarios

### US1 · Trazabilidad sin PII (P1)
Cada petición tiene un `request_id` correlacionable en logs y respuesta.
- **Given** una petición, **When** se atiende, **Then** se registra `request_id`, método, ruta, estado y latencia en JSON.
- **Given** un `X-Request-ID` válido, **Then** se reutiliza; si es inválido, se genera uno nuevo.

### US2 · Salud, readiness y métricas (P1)
Operación puede saber si el servicio vive, si puede atender y cuánto tráfico procesa.
- **Given** `/healthz`, **Then** responde 200 si el proceso vive.
- **Given** `/readyz`, **Then** 200 solo si índice y catálogo están listos; 503 si no.
- **Given** `/metrics`, **Then** expone contadores y latencias en formato Prometheus sin PII.

### US3 · Despliegue reproducible (P2)
Se puede construir y ejecutar con Docker y seguir un runbook.
- **Given** la imagen, **Then** arranca sin root y con healthcheck.
- **Given** el compose, **Then** define app, Ollama y volúmenes de datos/caché.
- **Given** el runbook, **Then** cubre arranque, health, logs, backup y rollback.

### US4 · Seguridad operativa (P2)
Respuestas con cabeceras seguras y sin filtrar secretos ni preguntas.
- **Given** cualquier respuesta, **Then** incluye `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` y `Permissions-Policy`.
- **Given** logs y métricas, **Then** no contienen pregunta, comentario, tokens ni claves.

## Requirements

- **FR-001**: Logs JSON con timestamp, nivel, logger, mensaje, `request_id`, método, ruta, estado y latencia.
- **FR-002**: `request_id` por petición, propagado en `X-Request-ID` y en logs.
- **FR-003**: `/healthz` liveness con estado del proceso.
- **FR-004**: `/readyz` readiness con índice, catálogo y proveedor.
- **FR-005**: `/metrics` Prometheus con requests, errores, duración, uptime y gauges de índice/catálogo.
- **FR-006**: Middleware de cabeceras de seguridad.
- **FR-007**: Sin PII ni contenido de preguntas en logs/métricas.
- **FR-008**: `Dockerfile` multi-stage, usuario no root y healthcheck.
- **FR-009**: `docker-compose.yml` con app, Ollama y volúmenes documentados.
- **FR-010**: `docs/operacion.md` con runbook (arranque, health, logs, backup, rollback, troubleshooting).
- **FR-011**: `LOG_LEVEL` configurable; formato JSON por defecto.
- **FR-012**: Conservar endpoints, SSE, catálogo, solicitudes y UI sin regresiones.
- **FR-013**: Pruebas de logs, readiness, métricas, cabeceras y request_id.
- **FR-014**: `make check` y CI en verde.

## Success Criteria

- **SC-001**: 100% de peticiones registran `X-Request-ID` y una línea JSON.
- **SC-002**: `/readyz` responde 503 sin índice/catálogo y 200 con ambos.
- **SC-003**: `/metrics` expone al menos requests, duración y gauges.
- **SC-004**: 0 PII/contenido de pregunta en logs y métricas.
- **SC-005**: Imagen y compose construibles/validables; runbook completo.
- **SC-006**: 174+ pruebas previas verdes.
