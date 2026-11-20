"""Índice vectorial Qdrant: creación, carga y búsqueda por similitud."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from assistant.chunking import Fragment
from assistant.config import EMBEDDING_DIM, Settings

_NAMESPACE = uuid.UUID("6f6c1c1e-0b7a-4f7e-9a53-3d3a4f0e4b1c")


class IndexError(RuntimeError):
    """El índice no está disponible o no cumple el esquema esperado."""


@dataclass(frozen=True)
class SearchHit:
    """Coincidencia recuperada del índice."""

    score: float
    payload: dict[str, Any]


def _point_id(slug: str, chunk_index: int) -> str:
    return str(uuid.uuid5(_NAMESPACE, f"{slug}:{chunk_index}"))


class QdrantIndex:
    """Envoltorio mínimo sobre Qdrant para el corpus del asistente."""

    def __init__(self, client: QdrantClient, collection: str, dim: int = EMBEDDING_DIM) -> None:
        self._client = client
        self.collection = collection
        self._dim = dim

    @classmethod
    def open(cls, settings: Settings) -> QdrantIndex:
        try:
            if settings.qdrant_url:
                client = QdrantClient(url=settings.qdrant_url)
            else:
                client = QdrantClient(path=str(settings.qdrant_path))
        except Exception as error:  # pragma: no cover - depende del entorno
            raise IndexError(f"No se pudo abrir Qdrant: {error}") from error
        return cls(client, settings.qdrant_collection)

    def ensure_collection(self, *, recreate: bool = False) -> None:
        """Crea la colección (o la recrea) y verifica la dimensión."""
        try:
            exists = self._client.collection_exists(self.collection)
            if recreate and exists:
                self._client.delete_collection(self.collection)
                exists = False
            if not exists:
                self._client.create_collection(
                    collection_name=self.collection,
                    vectors_config=VectorParams(size=self._dim, distance=Distance.COSINE),
                )
            self._check_dimension()
        except Exception as error:
            raise IndexError(
                f"No se pudo preparar la colección {self.collection!r}: {error}"
            ) from error

    def _check_dimension(self) -> None:
        info = self._client.get_collection(self.collection)
        vectors: Any = info.config.params.vectors
        size = getattr(vectors, "size", None)
        if size is None and isinstance(vectors, dict):
            first = next(iter(vectors.values()), None)
            size = getattr(first, "size", None)
        if size is not None and int(size) != self._dim:
            raise IndexError(
                f"La colección {self.collection!r} usa {size} dims; se esperaban {self._dim}."
            )

    def upsert(self, fragments: list[Fragment], vectors: list[list[float]]) -> None:
        if len(fragments) != len(vectors):
            raise IndexError("Fragmentos y vectores no coinciden en número.")
        points = [
            PointStruct(
                id=_point_id(fragment.slug, fragment.chunk_index),
                vector=vector,
                payload={
                    "slug": fragment.slug,
                    "url": fragment.url,
                    "title": fragment.title,
                    "source_type": fragment.source_type,
                    "section": fragment.section,
                    "chunk_index": fragment.chunk_index,
                    "text": fragment.text,
                    "char_start": fragment.char_start,
                },
            )
            for fragment, vector in zip(fragments, vectors, strict=True)
        ]
        try:
            self._client.upsert(collection_name=self.collection, points=points, wait=True)
        except Exception as error:
            raise IndexError(f"No se pudo indexar en Qdrant: {error}") from error

    def search(self, vector: list[float], limit: int) -> list[SearchHit]:
        try:
            response = self._client.query_points(
                collection_name=self.collection,
                query=vector,
                limit=limit,
                with_payload=True,
            )
        except Exception as error:
            raise IndexError(f"No se pudo consultar Qdrant: {error}") from error
        return [
            SearchHit(score=float(point.score), payload=dict(point.payload or {}))
            for point in response.points
        ]

    def count(self) -> int:
        try:
            result = self._client.count(self.collection, exact=True)
        except Exception as error:
            raise IndexError(
                f"No se pudo contar la colección {self.collection!r}: {error}"
            ) from error
        return int(result.count)

    def is_ready(self) -> bool:
        try:
            return self._client.collection_exists(self.collection) and self.count() > 0
        except Exception:
            return False

    def close(self) -> None:
        self._client.close()
