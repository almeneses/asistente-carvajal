# Feature Specification: Pulido intermedio de interfaz

**Fase**: 6.1 (pulido antes de operación) · **Branch**: `feat/007-pulido-interfaz`

## Objetivo

Pulir la experiencia del asistente único sin cambiar el alcance funcional: animación de
Carva, móvil, compactación de tarjetas, accesibilidad y detalles visuales pendientes.

## Requisitos

- **FR-001**: Al primer envío, Carva debe animarse desde su posición central hasta el
  avatar pequeño del primer mensaje (vuelo + reducción), no solo encogerse en su fila.
- **FR-002**: `prefers-reduced-motion` debe mostrar el estado final sin animación.
- **FR-003**: El panel de chat debe comportarse bien en 390 px (sin scroll horizontal,
  compositor usable, presencia legible).
- **FR-004**: La tarjeta de recomendación debe compactarse a horizontal dentro del hilo y
  poder expandirse de nuevo.
- **FR-005**: La cabecera y el fondo no deben tapar contenido ni romper contraste.
- **FR-006**: Revisión de foco/teclado en inicio, chat, catálogo y confirmación.
- **FR-007**: Sin regresiones: 172 pruebas y CI en verde.

## Criterios de aceptación

- Captura de la transición (o evidencia de estados) y del chat en 390 px.
- La animación se ejecuta una sola vez y no bloquea el envío.
- La tarjeta compacta se expande con teclado.
- Sin desbordes horizontales en móvil.
