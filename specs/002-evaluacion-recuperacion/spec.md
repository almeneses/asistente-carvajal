# Feature Specification: Evaluación de recuperación y métricas de calidad

**Feature Branch**: `feat/002-evaluacion-recuperacion`

**Created**: 2026-11-20

**Status**: Draft

**Input**: User description: "Evaluación de recuperación y métricas de calidad. Medir la calidad del corte vertical con evidencia esperada por pregunta, comparar variantes de recuperación y dejar una decisión registrada."

## Clarifications

### Session 2026-11-20

- Q: ¿La fase puede cambiar el modelo de embeddings o se limita a ajustar la recuperación actual? → A: Se evalúa `bge-m3` (1024 dims, multilingüe) y solo se migra si mejora al menos 5 puntos porcentuales; implica reconstruir el índice y enmendar la constitución.
- Q: ¿Cómo se construye la evidencia esperada de las 30 preguntas? → A: El LLM propone evidencia y estado esperado; una persona revisa y corrige las 30 antes de usarlas como ground truth.
- Q: ¿Qué parte de la evaluación corre en CI? → A: Solo las pruebas del harness con fixtures; la evaluación real se ejecuta a mano con servicios.
- Q: ¿Qué umbrales de salida se fijan? → A: `recall@5 ≥ 95 %`, precisión de citas 100 % y abstención correcta ≥ 90 %, recalibrables contra el baseline con registro en el ADR.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ejecutar la evaluación y leer un reporte por pregunta (Priority: P1)

Quien mantiene el asistente ejecuta una evaluación sobre el corpus actual y obtiene un
reporte que, para cada pregunta, dice si la evidencia esperada fue recuperada, si las
citas son correctas y si el asistente respondió o se abstuvo como correspondía.

**Why this priority**: hoy existe un set de 30 preguntas y una métrica de citas, pero no
hay evidencia esperada ni métricas de recuperación. Sin eso no se puede distinguir entre
un fallo de búsqueda, un fallo del modelo o una pregunta que el corpus no sustenta.

**Independent Test**: se ejecuta la evaluación sobre el set anotado y el reporte contiene
una fila por pregunta y los agregados; los totales cuadran con las filas.

**Acceptance Scenarios**:

1. **Given** el set de evaluación anotado, **When** se ejecuta la evaluación, **Then** el
   reporte incluye por pregunta: evidencia esperada, evidencia recuperada, citas
   producidas, estado (respondida/abstención) y latencia.
2. **Given** una pregunta cuya evidencia esperada está entre los fragmentos
   recuperados, **When** se evalúa, **Then** cuenta como acierto de recuperación.
3. **Given** una pregunta marcada como no sustentable, **When** el asistente se
   abstiene, **Then** cuenta como acierto de abstención y no como fallo de recuperación.

---

### User Story 2 - Comparar configuraciones de recuperación (Priority: P2)

Quien mantiene el asistente compara al menos tres variantes de recuperación (modelo de
embeddings, tamaño de fragmento y mezcla de señales) con el mismo set y obtiene una
tabla comparativa con las mismas métricas.

**Why this priority**: la decisión sobre el modelo y la fragmentación debe tomarse con
evidencia, no por intuición; cambiar de modelo afecta dimensión del índice y constitución.

**Independent Test**: se ejecuta la misma evaluación con dos configuraciones distintas y
el reporte comparativo muestra ambas con sus métricas y la ganadora por criterio.

**Acceptance Scenarios**:

1. **Given** dos variantes declaradas, **When** se ejecutan sobre el mismo set, **Then**
   el reporte las compara con idénticas preguntas y métricas.
2. **Given** una variante cuyo modelo no está disponible, **When** se evalúa, **Then** se
   marca como omitida con la causa y la comparación sigue con las demás.
3. **Given** una variante que mejora `recall@5`, **When** se compara, **Then** aparece
   destacada como candidata sin alterar el índice del entorno de desarrollo.

---

### User Story 3 - Decidir y registrar la configuración ganadora (Priority: P3)

Al cerrar la evaluación, la configuración elegida queda registrada en la constitución y en
un ADR, y si implicó cambiar el modelo de embeddings se documenta la migración del índice.

**Why this priority**: la spec no debe terminar en un reporte; la decisión es el producto
y debe quedar auditable para las fases siguientes.

**Independent Test**: se revisa `CONSTITUTION.md` §9 y el ADR y coinciden con la
configuración usada por la evaluación final.

**Acceptance Scenarios**:

1. **Given** el reporte final, **When** se cierra la fase, **Then** existe un ADR con la
   decisión, alternativas y evidencia.
2. **Given** un cambio de modelo o dimensión, **When** se registra, **Then** la
   constitución y la proyección de Spec Kit se actualizan en el mismo commit y el índice
   se reconstruye.
3. **Given** que se mantiene la configuración actual, **When** se cierra, **Then** el ADR
   lo dice explícitamente con la evidencia que lo respalda.

---

### User Story 4 - Reproducir y auditar la evaluación (Priority: P4)

Cualquier persona puede repetir la evaluación y obtener los mismos números, sabiendo
sobre qué corpus y con qué configuración se ejecutó.

**Why this priority**: una métrica sin condiciones reproducibles no sirve como puerta de
calidad ni como base de comparación entre fases.

**Independent Test**: se ejecuta dos veces con el mismo corpus y configuración y las
métricas agregadas coinciden; el reporte registra el fingerprint del corpus.

**Acceptance Scenarios**:

1. **Given** el mismo corpus y configuración, **When** se ejecuta dos veces, **Then** las
   métricas agregadas son iguales salvo la latencia.
2. **Given** un corpus modificado, **When** se ejecuta, **Then** el reporte lo detecta por
   fingerprint y advierte que no es comparable con el anterior.

