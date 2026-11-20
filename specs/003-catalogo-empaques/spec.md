# Feature Specification: Consulta del catálogo de empaques con precios y validación técnica

**Feature Branch**: `feat/003-catalogo-empaques`

**Created**: 2026-11-20

**Status**: Draft

**Input**: User description: "Consulta del catálogo de empaques con precios y validación técnica. El asistente debe responder preguntas sobre referencias, precios y distribuidores del catálogo de Carvajal Empaques, validar que el material sea apto para el uso y citar la fuente, sin inventar precios ni disponibilidad."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recibir referencias técnicamente válidas (Priority: P1)

Una persona que administra una cafetería, restaurante o evento describe lo que necesita
empacar («vasos de 12 oz para café caliente», «contenedores para sopa que aguanten
microondas») y recibe referencias del catálogo cuyo material y rango de temperatura son
compatibles con ese uso. Cada referencia muestra SKU, nombre, material, presentación por
caja y la ficha de origen con su fecha de captura.

**Why this priority**: una recomendación técnicamente inválida (por ejemplo, poliestireno
para bebida caliente) es un error objetivo que destruye la confianza y no se puede
compensar con una buena redacción.

**Independent Test**: pedir vasos para café caliente y comprobar que ninguna referencia
sugerida pertenece a un material marcado como no apto para contenido caliente y que todas
citan su ficha.

**Acceptance Scenarios**:

1. **Given** una necesidad de comida o bebida caliente, **When** se recomienda, **Then**
   ninguna referencia usa un material no apto para calor.
2. **Given** una necesidad de microondas o congelación, **When** se recomienda, **Then**
   solo aparecen materiales declarados aptos para ese uso.
3. **Given** una necesidad sin uso o temperatura, **When** se envía, **Then** el asistente
   pide el dato que falta en lugar de suponerlo.
4. **Given** una preferencia por materiales renovables, **When** se recomienda, **Then** se
   priorizan papel, pulpa o fibra y se indica si no cumplen el resto de requisitos.

---

### User Story 2 - Conocer el precio de referencia con su vigencia (Priority: P2)

La misma persona pregunta cuánto cuesta una referencia o un paquete de referencias y
recibe el precio con su moneda, país, si incluye impuestos, la fuente, la fecha de captura
y la vigencia. Si el precio expiró o no existe, el asistente lo dice y nunca inventa una
cifra ni promete disponibilidad.

**Why this priority**: el precio es el dato más sensible a errores y el que más rápido
envejece; presentarlo sin vigencia o inventarlo es peor que no responder.

**Independent Test**: preguntar por una referencia con precio vigente y comprobar que la
respuesta incluye moneda, impuestos, fuente y vigencia; preguntar por una sin precio y
comprobar que lo declara.

**Acceptance Scenarios**:

1. **Given** una referencia con precio vigente, **When** se consulta, **Then** la
   respuesta incluye monto, moneda, país, tratamiento de impuestos, fuente y vigencia.
2. **Given** una referencia cuyo precio expiró, **When** se consulta, **Then** el asistente
   marca la vigencia vencida y no lo presenta como precio actual.
3. **Given** una referencia sin precio en el catálogo, **When** se consulta, **Then** lo
   declara explícitamente y no estima ni convierte cifras.
4. **Given** una pregunta que mezcla países o monedas, **When** se responde, **Then** no se
   mezclan precios de un país con referencias de otro.

---

### User Story 3 - Encontrar el canal de compra (Priority: P3)

La persona pregunta dónde comprar o quién distribuye una referencia en su ciudad y recibe
los distribuidores del catálogo con dirección, teléfono y fuente.

**Why this priority**: cierra el recorrido comercial de la recomendación sin prometer
disponibilidad ni logística.

**Independent Test**: preguntar por distribuidores en una ciudad del catálogo y comprobar
que la respuesta lista nombres, contacto y fuente.

**Acceptance Scenarios**:

1. **Given** una ciudad con distribuidores, **When** se consulta, **Then** se listan con
   dirección, teléfono y fuente.
2. **Given** una ciudad sin distribuidores, **When** se consulta, **Then** el asistente lo
   dice y no inventa contactos.
3. **Given** una consulta de distribuidor, **When** se responde, **Then** no se afirma
   disponibilidad de inventario ni tiempos de entrega.

---

### User Story 4 - Enrutar y responder preguntas mixtas (Priority: P4)

El asistente distingue entre preguntas documentales (corpus web), comerciales (catálogo) y
mixtas. Ante una pregunta mixta responde las dos partes con sus citas separadas; ante una
pregunta no reconocida pide aclaración. Las preguntas documentales siguen funcionando
igual que antes.

**Why this priority**: el valor del asistente crece al combinar las dos fuentes, pero solo
si el usuario entiende qué respondió cada una y por qué.

**Independent Test**: enviar una batería de preguntas documentales, comerciales y mixtas y
comprobar que la ruta elegida es la correcta y que ninguna pierde sus citas.

**Acceptance Scenarios**:

1. **Given** una pregunta documental, **When** se responde, **Then** usa el corpus y no
   mezcla precios del catálogo.
2. **Given** una pregunta comercial, **When** se responde, **Then** usa el catálogo y no
   responde con el corpus.
3. **Given** una pregunta mixta, **When** se responde, **Then** presenta las dos partes con
   citas separadas.
4. **Given** una pregunta ambigua, **When** se responde, **Then** pide una aclaración breve
   en lugar de adivinar la fuente.

---

### Edge Cases

- **Precio vencido**: se muestra la cifra solo si se advierte que la vigencia expiró; nunca
  como precio actual.
- **Precio ausente**: se declara la ausencia; no se estima, convierte ni reutiliza el
  precio de otra referencia.
