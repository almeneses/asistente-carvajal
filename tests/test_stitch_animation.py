"""Pruebas de contrato de la animación portada de Stitch."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "assistant/static/stitch/stitch.js"
BASE = ROOT / "assistant/templates/base_stitch.html"


def test_script_incluye_funciones_de_transicion() -> None:
    # Arrange / Act
    text = SCRIPT.read_text(encoding="utf-8")

    # Assert
    for function in (
        "function minimizeToChat",
        "function expandFullCard",
        "function startCountdown",
        "function toggleFullCard",
        "window.minimizeToChat",
    ):
        assert function in text


def test_respeta_movimiento_reducido() -> None:
    # Arrange / Act
    text = SCRIPT.read_text(encoding="utf-8")

    # Assert
    assert "prefers-reduced-motion: reduce" in text
    assert "reducedMotion.matches" in text


def test_cuenta_atras_de_diez_segundos() -> None:
    # Arrange / Act
    text = SCRIPT.read_text(encoding="utf-8")

    # Assert
    assert "startCountdown(seconds = 10)" in text
    assert "Minimizando al chat en" in text


def test_base_usa_activos_locales() -> None:
    # Arrange / Act
    text = BASE.read_text(encoding="utf-8")

    # Assert
    assert "/static/stitch/tailwind.js" in text
    assert "/static/stitch/stitch.js" in text
    assert "https://cdn.tailwindcss.com" not in text
    assert "fonts.googleapis.com" not in text
