"""Recuperación de evidencia: pregunta → embedding → búsqueda → fragmentos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from assistant.embeddings import Embedder
from assistant.index import SearchHit


class RetrievalError(RuntimeError):
    """La recuperación no pudo completarse."""


@dataclass(frozen=True)
class RetrievedFragment:
    """Fragmento recuperado con su puntuación y metadatos de cita."""

    score: float
    slug: str
    url: str
    title: str
    source_type: str
    section: str
    chunk_index: int
    text: str
    char_start: int


class Retriever(Protocol):
    """Contrato mínimo de un recuperador."""

    def search(self, question: str, limit: int) -> list[RetrievedFragment]: ...


class SearchIndex(Protocol):
    """Contrato mínimo del índice consultado por el recuperador."""

    def search(self, vector: list[float], limit: int) -> list[SearchHit]: ...


class CorpusRetriever:
    """Recuperador sobre el índice Qdrant del corpus."""

    def __init__(self, embedder: Embedder, index: SearchIndex) -> None:
        self._embedder = embedder
        self._index = index

    def search(self, question: str, limit: int) -> list[RetrievedFragment]:
        vectors = self._embedder.embed([question])
        if len(vectors) != 1:
            raise RetrievalError("El embedder no devolvió un vector para la pregunta.")
        hits = self._index.search(vectors[0], limit=limit)
        fragments: list[RetrievedFragment] = []
        for hit in hits:
            payload = hit.payload
            try:
                fragments.append(
                    RetrievedFragment(
                        score=hit.score,
                        slug=str(payload["slug"]),
                        url=str(payload["url"]),
                        title=str(payload["title"]),
                        source_type=str(payload["source_type"]),
                        section=str(payload["section"]),
                        chunk_index=int(payload["chunk_index"]),
                        text=str(payload["text"]),
                        char_start=int(payload["char_start"]),
                    )
                )
            except (KeyError, TypeError, ValueError) as error:
                raise RetrievalError("El índice devolvió un fragmento sin metadatos.") from error
        return fragments
