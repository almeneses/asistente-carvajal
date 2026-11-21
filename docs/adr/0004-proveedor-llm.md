# ADR 0004 — Ollama local como proveedor por defecto

- **Estado**: aceptada
- **Fecha**: 2026-11-21
- **Contexto**: el proyecto debe funcionar sin cuentas ni claves y ser reproducible en
  local/CI; DeepSeek ofrece mejor calidad a cambio de red y clave.
- **Decisión**: `LLM_PROVIDER=ollama` por defecto. DeepSeek queda opt-in
  (`LLM_PROVIDER=deepseek` + `DEEPSEEK_API_KEY`) y conserva fallback a Ollama.
- **Alternativas**: DeepSeek por defecto (fricción de clave), solo nube (sin offline),
  solo local (menor calidad en casos complejos).
- **Consecuencias**: arranque sin secretos y operación offline; para producción con
  calidad máxima se recomienda DeepSeek. Se documenta en `.env.example` y README.
- **Evidencia**: `build_llm`, `tests/test_config.py`, `.env.example`.
