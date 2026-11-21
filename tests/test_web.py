"""Pruebas de la interfaz web (HTMX) con una cadena RAG inyectada."""

from __future__ import annotations

from pathlib import Path

from assistant.config import Settings
from assistant.llm import LLMError
from assistant.prompting import NO_EVIDENCE_TEXT
from assistant.rag import Answer, Source
from assistant.web import AppContext, create_app
from fastapi.testclient import TestClient

SOURCE = Source(
    title="Compañía Carvajal",
    source_type="oficial",
    url="https://www.carvajal.com/compania",
    slug="compania",
)


class ScriptedRag:
    """Doble de la cadena RAG con respuestas prefijadas."""

    def __init__(self, answer: Answer | None = None, *, raises: bool = False) -> None:
        self.answer_obj = answer or Answer(
            status="answered",
            text="Carvajal opera en cuatro sectores [1].",
            sources=(SOURCE,),
            provider="fake",
            latency_ms=12,
            request_id="rid",
        )
        self.raises = raises

    def answer(self, question: str, request_id: str | None = None) -> Answer:
        if not question.strip() or len(question) > 2000:
            raise ValueError("La pregunta debe tener entre 1 y 2000 caracteres.")
        if self.raises:
            raise LLMError("proveedor caído")
        return self.answer_obj


def _client(tmp_path: Path, rag: ScriptedRag) -> TestClient:
    context = AppContext(
        settings=Settings(corpus_gold_dir=tmp_path),
        rag=rag,  # type: ignore[arg-type]
        documents=[],
        index_ready=True,
        provider="fake",
    )
    return TestClient(create_app(context=context))


def test_pagina_de_chat(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path, ScriptedRag())

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 200
    assert "Asistente Carvajal" in response.text
    assert 'action="/ask"' in response.text
    assert "chat.js" in response.text
    assert "Nueva conversación" in response.text


def test_respuesta_citada(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path, ScriptedRag())

    # Act
    response = client.post("/ask", data={"question": "¿Qué es Carvajal?"})

    # Assert
    assert response.status_code == 200
    assert 'data-status="answered"' in response.text
    assert "Compañía Carvajal" in response.text
    assert "https://www.carvajal.com/compania" in response.text
    assert "oficial" in response.text


def test_pregunta_vacia_devuelve_422(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path, ScriptedRag())

    # Act
    response = client.post("/ask", data={"question": ""})

    # Assert
    assert response.status_code == 422
    assert 'data-status="error"' in response.text


def test_abstencion_sin_fuentes(tmp_path: Path) -> None:
    # Arrange
    rag = ScriptedRag(
        Answer(
            status="no_evidence",
            text=NO_EVIDENCE_TEXT,
            sources=(),
            provider=None,
            latency_ms=3,
            request_id="rid",
        )
    )
    client = _client(tmp_path, rag)

    # Act
    response = client.post("/ask", data={"question": "¿Cuánto cuesta?"})

    # Assert
    assert response.status_code == 200
    assert 'data-status="no_evidence"' in response.text
    assert "No encontré evidencia" in response.text


def test_error_del_proveedor_devuelve_503(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path, ScriptedRag(raises=True))

    # Act
    response = client.post("/ask", data={"question": "¿Qué es Carvajal?"})

    # Assert
    assert response.status_code == 503
    assert 'data-status="error"' in response.text
    assert "Referencia:" in response.text


def test_healthz(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path, ScriptedRag())

    # Act
    response = client.get("/healthz")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["corpus_documents"] == 0
    assert payload["collection"] == "corpus_carvajal"
