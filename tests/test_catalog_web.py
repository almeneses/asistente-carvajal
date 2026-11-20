"""Pruebas de la web con la rama de catálogo."""

from __future__ import annotations

from pathlib import Path

from assistant.config import Settings
from assistant.rag import Answer, Source
from assistant.web import AppContext, create_app
from fastapi.testclient import TestClient
from tests.catalog_fixtures import sample_snapshot


class ScriptedRag:
    def __init__(self) -> None:
        self.calls = 0

    def answer(self, question: str, request_id: str | None = None) -> Answer:
        self.calls += 1
        return Answer(
            status="answered",
            text="Respuesta documental de prueba [1].",
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
            request_id=request_id or "rid",
        )


def _client(tmp_path: Path, rag: ScriptedRag | None = None) -> TestClient:
    context = AppContext(
        settings=Settings(corpus_gold_dir=tmp_path),
        rag=rag or ScriptedRag(),  # type: ignore[arg-type]
        documents=[],
        index_ready=True,
        provider="fake",
        catalog=sample_snapshot(tmp_path / "catalog"),
    )
    return TestClient(create_app(context=context))


def test_pregunta_comercial_usa_catalogo(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act
    response = client.post(
        "/ask", data={"question": "¿cuánto cuesta la caja de vasos PP de 12 oz?"}
    )

    # Assert
    assert response.status_code == 200
    assert 'data-intent="commercial"' in response.text
    assert 'data-section="catalog"' in response.text
    assert "MX-VASO-12-PP" in response.text


def test_pregunta_documental_sigue_usando_corpus(tmp_path: Path) -> None:
    # Arrange
    rag = ScriptedRag()
    client = _client(tmp_path, rag)

    # Act
    response = client.post(
        "/ask", data={"question": "¿Qué es Carvajal y a qué sectores se dedica?"}
    )

    # Assert
    assert response.status_code == 200
    assert 'data-status="answered"' in response.text
    assert rag.calls == 1


def test_pregunta_mixta_prioriza_catalogo(tmp_path: Path) -> None:
    # Arrange
    rag = ScriptedRag()
    client = _client(tmp_path, rag)

    # Act
    response = client.post(
        "/ask",
        data={"question": "¿qué empaques sostenibles ofrece Carvajal y cuánto cuestan?"},
    )

    # Assert
    assert response.status_code == 200
    assert 'data-intent="mixed"' in response.text
    assert rag.calls == 0


def test_healthz_incluye_catalogo(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act
    response = client.get("/healthz")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["catalog"]["references"] == 4
    assert payload["catalog"]["prices"] == 1
