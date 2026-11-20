# Feature Specification: Corte vertical del asistente con citas del corpus

**Feature Branch**: `feat/001-corte-vertical-citas`

**Created**: 2026-11-19

**Status**: Draft

**Input**: User description: "Corte vertical del asistente de preguntas sobre Carvajal, con citas verificables. El corpus web curado ya existe aguas arriba; una persona pregunta en lenguaje natural y el asistente responde usando solo evidencia de ese corpus, citando la fuente. Es la fase 1 del roadmap; el catálogo de empaques no entra todavía."

## Clarifications

### Session 2026-11-19

- Q: ¿Debe la respuesta mostrar un extracto textual de la evidencia, además del título, tipo y enlace de la fuente? → A: Solo cita con enlace; sin extractos textuales en la respuesta.
- Q: Si el servicio de recuperación del corpus no está disponible, ¿debe la aplicación negarse a arrancar o arrancar degradada? → A: Falla al arrancar, con un mensaje que indica qué revisar.
- Q: ¿Cuántas preguntas debe tener el set de aceptación de este corte? → A: El set completo del proyecto de corpus (~40 preguntas), adaptado.
- Q: ¿Qué hace que una cita cuente como válida al evaluar las respuestas? → A: El enlace pertenece a un documento del corpus y coinciden título y tipo de fuente con sus metadatos.
- Q: Durante una misma sesión de chat, ¿la página debe mostrar los intercambios anteriores o solo la última respuesta? → A: Historial de la sesión en memoria, sin persistir al recargar ni entre sesiones.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preguntar y recibir una respuesta citada (Priority: P1)

Una persona interesada en Carvajal (prensa, inversionistas, colaboradores) escribe una
pregunta en español en un chat web y recibe una respuesta construida únicamente con
evidencia del corpus curado, acompañada de las fuentes consultadas.

**Why this priority**: es la razón de ser del producto. Sin respuesta citada y
verificable no hay asistente confiable; todo lo demás es accesorio a este recorrido.

**Independent Test**: se puede probar publicando una pregunta cuya respuesta esté
explícitamente en un documento del corpus y verificando que la respuesta coincide con
ese documento y que la cita incluye título, tipo de fuente y enlace.

**Acceptance Scenarios**:

1. **Given** una pregunta cubierta por el corpus, **When** la persona la envía desde el
   chat, **Then** recibe una respuesta en español que cita al menos una fuente con
   título, tipo de fuente (oficial o tercero) y enlace.
2. **Given** una sesión con intercambios previos, **When** la persona envía otra
   pregunta, **Then** los intercambios anteriores siguen visibles en la misma página.
3. **Given** una respuesta con varias fuentes, **When** la persona revisa las citas,
   **Then** cada enlace corresponde a un documento del corpus y el texto citado aparece
   en él.
4. **Given** una pregunta que menciona dos temas del corpus, **When** el asistente
   responde, **Then** cubre ambos temas o indica cuál no pudo sustentar.

---

### User Story 2 - No inventar cuando no hay evidencia (Priority: P2)

Una persona pregunta algo que el corpus no cubre (por ejemplo, el precio de un empaque)
y el asistente se lo dice explícitamente, sin cifras ni hechos inventados.

**Why this priority**: la confianza es el activo principal del asistente; una respuesta
inventada es peor que un "no lo sé".

**Independent Test**: se puede probar enviando preguntas cuyo tema no aparece en el
corpus y verificando que la respuesta declare la ausencia de evidencia y no incluya
datos no sustentados.

**Acceptance Scenarios**:

1. **Given** una pregunta fuera del alcance del corpus, **When** la persona la envía,
   **Then** el asistente responde que no encontró evidencia suficiente y no inventa
   cifras, fechas ni nombres.
2. **Given** una pregunta dentro del alcance pero sin coincidencias relevantes, **When**
   el asistente busca, **Then** informa que no pudo sustentar la respuesta en el corpus.
3. **Given** una respuesta negativa, **When** la persona la lee, **Then** entiende qué
   sí puede responder el asistente y qué no.

---

### User Story 3 - Operar el asistente con configuración explícita y degradación (Priority: P3)

Quien opera el proyecto configura las rutas del corpus, el servicio de recuperación y
el proveedor de lenguaje por variables de entorno; si falta algo crítico, el arranque
falla con un mensaje accionable; si el proveedor principal no está disponible, el
asistente sigue respondiendo con el respaldo local.

