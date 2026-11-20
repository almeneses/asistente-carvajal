"""Pruebas de carga y validación del ground truth."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from assistant.evaluation.dataset import (
    DatasetError,
    load_and_validate,
    load_evaluation_set,
    validate_evaluation_set,
)
from tests.eval_fixtures import sample_payload, sample_questions, sample_set

CORPUS_SLUGS = {"compania", "empaques"}


def _write(tmp_path: Path, payload: dict[str, object]) -> Path:
    path = tmp_path / "questions.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_carga_y_valida_set_sintetico(tmp_path: Path) -> None:
    # Arrange
    path = _write(tmp_path, sample_payload())

    # Act
    evaluation_set = load_and_validate(path, CORPUS_SLUGS, strict_count=False)

    # Assert
    assert len(evaluation_set.questions) == 3
    assert evaluation_set.reviewed_by == "revision-sintetica"


def test_set_sin_firma_falla(tmp_path: Path) -> None:
    # Arrange
    payload = sample_payload()
    payload["reviewed_by"] = ""
    path = _write(tmp_path, payload)

    # Act / Assert
    with pytest.raises(DatasetError, match="reviewed_by"):
        load_and_validate(path, CORPUS_SLUGS, strict_count=False)


def test_id_duplicado_falla(tmp_path: Path) -> None:
    # Arrange
    payload = sample_payload()
    questions = payload["questions"]
    assert isinstance(questions, list)
    questions.append(dict(questions[0]))
    path = _write(tmp_path, payload)

    # Act / Assert
    with pytest.raises(DatasetError, match="duplicado"):
        load_and_validate(path, CORPUS_SLUGS, strict_count=False)


def test_slug_fuera_del_corpus_falla(tmp_path: Path) -> None:
    # Arrange
    payload = sample_payload()
    questions = payload["questions"]
    assert isinstance(questions, list)
    questions[0]["expected_slugs"] = ["inexistente"]
    path = _write(tmp_path, payload)

    # Act / Assert
    with pytest.raises(DatasetError, match="fuera del corpus"):
        load_and_validate(path, CORPUS_SLUGS, strict_count=False)


def test_sustentable_sin_evidencia_falla(tmp_path: Path) -> None:
    # Arrange
    payload = sample_payload()
    questions = payload["questions"]
    assert isinstance(questions, list)
    questions[0]["expected_slugs"] = []
    path = _write(tmp_path, payload)

    # Act / Assert
    with pytest.raises(DatasetError, match="necesita evidencia"):
        load_and_validate(path, CORPUS_SLUGS, strict_count=False)


def test_no_sustentable_con_evidencia_falla(tmp_path: Path) -> None:
    # Arrange
    payload = sample_payload()
    questions = payload["questions"]
    assert isinstance(questions, list)
    questions[2]["expected_slugs"] = ["compania"]
    path = _write(tmp_path, payload)

    # Act / Assert
    with pytest.raises(DatasetError, match="no debe tener evidencia"):
        load_and_validate(path, CORPUS_SLUGS, strict_count=False)


def test_conteo_exigido() -> None:
    # Arrange
    evaluation_set = sample_set()

    # Act
    errors = validate_evaluation_set(
        evaluation_set, CORPUS_SLUGS, expected_count=30, strict_count=True
    )

    # Assert
    assert any("30 preguntas" in error for error in errors)


def test_set_valido_sin_errores() -> None:
    # Arrange
    evaluation_set = sample_set()

    # Act
    errors = validate_evaluation_set(evaluation_set, CORPUS_SLUGS, strict_count=False)

    # Assert
    assert errors == []


def test_json_invalido(tmp_path: Path) -> None:
    # Arrange
    path = tmp_path / "roto.json"
    path.write_text("{no es json", encoding="utf-8")

    # Act / Assert
    with pytest.raises(DatasetError, match="inválido"):
        load_evaluation_set(path)


def test_carga_sin_validar(tmp_path: Path) -> None:
    # Arrange
    path = _write(tmp_path, sample_payload())

    # Act
    evaluation_set = load_evaluation_set(path)

    # Assert
    assert [question.id for question in evaluation_set.questions] == [
        "q01",
        "q02",
        "q03",
    ]
    assert sample_questions()[0].expected_status == "sustainable"
