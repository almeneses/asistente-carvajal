"""Serialización de reportes de evaluación."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from assistant.evaluation.variants import VariantConfig

SCHEMA_VERSION = 1


class ReportError(RuntimeError):
    """El reporte no se pudo escribir."""


@dataclass(frozen=True)
class QuestionRow:
    """Resultado de una pregunta en una variante."""

    id: str
    question: str
    expected_slugs: tuple[str, ...]
    expected_status: str
    retrieved_slugs: tuple[str, ...]
    rank_first_expected: int | None
    status: str | None
    sources: tuple[str, ...]
    source_slugs: tuple[str, ...]
    citations_invalid: int
    latency_ms: int
    error: str | None = None


@dataclass(frozen=True)
class VariantReport:
    """Configuración, métricas y filas de una variante."""

    config: VariantConfig
    metrics: dict[str, Any]
    rows: tuple[QuestionRow, ...]


@dataclass(frozen=True)
class RunReport:
    """Reporte completo de una ejecución."""

    generated_at: str
    mode: str
    corpus_fingerprint: str
    index_jsonl_sha256: str
    indexed_fragments: dict[str, int]
    provider: str | None
    variants: tuple[VariantReport, ...]
    winner: str | None
    schema_version: int = SCHEMA_VERSION
    not_comparable_with: str | None = None
    omitted: tuple[dict[str, str], ...] = ()
    migration_recommendation: str | None = None


def _row_to_dict(row: QuestionRow) -> dict[str, Any]:
    return {
        "id": row.id,
        "question": row.question,
        "expected_slugs": list(row.expected_slugs),
        "expected_status": row.expected_status,
        "retrieved_slugs": list(row.retrieved_slugs),
        "rank_first_expected": row.rank_first_expected,
        "status": row.status,
        "sources": list(row.sources),
        "source_slugs": list(row.source_slugs),
        "citations_invalid": row.citations_invalid,
        "latency_ms": row.latency_ms,
        "error": row.error,
    }


def report_to_dict(report: RunReport) -> dict[str, Any]:
    """Convierte el reporte a un diccionario JSON serializable."""
    return {
        "schema_version": report.schema_version,
        "generated_at": report.generated_at,
        "mode": report.mode,
        "corpus_fingerprint": report.corpus_fingerprint,
        "index_jsonl_sha256": report.index_jsonl_sha256,
        "indexed_fragments": dict(sorted(report.indexed_fragments.items())),
        "provider": report.provider,
        "variants": [
            {
                "config": {
                    "id": variant.config.id,
                    "embedding_model": variant.config.embedding_model,
                    "embedding_dim": variant.config.embedding_dim,
                    "chunk_size": variant.config.chunk_size,
                    "overlap": variant.config.overlap,
                    "cosine_weight": variant.config.cosine_weight,
                    "lexical_weight": variant.config.lexical_weight,
                    "collection": variant.config.collection,
                    "min_score": variant.config.min_score,
                },
                "metrics": dict(sorted(variant.metrics.items())),
                "rows": [_row_to_dict(row) for row in variant.rows],
            }
            for variant in report.variants
        ],
        "winner": report.winner,
        "not_comparable_with": report.not_comparable_with,
        "omitted": list(report.omitted),
        "migration_recommendation": report.migration_recommendation,
    }


def _format_metric(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def render_markdown(report: RunReport) -> str:
    """Tabla comparativa y hallazgos accionables."""
    e2e = report.mode == "e2e"
    lines = [
        "# Reporte de evaluación",
        "",
        f"- Modo: `{report.mode}`",
        f"- Generado: {report.generated_at}",
        f"- Fingerprint del corpus: `{report.corpus_fingerprint[:16]}…`",
        f"- Fingerprint de index.jsonl: `{report.index_jsonl_sha256[:16]}…`",
        f"- Proveedor: {report.provider or '—'}",
        "",
        "| Variante | recall@1 | recall@5 | MRR | p50 ms | p95 ms |"
        + (" Citas | Abstención | Cobertura |" if e2e else ""),
        "|---|---|---|---|---|---|" + ("---|---|---|" if e2e else ""),
    ]
    for variant in report.variants:
        metrics = variant.metrics
        row = (
            f"| {variant.config.id} | "
            f"{_format_metric(metrics.get('recall_at_1'))} | "
            f"{_format_metric(metrics.get('recall_at_5'))} | "
            f"{_format_metric(metrics.get('mrr'))} | "
            f"{_format_metric(metrics.get('latency_p50_ms'))} | "
            f"{_format_metric(metrics.get('latency_p95_ms'))} |"
        )
        if e2e:
            row += (
                f" {_format_metric(metrics.get('citation_precision'))} |"
                f" {_format_metric(metrics.get('abstention_accuracy'))} |"
                f" {_format_metric(metrics.get('expected_citation_coverage'))} |"
            )
        lines.append(row)
    lines.append("")
    lines.append(f"**Ganadora**: `{report.winner}`" if report.winner else "**Ganadora**: —")
    if report.omitted:
        lines.append("")
        lines.append("## Variantes omitidas")
        lines.append("")
        lines.extend(f"- `{item['id']}`: {item['reason']}" for item in report.omitted)
    if report.migration_recommendation:
        lines.append("")
        lines.append(f"**Recomendación**: {report.migration_recommendation}")
    if report.not_comparable_with:
        lines.append("")
        lines.append(f"⚠️ No comparable con `{report.not_comparable_with}`: fingerprint distinto.")
    failures = [
        f"- `{row.id}` ({row.expected_status}): "
        f"{'sin evidencia esperada recuperada' if row.rank_first_expected is None else 'ok'}"
        for variant in report.variants
        for row in variant.rows
        if row.expected_status == "sustainable" and row.rank_first_expected is None
    ]
    if failures:
        lines.append("")
        lines.append("## Preguntas sin evidencia recuperada")
        lines.append("")
        lines.extend(failures[:20])
    return "\n".join(lines) + "\n"


def write_reports(
    report: RunReport,
    *,
    json_path: Path | None = None,
    markdown_path: Path | None = None,
) -> None:
    """Escribe los reportes JSON y/o Markdown; falla con mensaje accionable."""
    if json_path is not None:
        try:
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(
                json.dumps(report_to_dict(report), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError as error:
            raise ReportError(f"No se pudo escribir {json_path}: {error}") from error
    if markdown_path is not None:
        try:
            markdown_path.parent.mkdir(parents=True, exist_ok=True)
            markdown_path.write_text(render_markdown(report), encoding="utf-8")
        except OSError as error:
            raise ReportError(f"No se pudo escribir {markdown_path}: {error}") from error


def index_rows(
    rows: Sequence[QuestionRow], ids: Sequence[str] | None = None
) -> tuple[QuestionRow, ...]:
    """Ordena las filas por id y, opcionalmente, restringe a ids dados."""
    if ids is not None:
        wanted = set(ids)
        rows = [row for row in rows if row.id in wanted]
    return tuple(sorted(rows, key=lambda row: row.id))
