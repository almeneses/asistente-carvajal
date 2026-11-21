# Quickstart: fidelidad Stitch y solicitud

**Feature**: `specs/005-fidelidad-stitch`

## Arranque

```bash
uv sync
make run          # http://127.0.0.1:8010
```

## Recorrido manual

| Paso | Acción | Resultado esperado |
|---|---|---|
| 1 | Abrir `/` | Bienvenida idéntica al prototipo: Carva, dos tarjetas, footer |
| 2 | “Conversar” | Chat con cabecera, barra de micrófono visual, burbujas y campo |
| 3 | “Empaques” | Flujo de empaques con resumen y recomendación del catálogo |
| 4 | Pedir vasos para café caliente | Tarjeta de recomendación + “Solicitar cotización” |
| 5 | Solicitar cotización | Tarjeta completa con código `OC-…`, total y aviso |
| 6 | Esperar 10 s o “Minimizar ahora” | La tarjeta se minimiza a tarjeta compacta dentro del chat |
| 7 | “Ver detalle completo” | Se expande de nuevo |
| 8 | Repetir con `prefers-reduced-motion` | Cambio instantáneo, sin animación |
| 9 | Revisar `.cache/solicitudes.jsonl` | Una línea por solicitud, sin PII |
| 10 | Probar 390/768/1280 px y teclado | Sin scroll horizontal; foco visible |

## Validación por API

```bash
curl -sS -X POST http://127.0.0.1:8010/quotes \
  -d "sku=MX-VASO-12-PP&boxes=5&city=Ciudad de México&business=Café Origen" | jq
cat .cache/solicitudes.jsonl
```

## Fidelidad visual

- Comparar contra las capturas de Stitch: bienvenida, conversación, empaques,
  confirmación completa y minimizada.
- Checklist mínimo por pantalla: composición, tipografía, paleta, espaciados, iconos,
  estados de botones, responsive.
- Tailwind, fuentes, iconos e imágenes deben ser locales (`0` peticiones a CDN).

## Pruebas

```bash
uv run pytest tests/test_quotes.py tests/test_quotes_web.py \
  tests/test_stitch_templates.py tests/test_stitch_animation.py
make check
```

## Evidencia de la implementación (2026-11-20)

- **172 pruebas** en verde; Ruff y `ty` limpios.
- Pantallas portadas: Bienvenida (`/`), Conversación (`/chat`), Empaques
  (hoy `/chat/empaques` redirige a `/chat`) y Confirmación con minimización/expansión.
- `POST /quotes` validado con el catálogo real: una solicitud quedó registrada en
  `.cache/solicitudes.jsonl` (código `OC-2026-1121-F7A9`) sin PII.
- Assets locales verificados: Tailwind, iconos, DM Sans, Carva y logo (0 CDN).
- Capturas headless de Bienvenida y Conversación comparadas con Stitch; se corrigieron
  el recorte de Carva y el logo.

### Checklist de fidelidad (resumen)

| Pantalla | Composición | Tipografía/color | Componentes | Responsive |
|---|---|---|---|---|
| Bienvenida | ✅ | ✅ | ✅ tarjetas + voz | ✅ |
| Conversación | ✅ | ✅ | ✅ mic + burbujas + compositor | ✅ |
| Empaques | ✅ | ✅ | ✅ resumen + recomendación + CTA | ✅ |
| Confirmación | ✅ | ✅ | ✅ código + total + countdown | ✅ |
| Minimizada | ✅ | ✅ | ✅ compacta + expandir | ✅ |

Pendiente menor: activo fotográfico del producto (la URL de Stitch devuelve 403); las
tarjetas usan los datos y estilos del prototipo sin foto.

## Evidencia esperada

- 4 pantallas portadas y comparadas.
- Animación completa → minimizada → expandida.
- Solicitud real con código y JSONL sin PII.
- Suites 1–4 verdes y CI `Calidad` en verde.
