"""Configuración del asistente, leída desde variables de entorno (y `.env`)."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

_COLLECTION_RE = re.compile(r"^[a-z0-9_]+$")
_PROVIDERS = ("deepseek", "ollama")
EMBEDDING_DIM = 1024


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
    embedding_model: str = "bge-m3"
    embedding_dim: int = EMBEDDING_DIM
    llm_provider: str = "ollama"
    deepseek_api_key: str | None = field(default=None, repr=False)
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    ollama_model: str = "qwen3:4b-instruct"
    top_k: int = 5
    acceptance_file: Path | None = None
    eval_qdrant_path: Path = Path(".qdrant-eval")
    catalog_dir: Path | None = None
    catalog_routing_file: Path | None = None
    catalog_price_today: str | None = None
    feedback_log_path: Path = Path(".cache/feedback.jsonl")
    quotes_log_path: Path = Path(".cache/solicitudes.jsonl")
    log_level: str = "INFO"
    log_format: str = "json"
    auth_enabled: bool = False
    auth_secret: str | None = None
    auth_users: dict[str, str] = field(default_factory=dict)
    auth_admins: tuple[str, ...] = ()
    auth_cookie_secure: bool = False
    session_ttl_seconds: int = 8 * 3600
    rate_limit_per_minute: int = 30
    quote_daily_limit: int = 50
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = field(default=None, repr=False)
    smtp_from: str | None = None
    smtp_tls: bool = True
    quote_retention_days: int = 90

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

        embedding_model = _clean(source, "EMBEDDING_MODEL", "bge-m3")
        dim_raw = _clean(source, "EMBEDDING_DIM", str(EMBEDDING_DIM)) or str(EMBEDDING_DIM)
        try:
            embedding_dim = int(dim_raw)
        except ValueError:
            embedding_dim = 0
        if not 1 <= embedding_dim <= 4096:
            errors.append("EMBEDDING_DIM debe ser un entero entre 1 y 4096.")
        provider = (_clean(source, "LLM_PROVIDER", "ollama") or "ollama").lower()
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

        catalog_raw = _clean(source, "CATALOG_DIR")
        catalog_dir = Path(catalog_raw).expanduser() if catalog_raw else None
        if catalog_dir is not None:
            required = (
                "referencias.csv",
                "precios.csv",
                "materiales.csv",
                "distribuidores.csv",
                "manifest.json",
            )
            if not catalog_dir.is_dir():
                errors.append(f"CATALOG_DIR no existe: {catalog_dir}")
            else:
                missing = [name for name in required if not (catalog_dir / name).is_file()]
                if missing:
                    errors.append(f"CATALOG_DIR no contiene: {', '.join(missing)}")

        routing_raw = _clean(source, "CATALOG_ROUTING_FILE")
        catalog_routing_file = Path(routing_raw).expanduser() if routing_raw else None
        if catalog_routing_file is not None and not catalog_routing_file.is_file():
            errors.append(f"CATALOG_ROUTING_FILE no existe: {catalog_routing_file}")

        feedback_raw = _clean(source, "FEEDBACK_LOG_PATH")
        feedback_log_path = Path(feedback_raw or ".cache/feedback.jsonl").expanduser()
        quotes_raw = _clean(source, "QUOTES_LOG_PATH")
        quotes_log_path = Path(quotes_raw or ".cache/solicitudes.jsonl").expanduser()
        log_level = (_clean(source, "LOG_LEVEL") or "INFO").upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            errors.append("LOG_LEVEL debe ser DEBUG, INFO, WARNING, ERROR o CRITICAL.")
        log_format = (_clean(source, "LOG_FORMAT") or "json").lower()
        if log_format not in {"json", "text"}:
            errors.append("LOG_FORMAT debe ser json o text.")
        auth_enabled = (_clean(source, "AUTH_ENABLED") or "false").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        auth_secret = _clean(source, "AUTH_SECRET")
        auth_users_raw = _clean(source, "AUTH_USERS") or "{}"
        try:
            parsed_users = json.loads(auth_users_raw)
            if not isinstance(parsed_users, dict) or not all(
                isinstance(k, str) and isinstance(v, str) for k, v in parsed_users.items()
            ):
                raise ValueError
            auth_users = {str(k): str(v) for k, v in parsed_users.items()}
        except ValueError:
            auth_users = {}
            errors.append("AUTH_USERS debe ser un JSON objeto usuario→hash.")
        auth_admins = tuple(
            item.strip()
            for item in (_clean(source, "AUTH_ADMINS") or "").split(",")
            if item.strip()
        )
        auth_cookie_secure = (_clean(source, "AUTH_COOKIE_SECURE") or "false").lower() in {
            "1",
            "true",
            "yes",
        }
        if auth_enabled and (not auth_secret or len(auth_secret) < 32):
            errors.append("AUTH_SECRET debe tener al menos 32 caracteres si AUTH_ENABLED=true.")
        if auth_enabled and not auth_users:
            errors.append("Define AUTH_USERS con al menos un usuario si AUTH_ENABLED=true.")
        try:
            rate_limit_per_minute = int(_clean(source, "RATE_LIMIT_PER_MINUTE") or "30")
            quote_daily_limit = int(_clean(source, "QUOTE_DAILY_LIMIT") or "50")
            if rate_limit_per_minute < 1 or quote_daily_limit < 1:
                raise ValueError
        except ValueError:
            errors.append("RATE_LIMIT_PER_MINUTE y QUOTE_DAILY_LIMIT deben ser enteros ≥ 1.")
            rate_limit_per_minute, quote_daily_limit = 30, 50
        smtp_host = _clean(source, "SMTP_HOST")
        smtp_from = _clean(source, "SMTP_FROM")
        if smtp_host and not smtp_from:
            errors.append("SMTP_FROM es obligatorio si SMTP_HOST está definido.")
        try:
            smtp_port = int(_clean(source, "SMTP_PORT") or "587")
            quote_retention_days = int(_clean(source, "QUOTE_RETENTION_DAYS") or "90")
            if smtp_port < 1 or quote_retention_days < 1:
                raise ValueError
        except ValueError:
            errors.append("SMTP_PORT y QUOTE_RETENTION_DAYS deben ser enteros ≥ 1.")
            smtp_port, quote_retention_days = 587, 90
        smtp_user = _clean(source, "SMTP_USER")
        smtp_password = _clean(source, "SMTP_PASSWORD")
        smtp_tls = (_clean(source, "SMTP_TLS") or "true").lower() in {"1", "true", "yes"}

        price_today = _clean(source, "CATALOG_PRICE_TODAY")
        if price_today is not None:
            try:
                date.fromisoformat(price_today)
            except ValueError:
                errors.append("CATALOG_PRICE_TODAY debe ser una fecha ISO (AAAA-MM-DD).")

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
            catalog_dir=catalog_dir,
            catalog_routing_file=catalog_routing_file,
            catalog_price_today=price_today,
            feedback_log_path=feedback_log_path,
            quotes_log_path=quotes_log_path,
            log_level=log_level,
            log_format=log_format,
            auth_enabled=auth_enabled,
            auth_secret=auth_secret,
            auth_users=auth_users,
            auth_admins=auth_admins,
            auth_cookie_secure=auth_cookie_secure,
            rate_limit_per_minute=rate_limit_per_minute,
            quote_daily_limit=quote_daily_limit,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            smtp_from=smtp_from,
            smtp_tls=smtp_tls,
            quote_retention_days=quote_retention_days,
        )
