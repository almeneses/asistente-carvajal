# Quickstart: validar el corte vertical con citas

**Feature**: `specs/001-corte-vertical-citas` · **Fecha**: 2026-11-19

Guía para levantar el corte y comprobar, de punta a punta, que responde con citas
válidas y que se abstiene cuando no hay evidencia. No sustituye a las pruebas: es la
validación manual reproducible.

## Prerrequisitos

- Python 3.13 y `uv` instalados.
- Ollama en marcha con `bge-m3` (embeddings) y un modelo de chat local:
  ```bash
  ollama pull bge-m3
  ollama list                 # debe incluir bge-m3 y qwen3:4b-instruct
  ```
- Corpus curado en una ruta local (por ejemplo, el repositorio hermano):
  ```bash
  ls ../carvajal/data/gold/index.jsonl
  ```
- Clave de DeepSeek (opcional si se opera solo con Ollama).

## Configuración

```bash
cp .env.example .env
# Editar CORPUS_GOLD_DIR y, si aplica, DEEPSEEK_API_KEY
```

Variables mínimas:

```dotenv
CORPUS_GOLD_DIR=/ruta/a/carvajal/data/gold
LLM_PROVIDER=deepseek            # o "ollama" para operar sin clave
DEEPSEEK_API_KEY=...             # solo si LLM_PROVIDER=deepseek
```

## Instalación e índice

```bash
uv sync
uv run python scripts/index_corpus.py --recreate
```

Resultado esperado: crea la colección en `.qdrant/` (o en `QDRANT_URL`), reporta
documentos y fragmentos indexados, y termina con código 0.

## Arranque

```bash
make run                 # puerto 8010 por defecto
make run PORT=8020       # o el que esté libre
```

Abrir `http://127.0.0.1:8010/`.

## Validación manual (SC-001 a SC-007)

| Paso | Acción | Resultado esperado |
|---|---|---|
| 1 | Abrir `/` y preguntar "¿Qué es Carvajal y a qué sectores se dedica?" | Respuesta en español con al menos una fuente (título, tipo, enlace) |
| 2 | Comprobar que el enlace abre el documento citado y el título coincide | Cita válida (FR-015) |
| 3 | Hacer una segunda pregunta sin recargar | El intercambio anterior sigue visible (FR-016) |
| 4 | Preguntar "¿Cuánto cuesta la caja de vasos de 12 oz?" | Abstención explícita; sin cifras ni fuentes inventadas (FR-004/013) |
| 5 | Detener Ollama y hacer una pregunta con `LLM_PROVIDER=ollama` | Error accionable con `request_id`, sin trazas internas |
| 6 | Arrancar con `CORPUS_GOLD_DIR` inexistente | Falla al arrancar nombrando la ruta (FR-008) |
| 7 | `GET /healthz` | `200` con `corpus_documents`, `collection` y `provider` |

## Aceptación automatizada

```bash
export ACCEPTANCE_FILE=../carvajal/data/questions.json
uv run python scripts/run_acceptance.py --json-out /tmp/aceptacion.json
```

Resultado esperado:

- Reporte con 30 filas y una fila por pregunta.
- `invalid_citations == 0`.
- `answered_with_valid_citation / 30 ≥ 0.9`.
- Código de salida 0.

## Evidencia de la implementación (2026-11-19)

Validación ejecutada sobre el corpus real (`../carvajal/data/gold`) con Ollama local y
DeepSeek como proveedor primario:

- Índice: **24 documentos → 123 fragmentos** en Qdrant embebido.
- `/healthz`: `200` con `corpus_documents: 24`, colección `corpus_carvajal` y proveedor.
- Chat: respuesta con fuentes citadas y abstención explícita sin evidencia.
- Pruebas: **49 pasan** con `pytest`; `make check` en verde.
- Aceptación (30 preguntas): **27/30 (90 %) con cita válida, 0 citas inválidas, 3
  abstenciones** (año/ciudad de fundación, contacto y balance al cierre de 2024).
- Ruta local completa (Ollama, 2 preguntas): 2/2 con cita válida; el set completo con
  modelo local en CPU excede el tiempo razonable de una sesión.

## Calidad

```bash
make check     # Ruff + formato + ty + pytest
```

Resultado esperado: todo en verde, sin red ni servicios externos (las pruebas de
integración se saltan si faltan corpus/Ollama/Qdrant).

## Problemas frecuentes

- **`bge-m3` no encontrado**: `ollama pull bge-m3`.
- **Dimensión distinta a 1024**: el índice está desactualizado; reconstruir con
  `--recreate`.
- **Qdrant remoto inaccesible**: revisar `QDRANT_URL` o quitarla para usar `.qdrant/`.
- **DeepSeek 401**: clave ausente o inválida; usar `LLM_PROVIDER=ollama` para continuar.
- **`address already in use`**: otro proceso usa el puerto; `make run PORT=8020`.
- **`Storage folder .qdrant is already accessed`**: el servidor tiene abierto el índice;
  detén `make run` antes de `make acceptance` o usa `QDRANT_URL` remoto.
- **Ollama ya está corriendo**: no lances otro `ollama serve`; comparte el de 11434.
