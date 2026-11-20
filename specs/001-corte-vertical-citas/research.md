# Research: Corte vertical del asistente con citas del corpus

**Feature**: `specs/001-corte-vertical-citas` · **Fecha**: 2026-11-19

Este documento resuelve las decisiones técnicas del plan. No quedan
`NEEDS CLARIFICATION` en el *Technical Context*.

## R1. Orquestación RAG: cadena propia

- **Decisión**: implementar la cadena en `assistant/rag.py` con pasos explícitos
  (recuperar → construir prompt → generar → validar citas/abstenerse → responder), sin
  framework de agentes.
- **Rationale**: el flujo es lineal y corto; una cadena legible se prueba con dobles y se
  depura sin capas. Cumple el principio IV (recuperación y generación separadas) y evita
  una dependencia pesada en el primer corte.
- **Alternativas consideradas**: LangGraph (grafo de estado útil cuando haya ramas,
  reintentos y catálogo; hoy sería sobreingeniería), LlamaIndex (framework completo con
  mucho código no usado), agentes ReAct (innecesario: no hay herramientas ni bucles).
- **Revisión**: se reevalúa en la fase 3 (router con catálogo) o si aparecen reintentos
  correctivos y ramas múltiples.

## R2. Qdrant en modo embebido local, con URL remota opcional

- **Decisión**: `QdrantClient(path=".qdrant/")` por defecto; si `QDRANT_URL` está
  definida, se usa el servicio remoto. La colección se crea de forma idempotente al
  indexar y se valida al arrancar.
- **Rationale**: permite desarrollar y probar sin Docker ni servicio externo; el
  índice persiste entre ejecuciones. El modo remoto queda disponible para despliegue sin
  cambiar código.
- **Alternativas consideradas**: contenedor Qdrant obligatorio (fricción de arranque),
  modo `:memory:` (reindexar en cada arranque), FAISS local (descartado por la decisión
  de stack de la constitución).

## R3. Embeddings vía HTTP a Ollama

- **Decisión**: `assistant/embeddings.py` llama a `POST {OLLAMA_BASE_URL}/api/embed` con
  `model=nomic-embed-text` usando `httpx`; soporta lote y valida la dimensión (768).
- **Rationale**: reutiliza el modelo ya instalado y evita otra dependencia; la
  dimensión se comprueba antes de crear la colección para fallar temprano.
- **Alternativas consideradas**: paquete `ollama` (capa fina sobre lo mismo),
  `sentence-transformers` (descarga modelo y más peso), FastEmbed de Qdrant (modelo
  distinto al acordado).

## R4. LLM: DeepSeek primario y Ollama de respaldo

- **Decisión**: cliente único `assistant/llm.py` con dos adaptadores HTTP
  OpenAI-compatibles: DeepSeek `POST /chat/completions` (primario) y Ollama
  `POST /api/chat` (respaldo). `temperature=0`, `max_tokens=800`, timeout primario 8 s y
  respaldo 60 s (incluye la carga en frío del modelo local); el fallback se activa ante
  error de red, 5xx o timeout.
- **Rationale**: cumple FR-006 y SC-004; el timeout acota la latencia percibida por
  debajo de los 20 s de SC-005 en el camino normal y en el de respaldo.
- **Alternativas consideradas**: solo DeepSeek (rompe operación offline), solo Ollama
  (calidad menor y sin GPU local), SDK oficial de DeepSeek (dependencia extra sobre la
  misma API).

## R5. HTMX vendorizado

- **Decisión**: versionar `assistant/static/htmx.min.js` y servirlo desde FastAPI; la
  página usa `hx-post="/ask"`, `hx-target` y `hx-swap="beforeend"` para conservar el
  historial en el DOM.
- **Rationale**: la operación debe funcionar sin CDN ni internet durante una pregunta;
  el historial en memoria del DOM cumple FR-016 sin sesión de servidor.
- **Alternativas consideradas**: CDN de HTMX (dependencia de red), SPA con React
  (prohibido por la constitución: sin SPA), JavaScript propio (reinventa HTMX).

## R6. Configuración con variables de entorno y cargador mínimo de `.env`

- **Decisión**: `assistant/config.py` lee variables de entorno, carga `.env` si existe
  (sin sobrescribir lo ya definido) y valida en un `dataclass` con mensajes de error que
  nombran la variable y la ruta. No se añade `pydantic-settings`.
- **Rationale**: FR-007/FR-008 piden configuración externa y errores accionables; un
  cargador de ~20 líneas evita una dependencia y mantiene el arranque explícito.
