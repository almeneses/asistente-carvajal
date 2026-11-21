"""Pruebas de autenticación multiusuario, límites y resumen admin."""

from __future__ import annotations

from pathlib import Path

from assistant.auth import hash_password, verify_password
from assistant.config import Settings
from assistant.rag import Answer, Source
from assistant.web import AppContext, create_app
from fastapi.testclient import TestClient
from tests.catalog_fixtures import sample_snapshot

SECRET = "x" * 40


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


def _client(
    tmp_path: Path, *, rate_limit_per_minute: int = 30, quote_daily_limit: int = 50
) -> TestClient:
    users = {"ana": hash_password("clave-segura-123"), "admin": hash_password("admin-segura-123")}
    settings = Settings(
        corpus_gold_dir=tmp_path,
        feedback_log_path=tmp_path / "feedback.jsonl",
        quotes_log_path=tmp_path / "solicitudes.jsonl",
        auth_enabled=True,
        auth_secret=SECRET,
        auth_users=users,
        auth_admins=("admin",),
        rate_limit_per_minute=rate_limit_per_minute,
        quote_daily_limit=quote_daily_limit,
    )
    context = AppContext(
        settings=settings,
        rag=FakeRag(),  # type: ignore[arg-type]
        documents=[],
        index_ready=True,
        provider="fake",
        catalog=sample_snapshot(tmp_path / "catalog"),
    )
    return TestClient(create_app(context=context))


def test_hash_y_verify() -> None:
    # Arrange
    encoded = hash_password("clave-segura-123")

    # Act / Assert
    assert verify_password("clave-segura-123", encoded)
    assert not verify_password("otra", encoded)


def test_login_y_proteccion(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act
    redirect = client.get("/", headers={"accept": "text/html"}, follow_redirects=False)
    api = client.get("/chat")
    login = client.post(
        "/login",
        data={"username": "ana", "password": "clave-segura-123"},
        follow_redirects=False,
    )

    # Assert
    assert redirect.status_code == 303
    assert redirect.headers["location"].startswith("/login")
    assert api.status_code == 401
    assert login.status_code == 303
    assert client.get("/").status_code == 200


def test_login_incorrecto(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)

    # Act
    response = client.post(
        "/login",
        data={"username": "ana", "password": "incorrecta"},
        follow_redirects=False,
    )

    # Assert
    assert response.status_code == 401
    assert "incorrectos" in response.text


def test_admin_summary_solo_admin(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path)
    client.post("/login", data={"username": "admin", "password": "admin-segura-123"})

    # Act
    response = client.get("/admin/summary")

    # Assert
    assert response.status_code == 200
    assert response.json()["feedback"]["total"] == 0
    assert response.json()["quotes"]["total"] == 0


def test_rate_limit(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path, rate_limit_per_minute=1, quote_daily_limit=50)
    client.post("/login", data={"username": "ana", "password": "clave-segura-123"})

    # Act
    first = client.post("/ask", data={"question": "hola"})
    second = client.post("/ask", data={"question": "hola"})

    # Assert
    assert first.status_code == 200
    assert second.status_code == 429
    assert "Retry-After" in second.headers


def test_cuota_diaria_cotizaciones(tmp_path: Path) -> None:
    # Arrange
    client = _client(tmp_path, rate_limit_per_minute=100, quote_daily_limit=1)
    client.post("/login", data={"username": "ana", "password": "clave-segura-123"})

    # Act
    first = client.post("/quotes", data={"sku": "MX-VASO-12-PP", "boxes": 1})
    second = client.post("/quotes", data={"sku": "MX-VASO-12-PP", "boxes": 1})

    # Assert
    assert first.status_code == 200
    assert second.status_code == 429


def test_auth_desactivada_compatible(tmp_path: Path) -> None:
    # Arrange
    settings = Settings(
        corpus_gold_dir=tmp_path,
        feedback_log_path=tmp_path / "feedback.jsonl",
        quotes_log_path=tmp_path / "solicitudes.jsonl",
    )
    client = TestClient(
        create_app(
            context=AppContext(
                settings=settings,
                rag=FakeRag(),  # type: ignore[arg-type]
                documents=[],
                index_ready=True,
                provider="fake",
                catalog=sample_snapshot(tmp_path / "catalog"),
            )
        )
    )

    # Act / Assert
    assert client.get("/").status_code == 200
    assert client.get("/chat").status_code == 200
