# Evaluación continua

## Reportes

| Reporte | Qué mide |
|---|---|
| `specs/002-evaluacion-recuperacion/reports/ganadora.json` | Variante ganadora: hit@5, citas, abstención. |
| `specs/003-catalogo-empaques/reports/acceptance.json` | Enrutamiento, atributos, cotizaciones y violaciones prohibidas. |

## Gates

```bash
make quality-gates
```

Umbrales actuales:

- hit@5 ≥ 0.90
- citation_precision ≥ 0.95
- abstention_accuracy ≥ 0.95
- expected_citation_coverage ≥ 0.90
- route/attributes/quote accuracy ≥ 0.95
- 0 violaciones de material prohibido

El gate corre en CI y falla con el detalle si algún valor baja.

## Reejecutar evaluación

```bash
make gt-propose      # proponer/actualizar ground truth (revisar)
make eval            # matriz de recuperación
make eval-e2e        # evaluación end-to-end
make catalog-acceptance
make quality-gates
```

Los reportes se versionan para comparar tendencias; no incluyas preguntas con datos
personales.
