# Feature Specification: Operación multiusuario

**Branch**: `feat/010-multiusuario` · **Fase**: 9

## Objetivo

Habilitar uso multiusuario seguro y acotado sin cambiar la experiencia del chat: login,
sesión firmada, límites por usuario y resumen operativo para administración. La
autenticación es opcional (`AUTH_ENABLED=false` por defecto) para no romper el uso local.

## User Scenarios

### US1 · Acceso autenticado (P1)
- **Given** `AUTH_ENABLED=true`, **When** abro `/`, **Then** se redirige a `/login`.
- **Given** credenciales válidas, **When** inicio sesión, **Then** obtengo una cookie de sesión firmada y acceso al asistente.
- **Given** credenciales inválidas, **Then** error claro sin filtrar si el usuario existe.
- **Given** cierro sesión, **Then** la cookie se invalida y vuelvo al login.

### US2 · Cuotas y límites (P1)
- **Given** un usuario, **When** supera el límite de peticiones por minuto, **Then** recibe 429 con reintento.
- **Given** un usuario, **When** supera su cuota diaria de cotizaciones, **Then** 429 y no se registra la solicitud.

### US3 · Resumen de producción (P2)
- **Given** un administrador autenticado, **When** consulta `/admin/summary`, **Then** obtiene conteos de feedback y solicitudes, sin contenido ni PII.

### US4 · Compatibilidad y operación (P2)
- **Given** `AUTH_ENABLED=false`, **Then** la app funciona como hoy.
- **Given** el despliegue, **Then** `.env.example` y docs explican usuarios, secreto, cookies y límites.

## Requirements

- **FR-001**: `AUTH_ENABLED`, `AUTH_SECRET`, `AUTH_USERS`, `AUTH_ADMINS`, `AUTH_COOKIE_SECURE`.
- **FR-002**: Contraseñas con PBKDF2-SHA256 (sal e iteraciones).
- **FR-003**: Cookie de sesión firmada (HMAC), `HttpOnly`, `SameSite=Lax`, expiración, `Secure` opcional.
- **FR-004**: `/login` y `/logout`; proteger `/`, `/chat`, `/ask`, `/ask/stream`, `/quotes`, `/feedback`.
- **FR-005**: API/SSE sin sesión responde 401; páginas HTML redirigen a login con `next`.
- **FR-006**: Rate limit por usuario (`RATE_LIMIT_PER_MINUTE`, defecto 30) en endpoints de coste.
- **FR-007**: Cuota diaria de cotizaciones (`QUOTE_DAILY_LIMIT`, defecto 50).
- **FR-008**: 429 con `Retry-After` cuando aplique.
- **FR-009**: `/admin/summary` solo administradores; conteos agregados, sin preguntas/comentarios.
- **FR-010**: Logs/métricas sin contraseñas ni contenido; usuarios no se registran en claro en métricas.
- **FR-011**: CLI para generar hashes de contraseña.
- **FR-012**: Sin regresiones con auth desactivada (183+ pruebas).

## Success Criteria

- **SC-001**: Login/logout y protección funcionan; cookie inválida/expirada no da acceso.
- **SC-002**: Límite por minuto y cuota diaria devuelven 429.
- **SC-003**: Resumen admin devuelve conteos y no contenido.
- **SC-004**: Auth desactivada conserva el comportamiento actual.
- **SC-005**: 0 secretos/contraseñas en logs, métricas o repo.
- **SC-006**: CI y `make check` verdes.
