"""Asistente Carvajal — pruebas del punto de entrada."""

from __future__ import annotations

import main


def test_main_es_invocable() -> None:
    # Arrange / Act / Assert
    assert callable(main.main)


def test_main_sin_argumentos_devuelve_cero() -> None:
    # Arrange
    argv: list[str] = []

    # Act
    exit_code = main.main(argv)

    # Assert
    assert exit_code == 0
