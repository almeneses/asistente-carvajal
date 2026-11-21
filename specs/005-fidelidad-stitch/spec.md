# Feature Specification: Fidelidad visual del flujo Stitch y solicitud de cotización

**Feature Branch**: `feat/005-fidelidad-stitch`

**Created**: 2026-11-20

**Status**: Draft

**Input**: User description: "La interfaz debe basarse en el prototipo de Stitch copiando sus pantallas y animaciones: bienvenida, conversación, asistente de empaques y la confirmación de solicitud que se minimiza al chat. La solicitud de cotización debe registrarse de verdad."

## Clarifications

### Session 2026-11-20

- Q: ¿Qué pantallas se copian? → A: El flujo completo: Bienvenida, Conversación, Asistente de Empaques y Confirmación/transición animada.
- Q: ¿La confirmación guarda algo? → A: Sí: se registra una solicitud real con código y se persiste en JSONL; luego se anima la minimización al chat.
- Q: ¿La voz debe funcionar? → A: Solo visual en esta fase: micrófono, barra y textos del prototipo, claramente etiquetados como no funcionales; la voz real llega después.
- Q: ¿Cómo se copia el diseño? → A: Se portan el HTML/CSS/JS del proyecto Stitch con Tailwind vendorizado localmente, conservando clases, componentes y animaciones; los datos se conectan a la app real.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Llegar a una bienvenida idéntica al prototipo (Priority: P1)

La persona abre el asistente y ve la pantalla de bienvenida de Stitch: cabecera con logo y
navegación, Carva saludando, las dos tarjetas grandes “Conversar” y “Empaques”, el botón de
escuchar bienvenida y el footer accesible.

**Why this priority**: es la primera impresión y define si la app “se siente” como el
prototipo aprobado.

**Independent Test**: abrir `/` y comparar con la captura de Bienvenida; las tarjetas
navegan al chat y al flujo de empaques.

**Acceptance Scenarios**:

1. **Given** la página de inicio, **When** se abre, **Then** se ven logo, Carva, título,
   subtítulo, dos tarjetas y footer como en el prototipo.
2. **Given** la tarjeta “Conversar”, **When** se pulsa, **Then** se abre el chat listo
   para escribir/hablar.
3. **Given** la tarjeta “Empaques”, **When** se pulsa, **Then** se abre el chat en modo
   empaques con su encabezado y resumen.
4. **Given** un lector de pantalla, **When** recorre la bienvenida, **Then** las tarjetas y
   acciones tienen roles y etiquetas correctas.

---

### User Story 2 - Conversar en la pantalla de chat del prototipo (Priority: P1)

La conversación replica el prototipo: cabecera, barra de micrófono (visual), burbujas de
Carva y de la persona, quick replies, campo de entrada con micrófono y botón Enviar, y el
footer.

**Why this priority**: es la pantalla principal de uso; debe verse y comportarse como el
diseño aprobado, no como una versión simplificada.

**Independent Test**: enviar una pregunta y comparar estructura/estilos con la captura de
Conversación; el streaming sigue funcionando.

**Acceptance Scenarios**:

1. **Given** el chat, **When** se envía una pregunta, **Then** se ve la burbuja del usuario
   y la respuesta de Carva con las mismas jerarquías visuales del prototipo.
2. **Given** una respuesta con fuentes, **When** termina, **Then** las citas aparecen como
   en el diseño y siguen siendo enlaces seguros.
3. **Given** la barra de voz, **When** se pulsa el micrófono, **Then** se muestra un aviso
   de “voz próximamente”, sin simular una grabación real.
4. **Given** una pantalla de 390 px, **When** se usa el chat, **Then** no hay desbordes y
   los targets siguen siendo táctiles.

---

### User Story 3 - Recibir la recomendación de empaques como en el prototipo (Priority: P2)

El flujo de empaques muestra el resumen de lo que la persona busca (qué empacar,
caliente/frío, cantidad, ubicación), la recomendación con tarjeta de producto, precio,
alternativa y el botón “Solicitar cotización”.

**Why this priority**: es el corazón comercial del prototipo y el punto de entrada a la
solicitud real.

**Independent Test**: pedir vasos para café caliente y comprobar resumen, tarjeta y CTA
contra la captura de Asistente de Empaques.

