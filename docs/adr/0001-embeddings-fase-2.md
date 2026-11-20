# ADR 0001 — Embeddings de la fase 2 (`nomic-embed-text` vs. `bge-m3`)

- **Estado**: propuesto (evidencia pendiente de la matriz real)
- **Fecha**: 2026-11-20
- **Contexto**: la fase 1 cerró con 90 % de respuestas citadas y tres abstenciones;
  `nomic-embed-text` (768 dims, inglés-céntrico) mostró debilidad en español. La fase 2
  mide si `bge-m3` (1024 dims, multilingüe) mejora la recuperación de forma material.
- **Decisión**: migrar a `bge-m3` **solo si** la mejora en `recall@5` es de al menos
  5 puntos porcentuales sobre la mejor variante con `nomic-embed-text`. En caso
  contrario, se mantiene `nomic` y se documenta la evidencia.
- **Alternativas consideradas**: mantener `nomic` sin evaluar (sin evidencia),
  `multilingual-e5` (dependencia pesada), API externa de embeddings (coste y red).
- **Consecuencias si se migra**: `EMBEDDING_DIM=1024`, reconstrucción del índice de la
  app con `--recreate`, actualización de `CONSTITUTION.md` §3/§9 y de la proyección de
  Spec Kit en el mismo commit.
- **Evidencia**: se completará con `reports/baseline.json` (matriz de recuperación) y
  `reports/ganadora.json` (e2e de la variante ganadora).
