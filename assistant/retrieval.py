"""Recuperación de evidencia: embedding + reordenamiento léxico (híbrido)."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Protocol

from assistant.embeddings import Embedder
from assistant.index import SearchHit

CANDIDATES = 200
LEXICAL_WEIGHT = 0.4
EMBEDDING_WEIGHT = 0.6
_STOPWORDS = frozenset(
    {
        "que",
        "qué",
        "como",
        "cómo",
        "cual",
        "cuál",
        "cuales",
        "cuáles",
        "cuando",
        "cuándo",
        "donde",
        "dónde",
        "para",
        "por",
        "con",
        "sin",
        "los",
        "las",
        "del",
        "una",
        "unos",
        "unas",
        "este",
        "esta",
        "estos",
        "estas",
        "ese",
        "esa",
        "sus",
        "mas",
        "más",
        "pero",
        "entre",
        "sobre",
        "desde",
        "hasta",
        "tiene",
        "tienen",
        "hace",
        "hacen",
        "ofrece",
        "ofrecen",
        "forma",
        "conforman",
    }
)


# Sinónimos de dominio para preguntas cuya formulación no aparece literalmente en el corpus.
_SYNONYMS = {
    "empleado": "colaborador",
    "empleados": "colaborador",
    "fundado": "fundacion",
    "fundada": "fundacion",
    "contacto": "contactar",
}


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


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9ñ]+", " ", without_accents)


def _stems(text: str) -> set[str]:
    """Tallo crudo de 5 letras: basta para unir singular/plural y derivados."""
    return {
        token[:5]
        for token in _normalize(text).split()
        if len(token) > 2 and token not in _STOPWORDS
    }


def _lexical_overlap(question_stems: set[str], text: str, title: str) -> float:
    if not question_stems:
        return 0.0
    text_stems = _stems(text) | _stems(title)
    matches = len(question_stems & text_stems)
    return matches / len(question_stems)


class CorpusRetriever:
    """Recuperador híbrido sobre el índice Qdrant del corpus."""

    def __init__(self, embedder: Embedder, index: SearchIndex) -> None:
        self._embedder = embedder
        self._index = index

    def search(self, question: str, limit: int) -> list[RetrievedFragment]:
        vectors = self._embedder.embed([question])
        if len(vectors) != 1:
            raise RetrievalError("El embedder no devolvió un vector para la pregunta.")
        expanded = (
            question
            + " "
            + " ".join(synonym for token, synonym in _SYNONYMS.items() if token in question.lower())
        )
        question_stems = _stems(expanded)
        candidates = self._index.search(vectors[0], limit=max(limit, CANDIDATES))
        fragments: list[RetrievedFragment] = []
        for hit in candidates:
            payload = hit.payload
            try:
                title = str(payload["title"])
                text = str(payload["text"])
                fragment = RetrievedFragment(
                    score=hit.score,
                    slug=str(payload["slug"]),
                    url=str(payload["url"]),
                    title=title,
                    source_type=str(payload["source_type"]),
                    section=str(payload["section"]),
                    chunk_index=int(payload["chunk_index"]),
                    text=text,
                    char_start=int(payload["char_start"]),
                )
            except (KeyError, TypeError, ValueError) as error:
                raise RetrievalError("El índice devolvió un fragmento sin metadatos.") from error
            lexical = _lexical_overlap(question_stems, fragment.text, fragment.title)
            combined = EMBEDDING_WEIGHT * fragment.score + LEXICAL_WEIGHT * lexical
            fragments.append(
                RetrievedFragment(
                    score=combined,
                    slug=fragment.slug,
                    url=fragment.url,
                    title=fragment.title,
                    source_type=fragment.source_type,
                    section=fragment.section,
                    chunk_index=fragment.chunk_index,
                    text=fragment.text,
                    char_start=fragment.char_start,
                )
            )
        fragments.sort(key=lambda fragment: fragment.score, reverse=True)
        return fragments[:limit]
