# ADR 0003 — Qdrant embebido por defecto, remoto opcional

- **Estado**: aceptada
- **Fecha**: 2026-11-21
- **Contexto**: desarrollo local y CI no deben depender de un servicio externo; la app
  necesita filtros por `source_type` y un índice reproducible.
- **Decisión**: `QDRANT_PATH` embebido por defecto; `QDRANT_URL` opcional para despliegue
  remoto. Un solo escritor por índice local; evaluación usa `EVAL_QDRANT_PATH` separado.
- **Alternativas**: Qdrant server siempre (más operación), pgvector (otro stack),
  FAISS (sin filtros/edición incremental).
- **Consecuencias**: arranque simple y sin credenciales; el lock local obliga a no abrir
  el mismo índice desde dos procesos; para escalar se usa Qdrant remoto.
- **Evidencia**: `.qdrant/` local, `tests/test_index.py`, runbook de operación.
