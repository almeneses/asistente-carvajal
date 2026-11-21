# ADR 0005 — Activos visuales, voz y animación de Carva

- **Estado**: aceptada
- **Fecha**: 2026-11-21
- **Contexto**: el prototipo Stitch usa fotos de producto y una voz funcional que no
  tienen activos oficiales accesibles (URLs 403) ni alcance aprobado.
- **Decisiones**:
  1. **Sin fotos de producto inventadas**: la tarjeta muestra nombre, material, unidades,
     precio y ficha; si llega el catálogo fotográfico oficial se incorpora.
  2. **Voz visual**: micrófono y estados del prototipo con aviso “próximamente”; la voz
     funcional (Web Speech/ASR) queda para una fase con permisos y navegadores definidos.
  3. **Animación de Carva**: transición central → avatar de 450 ms con
     `prefers-reduced-motion`; se acepta como definitiva salvo ajuste de marca.
- **Consecuencias**: no se simula disponibilidad ni se inventan fotos; se evita prometer
  voz que no funciona. El backlog queda cerrado hasta nueva evidencia/activos.
