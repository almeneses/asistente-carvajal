# Research: Consulta del catálogo de empaques

**Feature**: `specs/003-catalogo-empaques` · **Fecha**: 2026-11-20

Decisiones técnicas del plan; no quedan `NEEDS CLARIFICATION`.

## R1. Rama de catálogo determinista (sin LLM)

- **Decisión**: las respuestas de catálogo (recomendaciones, precios, distribuidores) se
  construyen con plantillas a partir de los datos; el LLM solo se usa en la rama
  documental existente. El router es determinista (reglas y extracción de atributos).
- **Rationale**: elimina por construcción los precios/SKU inventados (SC-002) y hace
  auditable cada cifra; cumple el principio IV (separación recuperación/generación) y no
  añade latencia de LLM a consultas comerciales.
- **Alternativas consideradas**: pedir al LLM que redacte desde filas del catálogo (riesgo
  de inventar o mezclar cifras), router con LLM (más caro y no determinista).

## R2. Carga y validación del catálogo

- **Decisión**: `CATALOG_DIR` apunta al directorio con los cuatro CSV y `manifest.json`.
  El loader valida cabeceras, tipos, SKUs únicos, cobertura de precios y consistencia de
  país/moneda; falla con mensaje accionable si falta un archivo o una columna.
- **Rationale**: un catálogo mal formado es peor que uno ausente; el arranque debe avisar
  antes de responder con datos incompletos.
- **Datos actuales**: 200 referencias (98 MX, 102 CO), 29 precios COP, 5 materiales, 29
  distribuidores. `CATALOG_DIR` será obligatorio en la configuración de la app.
- **Alternativas**: cargar en cada consulta (lento), base de datos (innecesaria para 200
  filas).

## R3. Validación de material y temperatura

- **Decisión**: para cada referencia se consulta su material en `materiales.csv` y se
  aplican: `applications[uso]` (`recomendable`/`aplicable`/`no_apto`), `microwave`,
  `refrigeration`, `freezing`, `hot_content` y el rango `temp_min_c`/`temp_max_c`. Si el
  uso pedido es `no_apto` o la temperatura excede el rango, la referencia se descarta. Si
  el material no tiene regla para el uso, se usa el rango de la ficha y se advierte.
- **Rationale**: evita el error objetivo de recomendar PET para caliente; la guía de
  materiales es la fuente de verdad.
- **Mapeo**: `bebida_caliente`→`comida_caliente`; `bebida_fria`→`comida_fria`; `sopas`→
  `sopas`; `microondas`→`microwave`; `congelación`→`freezing`.
- **Alternativas**: validar solo con la ficha (insuficiente), confiar en el LLM (prohibido).

## R4. Resolución de precio y vigencia

- **Decisión**: México usa el precio de `referencias.csv` (`price`, `currency`,
  `tax_included`, `price_valid_until`); Colombia usa `precios.csv` por `sku` (`amount`,
  `currency`, `tax_status`, `valid_until`, fuente). Se muestran monto, moneda, país,
  impuestos, fuente y fecha de captura. `valid_until` vacío → “vigencia no declarada”;
  fecha pasada → “vencido” (se muestra solo con advertencia). Sin precio → “sin precio”.
- **Rationale**: cumple FR-005/FR-006/FR-017 y SC-005; no hay conversión ni suma entre
  monedas.
- **Alternativas**: usar solo precios MX (deja fuera CO), convertir COP→MXN (prohibido por
  no tener tasa oficial).

## R5. Cantidad, cajas y total

- **Decisión**: si la pregunta trae cantidad, `cajas = ceil(cantidad / units_per_box)` y
  `total = cajas * precio`. Se muestra la presentación usada y se redondea hacia arriba;
  si no hay precio, se muestra la cantidad de cajas sin total.
- **Rationale**: FR-016/SC-009; evita prometer fracciones de caja.
- **Alternativas**: dividir exacto (imposible comprar fracciones), ignorar cantidad (menos
  útil).

## R6. Router determinista e intención

