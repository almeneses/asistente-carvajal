# ruff: noqa: E402
"""Genera una propuesta de ground truth para revisión humana."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from assistant.acceptance import AcceptanceError, load_questions
from assistant.config import ConfigError, Settings, load_dotenv
from assistant.corpus import CorpusError, load_corpus
from assistant.evaluation.fingerprint import corpus_fingerprint
from assistant.evaluation.ground_truth import (
    GroundTruthError,
    candidate_payload,
    propose,
    render_review,
)
from assistant.llm import LLMError, build_llm


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Propone evidencia y estado esperado para las preguntas de evaluación."
    )
    parser.add_argument("--questions", type=Path, required=True, help="JSON de preguntas.")
    parser.add_argument("--output", type=Path, required=True, help="Candidato JSON.")
    parser.add_argument("--review", type=Path, required=True, help="Tabla de revisión MD.")
    parser.add_argument("--limit", type=int, help="Primeras N preguntas.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        load_dotenv()
        settings = Settings.from_env()
        documents = load_corpus(settings.corpus_gold_dir)
        items = load_questions(args.questions)
    except (ConfigError, CorpusError, AcceptanceError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    questions = [item.question for item in items]
    llm = build_llm(settings)
    try:
        proposals = propose(
            llm,
            documents,
            questions,
            limit=args.limit,
            progress=lambda message: print(f"[gt] {message}", file=sys.stderr),
        )
    except (GroundTruthError, LLMError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    finally:
        close = getattr(llm, "close", None)
        if callable(close):
            close()

    fingerprint = corpus_fingerprint(documents)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(candidate_payload(proposals, fingerprint), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.review.parent.mkdir(parents=True, exist_ok=True)
    args.review.write_text(render_review(proposals, fingerprint), encoding="utf-8")
    print(f"Propuestas: {len(proposals)} → {args.output}\nRevisión: {args.review}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
