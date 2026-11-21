"""Pruebas del render de Markdown seguro."""

from __future__ import annotations

from assistant.ui.markdown import render_safe


def test_renderiza_formato_basico() -> None:
    # Arrange
    text = "# Título\n\n- uno\n- dos\n\n**negrita**"

    # Act
    html = render_safe(text)

    # Assert
    assert "<h1>Título</h1>" in html
    assert "<li>uno</li>" in html
    assert "<strong>negrita</strong>" in html


def test_escapa_html_crudo() -> None:
    # Arrange
    text = "Hola <script>alert('xss')</script> <img src=x onerror=alert(1)>"

    # Act
    html = render_safe(text)

    # Assert
    assert "<script" not in html
    assert "<img" not in html
    assert "&lt;script&gt;" in html


def test_enlaces_externos_seguros() -> None:
    # Arrange
    text = "[Carvajal](https://www.carvajal.com/historia/)"

    # Act
    html = render_safe(text)

    # Assert
    assert 'target="_blank"' in html
    assert 'rel="noopener noreferrer"' in html


def test_enlace_javascript_no_se_renderiza_como_enlace() -> None:
    # Arrange
    text = "[malo](javascript:alert(1))"

    # Act
    html = render_safe(text)

    # Assert
    assert 'href="javascript' not in html
