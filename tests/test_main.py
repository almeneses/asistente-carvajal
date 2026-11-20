"""Pruebas del punto de entrada."""

from __future__ import annotations

import main


def test_main_es_invocable() -> None:
    # Arrange / Act / Assert
    assert callable(main.main)


def test_main_version_devuelve_cero() -> None:
    # Arrange
    argv: list[str] = ["--version"]

    # Act
    exit_code = main.main(argv)

    # Assert
    assert exit_code == 0
