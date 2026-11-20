# Research: Evaluación de recuperación y métricas de calidad

**Feature**: `specs/002-evaluacion-recuperacion` · **Fecha**: 2026-11-20

Resuelve las decisiones técnicas del plan; no quedan `NEEDS CLARIFICATION`.

## R1. Modelo alternativo: `bge-m3` vía Ollama

- **Decisión**: evaluar `bge-m3` (multilingüe, 1024 dims, contexto largo) servido por
  Ollama con el mismo endpoint `/api/embed`; se descarga con `ollama pull bge-m3`. La
  migración solo procede si mejora `recall@5` en **≥5 puntos porcentuales** frente a
  `nomic-embed-text`.
- **Rationale**: `nomic-embed-text` es débil en español y la fase 1 ya mostró fallos de
  recuperación; `bge-m3` es el candidato multilingüe más directo y no añade dependencias
  Python (misma API HTTP). El umbral evita un cambio de stack por ruido estadístico
  (30 preguntas, muestra pequeña).
- **Alternativas consideradas**: `multilingual-e5` (requiere `sentence-transformers` y
  descarga local), `jina-embeddings-v3` (API externa), mantener `nomic` sin evaluar
  (rechazado: no hay evidencia para decidir).
- **Coste**: descarga de ~1.2 GB y ~1–2 min de embeddings en CPU para 123 fragmentos.

## R2. Matriz de variantes: 8 combinaciones

- **Decisión**: `modelo` ∈ {`nomic`, `bge-m3`} × `fragmentación` ∈ {1000/200, 500/100} ×
  `mezcla` ∈ {`0.6·coseno + 0.4·léxico`, `1.0·coseno`}. Las dos primeras dimensiones
  definen el índice (4 construcciones); la mezcla solo reordena candidatos y se evalúa
  sobre los mismos vectores. Total: 8 variantes de recuperación.
- **Rationale**: aísla el efecto del modelo, del tamaño de fragmento y del híbrido con un
  coste de indexación acotado; la variante puramente vectorial sirve de control.
- **Alternativas consideradas**: matriz completa de pesos (12+ corridas, poco retorno),
  búsqueda de hiperparámetros automática (sobreingeniería para 30 preguntas).

## R3. Ground truth: propuesta asistida + revisión humana

- **Decisión**: `scripts/propose_ground_truth.py` recupera los 5 fragmentos más similares
  por pregunta con el índice actual y pide al LLM una propuesta de `expected_slugs`,
  `expected_status` (`sustainable`/`not_sustainable`) y `key_facts`. Escribe
  `evaluation/questions.candidate.json` y una tabla de revisión en Markdown. Una persona
  corrige y firma; el resultado se congela en `evaluation/questions.json` con
  `reviewed_by`, `reviewed_at` y `corpus_fingerprint`.
- **Rationale**: reduce el coste de anotar 30 preguntas sin renunciar a la calidad; la
  revisión humana queda registrada (FR-012).
- **Alternativas consideradas**: anotación manual completa (lenta), solo LLM (riesgo de
  circularidad: el mismo modelo que responde define la verdad).

## R4. Definición de métricas

- **recall@k** (documento): para cada pregunta sustentable, `|esperados ∩ recuperados| /
  |esperados|`, donde recuperados son los slugs únicos de los `k` fragmentos; promedio
  macro sobre preguntas sustentables. `k` ∈ {1, 3, 5, 10}.
- **MRR**: inverso del rango (1-based) del primer fragmento cuyo slug está entre los
  esperados; promedio macro.
- **precisión de citas** (end-to-end): proporción de citas producidas que coinciden en
  URL, título y tipo con el corpus; por construcción debe ser 100 % (detecta regresiones).
- **cobertura de cita esperada**: proporción de respuestas que citan al menos un slug
  esperado.
- **abstención correcta**: en preguntas `not_sustainable`, proporción con
  `status="no_evidence"`; **falsa abstención**: en sustentables, proporción abstenida.
- **latencia**: p50/p95 con interpolación lineal sobre la lista ordenada.
- **Rationale**: separa recuperación (sin LLM) de generación y evita métricas compuestas
  difíciles de interpretar.

## R5. Fingerprint y comparabilidad

- **Decisión**: `sha256` de la concatenación ordenada de `slug:hash` de todos los
  documentos, más el `sha256` de `index.jsonl`; el reporte guarda ambos y el número de
  fragmentos indexados. Dos reportes solo se comparan si el fingerprint coincide.
- **Rationale**: el corpus puede cambiar entre corridas; comparar sin fingerprint produce
  conclusiones inválidas (edge case de la spec).

## R6. Aislamiento del índice de evaluación

- **Decisión**: la evaluación usa `EVAL_QDRANT_PATH` (defecto `.qdrant-eval`, ignorado por
  Git) o `QDRANT_URL` si se define; colecciones `eval_<variante>` creadas con `--recreate`.
  Nunca toca `.qdrant/` de la aplicación (FR-009).
- **Rationale**: permite correr la evaluación con la app encendida y evita mezclar
  dimensiones (768 vs. 1024) en una misma colección.
- **Alternativas consideradas**: reutilizar el índice de la app (rompe aislamiento y no
  admite bge-m3), colección temporal en el Qdrant de `carvajal` (acopla entornos).

## R7. Dimensión de embedding configurable

- **Decisión**: añadir `EMBEDDING_DIM` a la configuración (defecto 768, rango 1–4096);
  `OllamaEmbedder` valida contra la dimensión configurada y `QdrantIndex` la usa al crear
  la colección. La app sigue con 768 hasta que una migración aprobada cambie el defecto.
- **Rationale**: el código actual fija 768 en una constante; sin esto `bge-m3` no puede
  indexarse sin duplicar el índice.
- **Riesgo**: una colección existente con otra dimensión debe recrearse; el runner de
  evaluación siempre usa `--recreate` y la app requiere `index_corpus --recreate` tras la
  migración.

## R8. Modos de ejecución y CI

- **Decisión**: `--mode retrieval` (sin LLM, matriz completa) y `--mode e2e` (solo
  ganadora o variante explícita). CI ejecuta únicamente pruebas con fixtures; la
  evaluación real es manual y se documenta en `quickstart.md`.
- **Rationale**: evita coste y fragilidad en CI sin renunciar a la reproducibilidad.

## R9. Protocolo de decisión y migración

- **Decisión**: el reporte comparativo declara ganadora por `recall@5` y desempata por MRR
  y coste. Si `bge-m3` gana por ≥5 pp:
  1. enmendar `CONSTITUTION.md` §3 (embeddings 1024) y §9 + proyección de Spec Kit;
  2. cambiar el defecto de configuración y la dimensión;
  3. reconstruir el índice de la app con `scripts/index_corpus.py --recreate`;
  4. actualizar `data-model.md` y el ADR.
  Si no se cumple, el ADR registra “mantener `nomic`” con la evidencia.
- **Rationale**: cumple FR-010 y deja la decisión auditable.

## Dependencias

Ninguna nueva. Se reutilizan `httpx`, `qdrant-client`, `pytest` y la librería estándar.
`bge-m3` se obtiene con Ollama y no se versiona.
