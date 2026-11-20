"""Propuesta asistida del ground truth para revisión humana."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from assistant.corpus import CorpusDocument
from assistant.evaluation.dataset import VALID_STATUS
from assistant.llm import LLM, Message

Progress = Callable[[str], None]
BATCH_SIZE = 5
SNIPPET_CHARS = 500


class GroundTruthError(RuntimeError):
    """La propuesta del ground truth no se pudo generar o interpretar."""


@dataclass(frozen=True)
class Proposal:
    """Propuesta de anotación para una pregunta."""

    id: str
    question: str
    expected_slugs: tuple[str, ...]
    expected_status: str
    key_facts: tuple[str, ...]


def corpus_digest(documents: Sequence[CorpusDocument]) -> str:
    """Resumen legible del corpus para el prompt de anotación."""
    lines: list[str] = []
    for document in sorted(documents, key=lambda item: item.slug):
        snippet = " ".join(document.body.split())[:SNIPPET_CHARS]
        lines.append(
            f"- slug={document.slug} | título={document.title} | "
            f"tipo={document.source_type} | {snippet}"
        )
    return "\n".join(lines)


def _system_prompt() -> str:
    return (
        "Eres un anotador del corpus de Carvajal. Para cada pregunta decides si el corpus "
        "la sustenta y qué documentos la sustentan. Devuelves SOLO un array JSON, sin "
        "texto adicional ni bloques de código.\n"
        "Reglas: usa solo slugs del digest; si ningún documento sustenta la pregunta, "
        'usa expected_status="not_sustainable" y expected_slugs=[]; si la sustenta, '
        "incluye al menos un slug y 1-3 hechos clave verificables. No inventes slugs."
    )


def _user_prompt(digest: str, batch: Sequence[tuple[str, str]]) -> str:
    questions = "\n".join(f"- id={qid}: {text}" for qid, text in batch)
    return (
        "Corpus (slug | título | tipo | fragmento):\n"
        f"{digest}\n\n"
        "Preguntas a anotar:\n"
        f"{questions}\n\n"
        "Devuelve un array JSON con objetos: "
        '{"id": "...", "expected_slugs": [...], '
        '"expected_status": "sustainable" | "not_sustainable", '
        '"key_facts": ["..."]}.'
    )


def _extract_json_array(text: str) -> list[object]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise GroundTruthError(f"El LLM no devolvió un array JSON: {text[:200]!r}")
    try:
        payload = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as error:
        raise GroundTruthError(f"JSON inválido en la propuesta: {error}") from error
    if not isinstance(payload, list):
        raise GroundTruthError("La propuesta no es un array JSON.")
    return payload


def _proposal_from_raw(
    raw: object, question_id: str, question: str, known_slugs: set[str]
) -> Proposal:
    if not isinstance(raw, dict):
        raise GroundTruthError(f"{question_id}: la propuesta no es un objeto.")
    slugs_raw = raw.get("expected_slugs", [])
    status = raw.get("expected_status")
    facts_raw = raw.get("key_facts", [])
    slugs = (
        tuple(str(slug) for slug in slugs_raw if isinstance(slug, str) and slug in known_slugs)
        if isinstance(slugs_raw, list)
        else ()
    )
    facts = (
        tuple(str(fact) for fact in facts_raw if str(fact).strip())
        if isinstance(facts_raw, list)
        else ()
    )
    if status not in VALID_STATUS:
        status = "not_sustainable"
    if status == "sustainable" and not slugs:
        status = "not_sustainable"
    if status == "not_sustainable":
        slugs = ()
    if not facts:
        facts = ("(revisar: sin hechos propuestos)",)
    return Proposal(
        id=question_id,
        question=question,
        expected_slugs=slugs,
        expected_status=status,
        key_facts=facts,
    )


def propose(
    llm: LLM,
    documents: Sequence[CorpusDocument],
    questions: Sequence[str],
    *,
    limit: int | None = None,
    batch_size: int = BATCH_SIZE,
    progress: Progress | None = None,
) -> tuple[Proposal, ...]:
    """Genera propuestas por lotes; no firma el set."""
    selected = list(questions)
    if limit is not None:
        selected = selected[: max(0, limit)]
    known_slugs = {document.slug for document in documents}
    digest = corpus_digest(documents)
    indexed = [(f"q{number:02d}", text) for number, text in enumerate(selected, start=1)]
    proposals: list[Proposal] = []
    for start in range(0, len(indexed), batch_size):
        batch = indexed[start : start + batch_size]
        if progress is not None:
            progress(f"proponiendo preguntas {batch[0][0]}-{batch[-1][0]}")
        response = llm.generate(
            [
                Message(role="system", content=_system_prompt()),
                Message(role="user", content=_user_prompt(digest, batch)),
            ]
        )
        payload = _extract_json_array(response)
        by_id = {
            str(item.get("id")): item
            for item in payload
            if isinstance(item, dict) and item.get("id")
        }
        for question_id, question in batch:
            raw = by_id.get(question_id)
            if raw is None:
                raise GroundTruthError(f"La propuesta no incluyó la pregunta {question_id}.")
            proposals.append(_proposal_from_raw(raw, question_id, question, known_slugs))
    return tuple(proposals)


def candidate_payload(proposals: Sequence[Proposal], fingerprint: str) -> dict[str, object]:
    """Estructura del JSON candidato (sin firma humana)."""
    return {
        "version": 1,
        "corpus_fingerprint": fingerprint,
        "reviewed_by": "",
        "reviewed_at": "",
        "questions": [
            {
                "id": proposal.id,
                "question": proposal.question,
                "expected_slugs": list(proposal.expected_slugs),
                "expected_status": proposal.expected_status,
                "key_facts": list(proposal.key_facts),
                "notes": "",
            }
            for proposal in proposals
        ],
    }


def render_review(proposals: Sequence[Proposal], fingerprint: str) -> str:
    """Tabla Markdown para la revisión humana."""
    lines = [
        "# Revisión del ground truth",
        "",
        f"- Fingerprint del corpus: `{fingerprint}`",
        "- Revisado por: _(completar)_",
        "- Fecha: _(completar)_",
        "",
        "| id | pregunta | evidencia | estado | hechos | decisión | cambios |",
        "|---|---|---|---|---|---|---|",
    ]
    for proposal in proposals:
        slugs = ", ".join(proposal.expected_slugs) or "—"
        facts = "; ".join(proposal.key_facts).replace("|", "/")
        lines.append(
            f"| {proposal.id} | {proposal.question} | {slugs} | "
            f"{proposal.expected_status} | {facts} | _(ok/corregir)_ | _(describir)_ |"
        )
    return "\n".join(lines) + "\n"
