# ADR 0002 — Orquestación RAG propia (sin framework de agentes)

- **Estado**: aceptada
- **Fecha**: 2026-11-21
- **Contexto**: el flujo es lineal (validar → recuperar → prompt → generar → citar) y
  necesita control fino de citas, abstención y streaming.
- **Decisión**: mantener la cadena propia en `assistant/rag.py` y `assistant/prompting.py`,
  sin LangGraph ni framework de agentes.
- **Alternativas**: LangGraph (más dependencias y estado), LlamaIndex (abstracción que
  oculta citas), cadena artesanal (elegida).
- **Consecuencias**: menos dependencias, pruebas deterministas y control total del
  contrato; si aparecen ramas complejas/reintentos se reevalúa.
- **Evidencia**: fases 1–4 con citas, abstención y SSE; `tests/test_rag.py` y suites E2E.
