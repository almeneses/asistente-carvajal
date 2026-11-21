# Feature Specification: Evaluación continua y despliegue productivo

**Branch**: `feat/009-evaluacion-despliegue` · **Fase**: 8

## Objetivo

Cerrar el ciclo de calidad y operación: gates automáticos sobre los reportes de evaluación,
CSP estricta, despliegue con TLS/reverse proxy y verificación en CI. Sin cambios de
funcionalidad visible.

## User Scenarios

### US1 · Gates de calidad reproducibles (P1)
Antes de fusionar, CI verifica que la calidad no retrocedió.
- **Given** los reportes de evaluación, **When** se ejecuta el gate, **Then** valida hit@5, citas, abstención, enrutamiento, atributos, cotizaciones y violaciones prohibidas.
- **Given** un umbral incumplido, **Then** el comando falla con el detalle.

### US2 · CSP y hardening (P1)
La app productiva sirve la UI con política de contenido estricta.
- **Given** cualquier respuesta, **Then** incluye una CSP que permite solo recursos locales (estilos inline necesarios).
- **Given** la UI, **Then** sigue renderizando y el JS funciona bajo la CSP.

### US3 · Despliegue con TLS y reverse proxy (P2)
Se puede desplegar con dominio y HTTPS.
- **Given** `deploy/docker-compose.prod.yml` y `deploy/Caddyfile`, **Then** Caddy termina TLS y proxya a la app; la app no expone puerto público.
- **Given** el runbook, **Then** cubre dominio, secretos, backups, rollout y rollback.

### US4 · Verificación en CI (P2)
CI ejecuta gates y valida los artefactos de despliegue.
- **Given** un PR, **Then** corre `make quality-gates`, valida el compose de producción y construye la imagen.

## Requirements

- **FR-001**: Script de gates que lea reportes y aplique umbrales.
- **FR-002**: Umbrales mínimos: hit@5 ≥ 0.90; citation_precision ≥ 0.95; abstención ≥ 0.95; route/attributes/quote ≥ 0.95; 0 violaciones prohibidas.
- **FR-003**: `make quality-gates` y ejecución en CI.
- **FR-004**: CSP estricta con recursos locales; `style-src` inline permitido por los estilos dinámicos.
- **FR-005**: El resto de cabeceras de seguridad se conserva.
- **FR-006**: Compose de producción con Caddy, app y Ollama; app sin puerto público.
- **FR-007**: Caddyfile con TLS automático, compresión y cabeceras.
- **FR-008**: Runbook de despliegue (`docs/despliegue.md`) con secretos, backups y rollback.
- **FR-009**: Job de CI que valide compose y construya la imagen.
- **FR-010**: Sin PII ni secretos en artefactos; `.env` fuera de Git.
- **FR-011**: Pruebas de gates y CSP.
- **FR-012**: Sin regresiones (179+ pruebas).

## Success Criteria

- **SC-001**: Gate falla si cualquier umbral baja; pasa con los reportes actuales.
- **SC-002**: CSP presente y UI operativa (captura headless).
- **SC-003**: `docker compose -f deploy/docker-compose.prod.yml config` válido.
- **SC-004**: Job de despliegue construye la imagen en CI.
- **SC-005**: Runbook cubre dominio, TLS, secretos, backup y rollback.
- **SC-006**: 0 regresiones.
