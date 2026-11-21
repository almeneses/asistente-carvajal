# Operación del Asistente Carvajal

## Arranque local

```bash
make dev
make index          # una vez, o tras cambiar el corpus
make run            # http://127.0.0.1:8010
```

Variables clave en `.env`: `CORPUS_GOLD_DIR`, `CATALOG_DIR`, `CATALOG_ROUTING_FILE`,
`QDRANT_PATH`, `OLLAMA_BASE_URL`, `DEEPSEEK_API_KEY` (opcional), `LLM_PROVIDER`,
`LOG_LEVEL`, `LOG_FORMAT`.

## Salud y métricas

| Endpoint | Uso |
|---|---|
| `GET /healthz` | Liveness; 503 si el índice no está listo. |
| `GET /readyz` | Readiness; 200 solo con índice y catálogo cargados. |
| `GET /metrics` | Prometheus: peticiones, duración, SSE, quotes, feedback, uptime y gauges. |

```bash
curl -sS localhost:8010/healthz | jq
curl -sS localhost:8010/readyz | jq
curl -sS localhost:8010/metrics | head
```

Cada respuesta incluye `X-Request-ID` (se reutiliza si llega uno válido). Los logs son
JSON por defecto (`LOG_FORMAT=text` para texto) y no contienen preguntas, comentarios ni
secretos.

## Multiusuario (opcional)

```bash
export AUTH_ENABLED=true
export AUTH_SECRET="$(openssl rand -hex 32)"
export AUTH_USERS="{\"ana\": \"$(uv run python scripts/hash_password.py --password 'clave-segura')\"}"
export AUTH_ADMINS=ana
export AUTH_COOKIE_SECURE=true   # detrás de HTTPS
make run
```

- `/login` y `/logout`; las rutas del asistente quedan protegidas.
- Sesión firmada (HMAC), `HttpOnly`, `SameSite=Lax`; no hay estado en servidor.
- `RATE_LIMIT_PER_MINUTE` (30) y `QUOTE_DAILY_LIMIT` (50) por usuario.
- `GET /admin/summary` (solo `AUTH_ADMINS`) devuelve conteos de feedback y solicitudes.
- Si `AUTH_ENABLED=false`, el comportamiento es el actual (un solo usuario local).

## Logs

```json
{"ts":"…","level":"INFO","logger":"asistente","message":"request",
 "request_id":"…","method":"GET","path":"/chat","status":200,"latency_ms":4.1}
```

Eventos operativos: `sse_start`, `sse_done`, `quote_registered`, `feedback_registered`.

## Datos y respaldo

- Corpus/catálogo: solo lectura, montados desde `../carvajal/data`.
- Feedback: `.cache/feedback.jsonl` (sin PII).
- Solicitudes: `.cache/solicitudes.jsonl` (sin PII).
- Índice: `.qdrant/` (reconstruible con `make index`).

Respaldo recomendado: copiar los dos JSONL y `.qdrant/`. Restauración: detener la app,
restaurar archivos y arrancar; verificar `/readyz`.

## Docker

```bash
docker compose config      # valida el compose
docker build -t asistente-carvajal .
docker compose up -d
```

El compose monta `../carvajal/data` en `/data/carvajal` (solo lectura) y dos volúmenes:
caché de la app y modelos de Ollama. El contenedor corre como usuario no root y tiene
healthcheck a `/healthz`. Para construir el índice dentro del contenedor:

```bash
docker compose run --rm app python scripts/index_corpus.py --recreate
```

## Seguridad

- Sin secretos en la imagen (`.env` y `.dsh` excluidos por `.dockerignore`).
- Cabeceras: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`,
  `Permissions-Policy`.
- Pendiente recomendado: CSP estricta cuando se externalicen los scripts inline.

## Troubleshooting

| Síntoma | Causa / acción |
|---|---|
| `/readyz` 503 index=false | Ejecutar `make index`; revisar `QDRANT_PATH`. |
| `/readyz` 503 catalog=false | Revisar `CATALOG_DIR` y `CATALOG_ROUTING_FILE`. |
| `Ollama no responde` | Verificar `OLLAMA_BASE_URL` y `ollama serve`. |
| `Storage folder .qdrant is already accessed` | Otra instancia usa el índice; usar `QDRANT_PATH` distinto o detener la otra. |
| Stream sin tokens | Revisar logs `sse_*` y proveedor; `/ask` síncrono sigue disponible. |
| Puerto ocupado | `make run PORT=8011` o ajustar `PORT`. |

## Rollback

1. `docker compose down` (o detener `make run`).
2. Restaurar la imagen/commit anterior (`git checkout <tag>` y reconstruir).
3. Restaurar JSONL/índice si cambiaron los datos.
4. Arrancar y verificar `/healthz`, `/readyz` y una pregunta de humo.

## Humo

```bash
make smoke
```
