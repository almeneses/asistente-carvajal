"""Pruebas del endpoint de solicitudes y de su UI de confirmación."""

from __future__ import annotations

from pathlib import Path

from assistant.config import Settings
from assistant.rag import Answer, Source
from assistant.web import AppContext, create_app
from fastapi.testclient import TestClient
from tests.catalog_fixtures import sample_snapshot


class StaticRag:
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


def _client(tmp_path: Path) -> TestClient:
    context = AppContext(
        settings=Settings(
            corpus_gold_dir=tmp_path,
            feedback_log_path=tmp_path / "feedback.jsonl",
            quotes_log_path=tmp_path / "solicitudes.jsonl",
        ),
        rag=StaticRag(),  # type: ignore[arg-type]
        documents=[],
        index_ready=True,
        provider="fake",
        catalog=sample_snapshot(tmp_path / "catalog"),
    )
    return TestClient(create_app(context=context))


def test_quote_endpoint(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act
    response = client.post("/quotes", data={"sku": "MX-VASO-12-PP", "boxes": 5, "city": "Bogotá"})

    # Assert
    assert response.status_code == 200
    quote = response.json()["quote"]
    assert quote["code"].startswith("OC-")
    assert quote["boxes"] == 5
    assert quote["total"] == 4500
    assert (tmp_path / "solicitudes.jsonl").is_file()


def test_quote_invalida(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act / Assert
    assert client.post("/quotes", data={"sku": "NO-EXISTE", "boxes": 1}).status_code == 422
    assert client.post("/quotes", data={"sku": "MX-VASO-12-PP", "boxes": 0}).status_code == 422


def test_chat_incluye_confirmacion_y_cta(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act
    chat = client.get("/chat").text
    stream = client.post(
        "/ask/stream", data={"question": "necesito vasos para café caliente de 12 oz"}
    ).text

    # Assert
    assert 'id="confirmation-full"' in chat
    assert 'id="confirmation-compact"' in chat
    assert "Minimizar" in chat
    assert "Solicitar cotización" in stream
    assert "data-quote" in stream
