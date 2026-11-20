# Contrato: interfaz web y reporte de aceptación

**Feature**: `specs/001-corte-vertical-citas` · **Fecha**: 2026-11-19

La aplicación expone una interfaz HTTP mínima para el chat y un script de operación para
la aceptación. Todo el contenido se sirve en español.

## GET /

- **Respuesta**: `200 text/html; charset=utf-8` con la página de chat.
- **Contenido**: formulario `POST /ask` (`name="question"`, `required`, máximo 2000
  caracteres), contenedor de intercambios con `id="conversation"` y la referencia a
  `/static/htmx.min.js`.

## POST /ask

- **Consumo**: `application/x-www-form-urlencoded`, campo `question` (str).
- **Respuesta correcta**: `200 text/html; charset=utf-8`, parcial HTML con un intercambio
  (pregunta, respuesta, fuentes) para insertar con `hx-swap="beforeend"`.
- **Validación**: pregunta vacía o mayor a 2000 caracteres → `422` con un parcial de
  error legible; la conversación previa no se pierde.
- **Abstención**: `200` con `status="no_evidence"`; el parcial dice explícitamente que no
  se encontró evidencia y **no** incluye cifras ni fuentes inventadas.
- **Error interno o proveedor caído**: `503` con parcial de error accionable y
  `request_id`; no se exponen trazas.

### Parcial de intercambio (contrato de fragmento)

```html
<section class="exchange" data-status="answered" data-provider="deepseek"
         data-request-id="…">
  <p class="question">…</p>
  <div class="answer">…texto con referencias [1], [2]…</div>
  <ul class="sources">
    <li><a href="https://…" rel="noopener">Título</a> <span class="source-type">oficial</span></li>
  </ul>
</section>
```

- `data-status`: `answered` | `no_evidence` | `error`.
- Todo texto proveniente del corpus o del modelo se escapa (`html.escape`/Jinja2 autoescape).
- Las citas se generan desde los metadatos del corpus (FR-015); no se aceptan enlaces
  producidos por el modelo.

### Parcial de abstención

```html
<section class="exchange" data-status="no_evidence">
  <p class="question">…</p>
  <div class="answer">No encontré evidencia suficiente en el corpus para responder.</div>
</section>
```

## GET /healthz

- **Respuesta sana**: `200 application/json`

```json
{
  "status": "ok",
  "corpus_documents": 24,
  "collection": "corpus_carvajal",
  "provider": "deepseek"
}
```

- **Respuesta enferma**: `503 application/json` con `status`, `error` y `request_id`.
- No incluye claves, rutas absolutas ni contenido del corpus.

## GET /static/htmx.min.js

- Sirve el archivo vendorizado (`200 application/javascript`); no depende de CDN.

## Script de aceptación

`uv run python scripts/run_acceptance.py --questions "$ACCEPTANCE_FILE" --json-out report.json`

- **Entrada**: JSON con lista de strings o de objetos `{question, expected_out_of_scope?}`.
- **Salida**: reporte JSON con el esquema de `data-model.md` y un resumen Markdown por
  `stdout`.
- **Exit code**: `0` si `invalid_citations == 0` y `answered_with_valid_citation / 40 ≥
  0.9`; `1` en caso contrario; `2` si falta configuración o el corpus.
- **Requisitos**: no requiere el servidor web; usa la cadena RAG en proceso.

## Errores y trazas

- Cada petición genera un `request_id` (UUID v4) que aparece en el parcial HTML, en el
  log y en la respuesta de error.
- El log de una pregunta registra: `request_id`, ruta (`answered`/`no_evidence`),
  `provider`, `latency_ms`, `slug` citados y tamaño del contexto, sin PII ni claves.
