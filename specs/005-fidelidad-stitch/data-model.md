# Data Model: Fidelidad visual y solicitudes

**Feature**: `specs/005-fidelidad-stitch` · **Fecha**: 2026-11-20

## Solicitud de cotización

### QuoteRequest (entrada del endpoint)

| Campo | Tipo | Regla |
|---|---|---|
| `sku` | str | Obligatorio; debe existir en el catálogo |
| `boxes` | int | ≥1; se recalcula el total desde el catálogo |
| `city` | str | Opcional, ≤80; sin datos personales |
| `business` | str | Opcional, ≤80; no es PII obligatoria |

### QuoteRecord (persistido en JSONL)

| Campo | Tipo | Regla |
|---|---|---|
| `code` | str | `OC-AAAA-MMDD-XXXX`; único |
| `sku` | str | Del catálogo |
| `reference` | str | Nombre de la referencia |
| `boxes` | int | Cajas solicitadas |
| `units` | int | Cajas × unidades por caja |
| `unit_price` | float | Precio de referencia del catálogo |
| `total` | float | Recalculado por el servidor |
| `currency` | str | Moneda del catálogo |
| `city` | str | Opcional |
| `business` | str | Opcional |
| `created_at` | str | ISO-8601 UTC |

- **Prohibido**: nombre de persona, correo, teléfono, dirección, IP, user-agent.
- **Almacenamiento**: `QUOTES_LOG_PATH` (defecto `.cache/solicitudes.jsonl`),
  append-only; cada solicitud es una línea.

## Estado de la confirmación (cliente)

```text
idle → submitting → full → minimized ⇄ expanded
                 ↘ error (reintentar)
```

- `submitting`: botón deshabilitado.
- `full`: tarjeta completa + countdown 10 s + “Minimizar ahora”.
- `minimized`: tarjeta compacta dentro del chat + “Ver detalle completo”.
- `expanded`: tarjeta completa de nuevo, sin countdown.
- `error`: mensaje y reintento; nunca muestra código falso.

## Pantallas del prototipo

| Vista | Ruta | Referencia |
|---|---|---|
| Bienvenida | `/` | `17b56113…` |
| Conversación | `/chat` | `20ebe791…` |
| Asistente de Empaques | `/chat/empaques` | `cb7848c9…` |
| Confirmación completa | estado tras `POST /quotes` | `8045cfc2…` |
| Confirmación minimizada | estado del chat | `194f22dc…` |

## Tokens y activos

- Paleta, tipografía y radios de `docs/design/DESIGN.md`.
- Tailwind config y keyframes copiados del prototipo en `stitch.css`.
- Activos: Carva saludando/escuchando/celebrando, producto, logo.

## Configuración añadida

| Variable | Obligatoria | Defecto | Validación |
|---|---|---|---|
| `QUOTES_LOG_PATH` | no | `.cache/solicitudes.jsonl` | ruta escribible; ignorada por Git |
