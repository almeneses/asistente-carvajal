# Plan: cotizador refinado

- **Backend**: ampliar `QuoteRequest`/`QuoteRecord` con contacto, consentimiento y
  `consent_at`; validación estricta; `POST /quotes` recompone el total y envía correo.
- **Correo**: `assistant/mailer.py` con `smtplib` estándar, configuración SMTP opcional;
  sin `SMTP_HOST` devuelve `not_configured`; nunca loguea contacto.
- **UI**: panel de revisión en `chat.html`/`chat.js` con cajas, ciudad, negocio, nombre,
  correo, teléfono y checkbox de consentimiento; cálculo local informativo y total
  confirmado por el servidor.
- **Detalle**: tarjeta de confirmación con línea completa y botón Imprimir/PDF; CSS
  `@media print` que aísla la cotización.
- **Privacidad**: actualizar constitución y runbook; retención 90 días y borrado manual.
- **Pruebas**: validaciones, email mockeado, no-PII en logs, estructura de UI.
