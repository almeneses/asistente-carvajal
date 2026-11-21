"""Pruebas de las pantallas de Bienvenida y Conversación portadas de Stitch."""

from __future__ import annotations

from pathlib import Path

from assistant.config import Settings
from assistant.rag import Answer, Source
from assistant.web import AppContext, create_app
from fastapi.testclient import TestClient


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
    )
    return TestClient(create_app(context=context))


def test_bienvenida(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 200
    body = response.text
    assert "Hola, soy Carva." in body
    assert 'action="/chat"' in body
    assert "Historia Carvajal" in body
    assert "Necesito empaques" in body
    assert "Precios y cotización" in body
    assert 'href="/chat/empaques"' not in body
    assert "/static/stitch/tailwind.js" in body


def test_chat_conversacion(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act
    response = client.get("/chat")

    # Assert
    assert response.status_code == 200
    body = response.text
    assert "Conversación con Carva" in body
    assert 'class="chat-panel' in body
    assert 'action="/ask"' in body
    assert 'id="question"' in body
    assert "Habla o escribe" in body
    assert "Nueva conversación" in body
    assert "chat.js" in body


def test_modo_empaques_responde(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act
    response = client.get("/chat/empaques", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/chat"


def test_pantallas_sin_cdn(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act
    for route in ("/", "/chat"):
        body = client.get(route).text
        # Assert
        assert "cdn.tailwindcss.com" not in body
        assert "fonts.googleapis.com" not in body
        assert "lh3.googleusercontent.com" not in body
