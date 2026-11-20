# Implementation Plan: Corte vertical del asistente con citas del corpus

**Branch**: `feat/001-corte-vertical-citas` | **Date**: 2026-11-19 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-corte-vertical-citas/spec.md`

## Summary

Construir el primer corte funcional del asistente: una página de chat en español que
recibe una pregunta, recupera evidencia del corpus web curado (solo lectura), genera una
respuesta con DeepSeek y respaldo local en Ollama, y muestra las fuentes citadas
(título, tipo y enlace). Si no hay evidencia suficiente responde "no encontrado". Incluye
indexación del corpus en Qdrant, configuración por variables de entorno y un script que
ejecuta las ~40 preguntas de aceptación y emite un reporte de citación.

El enfoque técnico: cadena RAG propia (sin framework de agentes), embeddings
`nomic-embed-text` vía Ollama, Qdrant en modo embebido local (o remoto por URL), HTMX
vendorizado para el chat y pruebas unitarias con dobles de prueba (sin red ni LLM real).

## Technical Context

**Language/Version**: Python 3.13 (gestionado con `uv`)

**Primary Dependencies**: FastAPI, Uvicorn, Jinja2, `httpx`, `qdrant-client`; desarrollo:
pytest, Ruff, `ty`, pre-commit

**Storage**: Qdrant con embeddings de 768 dimensiones y distancia coseno. Por defecto en
modo embebido persistente en `.qdrant/` (ignorado por Git); si `QDRANT_URL` está definida,
se usa el servicio remoto. El corpus `gold` se lee del sistema de archivos en modo solo
lectura.

**Testing**: `pytest` con `TestClient` de Starlette para la capa web; pruebas unitarias
con `Embedder` y `LLM` falsos (sin red); prueba de integración opcional que se salta si
faltan corpus, Qdrant u Ollama.

**Target Platform**: Linux/macOS de desarrollo, ejecución local de una sola instancia.

**Project Type**: aplicación web de un solo proyecto; `main.py` es el entrypoint (modo
`--app`), sin paquete instalable.

**Performance Goals**: respuesta completa en menos de 20 s p95 en el entorno local
(SC-005); recuperación en menos de 1 s sobre ~200 fragmentos.

**Constraints**: corpus y catálogo de solo lectura; sin secretos en el repositorio;
arranque falla con mensaje accionable si falta configuración, corpus o Qdrant; interfaz y
respuestas en español; modo offline funcional con Ollama.

**Scale/Scope**: 24 documentos del corpus (≈ 60 000 caracteres), ~200 fragmentos, 40
preguntas de aceptación, un usuario concurrente.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio / restricción | Verificación en el plan | Estado |
|---|---|---|
| I. La constitución manda | El plan no contradice `CONSTITUTION.md`; las decisiones nuevas se registran en §9 al implementar (orquestación). | ✅ |
| II. Sin fuentes no hay respuesta | El prompt exige responder solo con contexto recuperado; el servidor construye las citas desde los metadatos del corpus; sin evidencia se responde "no encontrado" (FR-003/004, SC-002/003). | ✅ |
| III. El corpus es el contrato | El corpus se abre en solo lectura; la indexación escribe únicamente en Qdrant, nunca en el corpus; el formato consumido se documenta en `data-model.md`. | ✅ |
| IV. Recuperación separada de la generación | `Retriever`/`Embedder` y `LLM` son protocolos independientes, con dobles de prueba y pruebas separadas. | ✅ |
| V. Cero secretos y cero datos personales | `.env` ignorado, `.env.example` versionado; fixtures sintéticos; sin PII en corpus ni citas. | ✅ |
| Python 3.13 + `uv`, modo aplicación | `pyproject.toml` con dependencias en `uv`; `main.py` como entrypoint. | ✅ |
| FastAPI + HTMX, Qdrant 768 dims/nomic, DeepSeek + Ollama | Stack exacto de la constitución; HTMX vendorizado para operar sin CDN. | ✅ |
| Ruff, `ty`, pytest, pre-commit, CI, `make check` | Se añaden pruebas y se amplía `src` de Ruff para `assistant/` y `scripts/`; `make check` sigue siendo el gate. | ✅ |

Sin violaciones: no se requiere *Complexity Tracking*.

## Project Structure

### Documentation (this feature)

```text
specs/001-corte-vertical-citas/
├── plan.md              # Este archivo
├── research.md          # Fase 0: decisiones técnicas y alternativas
├── data-model.md        # Fase 1: entidades, esquema de payload y validaciones
├── quickstart.md        # Fase 1: guía de validación end-to-end
├── contracts/
│   └── http-api.md      # Fase 1: contrato de la interfaz web y del reporte
├── checklists/
│   └── requirements.md  # Calidad de la especificación
└── tasks.md             # Fase 2 (/speckit.tasks)
```

### Source Code (repository root)

```text
main.py                      # Entrypoint: arranca Uvicorn con la app
assistant/
├── __init__.py
├── config.py                # Configuración desde entorno + .env; validación al arrancar
├── corpus.py                # Carga gold/*.md + index.jsonl (solo lectura)
├── chunking.py              # Fragmentación 1000/200 con metadatos
├── embeddings.py            # Embedder sobre Ollama (/api/embed)
├── index.py                 # Qdrant: crear colección, upsert, búsqueda
├── retrieval.py             # Recuperador: pregunta → fragmentos con evidencia
├── prompting.py             # Prompt de sistema/usuario y formato de citas
├── llm.py                   # DeepSeek (OpenAI-compatible) + fallback Ollama
├── rag.py                   # Cadena: recuperar → prompt → generar → citar/abstenerse
├── acceptance.py            # Set de aceptación y validación de citas
├── web.py                   # FastAPI, rutas y plantillas
├── templates/index.html     # Chat (Jinja2)
├── templates/_exchange.html # Parcial HTMX: respuesta + fuentes
└── static/htmx.min.js       # HTMX vendorizado
scripts/
├── index_corpus.py          # Construye el índice Qdrant desde el corpus
└── run_acceptance.py        # Ejecuta el set de aceptación y emite reporte
tests/
├── conftest.py              # Fixtures: documentos sintéticos, embedder y LLM falsos
├── test_config.py
├── test_chunking.py
├── test_corpus.py
├── test_retrieval.py
├── test_rag.py
├── test_web.py
└── test_acceptance.py
.env.example                 # Variables documentadas (sin valores reales)
.qdrant/                     # Índice local embebido (ignorado por Git)
```

**Structure Decision**: un solo proyecto de aplicación. La lógica RAG vive en el paquete
local `assistant/` (importable con `pythonpath = ["."]`, sin instalación); `main.py` solo
lee configuración y arranca Uvicorn. Los scripts de operación (`scripts/`) son ejecutables
con `uv run python scripts/...`. Esta estructura respeta el modo aplicación de la
constitución y evita una capa `src/` instalable.

## Phase 0: Research

Salida en [research.md](research.md). Resuelve: orquestación RAG, modo de Qdrant,
embedding vía HTTP, cliente LLM y fallback, HTMX vendorizado, carga de `.env`, estrategia
de pruebas y contrato de citas.

## Phase 1: Design

Salidas: [data-model.md](data-model.md), [contracts/http-api.md](contracts/http-api.md) y
[quickstart.md](quickstart.md).

## Re-evaluación del Constitution Check (post-diseño)

| Principio / restricción | Verificación post-diseño | Estado |
|---|---|---|
| II. Sin fuentes no hay respuesta | El contrato HTTP exige `sources[]` con título/tipo/url y define la respuesta de abstención; el reporte de aceptación valida metadatos. | ✅ |
| III. Corpus de solo lectura | `data-model.md` separa "corpus de entrada" de "índice" y prohíbe escrituras en el corpus. | ✅ |
| IV. Separación recuperación/generación | Los protocolos `Embedder`, `Retriever` y `LLM` quedan definidos en `data-model.md`. | ✅ |
| V. Sin secretos | `.env.example` lista variables sin valores; el contrato no expone credenciales. | ✅ |

## Complexity Tracking

> No hay violaciones de la constitución; sección intencionalmente vacía.
