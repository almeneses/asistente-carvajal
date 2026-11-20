"""Evaluación de aceptación: ejecuta un set de preguntas y valida las citas."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from assistant.corpus import CorpusDocument
from assistant.rag import Answer, Rag, Source

MIN_ANSWER_RATIO = 0.9


class AcceptanceError(RuntimeError):
    """El set de aceptación no se pudo cargar o ejecutar."""


@dataclass(frozen=True)
class QuestionItem:
    question: str
    expected_out_of_scope: bool = False


@dataclass(frozen=True)
class Row:
    question: str
    status: str
    provider: str | None
    latency_ms: int
    sources: tuple[str, ...]
    citations_valid: bool
    expected_out_of_scope: bool


@dataclass
class Report:
    rows: list[Row] = field(default_factory=list)
    generated_at: str = ""
    questions_total: int = 0
    answered_with_valid_citation: int = 0
    no_evidence: int = 0
    invalid_citations: int = 0


def load_questions(path: Path) -> list[QuestionItem]:
    """Carga preguntas desde una lista de strings o de objetos."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AcceptanceError(f"No se pudo leer el set de preguntas {path}: {error}") from error
    if not isinstance(raw, list) or not raw:
        raise AcceptanceError("El set de preguntas debe ser una lista no vacía.")
    items: list[QuestionItem] = []
    for entry in raw:
        if isinstance(entry, str) and entry.strip():
            items.append(QuestionItem(entry.strip()))
        elif isinstance(entry, dict) and isinstance(entry.get("question"), str):
            items.append(
                QuestionItem(
                    question=entry["question"].strip(),
                    expected_out_of_scope=bool(entry.get("expected_out_of_scope", False)),
                )
            )
        else:
            raise AcceptanceError("Cada pregunta debe ser texto o un objeto con 'question'.")
    return items


def _source_is_valid(source: Source, documents_by_url: dict[str, CorpusDocument]) -> bool:
    document = documents_by_url.get(source.url)
    return (
        document is not None
        and document.title == source.title
        and document.source_type == source.source_type
    )


def _row(
    item: QuestionItem,
    answer: Answer,
    documents_by_url: dict[str, CorpusDocument],
) -> Row:
    valid = all(_source_is_valid(source, documents_by_url) for source in answer.sources)
    return Row(
        question=item.question,
        status=answer.status,
        provider=answer.provider,
        latency_ms=answer.latency_ms,
        sources=tuple(source.url for source in answer.sources),
        citations_valid=valid,
        expected_out_of_scope=item.expected_out_of_scope,
    )


def run_acceptance(
    rag: Rag,
    documents: list[CorpusDocument],
    questions: list[QuestionItem],
) -> Report:
    """Ejecuta todas las preguntas y agrega el reporte de citación."""
    documents_by_url = {document.url: document for document in documents}
    report = Report(
        generated_at=datetime.now(UTC).isoformat(),
        questions_total=len(questions),
    )
    for item in questions:
        answer = rag.answer(item.question)
        row = _row(item, answer, documents_by_url)
        report.rows.append(row)
        if row.status == "answered" and row.citations_valid:
            report.answered_with_valid_citation += 1
        if row.status == "no_evidence":
            report.no_evidence += 1
        if row.status == "answered" and not row.citations_valid:
            report.invalid_citations += 1
    return report


def exit_code(report: Report) -> int:
    """0 si el corte cumple SC-001/SC-002; 1 si no; 2 si no hay preguntas."""
    if report.questions_total == 0:
        return 2
    if report.invalid_citations > 0:
        return 1
    ratio = report.answered_with_valid_citation / report.questions_total
    return 0 if ratio >= MIN_ANSWER_RATIO else 1


def report_to_dict(report: Report) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "questions_total": report.questions_total,
        "answered_with_valid_citation": report.answered_with_valid_citation,
        "no_evidence": report.no_evidence,
        "invalid_citations": report.invalid_citations,
        "rows": [
            {
                "question": row.question,
                "status": row.status,
                "provider": row.provider,
                "latency_ms": row.latency_ms,
                "sources": list(row.sources),
                "citations_valid": row.citations_valid,
                "expected_out_of_scope": row.expected_out_of_scope,
            }
            for row in report.rows
        ],
    }


def summary_markdown(report: Report) -> str:
    ratio = (
        report.answered_with_valid_citation / report.questions_total
        if report.questions_total
        else 0.0
    )
    lines = [
        "# Reporte de aceptación",
        "",
        f"- Preguntas: {report.questions_total}",
        f"- Respondidas con cita válida: {report.answered_with_valid_citation} ({ratio:.0%})",
        f"- Sin evidencia (abstención): {report.no_evidence}",
        f"- Citas inválidas: {report.invalid_citations}",
        "",
        "| # | Pregunta | Estado | Cita válida |",
        "|---|---|---|---|",
    ]
    for number, row in enumerate(report.rows, start=1):
        lines.append(
            f"| {number} | {row.question[:80]} | {row.status} | "
            f"{'sí' if row.citations_valid else 'no'} |"
        )
    return "\n".join(lines)
