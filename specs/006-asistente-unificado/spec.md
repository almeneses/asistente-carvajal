# Feature Specification: Asistente único, chat al 70% y transición de Carva

**Feature Branch**: `feat/006-asistente-unificado`

**Created**: 2026-11-20 · **Status**: Draft

## Clarifications

- Q: ¿Se mantienen “Conversar” y “Empaques” como modos? → A: No. Un solo asistente atiende cualquier solicitud por texto o voz.
- Q: ¿Cómo es la presencia de Carva? → A: Central en el inicio; al dar la primera respuesta se reduce animadamente a un avatar pequeño dentro del hilo.
- Q: ¿La recomendación de empaques? → A: Inline en el chat; tras más interacción se compacta a una barra horizontal dentro del hilo.
- Q: ¿Tamaño del chat? → A: El panel de conversación ocupa el 70% de la pantalla en escritorio.
- Q: ¿Cabecera y fondo? → A: Cabecera simplificada (logo, Asistente Carvajal, Ayuda, Línea Directa) y fondo temático Carvajal Colombia.
- Q: ¿Estilo? → A: Limpio, con menos elementos, fiel al sistema Stitch.

## User Scenarios

### US1 · Inicio unificado (P1)
La persona abre el asistente y ve a Carva central, un único compositor texto/voz y sugerencias; no elige modo.
- **Given** el inicio, **When** escribe o dicta, **Then** el mismo asistente procesa la solicitud.
- **Given** una sugerencia, **When** la pulsa, **Then** se envía al mismo hilo.

### US2 · Transición de Carva (P1)
Al enviar, Carva pasa de presencia central a avatar pequeño junto a la respuesta.
- **Given** el inicio del chat, **When** llega la primera respuesta, **Then** Carva se reduce con una animación breve.
- **Given** `prefers-reduced-motion`, **Then** el cambio es instantáneo.

### US3 · Chat al 70% (P1)
El panel de conversación ocupa el 70% de la pantalla, con hilo desplazable y compositor fijo.
- **Given** escritorio, **Then** el panel mide ~70vw y ~70vh, centrado.
- **Given** móvil, **Then** ocupa el ancho disponible sin scroll horizontal.

### US4 · Recomendación inline y compacta (P2)
La recomendación aparece dentro del hilo; al continuar la conversación se compacta a una barra horizontal inline.
- **Given** una respuesta de catálogo, **Then** se ve la tarjeta inline con CTA.
- **Given** un mensaje posterior, **Then** la tarjeta anterior se compacta en una fila dentro del hilo.

### US5 · Cabecera, fondo y limpieza (P2)
Cabecera simplificada y fondo Carvajal Colombia; sin banners redundantes.
- **Given** cualquier pantalla, **Then** la cabecera solo tiene logo, Asistente Carvajal, Ayuda y Línea Directa.
- **Given** el fondo, **Then** incluye motivos Carvajal (montañas del Valle, cuaderno, libros y cuadrados del logo) sin romper contraste AAA.

## Requirements

- **FR-001**: Un solo flujo; eliminar tarjetas/modos “Conversar” y “Empaques”.
- **FR-002**: `/chat/empaques` redirige a `/chat`.
- **FR-003**: Carva central en inicio; avatar pequeño tras la primera respuesta.
- **FR-004**: Transición animada (~350 ms) con respeto a `prefers-reduced-motion`.
- **FR-005**: Panel de chat al 70vw × 70vh en escritorio; fluido en móvil.
- **FR-006**: Recomendación inline; compactación horizontal inline al continuar.
- **FR-007**: Cabecera simplificada y sin banners redundantes.
- **FR-008**: Fondo temático Carvajal Colombia (montañas, cuaderno, libros, cuadrados del logo) sutil y legible.
- **FR-009**: Cabecera y fondo accesibles: contraste AA/AAA, sin interferir con el texto.
- **FR-010**: Conservar SSE, Markdown, citas, feedback, solicitudes y confirmación animada.
- **FR-011**: Sin CDN; activos locales.
- **FR-012**: Sin regresiones en las suites 1–5.

## Success Criteria

- **SC-001**: 0 referencias a modos “Conversar/Empaques” en la UI.
- **SC-002**: Transición central→pequeña funciona y respeta movimiento reducido.
- **SC-003**: Panel de chat ≈70% de la pantalla en 1280 px; sin scroll horizontal en 390 px.
- **SC-004**: Tarjeta inline se compacta inline tras el siguiente mensaje.
- **SC-005**: Cabecera y fondo cumplen contraste y no tapan contenido.
- **SC-006**: 100% de pruebas previas verdes.