**Acceptance Scenarios**:

1. **Given** una consulta comercial, **When** el catálogo responde, **Then** se muestra el
   resumen de atributos y la recomendación con el formato del prototipo.
2. **Given** una recomendación con precio, **When** se pulsa “Solicitar cotización”,
   **Then** se abre la confirmación con los datos de esa recomendación.
3. **Given** una recomendación sin precio, **When** se intenta solicitar, **Then** se
   explica que no hay precio de referencia y no se inventa un total.

---

### User Story 4 - Confirmar y minimizar la solicitud al chat (Priority: P1)

Al solicitar la cotización se registra la solicitud, se muestra la tarjeta de confirmación
con el código, y tras una cuenta atrás (o al pulsar “Minimizar ahora”) la tarjeta se
transforma en una tarjeta compacta dentro del chat, como en el prototipo. La tarjeta se
puede expandir y volver a minimizar.

**Why this priority**: es la interacción diferenciadora que el usuario pidió copiar; sin
ella la fidelidad no existe.

**Independent Test**: solicitar una cotización y observar la transición completa; comparar
con las capturas de “Confirmación” y “Minimizando al chat”.

**Acceptance Scenarios**:

1. **Given** una recomendación, **When** se solicita la cotización, **Then** aparece la
   tarjeta completa con check, código, resumen, total y aviso de contacto.
2. **Given** la tarjeta completa, **When** transcurren 10 s o se pulsa “Minimizar ahora”,
   **Then** la tarjeta se anima hasta la versión compacta dentro del chat.
3. **Given** la tarjeta compacta, **When** se pulsa “Ver detalle completo”, **Then** se
   expande de nuevo con la misma animación inversa.
4. **Given** `prefers-reduced-motion`, **When** ocurre la transición, **Then** el cambio es
   inmediato, sin animación, y el foco se mantiene.
5. **Given** teclado, **When** se recorre la tarjeta, **Then** los botones son accesibles y
   el foco no queda atrapado.

---

### User Story 5 - Que la solicitud quede registrada de verdad (Priority: P2)

La solicitud enviada se guarda con un código legible y fecha, y el sistema puede leerla
después. No se guardan datos personales.

**Why this priority**: el prototipo muestra un código de solicitud; sin registro real la
confirmación sería decorativa.

**Independent Test**: enviar una solicitud y comprobar el código en la tarjeta y la línea
guardada en el archivo de solicitudes.

**Acceptance Scenarios**:

1. **Given** una cotización válida, **When** se solicita, **Then** se genera un código
   `OC-AAAA-MMDD-XXXX` y se persiste con SKU, cajas, total, moneda y fecha.
2. **Given** dos solicitudes iguales, **When** se envían, **Then** cada una recibe su
   propio código (no se sobrescribe).
3. **Given** un archivo de solicitudes, **When** se inspecciona, **Then** no contiene
   nombre, correo, teléfono, IP ni user-agent.

---

### Edge Cases

- **Doble clic en “Solicitar”**: se deshabilita el botón y se registra una sola solicitud.
- **Falla el registro**: la tarjeta muestra error accionable y permite reintentar; no
  muestra un código inventado.
- **Cuenta atrás en curso + navegación**: la tarjeta se minimiza o el flujo se cancela de
  forma consistente, sin dejar estados a medias.
- **Sin precio**: no se permite solicitar cotización de una referencia sin precio.
- **Voz pulsada**: aviso “próximamente”; nunca finge grabar.
- **Pantalla pequeña**: la tarjeta y el chat se apilan sin scroll horizontal.
- **Movimiento reducido**: sin animaciones esenciales; el estado final es el mismo.
- **Recarga**: la solicitud ya registrada no se pierde del archivo, pero la tarjeta de UI
  no se reconstruye (no hay historial persistente).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La bienvenida DEBE replicar la composición del prototipo: cabecera, Carva,
  dos tarjetas (“Conversar”, “Empaques”), botón de bienvenida y footer.
- **FR-002**: La pantalla de chat DEBE replicar cabecera, barra de micrófono, burbujas,
  quick replies, campo de entrada y footer del prototipo.
