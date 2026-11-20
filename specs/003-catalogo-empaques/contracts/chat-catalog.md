# Contrato: respuesta de chat con catálogo

**Feature**: `specs/003-catalogo-empaques` · **Fecha**: 2026-11-20

El endpoint `POST /ask` no cambia de forma; cambia el parcial devuelto. La sección de
catálogo es determinista (sin LLM) y la documental conserva el formato actual.

## Parcial de respuesta comercial

```html
<section class="exchange" data-intent="commercial">
  <p class="question">…</p>
  <div class="catalog-section" data-section="catalog">
    <h3>Catálogo</h3>
    <ul class="recommendations">
      <li data-sku="7704918100199" data-country="CO">
        <a href="https://…" rel="noopener noreferrer">Vaso rígido 9 oz</a>
        <span class="material">PET</span>
        <span class="presentation">2500 unidades por caja</span>
        <span class="price" data-validity="vencido">206.305 COP · impuestos incluidos</span>
      </li>
    </ul>
    <ul class="sources">
      <li><a href="https://…" rel="noopener noreferrer">Ficha de la referencia</a></li>
    </ul>
  </div>
</section>
```

- `data-intent`: `documental` \| `commercial` \| `mixed` \| `ambiguous`.
- `data-section="catalog"` marca la sección determinista; `data-section="corpus"` la
  generada por RAG.
- Cada recomendación incluye `data-sku`, `data-country`, material y presentación.
- Cada precio incluye monto, moneda, tratamiento de impuestos, fuente y
  `data-validity` (`vigente` \| `vencido` \| `no_declarada`).
- Con cantidad: se muestran cajas y total además del precio unitario por caja.

## Precio vencido o no declarado

- `data-validity="vencido"` y aviso textual: “precio de referencia vencido el
  AAAA-MM-DD; no es un precio actual”.
- `data-validity="no_declarada"` y aviso: “el precio no declara vigencia”.
- El monto se muestra solo si la fuente lo trae; nunca se estima.

## Sin coincidencia

```html
<section class="exchange" data-status="no_match" data-intent="commercial">
  <p class="question">…</p>
  <div class="answer">
    No encontré una referencia que cumpla: vaso, 12 oz, apto para caliente.
    Puedes ajustar la capacidad o el material.
  </div>
</section>
```

- Se listan las restricciones que no se pudieron cumplir; no se ofrecen alternativas que
  las violen.

## Aclaración

```html
<section class="exchange" data-status="clarification" data-intent="ambiguous">
  <p class="question">…</p>
  <div class="answer">¿Para qué uso y temperatura necesitas el empaque?</div>
</section>
```

## Pregunta mixta

1. Sección `catalog` (determinista) con sus citas.
2. Sección `corpus` (RAG) **solo si** el catálogo no cubre la parte documental.
3. Encabezados visibles “Catálogo” y “Corpus”; citas separadas.

## Consulta de distribuidores

- Lista nombre, ciudad, dirección (si existe), teléfono (si existe) y fuente por
  distribuidor.
- Sin resultados: mensaje explícito, sin contactos inventados.
- Prohibido afirmar inventario, entrega o disponibilidad.

## `GET /healthz` (extensión)

```json
{
  "status": "ok",
  "corpus_documents": 24,
  "collection": "corpus_carvajal",
  "provider": "deepseek",
  "catalog": {"references": 200, "prices": 29, "distributors": 29,
              "fingerprint": "sha256…"}
}
```

- Si el catálogo no carga, la app no arranca (mensaje accionable con `CATALOG_DIR`).

## Invariantes

- Ninguna cifra aparece sin fuente y vigencia declarada.
- Ninguna referencia se recomienda sin ficha.
- País de la referencia y moneda del precio coinciden.
- El texto de la sección de catálogo no proviene del LLM.
