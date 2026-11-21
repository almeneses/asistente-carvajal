# CONSTITUTION — Asistente Carvajal

> **Verdad central del proyecto.** Este documento define el propósito, el stack, la
> estructura, las convenciones y el flujo de trabajo de `Asistente Carvajal`. Si algo aquí
> contradice al código, el código manda **y este archivo se actualiza**.

> ⚠️ **Directiva de mantenimiento:** cada vez que se realicen cambios significativos
> (nuevas funcionalidades, cambios arquitectónicos, adición de clases/módulos o ajustes
> de tecnologías), **se debe actualizar este archivo en el mismo commit** para mantener
> la verdad central del proyecto bien documentada.

---

## 0. Identidad del proyecto

| Campo | Valor |
|-------|-------|
| **Nombre** | Asistente Carvajal |
| **Descripción** | Asistente conversacional con RAG sobre el corpus web y la documentación de empaques de Carvajal. |
| **Repositorio** | https://github.com/almeneses/asistente-carvajal |
| **Visibilidad** | Público 🌐 |
| **Metodología** | Spec-Driven Development con [GitHub Spec Kit](https://github.com/github/spec-kit) |
| **Versión** | 0.7.0 |
| **Autoría** | almeneses — almenesesp@gmail.com |
| **Licencia** | MIT |
| **Rama principal** | `main` |
| **Estado** | En construcción 🚧 |

## 1. Propósito y no-propósito

### Propósito

Ofrecer un asistente conversacional que responda preguntas sobre Carvajal recuperando
evidencia de dos fuentes curadas —el corpus web y la documentación de empaques— y
**cite la fuente** de cada afirmación para que la respuesta sea verificable.

### No-propósito

No es el pipeline de captura ni la curaduría del corpus (eso vive en el proyecto
`carvajal`), no es un motor de búsqueda general, no entrena ni ajusta modelos, no
sustituye la validación humana en decisiones comerciales y no almacena datos personales
de clientes.

## 2. Alcance

### Dentro del alcance

- Interfaz de chat para formular preguntas en lenguaje natural sobre Carvajal.
- Orquestación de recuperación aumentada (RAG): consulta → recuperación → generación.
- Recuperación sobre el corpus web curado y el catálogo de empaques.
- Respuestas con **trazabilidad de fuentes** (documento, sección y tipo de fuente).
- Configuración por variables de entorno (proveedor de LLM, rutas del corpus, índice).
- Suite de pruebas con `pytest` y verificación de tipos con `ty`.

### Fuera del alcance (por ahora)

- Captura, extracción y curación del corpus (proyecto aguas arriba).
- *Chunking* y construcción del índice como servicio propio (se consumirá un índice ya
  generado; ver roadmap).
- Despliegue productivo, autenticación multiusuario y facturación.
- *Fine-tuning* o entrenamiento de modelos.
- Preguntas sobre datos personales, credenciales o información no pública.

### Fases

| Fase | Estado | Entregable |
|------|--------|------------|
| 0. Estándar del repositorio (constitución, CI, gobernanza) | ✅ Hecha | Repo conforme a `jan-project-standard` |
| 1. Arquitectura objetivo y contrato del corpus | 🚧 En curso | `docs/arquitectura.*` + contrato en §5 |
| 2. Recuperación sobre el corpus web | ⬜ Pendiente | Módulo de recuperación + pruebas |
| 3. Consulta sobre documentación de empaques | ⬜ Pendiente | Índice del catálogo + pruebas |
| 4. Interfaz de chat y citación | ⬜ Pendiente | UI + respuestas con fuentes |
| 5. Evaluación y endurecimiento | ⬜ Pendiente | Set de preguntas, métricas y límites |

## 3. Stack técnico

| Categoría | Tecnología |
|-----------|------------|
| **Lenguaje** | Python 3.13+ |
| **Gestor de paquetes y entorno** | [`uv`](https://docs.astral.sh/uv/) |
| **Modo de proyecto** | Aplicación (`main.py` como punto de entrada, sin paquete instalable) |
| **Desarrollo dirigido por especificaciones** | [GitHub Spec Kit](https://github.com/github/spec-kit) (`specify` 1.4.3; integración OpenCode + extensión git) |
| **Orquestación RAG** | Cadena propia en `assistant/rag.py` (sin framework de agentes) |
| **Interfaz de chat** | FastAPI + HTMX (Jinja2 server-side, sin SPA) |
| **Índice vectorial** | Qdrant (1024 dims, coseno; embebido local por defecto, remoto por `QDRANT_URL`) |
| **Embeddings** | `bge-m3` vía Ollama (1024 dims; migrado en la fase 2 con evidencia) |
| **Proveedor LLM** | DeepSeek API con fallback a Ollama local |
| **Fuente de datos** | Corpus y catálogo por ruta configurable de solo lectura (`CORPUS_GOLD_DIR`, `CATALOG_DIR`) |
| **Streaming de respuestas** | SSE token a token (`POST /ask/stream`) con `POST /ask` de respaldo |
| **Identidad visual** | Tokens de `docs/design/DESIGN.md` (Stitch), DM Sans vendored y logo Carvajal |
| **Tipado estático** | [`ty`](https://github.com/astral-sh/ty) |
| **Testing** | [`pytest`](https://docs.pytest.org/) |
| **Linting / Formato** | [Ruff](https://docs.astral.sh/ruff/) |
| **Pre-commit** | [pre-commit](https://pre-commit.com) |
| **CI/CD** | [GitHub Actions](.github/workflows/ci.yml) |
| **Diagramas de arquitectura** | [Archify](https://github.com/tt-a1i/archify) (HTML interactivo en `docs/`) |
| **Dependencias automáticas** | [Dependabot](.github/dependabot.yml) |

> ⚠️ **Regla dura:** toda gestión de dependencias y entornos pasa por `uv`. Está
> **prohibido** `pip` y `requirements.txt`.

> 📝 **Decisiones de fase 1 (2026-11-19):** interfaz **FastAPI + HTMX**, índice
> **Qdrant** con `nomic-embed-text`, LLM **DeepSeek con fallback Ollama** y orquestación
> RAG con **cadena propia** (sin framework de agentes). El detalle está en
> `specs/001-corte-vertical-citas/plan.md`.

## 4. Estructura del repositorio

```text
asistente-carvajal/
├── main.py                  # punto de entrada de la aplicación
├── tests/                   # pruebas (pytest, patrón AAA)
├── specs/                   # especificaciones por feature (Spec Kit)
│   └── README.md            # índice de specs
├── docs/                    # documentación, ADRs e investigación
│   ├── arquitectura.json    # fuente tipada del mapa de arquitectura (Archify)
│   └── arquitectura.html    # diagrama interactivo autocontenido
├── .specify/                # motor de Spec Kit (templates, scripts, memoria)
├── .opencode/               # comandos /speckit.* y reglas para agentes (tgrep)
├── .github/                 # gobernanza (PR/issue templates, CI, Dependabot, labels)
├── AGENTS.md                # contexto para agentes LLM
├── CONSTITUTION.md          # este archivo — verdad central
├── README.md                # puerta de entrada pública
├── CONTRIBUTING.md          # guía de contribución
├── CODE_OF_CONDUCT.md       # código de conducta
├── Makefile                 # automatización de tareas
├── pyproject.toml           # metadatos y dependencias (uv)
├── uv.lock                  # lockfile determinista (versionado)
├── .python-version          # versión de Python fijada
└── .pre-commit-config.yaml  # hooks de calidad
```

## 5. Convenciones de código

- **Estilo:** [PEP 8](https://peps.python.org/pep-0008/) y [PEP 257](https://peps.python.org/pep-0257/),
  impuesto por **Ruff** (`line-length = 100`, comillas dobles).
- **Tipado:** anotaciones en funciones y firmas públicas.
- **Nomenclatura:** `snake_case` (funciones/variables), `PascalCase` (clases),
  `UPPER_CASE` (constantes).
- **Docstrings:** en módulos, clases y funciones públicas.
- **Pruebas:** `pytest` con el patrón **AAA** (*Arrange · Act · Assert*).
- **Idioma:** UI, documentación, comentarios y commits en español; identificadores de
  código en inglés.
- **Reglas propias:**
  - **Citar siempre:** una respuesta sin fuente identificable no se muestra como
    respuesta; se degrada a “no encontrado en el corpus”.
  - **El corpus es de solo lectura:** la aplicación consume el corpus y su índice, nunca
    los modifica ni los regenera en caliente.
  - **Cero secretos en el repo:** claves del proveedor de LLM y cadenas de conexión viven
    en `.env` (ignorado). Se versiona únicamente `.env.example`.
  - **Separar recuperación de generación:** el módulo de recuperación no depende del LLM
    y ambas piezas se prueban por separado.
  - **Contrato del corpus:** el consumidor recibe documentos Markdown con *front matter*
    (título, URL, tipo de fuente, fecha) e índice JSONL; cualquier cambio incompatible
    se documenta en esta constitución.

### Spec-Driven Development (Spec Kit)

- Toda capacidad nueva entra por `/speckit.specify` → `clarify` → `plan` → `tasks` →
  `analyze` → `implement`; los artefactos se versionan en `specs/NNN-slug/`.
- El `plan.md` incluye un *Constitution Check* contra `.specify/memory/constitution.md`.
- `.specify/memory/constitution.md` es una **proyección** de este documento (la raíz
  manda) y se sincroniza en el mismo commit que cualquier enmienda.
- Las specs no contradicen esta constitución; ante conflicto se corrige la spec o se
  enmienda la constitución, nunca ambas a medias.
- Toda spec nueva se numera de forma secuencial y se registra en `specs/README.md`.

## 6. Calidad y automatización

| Herramienta | Rol | Comando |
|-------------|-----|---------|
| `uv` | Entornos y dependencias | `uv sync` |
| Ruff | Lint + formato | `make lint` / `make format` |
| `ty` | Verificación de tipos | `make typecheck` |
| `pytest` | Pruebas | `make test` |
| `pre-commit` | Hooks antes de cada commit | `make pre-commit` |
| GitHub Actions | CI (pre-commit + ty + pytest) | `.github/workflows/ci.yml` |

- Ningún commit se salta los hooks (`--no-verify` está prohibido salvo causa justificada y documentada).
- La **CI debe estar en verde** antes de fusionar un Pull Request.
- Toda dependencia nueva entra con `uv add` / `uv add --dev` (nunca editando `uv.lock` a mano).

## 7. Repositorio y Git

- **Remoto (HTTPS):** `https://github.com/almeneses/asistente-carvajal.git`
  (autenticado con el credential helper de `gh`; el remoto SSH queda para cuando se
  repare la configuración SSH local — ver §11).
- **Rama principal:** `main`
- **Protección de `main`:** Pull Request obligatorio, check **`Calidad`** (CI) en verde y
  conversaciones resueltas; sin *force-push* ni borrado de la rama.
- **Estrategia de ramas:** `feat/...`, `fix/...`, `docs/...`, `refactor/...`, `test/...`, `chore/...`; integración vía Pull Request.
  Las features de Spec Kit usan `feat/NNN-slug` (la extensión git la crea con
  `branch_prefix: feat` y numeración secuencial).
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/) —
  `feat:`, `fix:`, `docs:`, `refactor:`, `style:`, `test:`, `chore:`.
- **Identidad git:** se resuelve con la configuración global (`user.name` /
  `user.email`); ver §11 para la alternativa automática por carpeta.

## 8. Flujo diario (commit + push)

```bash
# 1. Ver cambios
git status

# 2. Verificación completa (lint + formato + tipos + pruebas)
make check

# 3. Agregar y commitear (los hooks se ejecutan solos)
git add -A
git commit -m "tipo: mensaje descriptivo"

# 4. Subir a GitHub
git push
```

## 9. Historial de decisiones técnicas

| Fecha | Decisión | Motivo |
|-------|----------|--------|
| 2026-11-19 | Adoptar `uv` como gestor único de entornos y dependencias | Reproducibilidad; prohibido `pip`/`requirements.txt` |
| 2026-11-19 | Adoptar Ruff (lint + formato) y pre-commit | Calidad automatizada antes de cada commit |
| 2026-11-19 | Adoptar Conventional Commits | Historial legible y automatizable |
| 2026-11-19 | Adoptar licencia MIT y `CONSTITUTION.md` como fuente única de verdad | Claridad legal y operativa |
| 2026-11-19 | Arrancar como aplicación (`--app`, `main.py`) y no como paquete instalable | Es un servicio/producto, no una librería; simplifica el entrypoint |
| 2026-11-19 | Documentar la arquitectura objetivo con Archify y versionar el JSON fuente | Mapa de runtime legible antes de escribir código |
| 2026-11-19 | Diferir framework de UI, índice vectorial y proveedor de LLM | Evitar dependencias prematuras; se deciden en la fase 1 con evidencia |
| 2026-11-19 | Interfaz de chat con FastAPI + HTMX (Jinja2 server-side) | Coherencia con `carvajal`; UI sin SPA, fácil de probar |
| 2026-11-19 | Índice vectorial Qdrant con `nomic-embed-text` (768 dims, coseno) | Mismo stack del corpus; filtros por `source_type` y margen de crecimiento |
| 2026-11-19 | LLM DeepSeek API con fallback a Ollama local | Calidad con red/clave; operación offline y sin coste con modelos locales |
| 2026-11-19 | Consumo de corpus y catálogo por ruta configurable de solo lectura | No duplicar ni envejecer los datos; fixtures sintéticos en pruebas |
| 2026-11-19 | Orquestación RAG con cadena propia (`assistant/rag.py`), sin LangGraph | Flujo lineal de 4 pasos; menos dependencias y depuración directa. LangGraph se reevalúa en fase 3 o si aparecen ramas y reintentos |
| 2026-11-19 | Qdrant en modo embebido local (`.qdrant/`) por defecto; `QDRANT_URL` opcional | Desarrollo y CI sin servicio externo; el mismo cliente cubre el despliegue remoto |
| 2026-11-20 | Migrar embeddings a `bge-m3` (1024 dims) tras la fase 2 | Mejora de 10,3 pp en acierto@5 (0,966 vs. 0,862) en la matriz de 8 variantes; `bge-m3-500-hybrid` ganadora |
| 2026-11-20 | Rama de catálogo determinista (plantillas, sin LLM) y router por reglas | Cero precios/SKU inventados por construcción; router medido en 130 preguntas con 100 % de acierto |
| 2026-11-20 | `CATALOG_DIR` obligatorio para la app (solo lectura) | El catálogo se valida al arrancar; sin él la rama comercial no puede responder con fuentes |
| 2026-11-20 | Streaming por SSE con `POST` y `fetch`, no `EventSource` | La pregunta viaja en el cuerpo, se puede abortar y se conserva `/ask` síncrono |
| 2026-11-20 | Markdown seguro con `markdown-it-py` (HTML deshabilitado) | Evita XSS; el HTML final se renderiza en el servidor |
| 2026-11-20 | Feedback JSONL local sin PII | Permite mejorar sin base de datos ni datos personales |
| 2026-11-20 | Identidad visual basada en el proyecto Stitch `18086611055013390157` | Paleta azul/cian, DM Sans y accesibilidad AA/AAA; warning de texto oscurecido a `#8A5415` por contraste |
| 2026-11-19 | Si el modelo responde sin evidencia, la respuesta se normaliza a `no_evidence` y no se listan fuentes | Garantiza FR-004/SC-003 aunque el modelo local improvise |
| 2026-11-19 | Timeout de Ollama de 60 s (8 s en DeepSeek) | Cubre la carga en frío del modelo local sin romper la experiencia normal |
| 2026-11-19 | Usar remoto HTTPS con el credential helper de `gh` en lugar de SSH | La configuración SSH del sistema está rota (symlink de `/etc/ssh/ssh_config.d` con dueño `nobody`); ver §11 |
| 2026-11-19 | Publicar el repositorio como público | GitHub Free no permite proteger `main` en repos privados; la protección se habilita al hacerlo público |
| 2026-11-19 | Adoptar Spec Kit (specs versionadas por feature) | Trazabilidad requisito → plan → tareas y *Constitution Check* en cada plan |
| 2026-11-19 | Integración OpenCode + extensión git con `branch_prefix: feat` | Mantener la convención `feat/NNN-slug` y el flujo PR sin fricción |

## 10. Notas y tareas pendientes

- [x] Completar las secciones marcadas de este documento.
- [x] Configurar el remoto y proteger `main`.
- [x] Redactar la spec de fase 1 con `/speckit.specify` (spec, plan, tareas, análisis e implementación en `specs/001-corte-vertical-citas/`).
- [x] Decidir framework de UI, índice vectorial, embeddings y proveedor de LLM (fase 1).
- [x] Decidir la orquestación RAG: cadena propia (ver `specs/001-corte-vertical-citas/plan.md`).
- [x] Definir el contrato de consumo del corpus (rutas, *front matter*, índice JSONL): `specs/001-corte-vertical-citas/data-model.md` y `assistant/corpus.py`.
- [x] Implementar el módulo de recuperación y sus pruebas (fase 2): corte vertical de la spec 001.
- [x] Construir la interfaz de chat con citación de fuentes (fase 4): versión mínima en la spec 001.
- [x] Añadir `.env.example` con las variables configurables.
- [x] Fase 2: evaluación de recuperación y métricas de calidad (`specs/002-evaluacion-recuperacion/`); migración a `bge-m3` aprobada.
- [x] Fase 3: consulta del catálogo de empaques con precios y validación técnica (`specs/003-catalogo-empaques/`); aceptación 130/130.
- [x] Fase 4: experiencia de chat con streaming, Markdown, feedback e identidad (`specs/004-experiencia-chat/`); 154 pruebas.
- [ ] Fase 5: evaluación ampliada, operación, observabilidad y despliegue.
- [ ] Decidir el proveedor de LLM por defecto para nuevos usuarios (`deepseek` vs `ollama`).
- [x] Evaluar `bge-m3` frente a `nomic-embed-text` (fase 2: mejora de 10,3 pp en acierto@5).
- [ ] Registrar ADRs de embeddings, orquestación y modo Qdrant.

## 11. Configuración local (no trackear)

> Configuración específica de la máquina local. **NO incluir en commits.**

La identidad Git de este repositorio se resuelve con la configuración global:

```ini
[user]
    name = almeneses
    email = almenesesp@gmail.com
```

Opcionalmente, para que **todo** repositorio bajo una carpeta herede identidad y llave
SSH sin flags por proyecto:

```ini
# ~/.gitconfig
[includeIf "gitdir:~/projects/"]
    path = ~/.gitconfig-personal
```

```ini
# ~/.gitconfig-personal
[user]
    name = <Tu Nombre>
    email = <tu-correo>
[core]
    sshCommand = ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes
```

> Guía completa (macOS/Windows) en el skill `jan-project-standard` →
> `references/git-identity.md`.

Nota de esta máquina: el acceso SSH a GitHub falla porque
`/etc/ssh/ssh_config.d/20-systemd-ssh-proxy.conf` es un symlink con dueño `nobody`.
Por eso el remoto del proyecto usa HTTPS con el credential helper de `gh`. Cuando se
repare, se puede volver a SSH con:

```bash
git remote set-url origin git@github.com:almeneses/asistente-carvajal.git
```

Herramientas locales: `specify 1.4.3.dev0` (GitHub Spec Kit) y Node.js 24 para Archify.
