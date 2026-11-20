"""Carga del corpus gold (solo lectura) y validación de sus metadatos."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_REQUIRED_FIELDS = (
    "url",
    "title",
    "section",
    "source_type",
    "captured_at",
    "hash",
    "chars",
)
_VALID_SOURCE_TYPES = ("oficial", "tercero")


class CorpusError(RuntimeError):
    """El corpus no cumple el contrato esperado."""


@dataclass(frozen=True)
class CorpusDocument:
    """Documento curado del corpus, con sus metadatos de citación."""

    slug: str
    title: str
    url: str
    section: str
    source_type: str
    captured_at: str
    hash: str
    chars: int
    body: str


def _parse_front_matter(text: str, slug: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise CorpusError(f"{slug}: falta el front matter delimitado por '---'.")
    end = text.find("\n---", 4)
    if end == -1:
        raise CorpusError(f"{slug}: el front matter no está cerrado.")
    header = text[4:end]
    body = text[end + 4 :].lstrip("\n")
    metadata: dict[str, str] = {}
    for line in header.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata, body


def _to_document(path: Path) -> CorpusDocument:
    slug = path.stem
    metadata, body = _parse_front_matter(path.read_text(encoding="utf-8"), slug)
    missing = [name for name in _REQUIRED_FIELDS if not metadata.get(name)]
    if missing:
        raise CorpusError(f"{slug}: faltan metadatos obligatorios: {', '.join(missing)}")
    source_type = metadata["source_type"]
    if source_type not in _VALID_SOURCE_TYPES:
        raise CorpusError(f"{slug}: source_type inválido ({source_type!r}); usa oficial o tercero.")
    if not metadata["url"].startswith(("http://", "https://")):
        raise CorpusError(f"{slug}: url inválida ({metadata['url']!r}).")
    if len(metadata["hash"]) != 64:
        raise CorpusError(f"{slug}: hash debe tener 64 caracteres hexadecimales.")
    try:
        chars = int(metadata["chars"])
    except ValueError as error:
        raise CorpusError(f"{slug}: chars debe ser un entero.") from error
    if chars < 0:
        raise CorpusError(f"{slug}: chars no puede ser negativo.")
    return CorpusDocument(
        slug=slug,
        title=metadata["title"],
        url=metadata["url"],
        section=metadata["section"],
        source_type=source_type,
        captured_at=metadata["captured_at"],
        hash=metadata["hash"],
        chars=chars,
        body=body,
    )


def load_corpus(gold_dir: Path) -> list[CorpusDocument]:
    """Carga todos los documentos del corpus y valida el índice de slugs."""
    index_file = gold_dir / "index.jsonl"
    if not index_file.is_file():
        raise CorpusError(f"No existe el índice del corpus: {index_file}")
    indexed: set[str] = set()
    for number, raw in enumerate(index_file.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as error:
            raise CorpusError(f"index.jsonl:{number}: JSON inválido.") from error
        slug = payload.get("slug")
        if not slug:
            raise CorpusError(f"index.jsonl:{number}: falta el campo slug.")
        indexed.add(str(slug))

    documents: list[CorpusDocument] = []
    found: set[str] = set()
    for path in sorted(gold_dir.glob("*.md")):
        document = _to_document(path)
        if document.slug not in indexed:
            raise CorpusError(
                f"{document.slug}: no aparece en index.jsonl (el corpus y el índice divergen)."
            )
        documents.append(document)
        found.add(document.slug)

    missing = sorted(indexed - found)
    if missing:
        raise CorpusError(f"index.jsonl referencia documentos ausentes: {', '.join(missing)}")
    if not documents:
        raise CorpusError(f"No hay documentos *.md en {gold_dir}")
    return documents
