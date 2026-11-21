"""Cadena RAG: recuperar evidencia, generar y devolver respuesta con citas."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from time import perf_counter
from typing import Protocol
from uuid import uuid4

from assistant.llm import LLM
from assistant.prompting import NO_EVIDENCE_TEXT, build_messages
from assistant.retrieval import RetrievedFragment, Retriever

MIN_SCORE = 0.2
MAX_QUESTION_CHARS = 2000
MAX_SOURCES = 5
REFUSAL_MARKER = "no encontré evidencia"


class Rag(Protocol):
    """Contrato de la cadena que responde preguntas."""

    def answer(self, question: str, request_id: str | None = None) -> Answer: ...


@dataclass(frozen=True)
class Source:
    """Fuente citada, construida desde los metadatos del corpus."""

    title: str
    source_type: str
    url: str
    slug: str


@dataclass(frozen=True)
class Answer:
    """Respuesta del asistente y su trazabilidad."""

    status: str  # answered | no_evidence
    text: str
    sources: tuple[Source, ...] = ()
    provider: str | None = None
    latency_ms: int = 0
    request_id: str = ""


@dataclass
class StreamOutcome:
    """Resultado final de un stream (lo completa `stream_tokens`)."""

    answer: Answer | None = None


def _unique_sources(fragments: list[RetrievedFragment]) -> tuple[Source, ...]:
    seen: set[str] = set()
    sources: list[Source] = []
    for fragment in fragments:
        if fragment.slug in seen:
            continue
        seen.add(fragment.slug)
        sources.append(
            Source(
                title=fragment.title,
                source_type=fragment.source_type,
                url=fragment.url,
                slug=fragment.slug,
            )
        )
        if len(sources) >= MAX_SOURCES:
            break
    return tuple(sources)


class RagService:
    """Orquesta recuperación y generación; recuperación y LLM son independientes."""

    def __init__(
        self,
        retriever: Retriever,
        llm: LLM,
        *,
        top_k: int = 5,
        min_score: float = MIN_SCORE,
    ) -> None:
        self._retriever = retriever
        self._llm = llm
        self._top_k = top_k
        self._min_score = min_score

    def answer(self, question: str, request_id: str | None = None) -> Answer:
        """Responde una pregunta o se abstiene si no hay evidencia suficiente."""
        cleaned = question.strip()
        if not 1 <= len(cleaned) <= MAX_QUESTION_CHARS:
            raise ValueError(f"La pregunta debe tener entre 1 y {MAX_QUESTION_CHARS} caracteres.")
        trace_id = request_id or uuid4().hex
        started = perf_counter()

        fragments = [
            fragment
            for fragment in self._retriever.search(cleaned, self._top_k)
            if fragment.score >= self._min_score
        ]
        if not fragments:
            return Answer(
                status="no_evidence",
                text=NO_EVIDENCE_TEXT,
                provider=None,
                latency_ms=_elapsed_ms(started),
                request_id=trace_id,
            )

        text = self._llm.generate(build_messages(cleaned, fragments)).strip()
        if not text or REFUSAL_MARKER in text.lower():
            return Answer(
                status="no_evidence",
                text=NO_EVIDENCE_TEXT,
                provider=self._llm.provider,
                latency_ms=_elapsed_ms(started),
                request_id=trace_id,
            )
        return Answer(
            status="answered",
            text=text,
            sources=_unique_sources(fragments),
            provider=self._llm.provider,
            latency_ms=_elapsed_ms(started),
            request_id=trace_id,
        )

    def stream_tokens(
        self, question: str, request_id: str, outcome: StreamOutcome
    ) -> Iterator[str]:
        """Genera tokens y deja la respuesta final en `outcome`."""
        cleaned = question.strip()
        if not 1 <= len(cleaned) <= MAX_QUESTION_CHARS:
            raise ValueError(f"La pregunta debe tener entre 1 y {MAX_QUESTION_CHARS} caracteres.")
        started = perf_counter()
        fragments = [
            fragment
            for fragment in self._retriever.search(cleaned, self._top_k)
            if fragment.score >= self._min_score
        ]
        if not fragments:
            outcome.answer = Answer(
                status="no_evidence",
                text=NO_EVIDENCE_TEXT,
                provider=None,
                latency_ms=_elapsed_ms(started),
                request_id=request_id,
            )
            return
        messages = build_messages(cleaned, fragments)
        parts: list[str] = []
        stream = getattr(self._llm, "stream", None)
        if callable(stream):
            for token in stream(messages):
                if token:
                    parts.append(token)
                    yield token
        else:
            text = self._llm.generate(messages)
            parts.append(text)
            yield text
        text = "".join(parts).strip()
        if not text or REFUSAL_MARKER in text.lower():
            outcome.answer = Answer(
                status="no_evidence",
                text=NO_EVIDENCE_TEXT,
                provider=self._llm.provider,
                latency_ms=_elapsed_ms(started),
                request_id=request_id,
            )
            return
        outcome.answer = Answer(
            status="answered",
            text=text,
            sources=_unique_sources(fragments),
            provider=self._llm.provider,
            latency_ms=_elapsed_ms(started),
            request_id=request_id,
        )


def _elapsed_ms(started: float) -> int:
    return max(0, int((perf_counter() - started) * 1000))
