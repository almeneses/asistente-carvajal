# Plan: evaluación continua y despliegue

## Enfoque

- `assistant/quality.py`: funciones puras sobre reportes + CLI; umbrales declarativos.
- `scripts/check_quality.py`: entrada para Make/CI.
- CSP en `apply_security_headers` (observabilidad) con `default-src 'self'`,
  `script-src 'self'`, `style-src 'self' 'unsafe-inline'`, `img-src 'self' data:`,
  `font-src 'self'`, `connect-src 'self'`, `frame-ancestors 'none'`.
- `deploy/docker-compose.prod.yml`: Caddy (80/443) + app interna + Ollama; sin puerto de app.
- `deploy/Caddyfile`: TLS automático, reverse proxy a `app:8010`, cabeceras y compresión.
- CI: gate de calidad + job `Despliegue` que valida compose y construye imagen.
- Docs: `docs/despliegue.md` y `docs/evaluacion.md`.

## Constitution Check

| Principio | Verificación | Estado |
|---|---|---|
| V. Sin secretos/PII | Compose usa variables; `.env` no se versiona; gates no leen PII. | ✅ |
| II/IV | Sin cambios de RAG/SSE. | ✅ |
| Stack | Sin dependencias nuevas. | ✅ |
| Calidad | Gates + pruebas + CI. | ✅ |
