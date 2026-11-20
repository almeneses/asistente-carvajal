# Data Model: Corte vertical del asistente con citas del corpus

**Feature**: `specs/001-corte-vertical-citas` · **Fecha**: 2026-11-19

Este documento define las entidades que cruzan la especificación, el esquema del índice
Qdrant, los protocolos internos y las validaciones. Es la fuente para `tasks.md` y para
las pruebas.

## Entidades de entrada (solo lectura)

### Documento del corpus

Unidad curada del corpus web. Se carga desde `CORPUS_GOLD_DIR/*.md` y se valida contra
`index.jsonl`.

| Campo | Tipo | Origen | Regla |
|---|---|---|---|
| `slug` | str | nombre de archivo sin `.md` | único; no vacío |
| `title` | str | front matter | obligatorio |
| `url` | str | front matter | obligatorio; `http(s)` |
| `section` | str | front matter | obligatorio |
| `source_type` | `"oficial"` \| `"tercero"` | front matter | obligatorio |
| `captured_at` | str ISO-8601 | front matter | obligatorio |
| `hash` | str hex | front matter | 64 caracteres |
| `chars` | int | front matter | > 0 |
| `body` | str | cuerpo Markdown | no vacío |

- **Validación**: si un documento no tiene front matter completo o no aparece en
  `index.jsonl`, el arranque falla enumerando los documentos inválidos (FR-008, III).
- **Inmutabilidad**: la aplicación nunca escribe en el directorio del corpus.

### Fragmento (chunk)

Unidad indexada y recuperable, derivada de un documento.

| Campo | Tipo | Regla |
|---|---|---|
| `slug` | str | FK lógica a Documento |
| `url` | str | copiado del documento |
| `title` | str | copiado del documento |
| `source_type` | str | copiado del documento |
| `section` | str | copiado del documento |
| `chunk_index` | int | 0..n por documento |
| `text` | str | 1..1000 caracteres |
| `char_start` | int | posición en el cuerpo |

- **Regla de corte**: 1000 caracteres máximo, solape de 200 entre fragmentos contiguos
  del mismo documento; el último fragmento puede ser más corto.
- **Determinismo**: mismo documento → mismos fragmentos.

## Entidades del diálogo

### Pregunta

| Campo | Tipo | Regla |
|---|---|---|
| `text` | str | 1..2000 caracteres, no vacío tras `strip` |
| `asked_at` | datetime UTC | generado por el servidor |
| `request_id` | str | UUID v4 por petición (traza) |

### Respuesta

| Campo | Tipo | Regla |
|---|---|---|
| `status` | `"answered"` \| `"no_evidence"` \| `"error"` | |
| `text` | str | vacío solo si `status="error"` o `no_evidence` con mensaje |
| `sources` | list[Cita] | vacía si `status="no_evidence"` |
| `provider` | `"deepseek"` \| `"ollama"` \| `null` | null si no hubo generación |
| `latency_ms` | int | medido en servidor |
| `request_id` | str | mismo de la pregunta |

- **Invariante**: `status="answered"` ⇒ `sources` no vacía y todas las citas válidas.
- **Invariante**: `status="no_evidence"` ⇒ `sources=[]` y texto de abstención sin cifras.

### Cita

| Campo | Tipo | Regla |
|---|---|---|
| `title` | str | igual al del documento |
| `source_type` | str | igual al del documento |
| `url` | str | igual al del documento |
| `slug` | str | igual al del documento |

- **Validez (FR-015)**: `url`, `title` y `source_type` coinciden con un documento del
  corpus cargado; el servidor la construye, no el LLM.

## Configuración

| Variable | Obligatoria | Defecto | Validación |
|---|---|---|---|
| `CORPUS_GOLD_DIR` | sí | — | directorio existente con `*.md` e `index.jsonl` |
| `QDRANT_PATH` | no | `.qdrant` | ruta escribible |
| `QDRANT_URL` | no | — | si existe, tiene prioridad sobre `QDRANT_PATH` |
| `QDRANT_COLLECTION` | no | `corpus_carvajal` | regex `^[a-z0-9_]+$` |
| `OLLAMA_BASE_URL` | no | `http://localhost:11434` | URL http(s) |
| `EMBEDDING_MODEL` | no | `nomic-embed-text` | no vacío |
| `LLM_PROVIDER` | no | `deepseek` | `deepseek` \| `ollama` |
| `DEEPSEEK_API_KEY` | si `LLM_PROVIDER=deepseek` | — | no vacía (nunca se registra) |
| `DEEPSEEK_BASE_URL` | no | `https://api.deepseek.com` | URL http(s) |
| `DEEPSEEK_MODEL` | no | `deepseek-chat` | no vacío |
| `OLLAMA_MODEL` | no | `qwen3:4b-instruct` | no vacío |
| `TOP_K` | no | `5` | entero 1..10 |
| `ACCEPTANCE_FILE` | no | — | JSON con lista de preguntas |

- **Arranque**: el servicio valida corpus, colección Qdrant y proveedor; si algo falta,
  error con la variable o ruta concreta (FR-008).

## Esquema del índice Qdrant

Colección `corpus_carvajal`:

```text
vectors: size=768, distance=Cosine
payload:
  slug: keyword
  url: keyword (indexado)
  title: text
  source_type: keyword (indexado)
  section: keyword
  chunk_index: integer
  text: text
  char_start: integer
  doc_hash: keyword
id: UUID v5 determinista de "slug:chunk_index"
```

- **Búsqueda**: `query_points(vector, limit=TOP_K, with_payload=True)`; se descartan
  resultados con score < 0.2 (umbral configurable en código) para reducir evidencia
  irrelevante; si no queda ninguno, `no_evidence`.

## Protocolos internos

```text
Embedder.embed(texts: list[str]) -> list[list[float]]      # 768 dims
Retriever.search(question: str, k: int) -> list[Fragment]  # ordenado por score
LLM.generate(messages: list[Message]) -> str               # texto plano
```

- Los tres son sustituibles por dobles en pruebas (R9).
- `Retriever` no importa `LLM` ni viceversa (principio IV).

## Reporte de aceptación

| Campo | Tipo | Regla |
|---|---|---|
| `generated_at` | datetime UTC | |
| `questions_total` | int | 40 |
| `answered_with_valid_citation` | int | ≥ 36 para SC-001 |
| `no_evidence` | int | rechazos explícitos |
| `invalid_citations` | int | debe ser 0 (SC-002) |
| `rows` | list[Row] | una por pregunta |

`Row`: `question`, `status`, `provider`, `latency_ms`, `sources` (urls), `citations_valid`
(bool), `expected_out_of_scope` (bool, si la pregunta es de control).

## Transiciones de estado de una consulta

```text
recibida → validada → recuperando → (con evidencia) generando → respondida
                                  └ (sin evidencia) ──────────→ abstención
generando → (fallo primario) → respaldo → respondida
generando → (fallo total) → error controlado
```

- `error` no expone trazas internas al usuario; devuelve mensaje accionable y
  `request_id` para correlación.
