"""Pruebas de estructura accesible y del fallback síncrono."""

from __future__ import annotations

from pathlib import Path

from assistant.config import Settings
from assistant.rag import Answer, Source
from assistant.web import AppContext, create_app
from fastapi.testclient import TestClient


class ScriptedRag:
    def answer(self, question: str, request_id: str | None = None) -> Answer:
        return Answer(
            status="answered",
            text="Respuesta **documental** [1].",
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
        ),
        rag=ScriptedRag(),  # type: ignore[arg-type]
        documents=[],
        index_ready=True,
        provider="fake",
    )
    return TestClient(create_app(context=context))


def test_estructura_accesible(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act
    response = client.get("/chat")

    # Assert
    body = response.text
    assert 'aria-live="polite"' in body
    assert 'role="status"' in body
    assert 'for="question"' in body
    assert 'id="conversation"' in body
    assert "stitch.css" in body
    assert "Carvajal" in body
    assert "Nueva conversación" in body


def test_fallback_sincrono_renderiza_markdown(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act
    response = client.post("/ask", data={"question": "¿Qué es Carvajal?"})

    # Assert
    assert response.status_code == 200
    assert "<strong>documental</strong>" in response.text
    assert 'rel="noopener noreferrer"' in response.text
