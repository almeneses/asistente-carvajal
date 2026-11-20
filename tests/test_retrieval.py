"""Pruebas del recuperador con un Qdrant embebido real."""

from __future__ import annotations

from pathlib import Path

import pytest
from assistant.chunking import chunk_corpus
from assistant.config import EMBEDDING_DIM
from assistant.corpus import CorpusDocument
from assistant.index import IndexError as QdrantIndexError
from assistant.index import QdrantIndex, SearchHit
from assistant.retrieval import CorpusRetriever, RetrievalError
from qdrant_client import QdrantClient
from tests.conftest import FakeEmbedder


def test_recupera_fragmento_relevante(tmp_path: Path, documents: list[CorpusDocument]) -> None:
    # Arrange
    embedder = FakeEmbedder()
    fragments = chunk_corpus(documents)
    vectors = embedder.embed([fragment.text for fragment in fragments])
    index = QdrantIndex(QdrantClient(path=str(tmp_path / "qdrant")), "test_corpus")
    try:
        index.ensure_collection(recreate=True)
        index.upsert(fragments, vectors)
        retriever = CorpusRetriever(embedder, index)

        # Act
        hits = retriever.search("¿Qué es Carvajal?", 3)

        # Assert
        assert hits
        assert hits[0].slug == "compania"
        assert hits[0].score >= 0.9
    finally:
        index.close()


class BrokenIndex:
    """Índice que devuelve un payload incompleto."""

    def search(self, vector: list[float], limit: int) -> list[SearchHit]:
        return [SearchHit(score=0.9, payload={"slug": "x"})]


def test_fragmento_sin_metadatos_falla() -> None:
    # Arrange
    retriever = CorpusRetriever(  # type: ignore[arg-type]
        FakeEmbedder(),
        BrokenIndex(),  # type: ignore[arg-type]
    )

    # Act / Assert
    with pytest.raises(RetrievalError, match="metadatos"):
        retriever.search("pregunta", 5)


def test_error_de_indice_se_propaga(tmp_path: Path) -> None:
    # Arrange
    index = QdrantIndex(QdrantClient(path=str(tmp_path / "qdrant")), "inexistente")

    # Act / Assert
    with pytest.raises(QdrantIndexError):
        index.search([0.0] * EMBEDDING_DIM, 1)
    index.close()
