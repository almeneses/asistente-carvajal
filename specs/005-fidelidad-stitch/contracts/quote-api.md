# Contrato: solicitud de cotización

**Feature**: `specs/005-fidelidad-stitch` · **Fecha**: 2026-11-20

## `POST /quotes`

- **Consumo**: `application/x-www-form-urlencoded`:
  - `sku` (str, obligatorio)
  - `boxes` (int, obligatorio, ≥1)
  - `city` (str, opcional, ≤80)
  - `business` (str, opcional, ≤80)
- **Respuesta correcta**: `200 application/json`

```json
{
  "ok": true,
  "quote": {
    "code": "OC-2026-1121-A1B2",
    "sku": "MX-VASO-12-PP",
    "reference": "Vaso térmico 12 oz",
    "boxes": 5,
    "units": 5000,
    "unit_price": 1890.0,
    "total": 9450.0,
    "currency": "MXN",
    "city": "Ciudad de México",
    "business": "Café Origen",
    "created_at": "2026-11-21T01:00:00+00:00"
  }
}
```

- **Validación**: `422 application/json` si el SKU no existe, `boxes` no es entero ≥1 o
  los textos exceden 80 caracteres.
- **Error de escritura**: `500` con mensaje genérico; el cliente ofrece reintentar.
- **Idempotencia**: no hay clave de idempotencia; el cliente deshabilita el botón durante
  el envío. Dos envíos generan dos códigos.

## Código

- Formato `OC-AAAA-MMDD-XXXX` con 4 caracteres hex en mayúsculas.
- Se verifica que no exista en el archivo; si colisiona, se regenera.

## Persistencia

- `QUOTES_LOG_PATH` (defecto `.cache/solicitudes.jsonl`), una línea JSON por solicitud.
- Sin PII; solo datos del catálogo, cajas, ciudad/negocio opcionales y fecha.

## Cliente

- “Solicitar cotización” → `submitting` (botón deshabilitado).
- Éxito → tarjeta completa con código y total; countdown 10 s; “Minimizar ahora” →
  tarjeta compacta animada; “Ver detalle completo” → expandir.
- Error → mensaje + “Reintentar”, sin código.
- `prefers-reduced-motion` → transición instantánea.
