"""Pruebas del feedback local."""

from __future__ import annotations

from pathlib import Path

import pytest
from assistant.ui.feedback import (
    FeedbackError,
    read_feedback,
    record_feedback,
    validate_feedback,
)


def test_registra_y_lee(tmp_path: Path) -> None:
    # Arrange
    path = tmp_path / "feedback.jsonl"

    # Act
    record_feedback(path, message_id="m-1", rating="up", comment="clara")
    entries = read_feedback(path)

    # Assert
    assert len(entries) == 1
    assert entries[0].rating == "up"
    assert entries[0].comment == "clara"
    assert "m-1" not in entries[0].created_at


def test_ultimo_valor_gana(tmp_path: Path) -> None:
    # Arrange
    path = tmp_path / "feedback.jsonl"
    record_feedback(path, message_id="m-1", rating="up")
    record_feedback(path, message_id="m-1", rating="down")

    # Act
    entries = read_feedback(path)

    # Assert
    assert len(entries) == 1
    assert entries[0].rating == "down"


def test_validaciones() -> None:
    # Arrange / Act / Assert
    with pytest.raises(FeedbackError, match="message_id"):
        validate_feedback("", "up", "")
    with pytest.raises(FeedbackError, match="rating"):
        validate_feedback("m-1", "meh", "")
    with pytest.raises(FeedbackError, match="500"):
        validate_feedback("m-1", "up", "x" * 501)


def test_no_guarda_datos_personales(tmp_path: Path) -> None:
    # Arrange
    path = tmp_path / "feedback.jsonl"

    # Act
    record_feedback(path, message_id="m-1", rating="up", comment="sin nombre")
    raw = path.read_text(encoding="utf-8").lower()

    # Assert
    for forbidden in ("email", "correo", "usuario", "ip", "user-agent"):
        assert forbidden not in raw
