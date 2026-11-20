# Especificaciones (Spec Kit)

Índice de las capacidades del proyecto, especificadas antes de implementarse con
[GitHub Spec Kit](https://github.com/github/spec-kit). La verdad técnica (stack,
convenciones y decisiones) vive en [`CONSTITUTION.md`](../CONSTITUTION.md); aquí vive el
**qué** y el **porqué** de cada feature.

## Convenciones

- Numeración secuencial de tres dígitos: `NNN-slug-descriptivo`.
- Rama asociada: `feat/NNN-slug` (la crea la extensión git de Spec Kit).
- El directorio `specs/NNN-slug/` contiene como mínimo `spec.md`; el flujo completo añade
  `plan.md`, `tasks.md` y, si aplica, `research.md`, `data-model.md`, `contracts/` y
  `quickstart.md`.
- Toda spec se registra en esta tabla al crearse y se actualiza su estado al fusionarse.
- Una spec no puede contradecir `CONSTITUTION.md`: ante conflicto se corrige la spec o se
  enmienda la constitución, nunca ambas a medias.

## Índice

| Nº | Feature | Estado | Spec |
|----|---------|--------|------|
| 001 | Corte vertical del asistente con citas del corpus | ✅ fusionada | [spec.md](001-corte-vertical-citas/spec.md) |
| 002 | Evaluación de recuperación y métricas de calidad | ✅ fusionada | [spec.md](002-evaluacion-recuperacion/spec.md) |

> Estados: 📝 borrador · 🔎 en clarificación · 📐 planeada · ⚙️ en implementación · ✅ fusionada.
