"""Pruebas del runner de evaluación (Qdrant embebido y dobles de prueba)."""

from __future__ import annotations

from pathlib import Path

from assistant.config import Settings
from assistant.evaluation.fingerprint import corpus_fingerprint
from assistant.evaluation.reports import render_markdown, report_to_dict
from assistant.evaluation.runner import run_end_to_end, run_retrieval
from assistant.evaluation.variants import select_variants
from tests.eval_fixtures import (
    FakeEmbedder,
    ScriptedLLM,
    sample_documents,
    sample_set,
)


def _settings(tmp_path: Path) -> Settings:
    (tmp_path / "index.jsonl").write_text("{}\n", encoding="utf-8")
    return Settings(
        corpus_gold_dir=tmp_path,
        eval_qdrant_path=tmp_path / "qdrant-eval",
    )


def _factory(_model: str, dim: int) -> FakeEmbedder:
    return FakeEmbedder(dim)


def _sample_set():
    return sample_set(fingerprint="fp-sintetico")


def test_recuperacion_por_variante(tmp_path: Path) -> None:
    # Arrange
    settings = _settings(tmp_path)
    documents = sample_documents()
    variants = select_variants("nomic-1000-hybrid")

    # Act
    report = run_retrieval(
        settings,
        documents,
        _sample_set(),
        variants,
        recreate=True,
        embedder_factory=_factory,
    )

    # Assert
    assert report.mode == "retrieval"
    assert report.winner == "nomic-1000-hybrid"
    variant = report.variants[0]
    assert variant.metrics["recall_at_5"] == 1.0
    rows = {row.id: row for row in variant.rows}
    assert rows["q01"].rank_first_expected == 1
    assert rows["q02"].rank_first_expected == 1
    assert rows["q03"].rank_first_expected is None
    assert report.corpus_fingerprint == corpus_fingerprint(documents)


def test_end_to_end_con_citas_y_abstencion(tmp_path: Path) -> None:
    # Arrange
    settings = _settings(tmp_path)
    documents = sample_documents()
    variant = select_variants("nomic-1000-hybrid")[0]

    # Act
    report = run_end_to_end(
        settings,
        documents,
        _sample_set(),
        variant,
        recreate=True,
        embedder_factory=_factory,
        llm_factory=lambda: ScriptedLLM(),
    )

    # Assert
    assert report.mode == "e2e"
    variant_report = report.variants[0]
    rows = {row.id: row for row in variant_report.rows}
    assert rows["q01"].status == "answered"
    assert rows["q02"].status == "answered"
    assert rows["q03"].status == "no_evidence"
    assert variant_report.metrics["citation_precision"] == 1.0
    assert variant_report.metrics["abstention_accuracy"] == 1.0
    assert variant_report.metrics["recall_at_5"] == 1.0


def test_fila_con_error_no_rompe_el_reporte(tmp_path: Path) -> None:
    # Arrange
    settings = _settings(tmp_path)
    variant = select_variants("nomic-1000-hybrid")[0]

    class FailingLLM(ScriptedLLM):
        def generate(self, messages):  # type: ignore[no-untyped-def]
            raise RuntimeError("proveedor caído")

    # Act
    report = run_end_to_end(
        settings,
        sample_documents(),
        _sample_set(),
        variant,
        limit=1,
        recreate=True,
        embedder_factory=_factory,
        llm_factory=lambda: FailingLLM(),
    )

    # Assert
    row = report.variants[0].rows[0]
    assert row.status == "error"
    assert row.error is not None


def test_reporte_json_y_markdown(tmp_path: Path) -> None:
    # Arrange
    settings = _settings(tmp_path)
    report = run_retrieval(
        settings,
        sample_documents(),
        _sample_set(),
        select_variants("nomic-1000-hybrid"),
        recreate=True,
        embedder_factory=_factory,
    )

    # Act
    payload = report_to_dict(report)
    markdown = render_markdown(report)

    # Assert
    assert payload["schema_version"] == 1
    assert payload["winner"] == "nomic-1000-hybrid"
    assert payload["variants"][0]["config"]["embedding_dim"] == 768
    assert "nomic-1000-hybrid" in markdown


def test_determinismo_de_filas(tmp_path: Path) -> None:
    # Arrange
    settings = _settings(tmp_path)
    variants = select_variants("nomic-1000-hybrid")

    # Act
    first = run_retrieval(
        settings,
        sample_documents(),
        _sample_set(),
        variants,
        recreate=True,
        embedder_factory=_factory,
    )
    second = run_retrieval(
        settings,
        sample_documents(),
        _sample_set(),
        variants,
        recreate=True,
        embedder_factory=_factory,
    )

    # Assert
    first_rows = [
        (row.id, row.retrieved_slugs, row.rank_first_expected) for row in first.variants[0].rows
    ]
    second_rows = [
        (row.id, row.retrieved_slugs, row.rank_first_expected) for row in second.variants[0].rows
    ]
    assert first_rows == second_rows
    assert first.variants[0].metrics["recall_at_5"] == second.variants[0].metrics["recall_at_5"]
