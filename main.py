"""Punto de entrada de la aplicación: arranca el servidor web."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

import uvicorn
from assistant.web import create_app

__version__ = "0.1.0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="asistente-carvajal",
        description="Asistente conversacional con citas del corpus de Carvajal.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Interfaz de escucha.")
    parser.add_argument("--port", type=int, default=8000, help="Puerto de escucha.")
    parser.add_argument("--version", action="store_true", help="Muestra la versión y sale.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Ejecuta la aplicación; devuelve 0 al salir ordenadamente."""
    args = build_parser().parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    app = create_app()
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
