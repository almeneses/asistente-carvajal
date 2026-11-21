"""Codificación de eventos SSE para el chat."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

KEEPALIVE = ": keep-alive\n\n"


@dataclass(frozen=True)
class StreamEvent:
    """Un evento del stream SSE."""

    event: str
    data: dict[str, Any] = field(default_factory=dict)


def encode_event(event: StreamEvent) -> str:
    """Serializa un evento en el formato SSE (`event:` + `data:`)."""
    payload = json.dumps(event.data, ensure_ascii=False)
    return f"event: {event.event}\ndata: {payload}\n\n"
