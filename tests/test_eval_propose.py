"""Pruebas de la propuesta de ground truth."""

from __future__ import annotations

import json

import pytest
from assistant.evaluation.ground_truth import (
    GroundTruthError,
    candidate_payload,
    corpus_digest,
    propose,
    render_review,
)
from tests.eval_fixtures import ScriptedLLM, sample_documents

QUESTIONS = [
    "¿Qué es Carvajal?",
    "¿Qué productos de empaques hay?",
    "¿Cuánto cuesta la caja de platos?",
]

PROPOSAL = json.dumps(
    [
        {
            "id": "q01",
            "expected_slugs": ["compania"],
            "expected_status": "sustainable",
            "key_facts": ["cuatro sectores"],
        },
        {
            "id": "q02",
            "expected_slugs": ["empaques"],
            "expected_status": "sustainable",
            "key_facts": ["contenedores y vasos"],
        },
        {
            "id": "q03",
            "expected_slugs": ["fantasma"],
            "expected_status": "sustainable",
            "key_facts": ["precio"],
        },
    ]
)


def test_digest_incluye_slugs_y_titulos() -> None:
    # Arrange / Act
    digest = corpus_digest(sample_documents())

    # Assert
    assert "slug=compania" in digest
    assert "Compañía Carvajal" in digest


def test_propuesta_valida_y_filtra_slugs_desconocidos() -> None:
    # Arrange
    llm = ScriptedLLM(PROPOSAL)

    # Act
    proposals = propose(llm, sample_documents(), QUESTIONS)

    # Assert
    assert [proposal.id for proposal in proposals] == ["q01", "q02", "q03"]
    assert proposals[0].expected_slugs == ("compania",)
    assert proposals[2].expected_slugs == ()
    assert proposals[2].expected_status == "not_sustainable"
    assert len(llm.calls) == 1


def test_candidate_y_revision() -> None:
    # Arrange
    proposals = propose(ScriptedLLM(PROPOSAL), sample_documents(), QUESTIONS)

    # Act
    payload = candidate_payload(proposals, "fp-test")
    review = render_review(proposals, "fp-test")

    # Assert
    assert payload["reviewed_by"] == ""
    assert payload["corpus_fingerprint"] == "fp-test"
    questions = payload["questions"]
    assert isinstance(questions, list) and len(questions) == 3
    assert "| q01 |" in review
    assert "fingerprint" in review.lower()


def test_propuesta_sin_json_falla() -> None:
    # Arrange
    llm = ScriptedLLM("No puedo anotar esto.")

    # Act / Assert
    with pytest.raises(GroundTruthError, match="array JSON"):
        propose(llm, sample_documents(), QUESTIONS)


def test_propuesta_incompleta_falla() -> None:
    # Arrange
    llm = ScriptedLLM(json.dumps([{"id": "q01", "expected_slugs": ["compania"]}]))

    # Act / Assert
    with pytest.raises(GroundTruthError, match="q02"):
        propose(llm, sample_documents(), QUESTIONS)