- **Alternativas consideradas**: `pydantic-settings` (cómodo pero dependencia extra para
  una docena de variables), `python-dotenv` (otra dependencia para el mismo efecto).
- **Variables**: `CORPUS_GOLD_DIR`, `QDRANT_PATH`/`QDRANT_URL`, `QDRANT_COLLECTION`,
  `OLLAMA_BASE_URL`, `EMBEDDING_MODEL`, `LLM_PROVIDER`, `DEEPSEEK_API_KEY`,
  `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`, `OLLAMA_MODEL`, `TOP_K`, `ACCEPTANCE_FILE`.

## R7. Fragmentación y recuperación

- **Decisión**: fragmentos de 1000 caracteres con 200 de solape (herencia del corpus
  upstream), `k=5` fragmentos por pregunta y **recuperación híbrida**: hasta 200
  candidatos por coseno y reordenamiento `0.6 · coseno + 0.4 · solape léxico` (tallos de
  5 letras, sinónimos de dominio como empleado→colaborador y fundada→fundación). El
  payload guarda `slug`, `url`, `title`, `source_type`, `section`, `chunk_index` y `text`.
- **Rationale**: mantiene compatibilidad con el contrato del corpus y la convención ya
  documentada aguas arriba; sobre 24 documentos es suficiente y barato de reconstruir.
- **Alternativas consideradas**: fragmentos por sección Markdown (más fieles pero
  variables), 500/100 (más fragmentos y latencia), sin solape (pierde continuidad).
- **Rationale del híbrido**: nomic-embed-text degrada en español y no recuperaba
  documentos con términos poco frecuentes; el solape léxico sobre todo el corpus (123
  fragmentos) corrigió 5 de 30 preguntas sin cambiar el modelo ni añadir dependencias.
- **Alternativas consideradas**: solo coseno (67 % de respuestas aceptadas), reescritura
  de consulta con LLM (acopla recuperación y generación, viola el principio IV),
  embeddings multilingües (cambio de stack que requiere enmienda constitucional).
- **Revisión**: el umbral de 90 % se cumple (27/30) con el set actual; al crecer el
  corpus, el escaneo completo de candidatos debe pasar a búsqueda por servidor Qdrant.

## R8. Citas construidas en el servidor

- **Decisión**: el servidor arma `sources[]` a partir de los documentos recuperados
  (título, tipo, URL, slug) y el LLM solo devuelve texto con referencias `[n]`. Aunque el
  modelo no cite nada, las fuentes consultadas se muestran; si no hay evidencia
  recuperada, se responde con abstención.
- **Rationale**: garantiza que toda cita sea válida por construcción (FR-015) y evita
  parsear alucinaciones de enlaces del modelo.
- **Alternativas consideradas**: extraer enlaces del texto generado (frágil y
  verificable solo a posteriori), pedir JSON al modelo (más fallos de formato).

## R9. Pruebas: dobles de prueba y integración opcional

- **Decisión**: protocolos `Embedder`, `Retriever` y `LLM`; en unit tests se usan fakes
  deterministas. La prueba de integración real se marca y se salta si faltan
  `CORPUS_GOLD_DIR`, Ollama o Qdrant; CI ejecuta solo unitarias.
- **Rationale**: FR-014 y SC-007 exigen un reporte reproducible; CI no debe depender de
  red ni servicios. El script de aceptación usa la cadena real, no la web, para aislar
  el fallo.
- **Alternativas consideradas**: mocks de HTTP (más acoplados), VCR/cassettes (mantener
  grabaciones), integración obligatoria en CI (frágil y con secretos).

## R10. Defensa ante inyección de prompt

- **Decisión**: el prompt de sistema delimita el contexto como datos, ordena ignorar
  instrucciones dentro de documentos o pregunta y prohíbe usar conocimiento externo; el
  modelo no tiene herramientas ni acceso a red.
- **Rationale**: FR-012 y el edge case de manipulación; el corpus es de terceros y no se
  controla su contenido.
- **Alternativas consideradas**: filtros de palabras (evadibles), moderación externa
  (otra dependencia y latencia), confiar en el modelo (insuficiente).

## Dependencias nuevas (a añadir con `uv add`)

`fastapi`, `uvicorn`, `jinja2`, `httpx`, `qdrant-client`. Desarrollo: ninguno nuevo
(pytest ya presente). `uv.lock` se actualiza en el mismo commit.
