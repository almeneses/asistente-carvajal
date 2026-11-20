# Implementation Plan: Consulta del catálogo de empaques con precios y validación técnica

**Branch**: `feat/003-catalogo-empaques` | **Date**: 2026-11-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-catalogo-empaques/spec.md`

## Summary

Añadir una rama de catálogo al asistente: cargar en solo lectura las referencias, precios,
materiales y distribuidores de Carvajal Empaques (México y Colombia), enrutar cada pregunta
entre corpus documental y catálogo, validar material/temperatura contra el uso, resolver
precios con vigencia y calcular cajas/total cuando se indica cantidad. La rama de catálogo
es **determinista**: las respuestas se construyen con plantillas desde los datos, sin LLM,
para que ningún precio o SKU sea inventado. El LLM sigue usándose solo en la rama
documental (RAG existente); las preguntas mixtas muestran primero el catálogo y añaden el
corpus solo si hace falta.

## Technical Context

**Language/Version**: Python 3.13 (gestionado con `uv`)

**Primary Dependencies**: sin dependencias nuevas; `csv` y `json` de la librería estándar,
más los módulos existentes de RAG/LLM/Web.

**Storage**: CSVs del catálogo en `CATALOG_DIR` (solo lectura): `referencias.csv`,
`precios.csv`, `materiales.csv`, `distribuidores.csv` y `manifest.json`. Sin base de datos
nueva; el corpus/Qdrant de fases anteriores no cambia.

**Testing**: `pytest` con CSVs sintéticos en `tmp_path`; sin red. El set de aceptación usa
el `routing_questions.json` del proyecto de corpus (130 preguntas) más casos de precio
vencido/ausente y no coincidencia.

**Target Platform**: Linux/macOS de desarrollo; una instancia local.

**Project Type**: aplicación web existente; el catálogo es un módulo nuevo consumido por
la cadena de respuesta y por un script de aceptación.

**Performance Goals**: consulta de catálogo < 50 ms p95; pregunta mixta completa < 5 s p95
con DeepSeek (la parte documental es la que usa LLM).

**Constraints**: respuestas de catálogo deterministas y sin LLM; precios nunca inventados
ni convertidos; catálogo de solo lectura; mezcla de países/monedas prohibida; sin
disponibilidad ni inventario.

**Scale/Scope**: 200 referencias (98 MX, 102 CO), 29 precios COP, 5 materiales, 29
distribuidores, 130 preguntas de aceptación.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio / restricción | Verificación en el plan | Estado |
|---|---|---|
| I. La constitución manda | El plan no contradice la constitución; la decisión de rama determinista se registra en §9 al implementar. | ✅ |
| II. Sin fuentes no hay respuesta | Toda recomendación y precio cita ficha/fuente; sin coincidencia se responde explícitamente; el catálogo se construye desde datos. | ✅ |
| III. El corpus es el contrato | El catálogo se abre en solo lectura y se valida contra su manifiesto; nunca se escribe. | ✅ |
| IV. Recuperación separada de la generación | La rama de catálogo no invoca LLM (plantillas deterministas); la rama documental conserva el RAG actual. | ✅ |
| V. Cero secretos y cero datos personales | Solo datos comerciales públicos del catálogo; sin claves ni PII. | ✅ |
| Python 3.13 + `uv`, modo aplicación | Sin paquete instalable; `main.py` sigue siendo el entrypoint. | ✅ |
| FastAPI + HTMX, Qdrant, DeepSeek/Ollama | Se reutilizan; la UI solo añade secciones y citas. | ✅ |
| Ruff, `ty`, pytest, pre-commit, CI | Nuevas pruebas unitarias y `make check` como gate. | ✅ |

Sin violaciones; no se requiere *Complexity Tracking*.

## Project Structure

### Documentation (this feature)

```text
specs/003-catalogo-empaques/
├── plan.md                      # Este archivo
├── research.md                  # Fase 0: decisiones y alternativas
├── data-model.md                # Fase 1: entidades, reglas y validaciones
├── quickstart.md                # Fase 1: validación end-to-end
├── contracts/
│   ├── chat-catalog.md          # Fase 1: estructura de respuesta y citas
│   └── acceptance-cli.md        # Fase 1: script de aceptación y reporte
├── checklists/
│   └── requirements.md
└── tasks.md                     # Fase 2 (/speckit.tasks)
```

### Source Code (repository root)

```text
assistant/catalog/
├── __init__.py
├── models.py                    # Referencia, Precio, MaterialRule, Distribuidor, Consulta
├── loader.py                    # Carga/validación de CSVs y manifiesto
├── materials.py                 # Validación material/temperatura/uso
├── money.py                     # Precio, vigencia, cajas y total
├── router.py                    # Intención y extracción de atributos (determinista)
├── query.py                     # Búsqueda de referencias/precios/distribuidores
├── answers.py                   # Plantillas de respuesta y citas
└── acceptance.py                # Set de enrutamiento y métricas
scripts/
└── run_catalog_acceptance.py    # CLI del set de aceptación
tests/
├── catalog_fixtures.py
├── test_catalog_loader.py
├── test_catalog_router.py
├── test_catalog_materials.py
├── test_catalog_money.py
├── test_catalog_query.py
├── test_catalog_answers.py
└── test_catalog_acceptance.py
```

**Structure Decision**: subpaquete `assistant/catalog/` (importable con
`pythonpath = ["."]`), un script de aceptación y fixtures sintéticas. La app resuelve el
catálogo al arrancar y lo inyecta en el contexto; `assistant/web.py` añade la rama
comercial/mixta sin reemplazar la documental.

## Phase 0: Research

Salida en [research.md](research.md): router determinista, contrato de carga, reglas de
materiales, resolución de precio/vigencia, cálculo de cajas, respuestas por plantilla,
composición de preguntas mixtas, set de aceptación y configuración.

## Phase 1: Design

Salidas: [data-model.md](data-model.md), [contracts/chat-catalog.md](contracts/chat-catalog.md),
[contracts/acceptance-cli.md](contracts/acceptance-cli.md) y
[quickstart.md](quickstart.md).

## Re-evaluación del Constitution Check (post-diseño)

| Principio / restricción | Verificación post-diseño | Estado |
|---|---|---|
| II. Sin fuentes no hay respuesta | Las plantillas exigen fuente y vigencia; SC-002/SC-008 con cero invenciones. | ✅ |
| III. Catálogo de solo lectura | El loader valida y nunca escribe; el manifiesto se conserva. | ✅ |
| IV. Sin LLM en catálogo | `answers.py` construye texto desde datos; el router es determinista. | ✅ |
| UI | La sección de catálogo y la documental se distinguen en el parcial HTMX. | ✅ |
| CI sin servicios | Fixtures CSV; aceptación real manual. | ✅ |

## Complexity Tracking

> Sin violaciones de la constitución. La lógica de validación y precios es explícita y
> acotada a `assistant/catalog/`.