- **SKU inexistente**: se responde que no está en el catálogo; no se propone un SKU
  parecido.
- **Uso o temperatura ambiguos**: se pide aclaración antes de recomendar.
- **Material sin regla de temperatura**: se aplica el rango declarado por la ficha y se
  advierte la limitación.
- **Precio en el corpus y en el catálogo**: para precios manda el catálogo con su vigencia;
  el corpus solo se usa como contexto documental.
- **Distribuidor no encontrado**: se informa; no se inventan teléfonos ni direcciones.
- **Pregunta en otro idioma**: se responde en español y se aclara la limitación.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE clasificar cada pregunta en documental, comercial, mixta o
  ambigua y enrutarla a la fuente correspondiente.
- **FR-002**: El sistema DEBE consumir el catálogo de empaques en solo lectura:
  referencias, precios, materiales y distribuidores, con su manifesto y fecha de captura.
- **FR-003**: El sistema DEBE validar el material y el rango de temperatura contra el uso
  declarado antes de recomendar una referencia.
- **FR-004**: Cada recomendación DEBE mostrar SKU, nombre, material, presentación por caja
  y la ficha de origen con su fecha de captura.
- **FR-005**: Cada respuesta de precio DEBE incluir monto, moneda, país, tratamiento de
  impuestos, fuente, fecha de captura y vigencia.
- **FR-006**: El sistema DEBE marcar los precios vencidos y DEBE declarar los precios
  ausentes, sin estimarlos, convertirlos ni inventarlos.
- **FR-007**: El sistema NO DEBE afirmar disponibilidad de inventario, tiempos de entrega
  ni ofertas comerciales.
- **FR-008**: El sistema DEBE permitir buscar por familia, uso, material, capacidad,
  temperatura y país.
- **FR-009**: El sistema DEBE responder consultas de distribuidores por ciudad o país con
  nombre, dirección, teléfono y fuente.
- **FR-010**: Las preguntas mixtas DEBEN responderse con las dos secciones y sus citas
  separadas.
- **FR-011**: Cuando no haya coincidencias, el sistema DEBE decir qué restricciones no
  pudo cumplir y no DEBE proponer alternativas que las violen.
- **FR-012**: Una cita DEBE considerarse válida solo si su URL pertenece a una fuente del
  catálogo y el SKU o distribuidor existen en los datos.
- **FR-013**: Las preguntas documentales DEBEN seguir respondiéndose con el corpus sin
  regresiones.
- **FR-014**: El sistema DEBE permitir ejecutar un set de aceptación con preguntas de
  enrutamiento (documental, comercial, Colombia), precios vigentes/vencidos/ausentes y
  casos de no coincidencia.
- **FR-015**: El sistema NO DEBE mezclar referencias de un país con precios de otro ni
  sumar montos de monedas distintas.

### Key Entities *(include if feature involves data)*

- **Referencia**: producto del catálogo (SKU, nombre, familia, uso, material, capacidad,
  presentación por caja, país, fuente y captura).
- **Precio**: monto asociado a un SKU con país, moneda, impuestos, fuente, captura y
  vigencia; puede no existir.
- **Regla de material**: aptitud del material para calor, microondas, congelación y
  aplicaciones.
- **Distribuidor**: punto de venta o canal con ciudad, dirección, teléfono y fuente.
- **Intención de consulta**: documental, comercial, mixta o ambigua.
- **Recomendación**: referencia propuesta con su validación técnica y citas.
- **Snapshot del catálogo**: versión de los datos con fingerprint para citar y auditar.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de las respuestas con precio incluye país, moneda, impuestos, fuente
  y vigencia.
- **SC-002**: Cero precios o SKU inventados en el set de aceptación.
- **SC-003**: Cero recomendaciones con material incompatible con el uso o la temperatura
  declarados.
- **SC-004**: El enrutamiento acierta al menos el 90 % en el set mixto de preguntas.
- **SC-005**: El 100 % de los precios vencidos se marca como vencido y ninguno se presenta
  como actual.
- **SC-006**: El 100 % de las consultas sin coincidencia recibe una respuesta explícita sin
  alternativas inválidas.
- **SC-007**: Las preguntas mixtas incluyen las dos secciones con citas válidas en al menos
  el 90 % de los casos.
- **SC-008**: El 100 % de las citas del catálogo apunta a una fuente existente y a un SKU o
  distribuidor presente en los datos.

## Assumptions

- El catálogo disponible es el snapshot actual: 200 referencias (98 México, 102 Colombia),
  5 materiales, 29 precios de Colombia y 29 distribuidores; México trae precio MXN en la
  referencia y Colombia usa el archivo de precios en COP.
- Los precios son de referencia, no ofertas; algunos pueden estar vencidos o ausentes.
- El catálogo es de solo lectura y se consume desde una ruta configurable; no se scrapea ni
  se actualiza en caliente.
- No se convierten monedas ni se suman importes de países distintos.
- La interfaz sigue siendo el chat actual; no se añade carrito ni checkout.
- El set de aceptación reutiliza las preguntas de enrutamiento del proyecto de corpus
  (comerciales y Colombia) más casos de precio vencido/ausente y no coincidencia.

## Out of Scope

- Inventario en vivo, disponibilidad, tiempos de entrega y logística.
- Carrito, checkout, cotizaciones formales y facturación.
- Scraping o actualización del catálogo (sigue siendo responsabilidad aguas arriba).
- Conversión de divisas y nuevos países fuera del snapshot.
- Recomendaciones de marketing o ranking comercial más allá de la validación técnica.
- Cambios de interfaz distintos de los necesarios para mostrar secciones y citas.
