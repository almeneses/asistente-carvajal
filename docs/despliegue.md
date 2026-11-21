# Despliegue productivo

## Arquitectura

```text
Internet → Caddy (:80/:443, TLS) → app:8010 (sin puerto público)
                                    └── Ollama:11434 (red interna)
Datos: /data/carvajal (solo lectura) + volúmenes app-cache y caddy
```

La app corre como usuario no root, con healthcheck a `/readyz` y logs JSON.

## Preparación

1. Copiar `deploy/.env.prod.example` a `deploy/.env.prod` y completar `DOMAIN` y
   `DEEPSEEK_API_KEY` (opcional si usas Ollama).
2. Asegurar que `../carvajal/data` existe y contiene corpus/catálogo.
3. Construir el índice una vez (con el mismo `QDRANT_PATH` del volumen):
   ```bash
   docker compose -f deploy/docker-compose.prod.yml run --rm app \
     python scripts/index_corpus.py --recreate
   ```
4. Levantar:
   ```bash
   docker compose --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml up -d --build
   ```
5. Verificar:
   ```bash
   curl -fsS https://$DOMAIN/readyz
   curl -fsS https://$DOMAIN/metrics | head
   ```

Caddy obtiene y renueva el certificado automáticamente si el DNS apunta al servidor y los
puertos 80/443 están abiertos. Para pruebas locales usa `DOMAIN=localhost` (Caddy usa TLS
interno) o accede por HTTP al puerto 80.

## Secretos

- `deploy/.env.prod` no se versiona (`.gitignore`).
- La imagen no incluye `.env` (`.dockerignore`).
- Rota `DEEPSEEK_API_KEY` y reinicia `app` si se filtra.

## Actualización y rollback

```bash
git pull
docker compose --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml up -d --build
```

Rollback:
1. `git checkout <commit-anterior>`
2. Reconstruir y levantar con el mismo comando.
3. Verificar `/healthz` y `/readyz`; si los datos cambiaron, restaurar los JSONL/índice.

## Respaldo

- `.cache/feedback.jsonl` y `.cache/solicitudes.jsonl` (volumen `app-cache`).
- `.cache/qdrant` (reconstruible con `make index`).
- Configuración: `.env.prod` y `Caddyfile`.
- Programar copia diaria y probar restauración mensual.

## Operación

- Logs: `docker compose -f deploy/docker-compose.prod.yml logs -f app` (JSON, sin PII).
- Métricas: `/metrics` (protegido por la red; si se expone, ponerlo tras autenticación).
- Readiness: `/readyz`; liveness: `/healthz`.
- Alertas sugeridas: `readyz` 503 > 2 min, tasa de 5xx, latencia p95 y SSE sin `done`.

## Límites y siguientes pasos

- Una instancia; sin autenticación multiusuario ni cuotas por usuario.
- CSP estricta ya activa; revisar si se añaden scripts de terceros.
- Para escalar: Qdrant remoto (`QDRANT_URL`), varios workers de app y rate limiting en Caddy.
