# Quickstart: validar el corte vertical con citas

**Feature**: `specs/001-corte-vertical-citas` · **Fecha**: 2026-11-19

Guía para levantar el corte y comprobar, de punta a punta, que responde con citas
válidas y que se abstiene cuando no hay evidencia. No sustituye a las pruebas: es la
validación manual reproducible.

## Prerrequisitos

- Python 3.13 y `uv` instalados.
- Ollama en marcha con `nomic-embed-text` y un modelo de chat local:
  ```bash
  ollama list                 # debe incluir nomic-embed-text y qwen3:4b-instruct
  ollama serve                # si no está corriendo como servicio
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
uv run python main.py
# o: uv run uvicorn assistant.web:app --reload
```

Abrir `http://127.0.0.1:8000/`.

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

- Reporte con 40 filas y una fila por pregunta.
- `invalid_citations == 0`.
- `answered_with_valid_citation / 40 ≥ 0.9`.
- Código de salida 0.

## Calidad

```bash
make check     # Ruff + formato + ty + pytest
```

Resultado esperado: todo en verde, sin red ni servicios externos (las pruebas de
integración se saltan si faltan corpus/Ollama/Qdrant).

## Problemas frecuentes

- **`nomic-embed-text` no encontrado**: `ollama pull nomic-embed-text`.
- **Dimensión distinta a 768**: el índice está desactualizado; reconstruir con
  `--recreate`.
- **Qdrant remoto inaccesible**: revisar `QDRANT_URL` o quitarla para usar `.qdrant/`.
- **DeepSeek 401**: clave ausente o inválida; usar `LLM_PROVIDER=ollama` para continuar.
