"""Fixtures compartidas: corpus sintético y dobles de prueba."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import pytest
from assistant.chunking import Fragment
from assistant.config import EMBEDDING_DIM
from assistant.corpus import CorpusDocument, load_corpus
from assistant.llm import Message
from assistant.retrieval import RetrievedFragment

DOC_A_BODY = (
    "Carvajal es una organización multilatinoamericana fundada en 1904 en Cali, Colombia. "
    "Opera en cuatro sectores: papel y empaques, educación, tecnología y servicios, y "
    "comunicación. Su propósito superior es mejorar la calidad de vida de las personas."
)
DOC_B_BODY = (
    "El catálogo de empaques reúne referencias de contenedores, vasos y charolas. "
    "Los precios se expresan en pesos mexicanos y tienen vigencia anual."
)


def write_document(
    gold_dir: Path,
    *,
    slug: str,
    url: str,
    title: str,
    source_type: str = "oficial",
    section: str = "compania",
    body: str,
) -> None:
    """Escribe un documento con front matter válido."""
    front = (
        "---\n"
        f"url: {url}\n"
        f"title: {title}\n"
        f"section: {section}\n"
        f"domain: carvajal.com\n"
        f"source_type: {source_type}\n"
        "captured_at: 2026-11-01T00:00:00+00:00\n"
        f"hash: {'a' * 64}\n"
        f"chars: {len(body)}\n"
        "---\n\n"
    )
    (gold_dir / f"{slug}.md").write_text(front + body, encoding="utf-8")


@pytest.fixture
def gold_dir(tmp_path: Path) -> Path:
    """Corpus sintético de dos documentos con su index.jsonl."""
    directory = tmp_path / "gold"
    directory.mkdir()
    write_document(
        directory,
        slug="compania",
        url="https://www.carvajal.com/compania",
        title="Compañía Carvajal",
        body=DOC_A_BODY,
    )
    write_document(
        directory,
        slug="empaques",
        url="https://www.carvajal.com/empaques",
        title="Empaques Carvajal",
        source_type="tercero",
        section="negocios",
        body=DOC_B_BODY,
    )
    index_lines = [
        {"slug": "compania", "url": "https://www.carvajal.com/compania"},
        {"slug": "empaques", "url": "https://www.carvajal.com/empaques"},
    ]
    (directory / "index.jsonl").write_text(
        "\n".join(json.dumps(line) for line in index_lines) + "\n", encoding="utf-8"
    )
    return directory


@pytest.fixture
def documents(gold_dir: Path) -> list[CorpusDocument]:
    return load_corpus(gold_dir)


@pytest.fixture
def fragments(documents: list[CorpusDocument]) -> list[Fragment]:
    from assistant.chunking import chunk_corpus

    return chunk_corpus(documents)


class FakeEmbedder:
    """Embedder determinista: un eje por tema, sin red."""

    def __init__(self, dim: int = EMBEDDING_DIM) -> None:
        self._dim = dim

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            lower = text.lower()
            vector = [0.0] * self._dim
            if "carvajal" in lower or "sectores" in lower:
                vector[0] = 1.0
            elif "empaques" in lower or "precio" in lower:
                vector[1] = 1.0
            else:
                vector[2] = 1.0
            vectors.append(vector)
        return vectors

    def check(self) -> None:
        return None

    def close(self) -> None:
        return None


class FakeLLM:
    """LLM falso que registra los mensajes recibidos."""

    name = "fake"
    provider = "fake"

    def __init__(self, text: str = "Respuesta de prueba basada en [1].") -> None:
        self.text = text
        self.calls: list[list[Message]] = []

    def generate(self, messages: Sequence[Message]) -> str:
        self.calls.append(list(messages))
        return self.text

    def close(self) -> None:
        return None


def make_retrieved(
    *,
    slug: str = "compania",
    title: str = "Compañía Carvajal",
    url: str = "https://www.carvajal.com/compania",
    source_type: str = "oficial",
    section: str = "compania",
    chunk_index: int = 0,
    text: str = DOC_A_BODY,
    score: float = 0.9,
) -> RetrievedFragment:
    return RetrievedFragment(
        score=score,
        slug=slug,
        url=url,
        title=title,
        source_type=source_type,
        section=section,
        chunk_index=chunk_index,
        text=text,
        char_start=0,
    )


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()
