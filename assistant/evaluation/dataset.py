"""Carga y validación del ground truth de evaluación."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

VALID_STATUS = ("sustainable", "not_sustainable")
DEFAULT_QUESTION_COUNT = 33


class DatasetError(RuntimeError):
    """El set de evaluación no cumple el contrato."""


@dataclass(frozen=True)
class EvaluationQuestion:
    """Pregunta evaluada con su evidencia y estado esperados."""

    id: str
    question: str
    expected_slugs: tuple[str, ...]
    expected_status: str
    key_facts: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True)
class EvaluationSet:
    """Set de evaluación versionado y firmado."""

    version: int
    corpus_fingerprint: str
    reviewed_by: str
    reviewed_at: str
    questions: tuple[EvaluationQuestion, ...]


def _parse_question(raw: object, index: int) -> EvaluationQuestion:
    if not isinstance(raw, dict):
        raise DatasetError(f"questions[{index}]: debe ser un objeto.")
    question_id = raw.get("id")
    question = raw.get("question")
    slugs = raw.get("expected_slugs", [])
    status = raw.get("expected_status")
    facts = raw.get("key_facts", [])
    if not isinstance(question_id, str) or not question_id:
        raise DatasetError(f"questions[{index}]: falta id.")
    if not isinstance(question, str) or not question.strip():
        raise DatasetError(f"questions[{index}]: falta question.")
    if not isinstance(slugs, list) or not all(isinstance(slug, str) for slug in slugs):
        raise DatasetError(f"{question_id}: expected_slugs debe ser una lista de textos.")
    if status not in VALID_STATUS:
        raise DatasetError(f"{question_id}: expected_status inválido ({status!r}).")
    if not isinstance(facts, list) or not all(isinstance(fact, str) for fact in facts):
        raise DatasetError(f"{question_id}: key_facts debe ser una lista de textos.")
    return EvaluationQuestion(
        id=question_id,
        question=question.strip(),
        expected_slugs=tuple(slugs),
        expected_status=status,
        key_facts=tuple(facts),
        notes=str(raw.get("notes", "")),
    )


def load_evaluation_set(path: Path) -> EvaluationSet:
    """Carga el JSON del set; no valida contra el corpus."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise DatasetError(f"No se pudo leer el set {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise DatasetError(f"Set inválido en {path}: {error}") from error
    if not isinstance(payload, dict):
        raise DatasetError("El set debe ser un objeto JSON.")
    questions_raw = payload.get("questions")
    if not isinstance(questions_raw, list):
        raise DatasetError("El set debe incluir una lista questions.")
    return EvaluationSet(
        version=int(payload.get("version", 0)),
        corpus_fingerprint=str(payload.get("corpus_fingerprint", "")),
        reviewed_by=str(payload.get("reviewed_by", "")),
        reviewed_at=str(payload.get("reviewed_at", "")),
        questions=tuple(_parse_question(raw, index) for index, raw in enumerate(questions_raw)),
    )


def _is_iso_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_evaluation_set(
    evaluation_set: EvaluationSet,
    corpus_slugs: Iterable[str],
    *,
    expected_count: int = DEFAULT_QUESTION_COUNT,
    strict_count: bool = True,
) -> list[str]:
    """Devuelve la lista de errores; vacía si el set es válido."""
    errors: list[str] = []
    known = set(corpus_slugs)
    if evaluation_set.version != 1:
        errors.append("version debe ser 1.")
    if strict_count and len(evaluation_set.questions) != expected_count:
        errors.append(
            f"se esperaban {expected_count} preguntas y hay {len(evaluation_set.questions)}."
        )
    if not strict_count and not evaluation_set.questions:
        errors.append("el set no tiene preguntas.")
    if not evaluation_set.reviewed_by:
        errors.append("reviewed_by es obligatorio (revisión humana).")
    if not evaluation_set.reviewed_at or not _is_iso_datetime(evaluation_set.reviewed_at):
        errors.append("reviewed_at debe ser una fecha ISO-8601.")
    seen: set[str] = set()
    for question in evaluation_set.questions:
        if question.id in seen:
            errors.append(f"{question.id}: id duplicado.")
        seen.add(question.id)
        if not 1 <= len(question.question) <= 2000:
            errors.append(f"{question.id}: la pregunta debe tener entre 1 y 2000 caracteres.")
        if not question.key_facts:
            errors.append(f"{question.id}: key_facts no puede estar vacío.")
        missing = [slug for slug in question.expected_slugs if slug not in known]
        if missing:
            errors.append(f"{question.id}: slugs fuera del corpus: {', '.join(missing)}.")
        if question.expected_status == "sustainable" and not question.expected_slugs:
            errors.append(f"{question.id}: una pregunta sustentable necesita evidencia.")
        if question.expected_status == "not_sustainable" and question.expected_slugs:
            errors.append(f"{question.id}: una pregunta no sustentable no debe tener evidencia.")
    return errors


def load_and_validate(
    path: Path,
    corpus_slugs: Iterable[str],
    *,
    expected_count: int = DEFAULT_QUESTION_COUNT,
    strict_count: bool = True,
) -> EvaluationSet:
    """Carga y valida; lanza DatasetError con todos los errores juntos."""
    evaluation_set = load_evaluation_set(path)
    errors = validate_evaluation_set(
        evaluation_set,
        corpus_slugs,
        expected_count=expected_count,
        strict_count=strict_count,
    )
    if errors:
        raise DatasetError("Set inválido:\n- " + "\n- ".join(errors))
    return evaluation_set
