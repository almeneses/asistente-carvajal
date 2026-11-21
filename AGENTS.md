# AGENTS — Asistente Carvajal

> Contexto del proyecto para sesiones con asistentes LLM (OpenCode, Antigravity,
> GitHub Copilot CLI, Claude Code, etc.). Trackeado al repositorio.

## Proyecto

Asistente conversacional con RAG sobre el corpus web y la documentación de empaques de Carvajal.

> Metodología: **Spec-Driven Development** con GitHub Spec Kit. Las capacidades nuevas se
> especifican en `specs/NNN-slug/` antes de implementarse.

> 📘 La verdad técnica central —propósito, stack, estructura, convenciones, decisiones y
> flujo de trabajo— vive en [`CONSTITUTION.md`](./CONSTITUTION.md). **Léela antes de
> operar.** Ante cualquier cambio arquitectónico, tecnológico o de proceso, actualízala
> en el mismo commit.

---

## Flujo Diario (commit + push)

```bash
# 1. Ver cambios
git status

# 2. Verificación completa (lint + formato + pruebas)
make check

# 3. Agregar y commitear (los hooks de pre-commit se ejecutan solos)
git add -A
git commit -m "tipo: mensaje descriptivo"

# 4. Subir a GitHub
git push
```

**Convención de commits:** [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — nueva funcionalidad
- `fix:` — corrección de bug
- `docs:` — documentación
- `refactor:` — refactorización
- `style:` — formato, linting (sin cambio de lógica)
- `test:` — pruebas
- `chore:` — mantenimiento o configuración

---

## Comandos del proyecto (`make`)

```bash
make help      # lista los objetivos disponibles
make dev       # entornos + hooks de pre-commit
make check     # lint + formato + pruebas
make ui-check  # pruebas de interfaz (streaming, Markdown, feedback, contraste)
make smoke     # health, readiness y métricas del servidor local
make quality-gates # umbrales de evaluación y catálogo
make lint      # Ruff (lint)
make format    # Ruff (formato)
make test      # pytest
make run       # chat web en http://127.0.0.1:8010
make index     # índice Qdrant del corpus
make acceptance        # aceptación de citas
make catalog-acceptance # aceptación del catálogo (130 preguntas)
make eval / make eval-e2e # evaluación de recuperación de la fase 2
```

> ⚠️ **Regla dura:** toda gestión de dependencias y entornos pasa por `uv`. Está
> **prohibido** `pip` y `requirements.txt`.

---

## Spec-Driven Development (Spec Kit)

Flujo para una capacidad nueva:

```text
/speckit.specify → /speckit.clarify → /speckit.plan → /speckit.tasks → /speckit.analyze → /speckit.implement
```

- Artefactos: `specs/NNN-slug/{spec,plan,tasks}.md`; índice en `specs/README.md`.
- Rama: `feat/NNN-slug` (la crea la extensión git; numeración secuencial).
- `plan.md` incluye un *Constitution Check* contra `.specify/memory/constitution.md`.
- `.specify/memory/constitution.md` es una **proyección**: la fuente única es
  `CONSTITUTION.md`. Actualiza ambas en el mismo commit.

---

## Búsqueda de código: `tgrep`

Si [`tgrep`](https://github.com/microsoft/tgrep) está instalado, úsalo para búsquedas de
código en lugar de `grep` o `find` (índice de trigramas en `.tgrep/`, ignorado por Git):

```bash
tgrep -- "patrón" .            # búsqueda regex (usa -- antes del patrón)
tgrep -F -- "simbolo" .        # coincidencia literal
tgrep -t py -- "def " .        # filtrar por tipo de archivo
tgrep -g "src/**" -- "kw" .    # filtrar por ruta
tgrep -l -- "import torch" .   # listar archivos coincidentes
tgrep index .                  # (re)indexar
```

En OpenCode la preferencia se aplica automáticamente mediante la regla
[`.opencode/rules/tgrep.md`](./.opencode/rules/tgrep.md).

---

## Estructura y convenciones

- `main.py` — punto de entrada de la aplicación.
- `assistant/` — configuración, corpus, índice Qdrant, recuperación, LLM y web.
  - `catalog/` — rama determinista de catálogo (loader, router, precios, materiales).
  - `ui/` — Markdown seguro, SSE, feedback y tokens visuales.
  - `quotes/` — solicitudes de cotización en JSONL (recálculo desde catálogo, sin PII).
  - `observability.py` — logs JSON, request_id, métricas y cabeceras.
  - `quality.py` — gates de calidad sobre los reportes de evaluación.
  - `templates/` y `static/` — Jinja/HTMX, tema, `chat.js`, DM Sans y logo.
- `scripts/` — indexación, aceptación, propuesta de ground truth y evaluación.
- `docs/design/DESIGN.md` — fuente de verdad visual (proyecto Stitch de Carvajal).
- `docs/operacion.md` — runbook: salud, logs, métricas, Docker, backup y rollback.
- `docs/despliegue.md` y `docs/evaluacion.md` — producción y evaluación continua.
- `assistant/static/stitch/` — Tailwind, iconos, CSS/JS y activos copiados del prototipo.
- `tests/` — pruebas con `pytest` (patrón AAA).
- `specs/` — especificaciones por feature (Spec Kit), indexadas en `specs/README.md`.
- `.specify/` — motor de Spec Kit (templates, scripts, memoria, extensiones).
- `docs/` — documentación, ADRs y notas de investigación.
- `CONSTITUTION.md` — fuente única de verdad.
- Estilo impuesto por **Ruff** (`line-length = 100`, comillas dobles).
- Idioma: UI, comentarios y commits en español; identificadores en inglés.
