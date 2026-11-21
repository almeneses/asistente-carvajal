# Feature Specification: Cotizador refinado

**Branch**: `feat/011-cotizador-refinado` · **Fase**: 11

## Objetivo

Convertir el CTA actual (que registra de inmediato) en un flujo de revisión y confirmación:
elegir cajas, ciudad/negocio y contacto con consentimiento; ver el total recalculado;
confirmar; obtener detalle con código, impresión/PDF y envío por correo.

## User Scenarios

### US1 · Revisar antes de enviar (P1)
- **Given** una recomendación, **When** pulso “Solicitar cotización”, **Then** se abre un resumen editable con cajas, ciudad, negocio y contacto.
- **Given** cambio las cajas, **Then** veo unidades y total recalculados antes de confirmar.
- **Given** confirmo, **Then** se registra una sola solicitud con el total del servidor.

### US2 · Detalle, impresión y PDF (P1)
- **Given** una solicitud enviada, **Then** veo código, producto, cajas, unidades, precio unitario, total, ciudad y vigencia.
- **Given** pulso “Imprimir/PDF”, **Then** se imprime solo la cotización.

### US3 · Envío por correo (P2)
- **Given** un correo de contacto con consentimiento, **When** confirmo, **Then** el sistema intenta enviar la cotización; si SMTP no está configurado, lo informa sin fallar la solicitud.

### US4 · Privacidad y consentimiento (P1)
- **Given** el formulario, **Then** el contacto es opcional pero requiere consentimiento explícito y al menos un canal (correo o teléfono).
- **Given** logs/métricas, **Then** no aparecen nombre, correo ni teléfono.

## Requirements

- **FR-001**: Revisión editable antes de registrar (cajas 1..999, ciudad/negocio ≤80).
- **FR-002**: Contacto: nombre (≤120), correo (válido, ≤120), teléfono (≤40), al menos uno; consentimiento obligatorio.
- **FR-003**: `POST /quotes` valida consentimiento y contacto; recalcula total desde catálogo.
- **FR-004**: Respuesta incluye detalle de línea, unidades, precio unitario, total, moneda y `email_status`.
- **FR-005**: Confirmación con botón Imprimir/PDF y CSS de impresión dedicado.
- **FR-006**: Envío por correo mediante SMTP configurable; sin SMTP → `not_configured`.
- **FR-007**: No registrar contacto en logs/métricas; JSONL local con retención documentada.
- **FR-008**: Actualizar política de PII de la constitución (consentimiento, minimización, retención, borrado manual).
- **FR-009**: Errores de validación claros y accesibles; reintento sin duplicar.
- **FR-010**: Sin regresiones en chat, catálogo, cuotas, auth ni gates.

## Success Criteria

- **SC-001**: 0 solicitudes registradas sin consentimiento.
- **SC-002**: Total mostrado = total recalculado por el servidor.
- **SC-003**: Impresión/PDF muestra solo la cotización.
- **SC-004**: Correo enviado con SMTP de prueba; sin SMTP no rompe el flujo.
- **SC-005**: 0 PII en logs/métricas.
- **SC-006**: CI, Ruff, ty y gates en verde.
