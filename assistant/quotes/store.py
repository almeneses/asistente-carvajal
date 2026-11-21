"""Persistencia append-only de solicitudes en JSONL (sin PII)."""

from __future__ import annotations

import json
import secrets
from datetime import UTC, datetime
from pathlib import Path

from assistant.quotes.models import QuoteError, QuoteRecord

_CODE_CHARS = "0123456789ABCDEF"


def generate_code(now: datetime | None = None) -> str:
    """Código legible OC-AAAA-MMDD-XXXX."""
    moment = now or datetime.now(UTC)
    suffix = "".join(secrets.choice(_CODE_CHARS) for _ in range(4))
    return f"OC-{moment:%Y}-{moment:%m%d}-{suffix}"


def read_quotes(path: Path) -> list[QuoteRecord]:
    """Lee las solicitudes guardadas; ignora líneas corruptas."""
    if not path.is_file():
        return []
    records: list[QuoteRecord] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
            records.append(QuoteRecord(**payload))
        except (json.JSONDecodeError, TypeError):
            continue
    return records


def append_quote(path: Path, record: QuoteRecord) -> None:
    """Añade una línea JSON; no reescribe el archivo."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.__dict__, ensure_ascii=False) + "\n")
    except OSError as error:
        raise QuoteError(f"No se pudo registrar la solicitud: {error}") from error
