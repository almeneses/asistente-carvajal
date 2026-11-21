"""Observabilidad: logs JSON, request_id, métricas y cabeceras."""

from __future__ import annotations

import json
import logging
import re
import sys
import threading
import time
from collections import defaultdict
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from fastapi import Request, Response

REQUEST_ID: ContextVar[str] = ContextVar("request_id", default="-")
_RID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_METRIC_PATHS = {
    "/",
    "/chat",
    "/ask",
    "/ask/stream",
    "/feedback",
    "/quotes",
    "/healthz",
    "/readyz",
    "/metrics",
}


class JsonFormatter(logging.Formatter):
    """Formatter JSON con request_id y campos extra seguros."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": REQUEST_ID.get(),
        }
        for key in ("method", "path", "status", "latency_ms", "route", "provider", "count"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO", log_format: str = "json") -> None:
    """Configura el logger de la aplicación una sola vez."""
    logger = logging.getLogger("asistente")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    if any(isinstance(handler.formatter, JsonFormatter) for handler in logger.handlers):
        return
    handler = logging.StreamHandler(sys.stderr)
    if log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


def sanitize_request_id(value: str | None) -> str:
    """Acepta solo IDs seguros; si no, genera uno nuevo."""
    if value and _RID_PATTERN.match(value):
        return value
    import uuid

    return uuid.uuid4().hex


def metric_path(path: str) -> str:
    """Normaliza rutas para evitar cardinalidad alta."""
    if path.startswith("/static/"):
        return "/static/*"
    return path if path in _METRIC_PATHS else "other"


class Metrics:
    """Contadores y duraciones en memoria (formato Prometheus)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started = time.monotonic()
        self._requests: dict[tuple[str, str, int], int] = defaultdict(int)
        self._duration_sum: dict[tuple[str, str], float] = defaultdict(float)
        self._duration_count: dict[tuple[str, str], int] = defaultdict(int)
        self._events: dict[str, int] = defaultdict(int)

    def observe_request(self, method: str, path: str, status: int, seconds: float) -> None:
        with self._lock:
            self._requests[(method, metric_path(path), status)] += 1
            key = (method, metric_path(path))
            self._duration_sum[key] += seconds
            self._duration_count[key] += 1

    def inc(self, event: str, count: int = 1) -> None:
        with self._lock:
            self._events[event] += count

    @property
    def uptime_seconds(self) -> float:
        return time.monotonic() - self._started

    def render(self, gauges: dict[str, float]) -> str:
        lines = [
            "# HELP asistente_http_requests_total Peticiones HTTP atendidas.",
            "# TYPE asistente_http_requests_total counter",
        ]
        with self._lock:
            for (method, path, status), count in sorted(self._requests.items()):
                labels = f'method="{method}",path="{path}",status="{status}"'
                lines.append(f"asistente_http_requests_total{{{labels}}} {count}")
            lines += [
                "# HELP asistente_http_request_duration_seconds Duración acumulada.",
                "# TYPE asistente_http_request_duration_seconds summary",
            ]
            for (method, path), total in sorted(self._duration_sum.items()):
                labels = f'method="{method}",path="{path}"'
                count = self._duration_count[(method, path)]
                lines.append(f"asistente_http_request_duration_seconds_sum{{{labels}}} {total:.6f}")
                lines.append(f"asistente_http_request_duration_seconds_count{{{labels}}} {count}")
            lines += [
                "# HELP asistente_events_total Eventos operativos.",
                "# TYPE asistente_events_total counter",
            ]
            for event, count in sorted(self._events.items()):
                lines.append(f'asistente_events_total{{event="{event}"}} {count}')
        lines += [
            "# HELP asistente_uptime_seconds Tiempo desde el arranque.",
            "# TYPE asistente_uptime_seconds gauge",
            f"asistente_uptime_seconds {self.uptime_seconds:.3f}",
        ]
        for name, value in sorted(gauges.items()):
            lines += [
                f"# HELP {name} Indicador de estado.",
                f"# TYPE {name} gauge",
                f"{name} {value:g}",
            ]
        return "\n".join(lines) + "\n"


METRICS = Metrics()


async def observability_middleware(request: Request, call_next: Any) -> Response:
    """Añade request_id, seguridad, latencia y métricas a cada petición."""
    rid = sanitize_request_id(request.headers.get("X-Request-ID"))
    token = REQUEST_ID.set(rid)
    started = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        apply_security_headers(response)
        response.headers["X-Request-ID"] = rid
        return response
    except Exception:
        logging.getLogger("asistente").exception(
            "request_error", extra={"method": request.method, "path": request.url.path}
        )
        raise
    finally:
        elapsed = time.perf_counter() - started
        METRICS.observe_request(request.method, request.url.path, status, elapsed)
        logging.getLogger("asistente").info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": status,
                "latency_ms": round(elapsed * 1000, 1),
            },
        )
        REQUEST_ID.reset(token)


def apply_security_headers(response: Response) -> None:
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "microphone=(self)")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
    )
