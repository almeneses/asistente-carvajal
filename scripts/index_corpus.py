# ruff: noqa: E402
"""Construye el índice Qdrant del corpus gold (fragmenta, embebe y carga)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from assistant.chunking import chunk_corpus
from assistant.config import ConfigError, Settings, load_dotenv
from assistant.corpus import CorpusError, load_corpus
from assistant.embeddings import EmbeddingError, OllamaEmbedder
from assistant.index import IndexError, QdrantIndex

BATCH_SIZE = 32


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Indexa el corpus gold en Qdrant.")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recrea la colección antes de indexar (recomendado tras cambiar el corpus).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Indexa el corpus y reporta documentos y fragmentos cargados."""
    args = build_parser().parse_args(argv)
    try:
        load_dotenv()
        settings = Settings.from_env()
        documents = load_corpus(settings.corpus_gold_dir)
        fragments = chunk_corpus(documents)
        embedder = OllamaEmbedder(settings.ollama_base_url, settings.embedding_model)
        index = QdrantIndex.open(settings)
        try:
            index.ensure_collection(recreate=args.recreate)
            for start in range(0, len(fragments), BATCH_SIZE):
                batch = fragments[start : start + BATCH_SIZE]
                vectors = embedder.embed([fragment.text for fragment in batch])
                index.upsert(batch, vectors)
            print(
                f"Indexados {len(fragments)} fragmentos de {len(documents)} documentos "
                f"en la colección {settings.qdrant_collection!r}."
            )
        finally:
            index.close()
            embedder.close()
        return 0
    except (ConfigError, CorpusError, EmbeddingError, IndexError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
