# ruff: noqa: E402
"""Ejecuta el set de aceptación y emite un reporte de citación."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from assistant.acceptance import (
    AcceptanceError,
    exit_code,
    load_questions,
    report_to_dict,
    run_acceptance,
    summary_markdown,
)
from assistant.config import ConfigError, Settings, load_dotenv
from assistant.corpus import CorpusError
from assistant.embeddings import EmbeddingError
from assistant.index import IndexError
from assistant.web import build_context

MIN_ANSWER_RATIO_HINT = "SC-001 exige ≥ 90 % de respuestas con cita válida."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ejecuta las preguntas de aceptación contra la cadena RAG."
    )
    parser.add_argument("--questions", type=Path, help="JSON con la lista de preguntas.")
    parser.add_argument("--json-out", type=Path, help="Ruta donde escribir el reporte JSON.")
    parser.add_argument(
        "--limit", type=int, default=None, help="Ejecuta solo las primeras N preguntas."
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Devuelve 0 si el corte cumple los criterios; 1 si no; 2 si no puede evaluar."""
    args = build_parser().parse_args(argv)
    try:
        load_dotenv()
        settings = Settings.from_env()
        questions_path = args.questions or settings.acceptance_file
        if questions_path is None:
            print(
                "Error: define ACCEPTANCE_FILE o pasa --questions con el set de preguntas.",
                file=sys.stderr,
            )
            return 2
        questions = load_questions(questions_path)
        if args.limit is not None:
            questions = questions[: max(0, args.limit)]
        context = build_context(settings)
        report = run_acceptance(context.rag, context.documents, questions)
    except (
        AcceptanceError,
        ConfigError,
        CorpusError,
        EmbeddingError,
        IndexError,
        RuntimeError,
    ) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print(summary_markdown(report))
    if args.json_out is not None:
        args.json_out.write_text(
            json.dumps(report_to_dict(report), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    code = exit_code(report)
    if code != 0:
        print(f"Resultado: NO cumple ({MIN_ANSWER_RATIO_HINT}).", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
