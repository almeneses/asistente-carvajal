# ADR 0001 — Embeddings de la fase 2 (`nomic-embed-text` vs. `bge-m3`)

- **Estado**: aceptada (2026-11-20)
- **Fecha**: 2026-11-20
- **Contexto**: la fase 1 cerró con 90 % de respuestas citadas y tres abstenciones;
  `nomic-embed-text` (768 dims, inglés-céntrico) mostró debilidad en español. La fase 2
  mide si `bge-m3` (1024 dims, multilingüe) mejora la recuperación de forma material.
- **Decisión**: migrar a `bge-m3`. La mejor variante con `bge-m3` (`bge-m3-500-hybrid`)
  alcanzó `hit@5 = 0,966` frente a `0,862` de la mejor con `nomic-embed-text`
  (`nomic-500-hybrid`), una mejora de **10,3 pp**, por encima del umbral de 5 pp.
- **Alternativas consideradas**: mantener `nomic` sin evaluar (sin evidencia),
  `multilingual-e5` (dependencia pesada), API externa de embeddings (coste y red).
- **Consecuencias si se migra**: `EMBEDDING_DIM=1024`, reconstrucción del índice de la
  app con `--recreate`, actualización de `CONSTITUTION.md` §3/§9 y de la proyección de
  Spec Kit en el mismo commit.
- **Evidencia**: `specs/002-evaluacion-recuperacion/reports/baseline.json`
  (matriz de 8 variantes) y `specs/002-evaluacion-recuperacion/reports/ganadora.json` (e2e: `hit@5 0,966`, citas 1,0, abstención 1,0; umbrales
  cumplidos). Fingerprint del corpus `9952ecc5…`.
- **Consecuencias aplicadas**: `EMBEDDING_MODEL=bge-m3`, `EMBEDDING_DIM=1024`,
  constitución 0.5.0 y proyección sincronizada; el índice de la app se reconstruye con
  `scripts/index_corpus.py --recreate`.
