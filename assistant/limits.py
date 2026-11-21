"""Límites en memoria por usuario (una instancia)."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from datetime import date

_WINDOW_SECONDS = 60


class Limits:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._daily: dict[tuple[str, str], int] = defaultdict(int)

    def rate_limited(self, user: str, bucket: str, limit: int) -> int | None:
        """Devuelve segundos de espera si supera el límite por minuto."""
        now = time.monotonic()
        with self._lock:
            events = self._events[(user, bucket)]
            while events and now - events[0] > _WINDOW_SECONDS:
                events.popleft()
            if len(events) >= limit:
                return max(1, int(_WINDOW_SECONDS - (now - events[0])))
            events.append(now)
            return None

    def quote_quota_exceeded(self, user: str, limit: int) -> bool:
        key = (user, date.today().isoformat())
        with self._lock:
            return self._daily[key] >= limit

    def register_quote(self, user: str) -> None:
        key = (user, date.today().isoformat())
        with self._lock:
            self._daily[key] += 1


LIMITS = Limits()
