"""Clientes de generación: DeepSeek como primario y Ollama como respaldo."""

from __future__ import annotations

import json
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Protocol

import httpx

from assistant.config import Settings

MAX_TOKENS = 800
DEEPSEEK_TIMEOUT = 8.0
OLLAMA_TIMEOUT = 60.0  # incluye la carga en frío del modelo local


class LLMError(RuntimeError):
    """No se pudo generar una respuesta con ningún proveedor."""


@dataclass(frozen=True)
class Message:
    role: str
    content: str


class LLM(Protocol):
    """Contrato mínimo de un proveedor de generación."""

    name: str
    provider: str

    def generate(self, messages: Sequence[Message]) -> str: ...


def _as_json_messages(messages: Sequence[Message]) -> list[dict[str, str]]:
    return [{"role": message.role, "content": message.content} for message in messages]


class DeepSeekLLM:
    """Cliente OpenAI-compatible de DeepSeek."""

    name = "deepseek"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        *,
        client: httpx.Client | None = None,
        timeout: float = DEEPSEEK_TIMEOUT,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = client or httpx.Client(timeout=timeout)
        self.provider = "deepseek"

    def generate(self, messages: Sequence[Message]) -> str:
        try:
            response = self._client.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": _as_json_messages(messages),
                    "temperature": 0,
                    "max_tokens": MAX_TOKENS,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise LLMError(f"DeepSeek no respondió: {error}") from error
        payload = response.json()
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise LLMError("DeepSeek devolvió una respuesta con formato inesperado.") from error
        if not isinstance(content, str) or not content.strip():
            raise LLMError("DeepSeek devolvió una respuesta vacía.")
        return content.strip()

    def stream(self, messages: Sequence[Message]) -> Iterator[str]:
        try:
            with self._client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": _as_json_messages(messages),
                    "temperature": 0,
                    "max_tokens": MAX_TOKENS,
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        data = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    choices = data.get("choices") or []
                    delta = choices[0].get("delta", {}) if choices else {}
                    content = delta.get("content")
                    if isinstance(content, str) and content:
                        yield content
        except httpx.HTTPError as error:
            raise LLMError(f"DeepSeek no respondió: {error}") from error

    def close(self) -> None:
        self._client.close()


class OllamaLLM:
    """Cliente de chat local de Ollama."""

    name = "ollama"

    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        client: httpx.Client | None = None,
        timeout: float = OLLAMA_TIMEOUT,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = client or httpx.Client(timeout=timeout)
        self.provider = "ollama"

    def generate(self, messages: Sequence[Message]) -> str:
        try:
            response = self._client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": _as_json_messages(messages),
                    "stream": False,
                    "options": {"temperature": 0, "num_predict": MAX_TOKENS},
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise LLMError(f"Ollama no respondió: {error}") from error
        payload = response.json()
        content = payload.get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise LLMError("Ollama devolvió una respuesta vacía.")
        return content.strip()

    def stream(self, messages: Sequence[Message]) -> Iterator[str]:
        try:
            with self._client.stream(
                "POST",
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": _as_json_messages(messages),
                    "stream": True,
                    "options": {"temperature": 0, "num_predict": MAX_TOKENS},
                },
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    content = (data.get("message") or {}).get("content")
                    if isinstance(content, str) and content:
                        yield content
                    if data.get("done"):
                        break
        except httpx.HTTPError as error:
            raise LLMError(f"Ollama no respondió: {error}") from error

    def close(self) -> None:
        self._client.close()


class FallbackLLM:
    """Usa el proveedor primario y, si falla, el de respaldo."""

    name = "fallback"

    def __init__(self, primary: LLM, fallback: LLM) -> None:
        self._primary = primary
        self._fallback = fallback
        self.provider = primary.provider

    def generate(self, messages: Sequence[Message]) -> str:
        try:
            text = self._primary.generate(messages)
            self.provider = self._primary.provider
            return text
        except LLMError:
            text = self._fallback.generate(messages)
            self.provider = self._fallback.provider
            return text

    def stream(self, messages: Sequence[Message]) -> Iterator[str]:
        def _stream(provider: LLM) -> Iterator[str]:
            stream = getattr(provider, "stream", None)
            if callable(stream):
                yield from stream(messages)
            else:
                yield provider.generate(messages)

        try:
            iterator = _stream(self._primary)
            first = next(iterator)
        except LLMError:
            fallback_iterator = _stream(self._fallback)
            first = next(fallback_iterator)
            self.provider = self._fallback.provider
            yield first
            yield from fallback_iterator
            return
        self.provider = self._primary.provider
        yield first
        yield from iterator

    def close(self) -> None:
        for provider in (self._primary, self._fallback):
            close = getattr(provider, "close", None)
            if callable(close):
                close()


def build_llm(settings: Settings) -> LLM:
    """Construye el proveedor configurado (con respaldo si es DeepSeek)."""
    ollama = OllamaLLM(settings.ollama_base_url, settings.ollama_model)
    if settings.llm_provider == "deepseek":
        assert settings.deepseek_api_key is not None
        primary = DeepSeekLLM(
            settings.deepseek_api_key,
            settings.deepseek_base_url,
            settings.deepseek_model,
        )
        return FallbackLLM(primary, ollama)
    return ollama
