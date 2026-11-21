"""Pruebas del endpoint SSE y del feedback HTTP."""

from __future__ import annotations

from pathlib import Path

from assistant.config import Settings
from assistant.rag import Answer, Source, StreamOutcome
from assistant.web import AppContext, create_app
from fastapi.testclient import TestClient
from tests.catalog_fixtures import sample_snapshot

SOURCE = Source(
    title="Compañía Carvajal",
    source_type="oficial",
    url="https://www.carvajal.com/compania",
    slug="compania",
)


class StreamingRag:
    def __init__(self, *, error: bool = False) -> None:
        self.error = error

    def answer(self, question: str, request_id: str | None = None) -> Answer:
        return Answer(
            status="answered",
            text="Respuesta de prueba [1].",
            sources=(SOURCE,),
            provider="fake",
            latency_ms=5,
            request_id=request_id or "r",
        )

    def stream_tokens(self, question: str, request_id: str, outcome: StreamOutcome) -> object:
        if self.error:
            raise RuntimeError("proveedor caído")
        yield "Carvajal "
        yield "nació en 1904 [1]."
        outcome.answer = Answer(
            status="answered",
            text="Carvajal nació en 1904 [1].",
            sources=(SOURCE,),
            provider="fake",
            latency_ms=12,
            request_id=request_id,
        )


def _client(
    tmp_path: Path, *, rag: StreamingRag | None = None, with_catalog: bool = False
) -> TestClient:
    context = AppContext(
        settings=Settings(
            corpus_gold_dir=tmp_path,
            feedback_log_path=tmp_path / "feedback.jsonl",
        ),
        rag=(rag or StreamingRag()),  # type: ignore[arg-type]
        documents=[],
        index_ready=True,
        provider="fake",
        catalog=sample_snapshot(tmp_path / "catalog") if with_catalog else None,
    )
    return TestClient(create_app(context=context))


def test_stream_documental(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act
    response = client.post("/ask/stream", data={"question": "¿Qué es Carvajal?"})

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert "event: start" in body
    assert "event: token" in body
    assert "event: sources" in body
    assert "event: done" in body
    assert "final_html" in body
    assert "Carvajal nació en 1904" in body


def test_stream_pregunta_invalida(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act
    response = client.post("/ask/stream", data={"question": "   "})

    # Assert
    assert response.status_code == 422
    assert response.json()["detail"]


def test_stream_error_emite_evento(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path, rag=StreamingRag(error=True))

    # Act
    response = client.post("/ask/stream", data={"question": "¿Qué es Carvajal?"})

    # Assert
    assert response.status_code == 200
    assert "event: error" in response.text
    assert "retryable" in response.text


def test_stream_catalogo(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path, with_catalog=True)

    # Act
    response = client.post(
        "/ask/stream", data={"question": "necesito vasos para café caliente de 12 oz"}
    )

    # Assert
    assert response.status_code == 200
    body = response.text
    assert "event: quote_best" in body
    assert "Mejor opción" in body
    assert "Solicitar cotización" in body
    assert "data-image=" in body
    assert body.count("Elegir esta opción") <= 2
    assert "event: done" in body
    if "event: quote_alternatives" in body:
        assert body.index("event: quote_best") < body.index("event: quote_alternatives")


def test_feedback_http(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act
    response = client.post(
        "/feedback", data={"message_id": "m-1", "rating": "up", "comment": "clara"}
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert (tmp_path / "feedback.jsonl").is_file()


def test_feedback_invalido(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act
    response = client.post("/feedback", data={"message_id": "", "rating": "up"})

    # Assert
    assert response.status_code == 422
