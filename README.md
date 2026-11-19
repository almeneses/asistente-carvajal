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
- [Arquitectura del proyecto](#-arquitectura-del-proyecto)
- [Estructura del repositorio](#-estructura-del-repositorio)
- [Flujo de trabajo y contribución](#-flujo-de-trabajo-y-contribución)
- [Licencia](#-licencia)

## 🚧 Estado del proyecto

| Área | Estado |
|------|:------:|
| Estructura del repositorio y entorno (`uv`) | ✅ |
| Constitución técnica y gobernanza | ✅ |
| Diagrama de arquitectura objetivo | ✅ |
| Módulo de recuperación (corpus web) | ⏳ |
| Consulta sobre catálogo de empaques | ⏳ |
| Interfaz de chat con citación | ⏳ |
| Set de evaluación de respuestas | ⏳ |

> ⚠️ Fase actual: **diseño de la arquitectura**. El entrypoint `main.py` es un esqueleto
> funcional; el pipeline RAG todavía no está conectado. Roadmap en
> [`CONSTITUTION.md` §10](./CONSTITUTION.md#10-notas-y-tareas-pendientes).

## 🛠️ Stack tecnológico

| Categoría | Tecnología |
|-----------|------------|
| **Lenguaje** | Python 3.13+ |
| **Gestor de paquetes** | [`uv`](https://docs.astral.sh/uv/) |
| **Modo de proyecto** | Aplicación (`main.py` como entrypoint) |
| **Orquestación RAG** | Por definir (fase 1) |
| **Índice vectorial** | Por definir (fase 1) |
| **Proveedor LLM** | Por definir (fase 1) |
| **Interfaz de chat** | Por definir (fase 1) |
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

### Instalación

```bash
git clone https://github.com/almeneses/asistente-carvajal.git
cd asistente-carvajal

uv sync
uv run pre-commit install   # equivalente a: make dev
```

### Ejecución

```bash
uv run python main.py
```

### Verificación

```bash
make check   # lint + formato + tipos + pruebas
```

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

## 🗺️ Arquitectura del proyecto

Mapa de arquitectura **objetivo** (runtime) generado con
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
├── tests/                   # pruebas (pytest, patrón AAA)
├── docs/                    # documentación y arquitectura (JSON + HTML)
├── .github/                 # gobernanza: PR/issue templates, CI, Dependabot, labels
├── .opencode/rules/         # reglas para agentes (tgrep)
├── AGENTS.md                # contexto para agentes LLM
├── CONSTITUTION.md          # verdad central del proyecto
├── README.md                # este archivo
├── CONTRIBUTING.md          # guía de contribución
├── Makefile                 # automatización de tareas
├── pyproject.toml           # metadatos y dependencias (uv)
└── uv.lock                  # lockfile determinista
```

## 🤝 Flujo de trabajo y contribución

> 📘 La guía completa está en [`CONTRIBUTING.md`](./CONTRIBUTING.md). Resumen:

1. Crea una rama: `git checkout -b feat/nombre-corto`.
2. Desarrolla y verifica: `make check`.
3. Commitea con [Conventional Commits](https://www.conventionalcommits.org/): `git commit -m "feat: ..."`.
4. Abre un Pull Request con la plantilla oficial.
5. Mantén `CONSTITUTION.md` actualizado ante cambios arquitectónicos o tecnológicos.

## 📄 Licencia

Distribuido bajo la [Licencia MIT](./LICENSE).

---

<div align="center">
<sub>Hecho con ❤️ por almeneses</sub>
</div>
