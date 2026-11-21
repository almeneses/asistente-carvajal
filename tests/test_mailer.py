"""Pruebas del envío de cotizaciones por correo (SMTP simulado)."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import pytest
from assistant.config import Settings
from assistant.mailer import send_quote_email
from assistant.quotes.models import QuoteRequest
from assistant.quotes.service import create_quote
from tests.catalog_fixtures import sample_snapshot


class FakeSMTP:
    sent: ClassVar[list[object]] = []

    def __init__(self, host: str, port: int, timeout: int = 10) -> None:
        self.host = host
        self.port = port

    def __enter__(self) -> FakeSMTP:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def ehlo(self) -> None:
        return None

    def starttls(self) -> None:
        return None

    def login(self, user: str, password: str) -> None:
        return None

    def send_message(self, message: object) -> None:
        FakeSMTP.sent.append(message)


def test_envia_correo_si_smtp_configurado(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path / "catalog")
    record = create_quote(
        snapshot,
        tmp_path / "solicitudes.jsonl",
        QuoteRequest(
            sku="MX-VASO-12-PP",
            boxes=1,
            contact_email="ana@example.com",
            consent=True,
        ),
    )
    monkeypatch.setattr("assistant.mailer.smtplib.SMTP", FakeSMTP)
    settings = Settings(
        corpus_gold_dir=tmp_path,
        smtp_host="smtp.example.com",
        smtp_from="cotizaciones@example.com",
    )

    # Act
    status = send_quote_email(record, settings)

    # Assert
    assert status == "sent"
    assert len(FakeSMTP.sent) == 1


def test_sin_smtp_no_envia(tmp_path: Path) -> None:
    # Arrange
    snapshot = sample_snapshot(tmp_path / "catalog")
    record = create_quote(
        snapshot,
        tmp_path / "solicitudes.jsonl",
        QuoteRequest(
            sku="MX-VASO-12-PP",
            boxes=1,
            contact_email="ana@example.com",
            consent=True,
        ),
    )
    settings = Settings(corpus_gold_dir=tmp_path)

    # Act / Assert
    assert send_quote_email(record, settings) == "not_configured"
