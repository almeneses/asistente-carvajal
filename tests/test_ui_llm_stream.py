"""Pruebas del streaming con respaldo de proveedores."""

from __future__ import annotations

from collections.abc import Iterator, Sequence

import pytest
from assistant.llm import FallbackLLM, LLMError, Message


class FakeStreamingLLM:
    def __init__(self, name: str, tokens: Sequence[str], *, fail: bool = False) -> None:
        self.name = name
        self.provider = name
        self.tokens = tuple(tokens)
        self.fail = fail

    def generate(self, messages: Sequence[Message]) -> str:
        if self.fail:
            raise LLMError(f"{self.name} caído")
        return "".join(self.tokens)

    def stream(self, messages: Sequence[Message]) -> Iterator[str]:
        if self.fail:
            raise LLMError(f"{self.name} caído")
        yield from self.tokens

    def close(self) -> None:
        return None


def test_stream_primario_ok() -> None:
    # Arrange
    llm = FallbackLLM(
        FakeStreamingLLM("deepseek", ("Hola ", "mundo")),
        FakeStreamingLLM("ollama", ("respaldo",)),
    )

    # Act
    text = "".join(llm.stream([Message(role="user", content="hola")]))

    # Assert
    assert text == "Hola mundo"
    assert llm.provider == "deepseek"


def test_stream_cae_al_respaldo_si_falla_antes_del_primer_token() -> None:
    # Arrange
    llm = FallbackLLM(
        FakeStreamingLLM("deepseek", ("no",), fail=True),
        FakeStreamingLLM("ollama", ("respuesta ", "local")),
    )

    # Act
    text = "".join(llm.stream([Message(role="user", content="hola")]))

    # Assert
    assert text == "respuesta local"
    assert llm.provider == "ollama"


def test_stream_propaga_error_si_ambos_fallan() -> None:
    # Arrange
    llm = FallbackLLM(
        FakeStreamingLLM("deepseek", ("no",), fail=True),
        FakeStreamingLLM("ollama", ("no",), fail=True),
    )

    # Act / Assert
    with pytest.raises(LLMError, match="ollama caído"):
        list(llm.stream([Message(role="user", content="hola")]))
