<div align="center">

# Asistente Carvajal

**Asistente conversacional con RAG sobre el corpus web y la documentación de empaques de Carvajal.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/almeneses/asistente-carvajal/actions/workflows/ci.yml/badge.svg)](https://github.com/almeneses/asistente-carvajal/actions/workflows/ci.yml)
[![Managed with uv](https://img.shields.io/badge/managed%20with-uv-de5fe9.svg)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=precommit&logoColor=white)](./.pre-commit-config.yaml)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-fe5196.svg)](https://conventionalcommits.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](./CONTRIBUTING.md)

</div>

---

## 📖 Descripción general

Responder preguntas sobre Carvajal exige evidencia fiable: la información está repartida
entre el sitio web corporativo y la documentación de empaques, y un modelo sin contexto
tiende a inventar cifras. **Asistente Carvajal** recupera evidencia de dos fuentes curadas
—el corpus web y el catálogo de empaques— y genera respuestas que **citan la fuente** de
cada afirmación.

El repositorio contiene la **aplicación** (interfaz de chat, orquestación RAG y citación).
La captura y curaduría del corpus viven en un proyecto aguas arriba y se consumen como
entrada de solo lectura.

> 📘 La verdad técnica central —stack, decisiones, convenciones y flujo— vive en
> [`CONSTITUTION.md`](./CONSTITUTION.md). Es de lectura obligatoria antes de contribuir.

## 📑 Tabla de contenidos

- [Descripción general](#-descripción-general)
- [Estado del proyecto](#-estado-del-proyecto)
- [Stack tecnológico](#-stack-tecnológico)
- [Primeros pasos](#-primeros-pasos)
- [Calidad y automatización](#-calidad-y-automatización)
- [Desarrollo dirigido por especificaciones](#-desarrollo-dirigido-por-especificaciones-spec-kit)
- [Arquitectura del proyecto](#-arquitectura-del-proyecto)
- [Estructura del repositorio](#-estructura-del-repositorio)
- [Flujo de trabajo y contribución](#-flujo-de-trabajo-y-contribución)
- [Licencia](#-licencia)

## 🚧 Estado del proyecto

| Área | Estado |
|------|:------:|
| Estructura del repositorio y entorno (`uv`) | ✅ |
| Constitución técnica y gobernanza | ✅ |
| Diagrama de arquitectura del runtime | ✅ |
| Spec-Driven Development (Spec Kit) | ✅ |
| Decisiones de stack de la fase 1 | ✅ |
| Módulo de recuperación (corpus web) | ✅ |
| Interfaz de chat con citación | ✅ |
| Set de evaluación de respuestas | ✅ |
| Evaluación de recuperación (fase 2) | ✅ |
| Consulta del catálogo de empaques (fase 3) | ✅ |
| Experiencia de chat (fase 4) | ✅ |
| Fidelidad visual Stitch + solicitudes (fase 5) | ✅ |
| Asistente único y transición de Carva (fase 6) | ✅ |
| Pulido intermedio de interfaz (fase 6.1) | ✅ |
| Operación, observabilidad y despliegue (fase 7) | ✅ |
| Evaluación continua y despliegue productivo (fase 8) | ✅ |
| Decisiones y ADRs de arquitectura | ✅ |
| Operación multiusuario (fase 9) | ✅ |
| Cotizador refinado (fase 11) | ✅ |

> ✅ Fases 1–4 completas: corpus con citas, catálogo de empaques, evaluación de recuperación
> y chat accesible con streaming. Siguiente: fase 5 (operación, observabilidad y despliegue).
> Roadmap en [`CONSTITUTION.md` §10](./CONSTITUTION.md#10-notas-y-tareas-pendientes).

## 🛠️ Stack tecnológico

| Categoría | Tecnología |
|-----------|------------|
| **Lenguaje** | Python 3.13+ |
| **Gestor de paquetes** | [`uv`](https://docs.astral.sh/uv/) |
| **Modo de proyecto** | Aplicación (`main.py` como entrypoint) |
| **Especificaciones** | [GitHub Spec Kit](https://github.com/github/spec-kit) (`specify` + integraciones OpenCode y DSH) |
| **Orquestación RAG** | Cadena propia (`assistant/rag.py`), sin framework de agentes |
| **Interfaz de chat** | Asistente único texto/voz; Carva central → avatar; chat al 70%; fondo Carvajal; Tailwind/DM Sans/iconos locales |
| **Streaming de respuestas** | SSE token a token (`POST /ask/stream`) con `POST /ask` de respaldo |
| **Feedback** | JSONL local sin PII (`.cache/feedback.jsonl`) |
| **Solicitudes** | Revisión, contacto con consentimiento, detalle/PDF y correo opcional; JSONL local |
| **Observabilidad** | Logs JSON con `request_id`, `/readyz`, `/metrics` y cabeceras de seguridad |
| **Despliegue** | Dockerfile no-root, compose local/producción, Caddy con TLS y runbooks |
| **Calidad continua** | Gates sobre reportes de evaluación en CI (`make quality-gates`) |
| **Multiusuario** | Login con sesión firmada, cuotas por usuario y resumen admin (opcional) |
| **Índice vectorial** | Qdrant (1024 dims, coseno) |
| **Embeddings** | `bge-m3` vía Ollama (1024 dims) |
| **Proveedor LLM** | Ollama local por defecto; DeepSeek opcional (mejor calidad, requiere clave) |
| **Fuente de datos** | Corpus y catálogo por ruta configurable, solo lectura |
| **Catálogo de empaques** | CSV read-only (200 referencias, 29 precios COP, 29 distribuidores); rama determinista sin LLM |
| **Tipado estático** | [`ty`](https://github.com/astral-sh/ty) |
| **Testing** | [`pytest`](https://docs.pytest.org/) |
| **Linting / Formato** | [Ruff](https://docs.astral.sh/ruff/) |
| **Pre-commit** | [pre-commit](https://pre-commit.com) |
| **CI/CD** | [GitHub Actions](.github/workflows/ci.yml) |

## 🚀 Primeros pasos

### Requisitos previos

- [Python 3.13+](https://www.python.org/downloads/)
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
- [Git](https://git-scm.com/)
- [Ollama](https://ollama.com/) con `bge-m3` (embeddings) y un modelo de chat local
- Corpus gold y catálogo de empaques en rutas locales (solo lectura)

### Instalación

```bash
git clone https://github.com/almeneses/asistente-carvajal.git
cd asistente-carvajal

uv sync
uv run pre-commit install   # equivalente a: make dev

cp .env.example .env         # completar CORPUS_GOLD_DIR (y la clave si se usa DeepSeek)
```

### Indexación y ejecución

```bash
make index                     # construye el índice Qdrant desde el corpus
make run                       # arranca el chat en http://127.0.0.1:8010
make run PORT=8020             # o en otro puerto libre
make acceptance                # ejecuta el set de preguntas de aceptación
```

### Verificación

```bash
make check   # lint + formato + tipos + pruebas
```

### Convivencia con otros proyectos

- El chat usa el puerto **8010** por defecto (`make run PORT=...` para cambiarlo);
  no compite con los puertos de `carvajal` (Qdrant 6333/6334, Postgres 5433).
- El índice vive en `.qdrant/` (modo embebido, sin puerto). Solo un proceso puede
  abrirlo a la vez: detén `make run` antes de `make acceptance` y `make index`.
  Alternativa sin bloquear: apuntar `QDRANT_URL=http://127.0.0.1:6333` y usar una
  colección propia (`QDRANT_COLLECTION=asistente_carvajal`) en el Qdrant de `carvajal`.
- Ollama (11434) se comparte: un solo `ollama serve` sirve a ambos proyectos porque
  los dos usan `nomic-embed-text`. No hace falta levantar otro.

> ⚠️ **Regla del proyecto:** toda gestión de dependencias y entornos pasa por `uv`.
> Está **prohibido** `pip` y `requirements.txt`.

## ✅ Calidad y automatización

| Herramienta | Rol |
|-------------|-----|
| [`uv`](https://docs.astral.sh/uv/) | Entornos, dependencias y lockfile determinista. |
| [Ruff](https://docs.astral.sh/ruff/) | Lint y formato. |
| [`ty`](https://github.com/astral-sh/ty) | Verificación estática de tipos. |
| [pre-commit](https://pre-commit.com) | Hooks antes de cada commit. |
| [pytest](https://docs.pytest.org/) | Pruebas unitarias. |

| Comando | Descripción |
|---------|-------------|
| `make help` | Lista los objetivos disponibles. |
| `make dev` | `uv sync` + instala los hooks de pre-commit. |
| `make check` | Verificación completa (lint + formato + tipos + pruebas). |
| `make lint` / `make format` | Ruff. |
| `make test` | `pytest`. |
| `make run` | Arranca el chat web en el puerto `PORT` (8010 por defecto). |
| `make index` | Reconstruye el índice Qdrant del corpus. |
| `make acceptance` | Ejecuta las preguntas de aceptación y reporta citas. |
| `make catalog-acceptance` | Aceptación del catálogo (130 preguntas de enrutamiento). |
| `make ui-check` | Pruebas de streaming, Markdown, feedback y contraste. |
| `make smoke` | Health, readiness y métricas del servidor local. |
| `make quality-gates` | Umbrales de recuperación, citas, abstención y catálogo. |
| `uv run python scripts/hash_password.py` | Genera hashes para `AUTH_USERS`. |
| `make gt-propose` | Propone el ground truth de evaluación para revisión. |
| `make eval` | Matriz de recuperación de la fase 2. |
| `make eval-e2e` | Evaluación end-to-end de la variante ganadora. |

## 🧪 Desarrollo dirigido por especificaciones (Spec Kit)

Las capacidades nuevas se especifican **antes** de implementarse con
[GitHub Spec Kit](https://github.com/github/spec-kit). El flujo estándar:

| Paso | Comando | Artefacto |
|------|---------|-----------|
| 1 | `/speckit.specify "…"` | rama `feat/NNN-slug` + `specs/NNN-slug/spec.md` |
| 2 | `/speckit.clarify` | resuelve ambigüedades |
| 3 | `/speckit.plan` | `plan.md` con *Constitution Check* |
| 4 | `/speckit.tasks` | `tasks.md` |
| 5 | `/speckit.analyze` | coherencia entre artefactos |
| 6 | `/speckit.implement` | código y pruebas |

- El índice de specs vive en [`specs/README.md`](specs/README.md).
- `.specify/memory/constitution.md` es una **proyección** de `CONSTITUTION.md` (la
  raíz manda); ambas se actualizan en el mismo commit.
- Los comandos están en `.opencode/commands/speckit.*.md` y como skills en
  `.dsh/skills/speckit-*`; la extensión git crea ramas `feat/NNN-slug` con numeración
  secuencial.
- Feature 001 (corte vertical con citas): ver
  [`specs/001-corte-vertical-citas/`](specs/001-corte-vertical-citas/) (`spec.md`,
  `plan.md`, `tasks.md` y guía `quickstart.md`).

## 🗺️ Arquitectura del proyecto

Mapa de arquitectura **del runtime** generado con
[Archify](https://github.com/tt-a1i/archify): componentes, límites y flujo principal de una
consulta.

- 🔎 Diagrama interactivo: **[docs/arquitectura.html](docs/arquitectura.html)** (autocontenido; ábrelo en el navegador).
- 📦 Fuente tipada y versionada: [`docs/arquitectura.json`](docs/arquitectura.json).

> El JSON es la fuente; el HTML no se edita a mano. Para regenerarlo:
> `node bin/archify.mjs finalize architecture docs/arquitectura.json docs/arquitectura.html --quality showcase`.
> Requiere la skill [Archify](https://github.com/tt-a1i/archify) instalada.

## 📂 Estructura del repositorio

```text
asistente-carvajal/
├── main.py                  # punto de entrada de la aplicación
├── assistant/               # configuración, corpus, índice, RAG, LLM y web
│   ├── catalog/             # rama determinista del catálogo
│   ├── quotes/              # solicitudes de cotización (JSONL, sin PII)
│   ├── ui/                  # Markdown seguro, SSE, feedback y tokens
│   ├── templates/           # página de chat y parciales
│   └── static/              # stitch/ (Tailwind, CSS, JS, iconos, assets) y chat.js
├── scripts/                 # indexación del corpus y aceptación
├── tests/                   # pruebas (pytest, patrón AAA)
├── specs/                   # especificaciones por feature (Spec Kit)
│   └── README.md            # índice de specs
├── docs/                    # documentación, arquitectura y runbook de operación
├── Dockerfile               # imagen reproducible (uv, no root, healthcheck)
├── deploy/                  # compose productivo, Caddyfile y ejemplo de secretos
├── docker-compose.yml       # app + Ollama + volúmenes
├── .specify/                # motor de Spec Kit (templates, scripts, memoria)
├── .opencode/               # comandos /speckit.* y reglas para agentes (tgrep)
├── .github/                 # gobernanza: PR/issue templates, CI, Dependabot, labels
├── AGENTS.md                # contexto para agentes LLM
├── CONSTITUTION.md          # verdad central del proyecto
├── README.md                # este archivo
├── CONTRIBUTING.md          # guía de contribución
├── Makefile                 # automatización de tareas
├── pyproject.toml           # metadatos y dependencias (uv)
├── .env.example             # variables de configuración (sin valores reales)
└── uv.lock                  # lockfile determinista
```

## 🤝 Flujo de trabajo y contribución

> 📘 La guía completa está en [`CONTRIBUTING.md`](./CONTRIBUTING.md). Resumen:

1. Si es una capacidad nueva, espéranla con `/speckit.specify` (crea la rama
   `feat/NNN-slug` y `specs/NNN-slug/spec.md`) y completa `clarify` → `plan` →
   `tasks` → `analyze`. Regístrala en [`specs/README.md`](specs/README.md).
2. Desarrolla y verifica: `make check`.
3. Commitea con [Conventional Commits](https://www.conventionalcommits.org/): `git commit -m "feat: ..."`.
4. Abre un Pull Request con la plantilla oficial (CI `Calidad` en verde).
5. Mantén `CONSTITUTION.md` y su proyección `.specify/memory/constitution.md`
   sincronizadas ante cambios arquitectónicos o tecnológicos.

## 📄 Licencia

Distribuido bajo la [Licencia MIT](./LICENSE).

---

<div align="center">
<sub>Hecho con ❤️ por almeneses</sub>
</div>
