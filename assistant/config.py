"""Configuración del asistente, leída desde variables de entorno (y `.env`)."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

_COLLECTION_RE = re.compile(r"^[a-z0-9_]+$")
_PROVIDERS = ("deepseek", "ollama")
EMBEDDING_DIM = 768


class ConfigError(RuntimeError):
    """Configuración inválida; el mensaje nombra la variable o la ruta a corregir."""


def load_dotenv(path: Path = Path(".env")) -> None:
    """Carga un `.env` simple sin sobrescribir variables ya definidas."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.removeprefix("export ").strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _clean(env: Mapping[str, str], name: str, default: str | None = None) -> str | None:
    raw = env.get(name)
    if raw is None:
        return default
    value = raw.strip()
    return value or default


@dataclass(frozen=True)
class Settings:
    """Configuración validada de la aplicación."""

    corpus_gold_dir: Path
    qdrant_path: Path = Path(".qdrant")
    qdrant_url: str | None = None
    qdrant_collection: str = "corpus_carvajal"
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"
    embedding_dim: int = EMBEDDING_DIM
    llm_provider: str = "deepseek"
    deepseek_api_key: str | None = field(default=None, repr=False)
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    ollama_model: str = "qwen3:4b-instruct"
    top_k: int = 5
    acceptance_file: Path | None = None
    eval_qdrant_path: Path = Path(".qdrant-eval")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        """Construye y valida la configuración; agrega todos los errores."""
        source: Mapping[str, str] = os.environ if env is None else env
        errors: list[str] = []

        corpus_raw = _clean(source, "CORPUS_GOLD_DIR")
        corpus_dir = Path(corpus_raw).expanduser() if corpus_raw else None
        if corpus_dir is None:
            errors.append("Define CORPUS_GOLD_DIR con el directorio del corpus gold.")
        elif not corpus_dir.is_dir():
            errors.append(f"CORPUS_GOLD_DIR no existe o no es un directorio: {corpus_dir}")
        elif not (corpus_dir / "index.jsonl").is_file():
            errors.append(f"CORPUS_GOLD_DIR no contiene index.jsonl: {corpus_dir}")

        qdrant_path = Path(_clean(source, "QDRANT_PATH", ".qdrant") or ".qdrant").expanduser()
        qdrant_url = _clean(source, "QDRANT_URL")
        if qdrant_url is not None and not qdrant_url.startswith(("http://", "https://")):
            errors.append("QDRANT_URL debe empezar por http:// o https://.")

        collection = _clean(source, "QDRANT_COLLECTION", "corpus_carvajal") or "corpus_carvajal"
        if not _COLLECTION_RE.match(collection):
            errors.append("QDRANT_COLLECTION solo admite minúsculas, dígitos y guion bajo.")

        ollama_base = _clean(source, "OLLAMA_BASE_URL", "http://localhost:11434")
        if ollama_base is None or not ollama_base.startswith(("http://", "https://")):
            errors.append("OLLAMA_BASE_URL debe empezar por http:// o https://.")

        embedding_model = _clean(source, "EMBEDDING_MODEL", "nomic-embed-text")
        dim_raw = _clean(source, "EMBEDDING_DIM", str(EMBEDDING_DIM)) or str(EMBEDDING_DIM)
        try:
            embedding_dim = int(dim_raw)
        except ValueError:
            embedding_dim = 0
        if not 1 <= embedding_dim <= 4096:
            errors.append("EMBEDDING_DIM debe ser un entero entre 1 y 4096.")
        provider = (_clean(source, "LLM_PROVIDER", "deepseek") or "deepseek").lower()
        if provider not in _PROVIDERS:
            errors.append("LLM_PROVIDER debe ser deepseek u ollama.")

        api_key = _clean(source, "DEEPSEEK_API_KEY")
        if provider == "deepseek" and api_key is None:
            errors.append("Define DEEPSEEK_API_KEY o usa LLM_PROVIDER=ollama.")

        deepseek_base = _clean(source, "DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        if deepseek_base is None or not deepseek_base.startswith(("http://", "https://")):
            errors.append("DEEPSEEK_BASE_URL debe empezar por http:// o https://.")

        top_raw = _clean(source, "TOP_K", "5") or "5"
        try:
            top_k = int(top_raw)
        except ValueError:
            top_k = 0
        if not 1 <= top_k <= 10:
            errors.append("TOP_K debe ser un entero entre 1 y 10.")

        eval_qdrant_path = Path(
            _clean(source, "EVAL_QDRANT_PATH", ".qdrant-eval") or ".qdrant-eval"
        ).expanduser()

        acceptance_raw = _clean(source, "ACCEPTANCE_FILE")
        acceptance_file = Path(acceptance_raw).expanduser() if acceptance_raw else None
        if acceptance_file is not None and not acceptance_file.is_file():
            errors.append(f"ACCEPTANCE_FILE no existe: {acceptance_file}")

        if errors:
            raise ConfigError("Configuración inválida:\n- " + "\n- ".join(errors))

        assert corpus_dir is not None
        assert ollama_base is not None
        assert embedding_model is not None
        assert deepseek_base is not None
        return cls(
            corpus_gold_dir=corpus_dir,
            qdrant_path=qdrant_path,
            qdrant_url=qdrant_url,
            qdrant_collection=collection,
            ollama_base_url=ollama_base,
            embedding_model=embedding_model,
            embedding_dim=embedding_dim,
            llm_provider=provider,
            deepseek_api_key=api_key,
            deepseek_base_url=deepseek_base,
            deepseek_model=_clean(source, "DEEPSEEK_MODEL", "deepseek-chat") or "deepseek-chat",
            ollama_model=_clean(source, "OLLAMA_MODEL", "qwen3:4b-instruct") or "qwen3:4b-instruct",
            top_k=top_k,
            acceptance_file=acceptance_file,
            eval_qdrant_path=eval_qdrant_path,
        )
