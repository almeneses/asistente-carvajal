"""Fragmentación determinista del corpus para indexar y citar."""

from __future__ import annotations

from dataclasses import dataclass

from assistant.corpus import CorpusDocument

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_OVERLAP = 200


@dataclass(frozen=True)
class Fragment:
    """Unidad recuperable derivada de un documento, con su rastro de cita."""

    slug: str
    url: str
    title: str
    source_type: str
    section: str
    chunk_index: int
    text: str
    char_start: int


def chunk_document(
    document: CorpusDocument,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Fragment]:
    """Divide el cuerpo del documento en ventanas con solape."""
    if chunk_size <= 0:
        raise ValueError("chunk_size debe ser mayor que cero.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap debe estar entre 0 y chunk_size - 1.")

    body = document.body
    fragments: list[Fragment] = []
    start = 0
    while start < len(body):
        end = min(start + chunk_size, len(body))
        fragments.append(
            Fragment(
                slug=document.slug,
                url=document.url,
                title=document.title,
                source_type=document.source_type,
                section=document.section,
                chunk_index=len(fragments),
                text=body[start:end],
                char_start=start,
            )
        )
        if end == len(body):
            break
        start = end - overlap
    return fragments


def chunk_corpus(
    documents: list[CorpusDocument],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Fragment]:
    """Fragmenta todos los documentos, en orden estable por slug."""
    fragments: list[Fragment] = []
    for document in sorted(documents, key=lambda item: item.slug):
        fragments.extend(chunk_document(document, chunk_size=chunk_size, overlap=overlap))
    return fragments