---

### Edge Cases

- **Pregunta con varias fuentes válidas**: cuenta como acierto si al menos una de las
  esperadas aparece entre los recuperados.
- **Pregunta sin evidencia en el corpus**: se evalúa como abstención correcta; no baja
  `recall`.
- **Cita válida pero respuesta irrelevante**: se distingue en el reporte; no debe
  confundirse con precisión de citas.
- **Modelo o servicio no disponible**: la variante se omite con causa; la evaluación
  sigue.
- **Corpus cambiado a mitad de la fase**: los reportes de fingerprints distintos se
  marcan como no comparables.
- **Ejecución interrumpida**: el reporte parcial no se considera válido para cerrar la
  fase.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE mantener un set de evaluación versionado con pregunta,
  evidencia esperada (documento y enlace), estado esperado (sustentable o no sustentable)
  y hechos clave de la respuesta.
- **FR-002**: El sistema DEBE ejecutar la cadena real de recuperación y respuesta sobre el
  set y producir un reporte por pregunta.
- **FR-003**: El sistema DEBE calcular métricas de recuperación: `recall@k` para k=1, 3, 5
  y 10, y MRR.
- **FR-004**: El sistema DEBE calcular métricas de respuesta: precisión de citas,
  abstención correcta y latencia p50/p95.
- **FR-005**: El sistema DEBE permitir comparar al menos tres variantes de configuración
  (modelo de embeddings, tamaño de fragmento y mezcla de señales) sobre el mismo set.
- **FR-006**: El sistema DEBE emitir el reporte en JSON y Markdown con corpus fingerprint,
  configuración, fecha y versiones usadas.
- **FR-007**: El sistema DEBE devolver código de salida 0 si se cumplen los umbrales de la
  fase y 1 si no, informando cuál falló.
- **FR-008**: Las pruebas unitarias DEBEN usar fixtures y no depender de red ni de
  servicios externos; CI ejecuta solo esas pruebas y la evaluación real es una ejecución
  explícita.
- **FR-009**: La evaluación NO DEBE modificar el corpus ni el índice usado por la
  aplicación.
- **FR-010**: Al cerrar la fase, la decisión DEBE registrarse en `CONSTITUTION.md` §9 y en
  un ADR. Solo se migra a `bge-m3` si la mejora en `recall@5` es de al menos 5 puntos
  porcentuales; en ese caso, DEBE incluir la reconstrucción del índice y la actualización
  de la proyección de Spec Kit.
- **FR-012**: El ground truth DEBE generarse con una propuesta asistida por LLM y una
  revisión humana registrada de las 30 preguntas (quién revisó, fecha y cambios).
- **FR-013**: La evaluación DEBE separar la medición de recuperación (sin generación) de
  la medición end-to-end (con generación), para no gastar LLM en cada variante.
- **FR-011**: El set de evaluación DEBE cubrir las 30 preguntas actuales y marcar
  explícitamente cuáles son sustentables y cuáles no.

### Key Entities *(include if feature involves data)*

- **Evaluación**: ejecución completa sobre un set y una configuración, identificada por
  fecha, fingerprint del corpus y configuración.
- **Pregunta evaluada**: pregunta del set con su evidencia esperada y estado esperado.
- **Evidencia esperada**: documento o fragmento que sustenta la respuesta correcta.
- **Variante**: combinación declarada de modelo de embeddings, tamaño de fragmento y
  mezcla de señales.
- **Reporte**: filas por pregunta y agregados de métricas, comparable por fingerprint.
- **Decisión**: configuración elegida, alternativas y evidencia que la respalda.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de las 30 preguntas del set queda anotado con evidencia y estado
  esperado.
- **SC-002**: `recall@5 ≥ 95 %` en las preguntas sustentables (baseline medido al inicio
  de la fase).
- **SC-003**: La precisión de citas es del 100 %: ninguna cita producida apunta a un
  documento fuera del corpus o con metadatos alterados.
- **SC-004**: La abstención es correcta en al menos el 90 % de las preguntas marcadas como
  no sustentables.
- **SC-005**: Se comparan al menos tres variantes en una sola ejecución por variante y el
  reporte declara una ganadora por criterio.
- **SC-006**: Dos ejecuciones con el mismo corpus y configuración producen las mismas
  métricas agregadas (se excluye la latencia).
- **SC-007**: La decisión final queda registrada en la constitución y el ADR, con enlace
  al reporte que la sustenta.

## Assumptions

- El set de partida son las 30 preguntas del proyecto de corpus; algunas requerirán
  anotación manual de evidencia esperada.
- El corpus disponible es el actual (24 documentos, 123 fragmentos) y se consume en solo
  lectura.
- La evaluación se ejecuta con el proveedor configurado (DeepSeek para velocidad o Ollama
  para operación local); las métricas de recuperación no dependen del proveedor.
- La propuesta inicial de evidencia esperada la genera el LLM a partir del corpus y la
  revisa una persona antes de congelar el set; el archivo de revisión queda versionado.
- Cambiar el modelo de embeddings implica reconstruir el índice y enmendar la constitución;
  la fase incluye esa migración solo si la evidencia la justifica.
- No se implementan capacidades nuevas de producto (catálogo, UI, despliegue); solo
  evaluación y el ajuste de recuperación que la evidencia respalde.
- Los umbrales de SC-002 y SC-004 podrán recalibrarse una vez medido el baseline, dejando
  registro de por qué.

## Out of Scope

- Consultas sobre el catálogo de empaques (fase 3).
- Cambios de experiencia de chat, streaming o accesibilidad (fase 4).
- Despliegue, observabilidad y límites de coste (fase 5).
- Juicio humano a gran escala o anotación de nuevos corpus.
- Fine-tuning de modelos.
