"""Feedback local de respuestas: JSONL append-only, sin PII."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

VALID_RATINGS = ("up", "down")
MAX_COMMENT = 500


class FeedbackError(ValueError):
    """Feedback inválido."""


@dataclass(frozen=True)
class FeedbackEntry:
    message_id: str
    rating: str
    comment: str
    created_at: str


def validate_feedback(
    message_id: str | None, rating: str | None, comment: str | None
) -> tuple[str, str, str]:
    """Valida y normaliza; devuelve (message_id, rating, comment)."""
    if not message_id or not message_id.strip():
        raise FeedbackError("message_id es obligatorio.")
    if rating not in VALID_RATINGS:
        raise FeedbackError("rating debe ser 'up' o 'down'.")
    cleaned = (comment or "").strip()
    if len(cleaned) > MAX_COMMENT:
        raise FeedbackError(f"El comentario no puede superar {MAX_COMMENT} caracteres.")
    return message_id.strip(), rating, cleaned


def record_feedback(
    path: Path,
    *,
    message_id: str,
    rating: str,
    comment: str = "",
) -> FeedbackEntry:
    """Añade una línea JSON; last-wins por message_id al leer."""
    message_id, rating, comment = validate_feedback(message_id, rating, comment)
    entry = FeedbackEntry(
        message_id=message_id,
        rating=rating,
        comment=comment,
        created_at=datetime.now(UTC).isoformat(),
    )
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.__dict__, ensure_ascii=False) + "\n")
    except OSError as error:
        raise FeedbackError(f"No se pudo guardar el feedback: {error}") from error
    return entry


def read_feedback(path: Path) -> list[FeedbackEntry]:
    """Lee el archivo; si hay varios registros por message_id, conserva el último."""
    if not path.is_file():
        return []
    latest: dict[str, FeedbackEntry] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        entry = FeedbackEntry(
            message_id=str(payload.get("message_id", "")),
            rating=str(payload.get("rating", "")),
            comment=str(payload.get("comment", "")),
            created_at=str(payload.get("created_at", "")),
        )
        if entry.message_id:
            latest[entry.message_id] = entry
    return list(latest.values())
