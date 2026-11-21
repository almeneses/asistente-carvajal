# Constitución de Asistente Carvajal — proyección Spec Kit

> Proyección de la constitución del proyecto para el flujo de Spec-Driven Development.
> **La fuente única de verdad es [`CONSTITUTION.md`](../../CONSTITUTION.md) en la raíz del
> repositorio**: este archivo resume sus principios y su estado técnico para que los
> comandos de Spec Kit (`/speckit.*`) los verifiquen. Si hay discrepancia, manda la raíz.
>
> **Sincronizada**: 2026-11-20, con `CONSTITUTION.md` v1.0.0 (decisiones de §9 hasta esa
> fecha).

## Principios fundamentales

### I. La constitución manda

Todo cambio arquitectónico, tecnológico o de proceso se registra en `CONSTITUTION.md` en
el mismo commit. Las especificaciones y los planes de `specs/` no pueden contradecirla; si
lo hacen, se corrige la spec o se enmienda la constitución, nunca ambas a medias.

### II. Sin fuentes no hay respuesta (NO NEGOCIABLE)

Toda afirmación se sustenta en el corpus o en el catálogo de empaques y se cita. Una
respuesta sin fuente identificable se degrada a “no encontrado en el corpus”; el asistente
nunca presenta conocimiento externo ni cifras inventadas como si fueran del corpus.

### III. El corpus es el contrato

La aplicación consume el corpus web curado (capa `gold`, solo lectura) y el catálogo de
empaques como entradas; nunca los modifica, ni los regenera en caliente, ni consulta la
web durante una pregunta. Cambiar el formato consumido es un cambio incompatible y se
documenta en la constitución.

### IV. Recuperación separada de la generación

El módulo de recuperación no depende del proveedor de LLM y ambos se prueban por separado.
La interfaz es FastAPI + HTMX, el índice es Qdrant, el proveedor es DeepSeek con
fallback a Ollama y la orquestación es una cadena propia en `assistant/rag.py`.

### V. Cero secretos y cero datos personales

Claves, cadenas de conexión y configuración local viven en `.env` (ignorado); solo se
versiona `.env.example`. No se almacenan ni citan datos personales de clientes, y los
fixtures de prueba son sintéticos.

## Restricciones técnicas

- Python 3.13+ gestionado con `uv`; prohibido `pip` y `requirements.txt`.
- Aplicación (modo `--app`): `main.py` es el entrypoint; sin paquete instalable.
- Interfaz: FastAPI + Jinja2; asistente único texto/voz, chat al 70%, Carva central→avatar
  y fondo Carvajal; Tailwind, DM Sans e iconos locales; SSE y confirmación animada.
- Recuperación: Qdrant 1024 dims/coseno con `bge-m3` vía Ollama; índice embebido local
  por defecto (`QDRANT_PATH`) o remoto (`QDRANT_URL`).
- LLM: DeepSeek API con fallback a Ollama local; sin claves en el repo. Si el modelo
  no sustenta la respuesta, se normaliza a `no_evidence` sin fuentes.
- Orquestación: cadena propia (recuperar → prompt → generar → citar), sin framework.
- Datos: corpus y catálogo por ruta configurable, solo lectura; fixtures sintéticos.
- Catálogo: rama determinista (sin LLM) con router de reglas; precios con vigencia y sin
  conversión de moneda.
- Feedback y solicitudes: JSONL local sin PII; Markdown seguro con `markdown-it-py`
  (HTML deshabilitado).
- Calidad obligatoria: Ruff, `ty`, `pytest`, pre-commit, CI `Calidad` y `make check`.
- `main` protegida: PR obligatorio, check `Calidad` estricto, sin force-push ni borrado.
- Arquitectura objetivo versionada con Archify en `docs/arquitectura.json` (fuente) y
  `docs/arquitectura.html` (generado).
- Especificaciones versionadas en `specs/NNN-slug/`; ramas `feat/NNN-slug`.

## Flujo de desarrollo

1. `/speckit.specify` → rama `feat/NNN-slug` y `spec.md` (qué y para quién, sin tecnología).
2. `/speckit.clarify` → resuelve ambigüedades antes de planear.
3. `/speckit.plan` → `plan.md` con *Constitution Check* contra esta proyección.
4. `/speckit.tasks` → `tasks.md` accionable por historia de usuario.
5. `/speckit.analyze` → coherencia entre spec, plan y tareas antes de implementar.
6. `/speckit.implement` → código y pruebas; cerrar con `make check`.
7. Commit convencional → PR → CI `Calidad` en verde → squash & merge.

Toda spec nueva se numera de forma secuencial y se registra en el índice `specs/README.md`.

## Gobernanza

- **Enmiendas:** PR que modifique `CONSTITUTION.md` y, en el mismo commit, esta proyección
  (actualizando la línea de sincronización).
- **Cumplimiento:** el plan de cada feature incluye una sección *Constitution Check*; toda
  violación se justifica o se elimina antes de implementar.
- **Versión:** 1.0.0 — 2026-11-20, sincronizada con `CONSTITUTION.md` de la raíz.
