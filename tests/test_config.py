"""Pruebas de la configuración desde entorno."""

from __future__ import annotations

from pathlib import Path

import pytest
from assistant.config import ConfigError, Settings

BASE_ENV: dict[str, str] = {"LLM_PROVIDER": "ollama"}


def test_config_proveedor_por_defecto_ollama(gold_dir: Path) -> None:
    # Arrange / Act
    settings = Settings.from_env({"CORPUS_GOLD_DIR": str(gold_dir)})

    # Assert
    assert settings.llm_provider == "ollama"


def _env(gold_dir: Path, **overrides: str) -> dict[str, str]:
    env = {**BASE_ENV, "CORPUS_GOLD_DIR": str(gold_dir), **overrides}
    return env


def test_config_ollama_sin_clave(gold_dir: Path) -> None:
    # Arrange / Act
    settings = Settings.from_env(_env(gold_dir))

    # Assert
    assert settings.llm_provider == "ollama"
    assert settings.deepseek_api_key is None
    assert settings.top_k == 5
    assert settings.qdrant_collection == "corpus_carvajal"


def test_config_falta_corpus() -> None:
    # Arrange / Act / Assert
    with pytest.raises(ConfigError, match="CORPUS_GOLD_DIR"):
        Settings.from_env({"LLM_PROVIDER": "ollama"})


def test_config_ruta_corpus_inexistente(tmp_path: Path) -> None:
    # Arrange
    env = _env(tmp_path / "no-existe")

    # Act / Assert
    with pytest.raises(ConfigError, match="no existe"):
        Settings.from_env(env)


def test_config_deepseek_sin_clave(gold_dir: Path) -> None:
    # Arrange
    env = _env(gold_dir, LLM_PROVIDER="deepseek", DEEPSEEK_API_KEY="")

    # Act / Assert
    with pytest.raises(ConfigError, match="DEEPSEEK_API_KEY"):
        Settings.from_env(env)


def test_config_top_k_fuera_de_rango(gold_dir: Path) -> None:
    # Arrange
    env = _env(gold_dir, TOP_K="99")

    # Act / Assert
    with pytest.raises(ConfigError, match="TOP_K"):
        Settings.from_env(env)


def test_config_coleccion_invalida(gold_dir: Path) -> None:
    # Arrange
    env = _env(gold_dir, QDRANT_COLLECTION="Colección-Mala")

    # Act / Assert
    with pytest.raises(ConfigError, match="QDRANT_COLLECTION"):
        Settings.from_env(env)


def test_config_agrega_varios_errores() -> None:
    # Arrange / Act
    with pytest.raises(ConfigError) as excinfo:
        Settings.from_env({"LLM_PROVIDER": "otro", "TOP_K": "0"})

    # Assert
    assert "CORPUS_GOLD_DIR" in str(excinfo.value)
    assert "LLM_PROVIDER" in str(excinfo.value)
    assert "TOP_K" in str(excinfo.value)
