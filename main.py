"""Asistente Carvajal — punto de entrada de la aplicación."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser de argumentos de la aplicación."""
    return argparse.ArgumentParser(
        prog="asistente-carvajal",
        description=(
            "Asistente conversacional con RAG sobre el corpus web "
            "y la documentación de empaques de Carvajal."
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Ejecuta la aplicación. Devuelve el código de salida."""
    build_parser().parse_args(argv)
    print("Asistente Carvajal — el pipeline RAG aún no está conectado.")
    print("Estado y roadmap: CONSTITUTION.md §10.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
