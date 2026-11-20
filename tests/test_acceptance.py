"""Pruebas del set de aceptación y del reporte de citación."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from assistant.acceptance import (
    AcceptanceError,
    QuestionItem,
    exit_code,
    load_questions,
    report_to_dict,
    run_acceptance,
)
from assistant.corpus import CorpusDocument
from assistant.rag import Answer, Source

DOCUMENT = CorpusDocument(
    slug="compania",
    title="Compañía Carvajal",
    url="https://www.carvajal.com/compania",
    section="compania",
    source_type="oficial",
    captured_at="2026-11-01T00:00:00+00:00",
    hash="a" * 64,
    chars=100,
    body="Carvajal opera en cuatro sectores.",
)
VALID_SOURCE = Source(
    title=DOCUMENT.title,
    source_type=DOCUMENT.source_type,
    url=DOCUMENT.url,
    slug=DOCUMENT.slug,
)


class ScriptedRag:
    def __init__(self, answers: dict[str, Answer]) -> None:
        self.answers = answers

    def answer(self, question: str, request_id: str | None = None) -> Answer:
        return self.answers[question]


def _answered(source: Source = VALID_SOURCE) -> Answer:
    return Answer(
        status="answered",
        text="Carvajal opera en cuatro sectores [1].",
        sources=(source,),
        provider="fake",
        latency_ms=10,
        request_id="r",
    )


def test_reporte_cumple_con_cita_valida() -> None:
    # Arrange
    rag = ScriptedRag({"q1": _answered()})

    # Act
    report = run_acceptance(rag, [DOCUMENT], [QuestionItem("q1")])

    # Assert
    assert report.questions_total == 1
    assert report.answered_with_valid_citation == 1
    assert report.invalid_citations == 0
    assert exit_code(report) == 0
    assert report.rows[0].citations_valid is True


def test_cita_con_titulo_distinto_es_invalida() -> None:
    # Arrange
    wrong = Source(
        title="Otro título",
        source_type="oficial",
        url=DOCUMENT.url,
        slug=DOCUMENT.slug,
    )
    rag = ScriptedRag({"q1": _answered(wrong)})

    # Act
    report = run_acceptance(rag, [DOCUMENT], [QuestionItem("q1")])

    # Assert
    assert report.invalid_citations == 1
    assert exit_code(report) == 1


def test_abstencion_cuenta_como_sin_evidencia() -> None:
    # Arrange
    answer = Answer(
        status="no_evidence",
        text="No encontré evidencia.",
        sources=(),
        provider=None,
        latency_ms=2,
        request_id="r",
    )
    rag = ScriptedRag({"q1": answer})

    # Act
    report = run_acceptance(rag, [DOCUMENT], [QuestionItem("q1")])

    # Assert
    assert report.no_evidence == 1
    assert report.answered_with_valid_citation == 0
    assert exit_code(report) == 1


def test_sin_preguntas_codigo_dos() -> None:
    # Arrange
    rag = ScriptedRag({})

    # Act
    report = run_acceptance(rag, [DOCUMENT], [])

    # Assert
    assert exit_code(report) == 2


def test_load_questions_strings_y_objetos(tmp_path: Path) -> None:
    # Arrange
    path = tmp_path / "preguntas.json"
    path.write_text(
        json.dumps(
            [
                "¿Qué es Carvajal?",
                {"question": "¿Cuánto cuesta?", "expected_out_of_scope": True},
            ]
        ),
        encoding="utf-8",
    )

    # Act
    questions = load_questions(path)

    # Assert
    assert questions[0].question == "¿Qué es Carvajal?"
    assert questions[1].expected_out_of_scope is True


def test_load_questions_invalido(tmp_path: Path) -> None:
    # Arrange
    path = tmp_path / "preguntas.json"
    path.write_text('{"no": "es lista"}', encoding="utf-8")

    # Act / Assert
    with pytest.raises(AcceptanceError, match="lista"):
        load_questions(path)


def test_load_questions_archivo_ausente(tmp_path: Path) -> None:
    # Act / Assert
    with pytest.raises(AcceptanceError, match="No se pudo leer"):
        load_questions(tmp_path / "no-existe.json")


def test_report_to_dict() -> None:
    # Arrange
    rag = ScriptedRag({"q1": _answered()})
    report = run_acceptance(rag, [DOCUMENT], [QuestionItem("q1")])

    # Act
    payload = report_to_dict(report)

    # Assert
    assert payload["questions_total"] == 1
    assert payload["rows"][0]["citations_valid"] is True
    assert payload["rows"][0]["sources"] == [DOCUMENT.url]
