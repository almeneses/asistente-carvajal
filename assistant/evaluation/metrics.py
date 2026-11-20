"""Métricas de recuperación y respuesta (funciones puras)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol


class RowLike(Protocol):
    """Atributos mínimos que consumen las métricas (solo lectura)."""

    @property
    def expected_status(self) -> str: ...

    @property
    def expected_slugs(self) -> tuple[str, ...]: ...

    @property
    def retrieved_slugs(self) -> tuple[str, ...]: ...

    @property
    def rank_first_expected(self) -> int | None: ...

    @property
    def status(self) -> str | None: ...

    @property
    def sources(self) -> tuple[str, ...]: ...

    @property
    def source_slugs(self) -> tuple[str, ...]: ...

    @property
    def citations_invalid(self) -> int: ...

    @property
    def latency_ms(self) -> int: ...


def percentile(values: Sequence[float], percent: float) -> int:
    """Percentil con interpolación lineal; 0 si no hay datos."""
    if not values:
        return 0
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0])
    position = (len(ordered) - 1) * (percent / 100.0)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    value = ordered[lower] + (ordered[upper] - ordered[lower]) * fraction
    return round(value)


def _sustainable(rows: Sequence[RowLike]) -> list[RowLike]:
    return [row for row in rows if row.expected_status == "sustainable"]


def _not_sustainable(rows: Sequence[RowLike]) -> list[RowLike]:
    return [row for row in rows if row.expected_status == "not_sustainable"]


def recall_at_k(rows: Sequence[RowLike], k: int) -> float:
    """Recall macro de documentos esperados en los primeros k (únicos)."""
    sustainable = _sustainable(rows)
    if not sustainable:
        return 0.0
    values = []
    for row in sustainable:
        expected = set(row.expected_slugs)
        if not expected:
            continue
        retrieved = set(row.retrieved_slugs[:k])
        values.append(len(expected & retrieved) / len(expected))
    return sum(values) / len(values) if values else 0.0


def mrr(rows: Sequence[RowLike]) -> float:
    """Mean reciprocal rank del primer documento esperado."""
    sustainable = _sustainable(rows)
    if not sustainable:
        return 0.0
    values = [
        1.0 / row.rank_first_expected if row.rank_first_expected else 0.0 for row in sustainable
    ]
    return sum(values) / len(values)


def citation_precision(rows: Sequence[RowLike]) -> float | None:
    """Proporción de citas producidas que son válidas (solo e2e)."""
    answered = [row for row in rows if row.status == "answered"]
    total = sum(len(row.sources) for row in answered)
    if total == 0:
        return None
    invalid = sum(row.citations_invalid for row in answered)
    return max(0.0, (total - invalid) / total)


def expected_citation_coverage(rows: Sequence[RowLike]) -> float | None:
    """Proporción de respuestas sustentables que citan al menos un slug esperado."""
    answered = [
        row for row in _sustainable(rows) if row.status == "answered" and row.expected_slugs
    ]
    if not answered:
        return None
    covered = sum(1 for row in answered if set(row.source_slugs) & set(row.expected_slugs))
    return covered / len(answered)


def abstention_accuracy(rows: Sequence[RowLike]) -> float | None:
    """Proporción de preguntas no sustentables que se abstienen."""
    unsupported = _not_sustainable(rows)
    if not unsupported:
        return None
    correct = sum(1 for row in unsupported if row.status == "no_evidence")
    return correct / len(unsupported)


def false_abstention_rate(rows: Sequence[RowLike]) -> float | None:
    """Proporción de preguntas sustentables en las que el asistente se abstiene."""
    sustainable = _sustainable(rows)
    if not sustainable:
        return None
    abstained = sum(1 for row in sustainable if row.status == "no_evidence")
    return abstained / len(sustainable)


def latency_percentiles(rows: Sequence[RowLike]) -> tuple[int, int]:
    latencies = [float(row.latency_ms) for row in rows]
    return percentile(latencies, 50), percentile(latencies, 95)


def compute_metrics(rows: Sequence[RowLike], mode: str) -> dict[str, Any]:
    """Agrega todas las métricas del modo solicitado."""
    p50, p95 = latency_percentiles(rows)
    metrics: dict[str, Any] = {
        "questions_evaluated": len(rows),
        "recall_at_1": recall_at_k(rows, 1),
        "recall_at_3": recall_at_k(rows, 3),
        "recall_at_5": recall_at_k(rows, 5),
        "recall_at_10": recall_at_k(rows, 10),
        "mrr": mrr(rows),
        "citation_precision": None,
        "expected_citation_coverage": None,
        "abstention_accuracy": None,
        "false_abstention_rate": None,
        "latency_p50_ms": p50,
        "latency_p95_ms": p95,
    }
    if mode == "e2e":
        metrics["citation_precision"] = citation_precision(rows)
        metrics["expected_citation_coverage"] = expected_citation_coverage(rows)
        metrics["abstention_accuracy"] = abstention_accuracy(rows)
        metrics["false_abstention_rate"] = false_abstention_rate(rows)
    return metrics


def pick_winner(variants: Sequence[tuple[str, dict[str, Any]]]) -> str | None:
    """Ganadora por recall@5, desempate por MRR."""
    if not variants:
        return None
    return max(
        variants,
        key=lambda item: (item[1].get("recall_at_5", 0.0), item[1].get("mrr", 0.0)),
    )[0]


def meets_thresholds(metrics: dict[str, Any], mode: str) -> list[str]:
    """Devuelve las métricas que incumplen los umbrales de la fase."""
    failures: list[str] = []
    recall = metrics.get("recall_at_5")
    if recall is None or recall < 0.95:
        failures.append(f"recall_at_5={recall}")
    if mode == "e2e":
        precision = metrics.get("citation_precision")
        if precision is None or precision < 1.0:
            failures.append(f"citation_precision={precision}")
        abstention = metrics.get("abstention_accuracy")
        if abstention is None or abstention < 0.90:
            failures.append(f"abstention_accuracy={abstention}")
    return failures