**Why this priority**: el corte vertical debe poder ejecutarse y demostrarse en
cualquier máquina sin tocar el código, y sin depender de un único proveedor.

**Independent Test**: se puede probar arrancando con variables presentes, con una
variable crítica ausente y con el proveedor principal simulado como caído.

**Acceptance Scenarios**:

1. **Given** una configuración completa, **When** el asistente arranca, **Then** queda
   disponible para responder y lo indica en el registro de arranque.
2. **Given** una ruta de corpus inexistente o una configuración crítica ausente,
   **When** el asistente arranca, **Then** falla con un mensaje que dice exactamente qué
   variable o ruta corregir.
3. **Given** que el proveedor principal no responde, **When** llega una pregunta,
   **Then** el asistente responde usando el proveedor de respaldo, sin cambiar la
   experiencia de la persona.

---

### User Story 4 - Evaluar el corte con un set de preguntas (Priority: P4)

Quien evalúa el proyecto ejecuta un set de preguntas de aceptación (reutilizadas del
proyecto de corpus y adaptadas) y obtiene un reporte que indica, por pregunta, si la
respuesta trae al menos una cita válida.

**Why this priority**: convierte "funciona" en una afirmación medible y deja la base
para la evaluación automática de fases posteriores.

**Independent Test**: se puede probar ejecutando el set sobre el asistente y
comprobando que el reporte contiene una fila por pregunta con su resultado.

**Acceptance Scenarios**:

1. **Given** el set de aceptación (~40 preguntas), **When** se ejecuta sobre el
   asistente, **Then** se produce un reporte por pregunta con respuesta, citas y
   resultado (cita válida o no).
2. **Given** una pregunta del set cuya respuesta no está en el corpus, **When** se
   evalúa, **Then** el reporte la marca como rechazo correcto y no como fallo.

---

### Edge Cases

- **Pregunta ambigua**: el asistente responde con la interpretación más probable y
  cita la evidencia; si hay dos interpretaciones incompatibles, lo señala.
- **Fuentes contradictorias**: el asistente presenta las dos versiones, cita ambas y no
  elige un ganador sin base.
- **Servicio de recuperación no disponible**: al arrancar, la aplicación falla con un
  mensaje accionable; si deja de responder durante la operación, la pregunta informa
  que no puede consultar el corpus en ese momento.
- **Corpus vacío**: el asistente no responde con conocimiento general; informa que no
  hay evidencia disponible.
- **Pregunta en otro idioma**: se responde en español y se aclara la limitación.
- **Pregunta sobre catálogo o precios**: se informa que esa información no está
  disponible en este corte (llega en la fase 3).
- **Proveedor principal caído o sin credenciales**: se usa el respaldo local y se deja
  constancia en la traza de la respuesta.
- **Pregunta larga o con intento de manipular al asistente**: el asistente ignora
  instrucciones ajenas al corpus y responde solo con evidencia.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE ofrecer un chat web en español donde la persona escribe
  una pregunta y ve la respuesta en la misma página.
- **FR-002**: El sistema DEBE buscar la evidencia únicamente en el corpus curado de
  Carvajal configurado; no DEBE usar conocimiento general del modelo como fuente.
- **FR-003**: El sistema DEBE acompañar cada respuesta con las fuentes consultadas: al
  menos título, tipo de fuente (oficial o tercero) y enlace al documento original. Las
  citas NO incluyen extractos textuales: enlazan al documento para su verificación.
- **FR-004**: El sistema DEBE negarse explícitamente a responder cuando la evidencia
  recuperada no sustente la pregunta, sin inventar cifras, fechas ni nombres.
- **FR-005**: El sistema DEBE señalar las contradicciones entre fuentes en lugar de
  ocultarlas.
- **FR-006**: El sistema DEBE funcionar con un proveedor de lenguaje de respaldo cuando
  el principal no esté disponible, manteniendo el formato de respuesta y las citas.
- **FR-007**: El sistema DEBE tomar rutas del corpus, servicio de recuperación y
  proveedores desde configuración externa; no DEBE requerir cambios de código para
  operar en otra máquina.
- **FR-008**: El sistema DEBE fallar al arrancar con un mensaje accionable cuando falte
  configuración crítica, una ruta no exista o el servicio de recuperación no esté
  disponible.
