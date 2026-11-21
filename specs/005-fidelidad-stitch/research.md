# Research: Fidelidad visual del flujo Stitch

**Feature**: `specs/005-fidelidad-stitch` · **Fecha**: 2026-11-20

## R1. Copiar el HTML/CSS/JS del prototipo

- **Decisión**: portar cada pantalla desde los HTML descargados de Stitch, conservando
  estructura, clases Tailwind, estilos inline y funciones JS. Sustituir solo los datos
  estáticos por Jinja y conectar los eventos a la app.
- **Rationale**: es la única forma de lograr fidelidad real; reinterpretar con nuestro CSS
  ya demostró que no basta.
- **Alternativas**: iframe del prototipo (no integra backend), reescribir con CSS propio
  (menos fiel y más trabajo).

## R2. Tailwind, fuentes e iconos locales

- **Decisión**: vendorizar `tailwindcss` (Play CDN) en `assistant/static/stitch/tailwind.js`
  y la configuración inline extraída del prototipo; DM Sans ya está vendorizada; Material
  Symbols en woff2 local; imágenes de Carva/producto/logo descargadas a
  `assistant/static/stitch/assets/`.
- **Rationale**: cero peticiones a CDN (SC-008), funciona offline y conserva el diseño.
- **Alternativas**: CDN (rompe offline y añade latencia), compilar Tailwind (más pasos).

## R3. Animación de confirmación

- **Decisión**: portar `minimizeToChat()`, `expandFullCard()`, `startCountdown()` y
  `toggleFullCard()` del prototipo, adaptados a IDs/clases de nuestras plantillas y a la
  cuenta atrás de 10 s. Añadir `prefers-reduced-motion` para cambiar de estado sin animar.
- **Rationale**: la transición es el requisito diferencial; el prototipo ya trae la lógica.
- **Alternativas**: animación CSS pura sin JS (no maneja countdown ni foco), dejar solo
  tarjeta estática (no cumple).

## R4. Registro real de solicitudes

- **Decisión**: endpoint `POST /quotes` que recibe SKU, cajas, ciudad y referencia; el
  servidor recalcula unidades/total desde el catálogo, genera `OC-AAAA-MMDD-XXXX` y añade
  una línea JSONL. Sin nombre, correo, teléfono, IP ni user-agent.
- **Rationale**: evita totales manipulados y cumple “solicitud real” sin PII.
- **Alternativas**: guardar lo que manda el cliente (inseguro), solo localStorage (no
  analizable), sin persistencia (no cumple).

## R5. Rutas y estados

- **Decisión**: `/` bienvenida; `/chat` conversación; `/chat/empaques` empaques; la
  confirmación es un estado de la página de chat (overlay/tarjeta) tras `POST /quotes`.
- **Rationale**: mantiene una sola app y URLs compartibles sin SPA.
- **Alternativas**: SPA con router (fuera de alcance), todo en `/` (peor navegación).

## R6. Voz solo visual

- **Decisión**: micrófono y barra copiados; al pulsar muestran “Voz próximamente” con
  `aria-live`; no se simula grabación.
- **Rationale**: cumple el alcance y no engaña.

## R7. Pruebas y accesibilidad

- **Decisión**: pruebas de store/endpoint, estructura de plantillas (IDs/funciones/clases),
  ausencia de URLs CDN y respeto a `prefers-reduced-motion` (presencia de la media query y
  rama JS); checklist manual contra capturas; axe/Lighthouse.
- **Rationale**: sin navegador en CI se valida el contrato de la animación y la fidelidad
  se revisa manualmente contra las capturas.