- **FR-003**: El flujo de empaques DEBE mostrar el resumen de atributos, la recomendación,
  la alternativa y el CTA “Solicitar cotización” del prototipo.
- **FR-004**: La confirmación DEBE mostrar check, código, resumen, total y aviso de
  contacto; la cuenta atrás de 10 s y el control “Minimizar ahora”.
- **FR-005**: La confirmación DEBE animarse a una tarjeta compacta dentro del chat y
  poder expandirse de nuevo.
- **FR-006**: El sistema DEBE respetar `prefers-reduced-motion` y mantener foco y estado
  final accesible.
- **FR-007**: El sistema DEBE registrar la solicitud con código `OC-AAAA-MMDD-XXXX`,
  SKU, cajas, total, moneda, ciudad y fecha en un JSONL local.
- **FR-008**: El sistema NO DEBE guardar nombre, correo, teléfono, IP ni user-agent.
- **FR-009**: El botón de solicitud DEBE deshabilitarse durante el envío y manejar errores
  con reintento.
- **FR-010**: La voz DEBE ser solo visual y anunciar “próximamente” al pulsarla.
- **FR-011**: El HTML/CSS/JS DEBE portarse desde el prototipo Stitch con Tailwind
  vendorizado, sin CDN en runtime.
- **FR-012**: El streaming SSE, Markdown seguro, feedback y catálogo de fases anteriores
  DEBEN seguir funcionando sin regresiones.
- **FR-013**: La interfaz DEBE mantener AA/AAA de contraste, foco visible y targets
  táctiles del diseño original.
- **FR-014**: La UI DEBE funcionar en 390, 768 y 1280 px sin scroll horizontal.
- **FR-015**: Los datos mostrados (producto, precio, total) DEBEN venir del catálogo real;
  no se inventan cifras ni disponibilidad.
- **FR-016**: El sistema DEBE exponer un endpoint de solicitud con validación y respuesta
  con el código generado.

### Key Entities *(include if feature involves data)*

- **Solicitud de cotización**: código, SKU, nombre de referencia, cajas, unidades, total,
  moneda, ciudad, fecha; sin PII.
- **Recomendación**: referencia, precio, cajas/total y alternativa mostrada.
- **Confirmación visual**: estado completo, estado minimizado/compacto y estado expandido.
- **Pantalla del prototipo**: bienvenida, conversación, empaques y confirmación con sus
  capturas de referencia.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Las 4 pantallas del flujo coinciden con las capturas de Stitch en una
  checklist visual de al menos 20 puntos por pantalla (composición, tipografía, colores,
  espaciados y componentes).
- **SC-002**: La transición completa → compacta → expandida funciona en el 100 % de las
  pruebas manuales y automatizadas de estructura.
- **SC-003**: El 100 % de las solicitudes registradas tienen código único, SKU, cajas,
  total, moneda y fecha; 0 campos de PII.
- **SC-004**: El 100 % de los errores de registro muestran reintento y no un código falso.
- **SC-005**: 0 regresiones en streaming, catálogo, feedback y citas (suites 1–4 verdes).
- **SC-006**: Sin scroll horizontal en 390, 768 y 1280 px.
- **SC-007**: La versión con movimiento reducido llega al mismo estado final sin animación.
- **SC-008**: Tailwind y los activos se sirven localmente; 0 peticiones a CDN en runtime.

## Assumptions

- El proyecto Stitch es la referencia visual y su HTML/CSS/JS se puede portar; el logo y
  los activos se obtienen de allí.
- La voz, el avatar animado completo y la selección de alternativa quedan como UI; no se
  implementa reconocimiento de voz en esta fase.
- Las solicitudes son de demostración operativa, no cotizaciones comerciales vinculantes;
  el texto debe aclarar “sin cobro previo” y “un asesor contactará”.
- No hay inventario ni disponibilidad; no se promete entrega.
- El flujo se mantiene en una sola página con vistas/estados, sin SPA.

## Out of Scope

- Voz funcional, lectura en voz alta real y micrófono activo.
- Persistencia de conversaciones o historial de solicitudes en la UI.
- Inventario, pagos, facturación, entrega y CRM.
- Nuevas fuentes de datos o cambios al catálogo/corpus.
- Autenticación multiusuario.
