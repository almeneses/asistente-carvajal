# ruff: noqa: E402
"""Ejecuta la evaluación de recuperación (matriz) o end-to-end (una variante)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from assistant.config import ConfigError, Settings, load_dotenv
from assistant.corpus import CorpusError, load_corpus
from assistant.embeddings import EmbeddingError
from assistant.evaluation.dataset import DatasetError, load_and_validate
from assistant.evaluation.fingerprint import corpus_fingerprint
from assistant.evaluation.metrics import meets_thresholds
from assistant.evaluation.reports import ReportError, write_reports
from assistant.evaluation.runner import run_end_to_end, run_retrieval
from assistant.evaluation.variants import VariantError, select_variants
from assistant.index import IndexError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evalúa recuperación (matriz) o end-to-end (una variante)."
    )
    parser.add_argument("--set", type=Path, required=True, help="Ground truth JSON.")
    parser.add_argument("--mode", choices=("retrieval", "e2e"), default="retrieval")
    parser.add_argument(
        "--variants",
        default="all",
        help="'all' o lista de ids separada por comas (p. ej. nomic-1000-hybrid).",
    )
    parser.add_argument("--qdrant-path", type=Path, help="Índice de evaluación aislado.")
    parser.add_argument("--qdrant-url", help="Qdrant remoto para la evaluación.")
    parser.add_argument("--recreate", action="store_true", help="Recrea las colecciones.")
    parser.add_argument(
        "--allow-stale-set",
        action="store_true",
        help="Permite un set anotado sobre otro corpus (solo diagnóstico).",
    )
    parser.add_argument("--limit", type=int, help="Primeras N preguntas.")
    parser.add_argument("--validate-only", action="store_true", help="Valida el set y termina.")
    parser.add_argument("--json-out", type=Path, help="Reporte JSON de salida.")
    parser.add_argument("--markdown-out", type=Path, help="Reporte Markdown de salida.")
    return parser


def _progress(message: str) -> None:
    print(f"[eval] {message}", file=sys.stderr)


def _fail(message: str, code: int) -> int:
    print(f"Error: {message}", file=sys.stderr)
    return code


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        load_dotenv()
        settings = Settings.from_env()
        overrides: dict[str, object] = {}
        if args.qdrant_path is not None:
            overrides["eval_qdrant_path"] = args.qdrant_path
        if args.qdrant_url is not None:
            overrides["qdrant_url"] = args.qdrant_url
        if overrides:
            settings = replace(settings, **overrides)  # type: ignore[arg-type]
        documents = load_corpus(settings.corpus_gold_dir)
        evaluation_set = load_and_validate(args.set, {document.slug for document in documents})
    except (ConfigError, CorpusError, DatasetError) as error:
        return _fail(str(error), 2)

    if args.validate_only:
        print(f"Set válido: {len(evaluation_set.questions)} preguntas.")
        return 0

    expected = corpus_fingerprint(documents)
    if evaluation_set.corpus_fingerprint != expected:
        message = (
            "El set se anotó sobre otro corpus "
            f"(set={evaluation_set.corpus_fingerprint[:12]}…, "
            f"actual={expected[:12]}…)."
        )
        if not args.allow_stale_set:
            return _fail(message + " Usa --allow-stale-set para diagnóstico.", 1)
        print(f"Advertencia: {message}", file=sys.stderr)

    try:
        variants = select_variants(args.variants)
    except VariantError as error:
        return _fail(str(error), 2)
    if args.mode == "e2e" and len(variants) != 1:
        return _fail("--mode e2e exige exactamente una variante en --variants.", 2)

    try:
        if args.mode == "retrieval":
            report = run_retrieval(
                settings,
                documents,
                evaluation_set,
                variants,
                limit=args.limit,
                recreate=args.recreate,
                progress=_progress,
            )
        else:
            report = run_end_to_end(
                settings,
                documents,
                evaluation_set,
                variants[0],
                limit=args.limit,
                recreate=args.recreate,
                progress=_progress,
            )
    except (IndexError, EmbeddingError, RuntimeError) as error:
        return _fail(str(error), 2)

    try:
        write_reports(report, json_path=args.json_out, markdown_path=args.markdown_out)
    except ReportError as error:
        return _fail(str(error), 2)

    if args.mode == "retrieval":
        print(f"Variantes evaluadas: {len(report.variants)}. Ganadora: {report.winner}")
        return 0

    variant_report = report.variants[0]
    failures = meets_thresholds(variant_report.metrics, "e2e")
    print(f"Variante: {variant_report.config.id}")
    print(f"Métricas: {variant_report.metrics}")
    if failures:
        return _fail("Umbrales incumplidos: " + ", ".join(failures), 1)
    print("Umbrales cumplidos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
