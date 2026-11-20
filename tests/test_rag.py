"""Pruebas de la cadena RAG y de la abstención."""

from __future__ import annotations

import pytest
from assistant.llm import LLMError
from assistant.prompting import NO_EVIDENCE_TEXT
from assistant.rag import RagService
from assistant.retrieval import RetrievedFragment
from tests.conftest import FakeLLM, make_retrieved


class StaticRetriever:
    def __init__(self, fragments: list[RetrievedFragment]) -> None:
        self.fragments = fragments
        self.questions: list[str] = []

    def search(self, question: str, limit: int) -> list[RetrievedFragment]:
        self.questions.append(question)
        return self.fragments[:limit]


def test_respuesta_con_citas_unicas(fake_llm: FakeLLM) -> None:
    # Arrange
    fragments = [
        make_retrieved(score=0.95),
        make_retrieved(score=0.8, chunk_index=1),
        make_retrieved(
            slug="empaques",
            title="Empaques Carvajal",
            url="https://www.carvajal.com/empaques",
            source_type="tercero",
            score=0.7,
        ),
    ]
    service = RagService(StaticRetriever(fragments), fake_llm)

    # Act
    answer = service.answer("¿Qué es Carvajal?")

    # Assert
    assert answer.status == "answered"
    assert answer.text.startswith("Respuesta de prueba")
    assert [source.slug for source in answer.sources] == ["compania", "empaques"]
    assert answer.provider == "fake"
    assert len(fake_llm.calls) == 1


def test_sin_evidencia_no_llama_al_llm(fake_llm: FakeLLM) -> None:
    # Arrange
    service = RagService(StaticRetriever([]), fake_llm)

    # Act
    answer = service.answer("¿Cuánto cuesta la caja de vasos?")

    # Assert
    assert answer.status == "no_evidence"
    assert answer.text == NO_EVIDENCE_TEXT
    assert answer.sources == ()
    assert fake_llm.calls == []


def test_evidencia_bajo_umbral_se_descarta(fake_llm: FakeLLM) -> None:
    # Arrange
    service = RagService(StaticRetriever([make_retrieved(score=0.1)]), fake_llm)

    # Act
    answer = service.answer("Pregunta sin coincidencia")

    # Assert
    assert answer.status == "no_evidence"
    assert fake_llm.calls == []


def test_pregunta_vacia_es_invalida(fake_llm: FakeLLM) -> None:
    # Arrange
    service = RagService(StaticRetriever([]), fake_llm)

    # Act / Assert
    with pytest.raises(ValueError, match="2000"):
        service.answer("   ")


def test_modelo_que_se_abstiene_se_normaliza() -> None:
    # Arrange
    llm = FakeLLM(text="No encontré evidencia suficiente en el corpus para responder.")
    service = RagService(StaticRetriever([make_retrieved()]), llm)

    # Act
    answer = service.answer("¿Cuánto cuesta?")

    # Assert
    assert answer.status == "no_evidence"
    assert answer.sources == ()


def test_error_del_llm_se_propaga(fake_llm: FakeLLM) -> None:
    # Arrange
    class FailingLLM(FakeLLM):
        provider = "deepseek"

        def generate(self, messages):  # type: ignore[no-untyped-def]
            raise LLMError("proveedor caído")

    service = RagService(StaticRetriever([make_retrieved()]), FailingLLM())

    # Act / Assert
    with pytest.raises(LLMError):
        service.answer("¿Qué es Carvajal?")