- **Decisión**: clasificador por señales léxicas normalizadas (sin acentos):
  - **comercial**: familias (`vaso`, `contenedor`, `plato`, `tapa`, `charola`, `cubierto`,
    `envase`, `bolsa`), precios/cantidad (`precio`, `cuánto`, `cuesta`, `valor`, `total`,
    `cotiza`, patrones `N unidades`, `N oz`), canal (`distribuidor`, `proveedor`, `dónde
    comprar`) y ciudades del catálogo.
  - **documental**: empresa, historia, sectores, gobierno, ética, sostenibilidad,
    inversión, noticias, países.
  - **mixta**: señales de ambas; **ambigua**: ninguna señal clara.
  - Se prioriza comercial cuando hay ciudad/cantidad/familia/precio.
- **Rationale**: 130 preguntas de aceptación tienen rutas conocidas; un router de reglas es
  reproducible y se puede medir (SC-004). Si la aceptación no llega al 90 %, se evalúa un
  clasificador alternativo en una fase posterior, no se improvisa.
- **Alternativas**: LLM para enrutar (coste, no determinista), reglas por palabras clave
  sin normalización (peor cobertura).

## R7. Extracción de atributos

- **Decisión**: extraer `family`, `capacity_oz` (regex), `quantity` (miles con punto/coma),
  `city`/`country` (lista de ciudades del catálogo; “Colombia”/“México”), `use`
  (café/chocolate/caliente→`bebida_caliente`; jugo/limonada/frío→`bebida_fria`;
  sopa→`sopas`; microondas/congelación), `material` (PET, PP, EPS, PS, papel, pulpa,
  aluminio) y `prefers_renewable` (papel/pulpa/fibra/sostenible).
- **Regla**: si falta un dato crítico para validar (uso o temperatura cuando se pide
  caliente/frío), se pide aclaración antes de recomendar (US1 escenario 3).
- **Tolerancia**: capacidad con ±1 oz para permitir presentaciones redondeadas.

## R8. Respuestas y citas

- **Decisión**: plantillas por tipo:
  - **Recomendación**: lista de hasta 5 referencias con SKU, nombre, material,
    presentación por caja y ficha (URL + captura).
  - **Precio**: monto/moneda/país/impuestos/fuente/vigencia; con cantidad, cajas y total.
  - **Distribuidor**: nombre, ciudad, dirección, teléfono y fuente.
  - **Sin coincidencia**: qué restricciones no se pudieron cumplir; sin alternativas que
    las violen.
  - **Mixta**: sección “Catálogo” primero; sección “Corpus” solo si el catálogo no cubre
    la parte documental.
- **Citas**: válidas si la URL pertenece a una fuente del catálogo y el SKU/distribuidor
  existe (FR-012/SC-008).
- **Alternativas**: respuesta en JSON (peor UX), LLM redactor (riesgo de invención).

## R9. Set de aceptación

- **Decisión**: `scripts/run_catalog_acceptance.py` consume el
  `routing_questions.json` del corpus (130 ítems: 49 documentales, 61 comerciales y 20 de
  Colombia) y evalúa: ruta esperada, atributos extraídos, materiales prohibidos, precio
  total/cajas y casos sin precio (SKU placeholder `CO-*`). Reporte JSON/Markdown y exit
  codes.
- **Rationale**: reutiliza un set ya curado y permite medir SC-004 y SC-002 sin inventar
  preguntas; los 49 documentales protegen contra regresiones (FR-013).
- **Alternativas**: set nuevo (sesgo y trabajo), solo pruebas unitarias (no mide el router).

## R10. Configuración y compatibilidad

- **Decisión**: añadir `CATALOG_DIR` (obligatorio) y `CATALOG_ROUTING_FILE` (opcional, para
  aceptación) a `Settings`; `.env.example` los documenta. La app arranca solo si el
  catálogo valida; la rama documental no cambia.
- **Rationale**: FR-002/FR-013 y arranque accionable ante datos faltantes.
- **Riesgo**: entornos existentes sin catálogo no arrancan hasta configurarlo; se documenta
  en quickstart y README.

## Dependencias

Ninguna nueva: `csv`, `json`, `math`, `datetime` de la librería estándar.
