"""Pruebas del proveedor con respaldo y del cliente HTTP de Ollama."""

from __future__ import annotations

from collections.abc import Sequence

import pytest
from assistant.llm import FallbackLLM, LLMError, Message


class StubLLM:
    def __init__(self, name: str, text: str = "texto", *, fail: bool = False) -> None:
        self.name = name
        self.provider = name
        self.text = text
        self.fail = fail

    def generate(self, messages: Sequence[Message]) -> str:
        if self.fail:
            raise LLMError(f"{self.name} caído")
        return self.text


def test_fallback_usa_respaldo_si_primario_falla() -> None:
    # Arrange
    primary = StubLLM("deepseek", fail=True)
    fallback = StubLLM("ollama", text="respuesta local")
    llm = FallbackLLM(primary, fallback)

    # Act
    text = llm.generate([Message(role="user", content="hola")])

    # Assert
    assert text == "respuesta local"
    assert llm.provider == "ollama"


def test_fallback_usa_primario_si_responde() -> None:
    # Arrange
    llm = FallbackLLM(StubLLM("deepseek", text="respuesta cloud"), StubLLM("ollama"))

    # Act
    text = llm.generate([Message(role="user", content="hola")])

    # Assert
    assert text == "respuesta cloud"
    assert llm.provider == "deepseek"


def test_fallback_propaga_error_si_ambos_fallan() -> None:
    # Arrange
    llm = FallbackLLM(StubLLM("deepseek", fail=True), StubLLM("ollama", fail=True))

    # Act / Assert
    with pytest.raises(LLMError, match="ollama caído"):
        llm.generate([Message(role="user", content="hola")])
