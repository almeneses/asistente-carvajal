"""Pruebas de observabilidad: logs, request_id, readiness, métricas y cabeceras."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from assistant.config import Settings
from assistant.observability import REQUEST_ID, JsonFormatter
from assistant.rag import Answer, Source
from assistant.web import AppContext, create_app
from fastapi.testclient import TestClient
from tests.catalog_fixtures import sample_snapshot


class FakeRag:
    def answer(self, question: str, request_id: str | None = None) -> Answer:
        return Answer(
            status="answered",
            text="Respuesta [1].",
            sources=(
                Source(
                    title="Compañía Carvajal",
                    source_type="oficial",
                    url="https://www.carvajal.com/compania",
                    slug="compania",
                ),
            ),
            provider="fake",
            latency_ms=5,
            request_id=request_id or "r",
        )


def _client(tmp_path: Path, *, ready: bool = True) -> TestClient:
    context = AppContext(
        settings=Settings(
            corpus_gold_dir=tmp_path,
            feedback_log_path=tmp_path / "feedback.jsonl",
            quotes_log_path=tmp_path / "solicitudes.jsonl",
        ),
        rag=FakeRag(),  # type: ignore[arg-type]
        documents=[],
        index_ready=ready,
        provider="fake",
        catalog=sample_snapshot(tmp_path / "catalog"),
    )
    return TestClient(create_app(context=context))


def test_json_formatter_incluye_request_id() -> None:
    # Arrange
    token = REQUEST_ID.set("rid-123")
    record = logging.LogRecord("asistente", logging.INFO, __file__, 1, "evento", (), None)

    # Act
    payload = json.loads(JsonFormatter().format(record))

    # Assert
    REQUEST_ID.reset(token)
    assert payload["request_id"] == "rid-123"
    assert payload["message"] == "evento"


def test_request_id_y_cabeceras(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act
    response = client.get("/", headers={"X-Request-ID": "abc-123"})

    # Assert
    assert response.headers["X-Request-ID"] == "abc-123"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "strict-origin" in response.headers["Referrer-Policy"]
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]


def test_readyz_y_healthz(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)
    degraded = _client(tmp_path, ready=False)

    # Act / Assert
    assert client.get("/readyz").status_code == 200
    assert client.get("/readyz").json()["checks"] == {"index": True, "catalog": True}
    assert degraded.get("/readyz").status_code == 503
    assert degraded.get("/healthz").status_code == 503


def test_metrics_expone_contadores(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act
    client.get("/")
    response = client.get("/metrics")

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert "asistente_http_requests_total" in body
    assert "asistente_uptime_seconds" in body
    assert "asistente_index_ready 1" in body
    assert "asistente_catalog_loaded 1" in body


def test_logs_no_contienen_pregunta(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)
    secreto = "pregunta-secreta-123"
    records: list[logging.LogRecord] = []

    class Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = Capture()
    logger = logging.getLogger("asistente")
    logger.addHandler(handler)

    try:
        # Act
        client.post("/ask", data={"question": secreto})
    finally:
        logger.removeHandler(handler)

    # Assert
    assert any(record.getMessage() == "request" for record in records)
    for record in records:
        serialized = " ".join(str(value) for value in record.__dict__.values())
        assert secreto not in serialized


def test_contacto_de_cotizacion_no_aparece_en_logs(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)
    email = "contacto-secreto@example.com"
    records: list[logging.LogRecord] = []

    class Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = Capture()
    logger = logging.getLogger("asistente")
    logger.addHandler(handler)

    try:
        # Act
        client.post(
            "/quotes",
            data={
                "sku": "MX-VASO-12-PP",
                "boxes": 1,
                "contact_email": email,
                "consent": "true",
            },
        )
    finally:
        logger.removeHandler(handler)

    # Assert
    for record in records:
        serialized = " ".join(str(value) for value in record.__dict__.values())
        assert email not in serialized
