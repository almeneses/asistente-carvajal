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

## Evidencia esperada

- 4 pantallas portadas y comparadas.
- Animación completa → minimizada → expandida.
- Solicitud real con código y JSONL sin PII.
- Suites 1–4 verdes y CI `Calidad` en verde.
