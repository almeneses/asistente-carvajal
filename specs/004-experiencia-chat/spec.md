# Feature Specification: Experiencia de chat con identidad Carvajal

**Feature Branch**: `feat/004-experiencia-chat`

**Created**: 2026-11-20

**Status**: Draft

**Input**: User description: "Mejorar la experiencia de la interfaz del asistente: respuestas progresivas, formato legible, estados de carga y error, reinicio y feedback, accesibilidad móvil y rediseño visual con identidad de Carvajal."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver la respuesta mientras se construye (Priority: P1)

Una persona envía una pregunta y ve de inmediato que el asistente está trabajando; la
respuesta aparece de forma progresiva o por etapas claras (buscando, redactando,
fuentes) sin que la página se congele ni se pierda el historial.

**Why this priority**: la espera percibida es hoy el mayor defecto de la experiencia; una
respuesta que tarda sin señal parece rota aunque el resultado sea correcto.

**Independent Test**: enviar una pregunta y comprobar que en menos de un segundo hay una
señal visible de progreso y que la respuesta final no requiere recargar.

**Acceptance Scenarios**:

1. **Given** una pregunta enviada, **When** el asistente procesa, **Then** aparece un
   estado visible (“buscando…”, “redactando…”) antes de la respuesta final.
2. **Given** una respuesta larga, **When** llega, **Then** el texto se muestra de forma
   progresiva o por etapas sin bloquear la interacción.
3. **Given** una respuesta terminada, **When** la persona revisa, **Then** el historial
   previo sigue visible y la página conserva el foco.

---

### User Story 2 - Leer una respuesta clara y verificable (Priority: P1)

La respuesta usa formato legible (párrafos, listas, énfasis y tablas simples), separa la
sección de catálogo de la documental y muestra las fuentes de forma clara y segura.

**Why this priority**: una respuesta correcta pero ilegible no sirve; el formato es parte
del producto, no un adorno.

**Independent Test**: enviar una pregunta con listas y cifras y comprobar que el formato
se renderiza sin romper la página y que las fuentes siguen siendo enlaces seguros.

**Acceptance Scenarios**:

1. **Given** una respuesta con listas o énfasis, **When** se muestra, **Then** se renderiza
   con formato legible sin HTML inseguro.
2. **Given** una respuesta con cifras y enlaces, **When** se muestra, **Then** las cifras
   se leen bien y los enlaces abren en pestaña nueva con `rel` seguro.
3. **Given** una respuesta mixta, **When** se muestra, **Then** catálogo y corpus quedan
   visualmente separados con sus fuentes.

---

### User Story 3 - Controlar la conversación y recuperarse de errores (Priority: P2)

La persona puede reiniciar la conversación, reintentar una pregunta fallida sin volver a
escribirla, copiar una respuesta y usar atajos de teclado.

**Why this priority**: el chat actual no tiene reinicio ni reintento; un error obliga a
recargar y perder el contexto.

**Independent Test**: provocar un error, reintentar y comprobar que la pregunta se
conserva; reiniciar y comprobar que la conversación queda vacía y lista.

**Acceptance Scenarios**:

1. **Given** un error de respuesta, **When** la persona reintenta, **Then** se reenvía la
   misma pregunta y el error se reemplaza por el resultado.
2. **Given** una conversación con intercambios, **When** se reinicia, **Then** el historial
   queda vacío y el foco vuelve al campo de pregunta.
3. **Given** una respuesta, **When** la persona pulsa “copiar”, **Then** el texto se copia
   y se confirma visualmente.
4. **Given** el campo de pregunta, **When** se pulsa Enter, **Then** se envía; con
   Shift+Enter se inserta un salto de línea.

---

### User Story 4 - Dar feedback sobre la respuesta (Priority: P3)

La persona puede marcar una respuesta como útil o no útil y, opcionalmente, dejar un
comentario breve; el feedback no incluye datos personales y queda registrado para
mejorar el asistente.

**Why this priority**: sin señal de calidad no se puede priorizar qué mejorar en las
siguientes fases.

**Independent Test**: marcar una respuesta, recargar y comprobar que el feedback quedó
registrado sin datos personales.

**Acceptance Scenarios**:

1. **Given** una respuesta, **When** se marca útil/no útil, **Then** el estado del botón
   cambia y se confirma el registro.
2. **Given** un comentario opcional, **When** se envía, **Then** se guarda junto con la
   etiqueta y la pregunta, sin nombre ni correo.
3. **Given** una respuesta ya valorada, **When** se vuelve a valorar, **Then** se
   actualiza el registro sin duplicar.

---

### User Story 5 - Reconocer la identidad Carvajal y usar el chat en móvil (Priority: P2)

La interfaz refleja la identidad visual de Carvajal (logo, colores, tipografía) y funciona
en móvil, con contraste y foco visibles y sin depender del ratón.

**Why this priority**: el producto representa a Carvajal; una interfaz genérica reduce
confianza y el uso móvil es mayoritario en el contexto foodservice.

**Independent Test**: abrir en 360 px y con teclado; comprobar identidad, contraste,
foco y que no hay desbordes horizontales.

**Acceptance Scenarios**:

1. **Given** la página principal, **When** se abre, **Then** muestra logo/identidad
   Carvajal y una jerarquía visual coherente.
2. **Given** una pantalla de 360 px, **When** se usa el chat, **Then** no hay scroll
   horizontal y los botones son tocables.
