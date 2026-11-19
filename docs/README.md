# Documentación

Carpeta de documentación del proyecto. Convenciones sugeridas:

| Carpeta | Contenido |
|---------|-----------|
| `adr/` | *Architecture Decision Records*: decisiones grandes con contexto y consecuencias. |
| `spikes/` | Investigaciones técnicas acotadas (pregunta, timebox, hallazgo). |
| `research/` | Notas de investigación y comparativas. |
| `arquitectura.json` | Fuente tipada del mapa de arquitectura (Archify). |
| `arquitectura.html` | Diagrama interactivo autocontenido (generado; no se edita a mano). |

> El historial de decisiones resumido vive en
> [`../CONSTITUTION.md`](../CONSTITUTION.md); los ADR entran en detalle cuando la decisión
> lo amerita.

Reglas:

- Un documento, un tema.
- Fechas en ISO (`AAAA-MM-DD`).
- Enlaza cada documento desde la constitución o el README cuando sea relevante.
- No subas datos sensibles ni personales reales (usa *fixtures* sintéticos).
