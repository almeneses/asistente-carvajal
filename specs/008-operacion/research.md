# Research: operación

## R1. Logs JSON sin dependencias
`logging.Formatter` propio + `contextvars` para request_id. Se evita `structlog` para no
añadir dependencias y mantener control del esquema. Formatos: JSON por defecto, texto
opcional con `LOG_FORMAT=text`.

## R2. Métricas sin Prometheus client
Contadores y sumas en memoria con `threading.Lock`; render manual del formato Prometheus
(`# HELP`, `# TYPE`, labels). Suficiente para una instancia y evita dependencia/cardinalidad
alta. Las rutas se normalizan a plantillas conocidas.

## R3. Readiness real
`/readyz` verifica `index_ready` y `catalog is not None`; reporta proveedor. No llama a
Ollama en cada chequeo (evita latencia y falsos negativos); el estado del proveedor se
reporta como información.

## R4. Despliegue
Docker multi-stage con uv y `uv sync --frozen --no-dev`; usuario no root; healthcheck a
`/healthz`. Compose con app, Ollama y volúmenes de corpus/catálogo/caché; los datos no se
copian a la imagen.

## R5. Seguridad
Cabeceras `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`,
`Permissions-Policy`. No se añade CSP estricta porque la UI usa Tailwind/JS inline; se
documenta como siguiente paso. Request ID saneado a `[A-Za-z0-9._-]{1,64}`.
