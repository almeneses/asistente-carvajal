# Plan: Pulido intermedio

- **Animación**: Web Animations API en `chat.js`. Se captura el rect de `#carva-presence`,
  se crea un clon `position: fixed` y se anima a `translate + scale` hasta el avatar del
  primer intercambio; al terminar se revela el avatar y se oculta la presencia central.
  `prefers-reduced-motion` salta directo al estado final.
- **Móvil**: ajustes en `stitch.css` (@media 480 px), panel 100%, toolbar compacta,
  compositor apilado y tipografía legible.
- **Compactación**: la clase `.is-compact` ya existe; se asegura foco/teclado y se
  prueba el ciclo compactar → expandir.
- **Accesibilidad**: foco visible, `aria-live`, `aria-busy`, contraste; revisión manual
  con teclado. Sin dependencia nueva.
- **Pruebas**: estructura de animación (clon, reduced motion, avatar), móvil (clases) y
  regresión completa.
