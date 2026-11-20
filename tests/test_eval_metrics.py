"""Pruebas de las métricas de evaluación."""

from __future__ import annotations

import pytest
from assistant.evaluation import metrics
from tests.eval_fixtures import make_row


def test_recall_y_mrr() -> None:
    # Arrange
    rows = [
        make_row(row_id="q01", retrieved_slugs=("compania", "empaques"), rank_first_expected=1),
        make_row(
            row_id="q02",
            expected_slugs=("empaques",),
            retrieved_slugs=("compania", "empaques"),
            rank_first_expected=2,
        ),
    ]

    # Act / Assert
    assert metrics.recall_at_k(rows, 1) == 0.5
    assert metrics.recall_at_k(rows, 5) == 1.0
    assert metrics.mrr(rows) == 0.75


def test_recall_sin_preguntas_sustentables() -> None:
    # Arrange
    rows = [make_row(expected_status="not_sustainable", expected_slugs=())]

    # Act / Assert
    assert metrics.recall_at_k(rows, 5) == 0.0
    assert metrics.mrr(rows) == 0.0


def test_precision_de_citas_y_cobertura() -> None:
    # Arrange
    rows = [
        make_row(
            row_id="q01",
            status="answered",
            sources=("https://a", "https://b"),
            source_slugs=("compania", "empaques"),
            citations_invalid=1,
        ),
        make_row(
            row_id="q02",
            expected_slugs=("empaques",),
            status="answered",
            sources=("https://b",),
            source_slugs=("empaques",),
        ),
    ]

    # Act / Assert
    assert metrics.citation_precision(rows) == pytest.approx(2 / 3)
    assert metrics.expected_citation_coverage(rows) == 1.0


def test_abstencion_y_falsa_abstencion() -> None:
    # Arrange
    rows = [
        make_row(row_id="q01", status="answered"),
        make_row(
            row_id="q04",
            expected_status="not_sustainable",
            expected_slugs=(),
            retrieved_slugs=(),
            rank_first_expected=None,
            status="no_evidence",
        ),
        make_row(
            row_id="q05",
            expected_status="not_sustainable",
            expected_slugs=(),
            retrieved_slugs=(),
            rank_first_expected=None,
            status="answered",
        ),
    ]

    # Act / Assert
    assert metrics.abstention_accuracy(rows) == 0.5
    assert metrics.false_abstention_rate(rows) == 0.0


def test_percentiles() -> None:
    # Arrange
    values = [10, 20, 30, 40]

    # Act / Assert
    assert metrics.percentile(values, 50) == 25
    assert metrics.percentile(values, 95) == 38
    assert metrics.percentile([], 50) == 0


def test_ganadora_con_desempate_por_mrr() -> None:
    # Arrange
    variants = [
        ("a", {"recall_at_5": 0.9, "mrr": 0.5}),
        ("b", {"recall_at_5": 0.9, "mrr": 0.8}),
    ]

    # Act / Assert
    assert metrics.pick_winner(variants) == "b"


def test_metricas_e2e_incluyen_respuesta() -> None:
    # Arrange
    rows = [
        make_row(status="answered", sources=("https://a",), source_slugs=("compania",)),
        make_row(
            row_id="q04",
            expected_status="not_sustainable",
            expected_slugs=(),
            retrieved_slugs=(),
            rank_first_expected=None,
            status="no_evidence",
        ),
    ]

    # Act
    result = metrics.compute_metrics(rows, "e2e")

    # Assert
    assert result["citation_precision"] == 1.0
    assert result["abstention_accuracy"] == 1.0
    assert result["questions_evaluated"] == 2


def test_umbrales() -> None:
    # Arrange
    failing = {"recall_at_5": 0.9, "citation_precision": 1.0, "abstention_accuracy": 0.8}

    # Act
    failures = metrics.meets_thresholds(failing, "e2e")

    # Assert
    assert any("recall_at_5" in failure for failure in failures)
    assert any("abstention_accuracy" in failure for failure in failures)