- **FR-009**: El sistema DEBE tratar el corpus y sus índices como solo lectura.
- **FR-010**: El sistema DEBE registrar por respuesta la pregunta, las fuentes
  recuperadas y el proveedor usado, sin guardar conversaciones entre sesiones.
- **FR-011**: El sistema NO DEBE versionar credenciales; DEBE documentar las variables
  necesarias en un archivo de ejemplo.
- **FR-012**: El sistema DEBE impedir que instrucciones incluidas en el corpus o en la
  pregunta alteren las reglas de respuesta.
- **FR-013**: El sistema DEBE limitar el alcance a preguntas sobre el corpus web; las
  consultas de catálogo o precios DEBEN informarse como no disponibles en este corte.
- **FR-014**: El sistema DEBE permitir ejecutar un set de preguntas de aceptación y
  producir un reporte por pregunta con el resultado de citación.
- **FR-015**: Una cita DEBE considerarse válida solo si su enlace corresponde a un
  documento del corpus y su título y tipo de fuente coinciden con los metadatos de ese
  documento.
- **FR-016**: La página DEBE conservar en memoria los intercambios de la sesión actual
  y NO DEBE persistirlos al recargar la página ni entre sesiones.

### Key Entities *(include if feature involves data)*

- **Pregunta**: texto en lenguaje natural enviado por la persona, con idioma y momento
  del envío.
- **Respuesta**: texto en español, estado (sustentada o sin evidencia), proveedor usado
  y latencia percibida.
- **Cita**: referencia a un documento del corpus con título, tipo de fuente y enlace;
  es la unidad que hace verificable la respuesta. Es **válida** cuando enlace, título
  y tipo de fuente coinciden con los metadatos del documento.
- **Documento del corpus**: pieza curada del corpus web con título, enlace, tipo de
  fuente, sección y hash de contenido.
- **Configuración**: conjunto de valores externos (rutas, servicios, proveedores) que
  determinan cómo opera el asistente.
- **Ejecución de aceptación**: conjunto de preguntas de evaluación con su resultado de
  citación y rechazo correcto.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Al menos el 90 % de las 40 preguntas del set de aceptación reciben una
  respuesta con al menos una cita válida.
- **SC-002**: Cero respuestas del set de aceptación contienen cifras o hechos sin una
  cita que los sustente.
- **SC-003**: El 100 % de las preguntas deliberadamente fuera del corpus reciben un
  rechazo explícito, sin datos inventados.
- **SC-004**: Con el proveedor principal no disponible, el 100 % de las preguntas del
  set siguen recibiendo respuesta con citas.
- **SC-005**: Una persona completa una pregunta en dos pasos o menos (escribir y
  enviar) y ve la respuesta en menos de 20 segundos en el entorno local de desarrollo.
- **SC-006**: Cualquier configuración crítica ausente se detecta al arrancar y se
  informa con el nombre exacto del valor o la ruta a corregir.
- **SC-007**: El reporte de aceptación se genera en una sola ejecución y contiene una
  fila por cada una de las 40 preguntas con su resultado.

## Assumptions

- El corpus curado aguas arriba está disponible en una ruta local de solo lectura; a la
  fecha de esta especificación son 24 documentos con metadatos de título, enlace, tipo
  de fuente, sección y hash.
- El set de preguntas de aceptación se reutiliza y adapta del proyecto de corpus
  completo (~40 preguntas); no se inventa un set nuevo desde cero.
- El idioma de interfaz y de respuesta es español; no se implementa detección de idioma
  en este corte.
- El uso previsto es local o de una sola persona por instancia; no hay autenticación
  ni multiusuario. El historial de la sesión vive en memoria y no se persiste al
  recargar ni entre sesiones.
- El stack y las restricciones técnicas ya están decididos en `CONSTITUTION.md` y no se
  reabren en esta especificación; el plan los detalla.
- La información de catálogo y precios queda fuera de alcance (fase 3).

## Out of Scope

- Catálogo de empaques, precios, disponibilidad y consultas comerciales.
- Autenticación, cuentas, multiusuario y persistencia del historial.
- Despliegue en producción, contenedores y alta disponibilidad.
- Streaming de la respuesta, voz, imágenes y adjuntos.
- Evaluación automática con métricas de calidad más allá del reporte de citación.
- Crawling, reindexación o modificación del corpus (es de solo lectura).
