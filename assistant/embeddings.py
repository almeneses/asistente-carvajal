"""Embeddings locales sobre Ollama, vía su API HTTP."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

import httpx

from assistant.config import EMBEDDING_DIM


class EmbeddingError(RuntimeError):
    """No se pudieron obtener embeddings válidos."""


class Embedder(Protocol):
    """Contrato mínimo de un proveedor de embeddings."""

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class OllamaEmbedder:
    """Embedder que usa `POST {base}/api/embed` de Ollama."""

    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        dim: int = EMBEDDING_DIM,
        client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._dim = dim
        self._client = client or httpx.Client(timeout=timeout)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = self._client.post(
                f"{self._base_url}/api/embed",
                json={"model": self._model, "input": list(texts)},
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise EmbeddingError(
                f"No se pudo conectar con Ollama en {self._base_url}: {error}"
            ) from error
        payload = response.json()
        embeddings = payload.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise EmbeddingError("Ollama devolvió un número de embeddings inesperado.")
        vectors: list[list[float]] = []
        for vector in embeddings:
            if not isinstance(vector, list) or len(vector) != self._dim:
                raise EmbeddingError(
                    f"El modelo {self._model!r} no devolvió vectores de {self._dim} dims."
                )
            vectors.append([float(value) for value in vector])
        return vectors

    def check(self) -> None:
        """Comprueba que Ollama responde (validación de arranque)."""
        try:
            response = self._client.get(f"{self._base_url}/api/tags", timeout=2.0)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise EmbeddingError(
                f"Ollama no responde en {self._base_url}; revisa OLLAMA_BASE_URL."
            ) from error

    def close(self) -> None:
        self._client.close()
