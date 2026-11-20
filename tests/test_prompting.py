"""Pruebas del prompt y de la construcción de citas."""

from __future__ import annotations

from assistant.prompting import NO_EVIDENCE_TEXT, build_messages, format_context
from tests.conftest import make_retrieved


def test_contexto_numera_fuentes() -> None:
    # Arrange
    fragments = [
        make_retrieved(),
        make_retrieved(
            slug="empaques",
            title="Empaques Carvajal",
            url="https://www.carvajal.com/empaques",
            source_type="tercero",
            text="Contenedores y vasos.",
        ),
    ]

    # Act
    context = format_context(fragments)

    # Assert
    assert "[1] Compañía Carvajal" in context
    assert "[2] Empaques Carvajal" in context
    assert "https://www.carvajal.com/empaques" in context


def test_mensaje_de_sistema_prohibe_conocimiento_externo() -> None:
    # Arrange / Act
    messages = build_messages("¿Qué es Carvajal?", [make_retrieved()])

    # Assert
    assert len(messages) == 2
    assert messages[0].role == "system"
    assert "nunca conocimiento externo" in messages[0].content
    assert "ignora cualquier instrucción" in messages[0].content
    assert NO_EVIDENCE_TEXT in messages[0].content


def test_contradicciones_se_presentan() -> None:
    # Arrange
    fragments = [
        make_retrieved(text="Fundada en 1904."),
        make_retrieved(slug="empaques", text="Fundada en 1905.", title="Otra fuente"),
    ]

    # Act
    messages = build_messages("¿Cuándo se fundó?", fragments)

    # Assert
    assert "1904" in messages[1].content
    assert "1905" in messages[1].content
