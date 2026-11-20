"""Fixtures compartidas de la evaluación (datos sintéticos, sin red)."""

from __future__ import annotations

from collections.abc import Sequence
from hashlib import sha256

from assistant.corpus import CorpusDocument
from assistant.evaluation.dataset import EvaluationQuestion, EvaluationSet
from assistant.evaluation.reports import QuestionRow
from assistant.llm import Message

DOC_A_BODY = (
    "Carvajal es una organización fundada en 1904 en Cali. Opera en cuatro sectores: "
    "papel y empaques, educación, tecnología y servicios, y comunicación."
)
DOC_B_BODY = (
    "El catálogo de empaques reúne contenedores, vasos y charolas. "
    "Los precios se expresan en pesos mexicanos."
)


def sample_documents() -> list[CorpusDocument]:
    return [
        CorpusDocument(
            slug="compania",
            title="Compañía Carvajal",
            url="https://www.carvajal.com/compania",
            section="compania",
            source_type="oficial",
            captured_at="2026-11-01T00:00:00+00:00",
            hash=sha256(DOC_A_BODY.encode()).hexdigest(),
            chars=len(DOC_A_BODY),
            body=DOC_A_BODY,
        ),
        CorpusDocument(
            slug="empaques",
            title="Empaques Carvajal",
            url="https://www.carvajal.com/empaques",
            section="negocios",
            source_type="tercero",
            captured_at="2026-11-01T00:00:00+00:00",
            hash=sha256(DOC_B_BODY.encode()).hexdigest(),
            chars=len(DOC_B_BODY),
            body=DOC_B_BODY,
        ),
    ]


def sample_questions() -> list[EvaluationQuestion]:
    return [
        EvaluationQuestion(
            id="q01",
            question="¿Qué es Carvajal?",
            expected_slugs=("compania",),
            expected_status="sustainable",
            key_facts=("cuatro sectores",),
        ),
        EvaluationQuestion(
            id="q02",
            question="¿Qué productos de empaques hay?",
            expected_slugs=("empaques",),
            expected_status="sustainable",
            key_facts=("contenedores y vasos",),
        ),
        EvaluationQuestion(
            id="q03",
            question="¿Cuánto cuesta la caja de platos?",
            expected_slugs=(),
            expected_status="not_sustainable",
            key_facts=("no hay precios en el corpus",),
        ),
    ]


def sample_set(
    questions: Sequence[EvaluationQuestion] | None = None,
    *,
    reviewed: bool = True,
    fingerprint: str = "fp-sintetico",
) -> EvaluationSet:
    return EvaluationSet(
        version=1,
        corpus_fingerprint=fingerprint,
        reviewed_by="revision-sintetica" if reviewed else "",
        reviewed_at="2026-11-20" if reviewed else "",
        questions=tuple(questions or sample_questions()),
    )


def sample_payload() -> dict[str, object]:
    evaluation_set = sample_set()
    return {
        "version": 1,
        "corpus_fingerprint": evaluation_set.corpus_fingerprint,
        "reviewed_by": evaluation_set.reviewed_by,
        "reviewed_at": evaluation_set.reviewed_at,
        "questions": [
            {
                "id": question.id,
                "question": question.question,
                "expected_slugs": list(question.expected_slugs),
                "expected_status": question.expected_status,
                "key_facts": list(question.key_facts),
                "notes": "",
            }
            for question in evaluation_set.questions
        ],
    }


def make_row(
    *,
    row_id: str = "q01",
    expected_status: str = "sustainable",
    expected_slugs: tuple[str, ...] = ("compania",),
    retrieved_slugs: tuple[str, ...] = ("compania", "empaques"),
    rank_first_expected: int | None = 1,
    status: str | None = None,
    sources: tuple[str, ...] = (),
    source_slugs: tuple[str, ...] = (),
    citations_invalid: int = 0,
    latency_ms: int = 10,
) -> QuestionRow:
    return QuestionRow(
        id=row_id,
        question="pregunta sintética",
        expected_slugs=expected_slugs,
        expected_status=expected_status,
        retrieved_slugs=retrieved_slugs,
        rank_first_expected=rank_first_expected,
        status=status,
        sources=sources,
        source_slugs=source_slugs,
        citations_invalid=citations_invalid,
        latency_ms=latency_ms,
    )


class FakeEmbedder:
    """Embedder determinista de 768 dims, sin red."""

    def __init__(self, dim: int = 768) -> None:
        self.dim = dim

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            lower = text.lower()
            vector = [0.0] * self.dim
            if "carvajal" in lower or "sectores" in lower:
                vector[0] = 1.0
            elif "empaques" in lower or "vasos" in lower:
                vector[1] = 1.0
            else:
                vector[2] = 1.0
            vectors.append(vector)
        return vectors

    def close(self) -> None:
        return None


class ScriptedLLM:
    """LLM falso con texto fijo."""

    name = "fake"
    provider = "fake"

    def __init__(self, text: str = "Respuesta de prueba [1].") -> None:
        self.text = text
        self.calls: list[list[Message]] = []

    def generate(self, messages: Sequence[Message]) -> str:
        self.calls.append(list(messages))
        return self.text

    def close(self) -> None:
        return None


def fake_embedder_factory() -> object:
    def factory(_model: str, dim: int) -> FakeEmbedder:
        return FakeEmbedder(dim)

    return factory
