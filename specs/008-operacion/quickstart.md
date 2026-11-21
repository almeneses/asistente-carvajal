# Quickstart: operación

```bash
make check
make run
curl -sS http://127.0.0.1:8010/healthz | jq
curl -sS http://127.0.0.1:8010/readyz | jq
curl -sS http://127.0.0.1:8010/metrics | head
curl -sS -D - -o /dev/null http://127.0.0.1:8010/ | grep -i x-request-id
docker compose config
docker build -t asistente-carvajal .
```

Runbook completo en `docs/operacion.md`.
