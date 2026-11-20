"""Fingerprint del corpus para comparar evaluaciones."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from assistant.corpus import CorpusDocument


class FingerprintError(RuntimeError):
    """No se pudo calcular el fingerprint del corpus."""


def corpus_fingerprint(documents: list[CorpusDocument]) -> str:
    """sha256 de las parejas slug:hash en orden de slug."""
    payload = "\n".join(
        f"{document.slug}:{document.hash}"
        for document in sorted(documents, key=lambda item: item.slug)
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def index_jsonl_sha256(index_path: Path) -> str:
    """sha256 del archivo index.jsonl del corpus."""
    if not index_path.is_file():
        raise FingerprintError(f"No existe el índice del corpus: {index_path}")
    return sha256(index_path.read_bytes()).hexdigest()


def fingerprints(documents: list[CorpusDocument], index_path: Path) -> dict[str, str]:
    """Devuelve ambos fingerprints que se guardan en el reporte."""
    return {
        "corpus_fingerprint": corpus_fingerprint(documents),
        "index_jsonl_sha256": index_jsonl_sha256(index_path),
    }


def is_stale(set_fingerprint: str, documents: list[CorpusDocument]) -> bool:
    """Indica si el set se anotó sobre otro corpus."""
    return set_fingerprint != corpus_fingerprint(documents)
