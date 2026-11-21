# Documentación

Carpeta de documentación del proyecto. Convenciones sugeridas:

| Carpeta | Contenido |
|---------|-----------|
| `adr/` | *Architecture Decision Records* (índice en `adr/README.md`): decisiones grandes con contexto y consecuencias. |
| `design/` | Sistema de diseño (`DESIGN.md`) extraído del proyecto de Stitch; fuente visual de la UI. |
| `spikes/` | Investigaciones técnicas acotadas (pregunta, timebox, hallazgo). |
| `research/` | Notas de investigación y comparativas. |
| `arquitectura.json` | Fuente tipada del mapa de arquitectura (Archify). |
| `arquitectura.html` | Diagrama interactivo autocontenido (generado; no se edita a mano). |

> El diagrama se regenera con Archify y debe reflejar el runtime vigente (corpus, catálogo,
> streaming y feedback). Su recibo de entrega se versiona en `arquitectura.delivery.json`.

> Las especificaciones de features (Spec Kit) viven en [`specs/`](../specs/README.md);
> esta carpeta es para documentación transversal.

> El historial de decisiones resumido vive en
> [`../CONSTITUTION.md`](../CONSTITUTION.md); los ADR entran en detalle cuando la decisión
> lo amerita.

Reglas:

- Un documento, un tema.
- Fechas en ISO (`AAAA-MM-DD`).
- Enlaza cada documento desde la constitución o el README cuando sea relevante.
- No subas datos sensibles ni personales reales (usa *fixtures* sintéticos).