3. **Given** navegación solo con teclado, **When** se recorre la página, **Then** el foco
   es visible y el orden es lógico.
4. **Given** un lector de pantalla, **When** llega una respuesta, **Then** se anuncia sin
   interrumpir al usuario.

---

### Edge Cases

- **Respuesta muy larga**: el área de conversación hace scroll sin desplazar la página
  completa ni perder el campo de pregunta.
- **Markdown malicioso**: HTML y scripts embebidos se escapan; nunca se ejecutan.
- **Error de red o proveedor**: se muestra un mensaje accionable y el botón de reintento.
- **Reinicio durante una respuesta en curso**: se cancela y la conversación queda limpia.
- **Feedback duplicado**: se actualiza el registro existente, no se duplica.
- **Tema oscuro del sistema**: la interfaz mantiene contraste y legibilidad.
- **Usuario sin logo/activos**: se usa la identidad aprobada por el proyecto y se
  documenta el origen de los activos.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE mostrar una señal de progreso visible en menos de un segundo
  tras enviar una pregunta.
- **FR-002**: La respuesta DEBE mostrarse de forma progresiva o por etapas sin bloquear la
  interacción ni perder el historial.
- **FR-003**: El sistema DEBE renderizar Markdown de forma segura (listas, énfasis, código,
  tablas simples), escapando HTML y scripts.
- **FR-004**: Los enlaces DEBEN abrir en pestaña nueva con `rel="noopener noreferrer"`.
- **FR-005**: Las respuestas mixtas DEBEN separar visualmente catálogo y corpus con sus
  fuentes.
- **FR-006**: El sistema DEBE permitir reiniciar la conversación sin recargar la página y
  devolver el foco al campo de pregunta.
- **FR-007**: El sistema DEBE ofrecer reintento de una pregunta fallida conservando el
  texto original.
- **FR-008**: El sistema DEBE permitir copiar una respuesta con confirmación visual.
- **FR-009**: El campo de pregunta DEBE enviar con Enter y permitir salto de línea con
  Shift+Enter.
- **FR-010**: El sistema DEBE permitir marcar cada respuesta como útil o no útil y un
  comentario opcional, sin datos personales, con registro persistente local.
- **FR-011**: La interfaz DEBE aplicar la identidad visual de Carvajal (logo, colores y
  tipografía aprobados) a la página y a los estados.
- **FR-012**: La interfaz DEBE ser usable en 360 px, sin scroll horizontal, con objetivos
  táctiles de al menos 44 px.
- **FR-013**: La interfaz DEBE cumplir WCAG 2.1 AA: contraste, foco visible, etiquetas y
  regiones `aria-live` para anunciar respuestas.
- **FR-014**: El sistema DEBE respetar `prefers-color-scheme` y mantener contraste en ambos
  temas.
- **FR-015**: Los cambios NO DEBEN alterar las respuestas, citas ni enrutamiento de las
  ramas documental y de catálogo (sin regresión).
- **FR-016**: Los activos visuales DEBEN tener origen y licencia documentados.

### Key Entities *(include if feature involves data)*

- **Conversación**: intercambios de la sesión actual (pregunta, respuesta, fuentes,
  estado); vive en el navegador y se pierde al recargar.
- **Estado de respuesta**: enviando, buscando, redactando, completada, error, cancelada.
- **Feedback**: etiqueta (útil/no útil), comentario opcional, id de la pregunta y fecha;
  sin PII.
- **Identidad visual**: logo, paleta, tipografía y componentes aprobados con su origen.
- **Activo de fuente**: enlace y metadatos de la cita mostrada.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de las preguntas muestra una señal de progreso en menos de 1 s.
- **SC-002**: Cero ejecuciones de HTML/script inyectado en las pruebas de Markdown (0 XSS).
- **SC-003**: El 100 % de los errores ofrece reintento y conserva la pregunta.
- **SC-004**: Reiniciar deja la conversación con 0 intercambios y el foco en el campo.
- **SC-005**: El 100 % de las respuestas valoradas registra etiqueta y fecha sin PII.
- **SC-006**: 0 problemas críticos de accesibilidad en las comprobaciones automáticas y
  contraste AA en los pares de color usados.
- **SC-007**: Sin scroll horizontal en 360, 768 y 1280 px.
- **SC-008**: Las suites de las fases 1–3 siguen en verde (sin regresión).

## Assumptions

- La interfaz sigue siendo una página FastAPI + HTMX; no se introduce una SPA.
- La conversación no se persiste en servidor; el historial vive en el DOM de la sesión.
- El feedback se guarda en un archivo local (JSONL) sin datos personales; no hay panel de
  administración en esta fase.
- La identidad visual usará activos oficiales si están disponibles; si no, una identidad
  inspirada aprobada por el proyecto, documentada en el repositorio.
- El streaming puede ser token a token o por etapas; el plan técnico decide el mecanismo.
- El tema oscuro se deriva de la paleta aprobada, no es un rediseño independiente.

## Out of Scope

- Autenticación, cuentas y persistencia de conversaciones en servidor.
- Voz, adjuntos de archivos e imágenes.
- Panel de administración de feedback o analítica avanzada.
- Aplicación móvil nativa o PWA instalable.
- Internacionalización más allá del español.
- Cambios de modelo, recuperación o catálogo (fases 1–3).
