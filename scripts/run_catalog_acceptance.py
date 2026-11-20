# ruff: noqa: E402
"""Ejecuta la aceptación de la rama de catálogo."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from assistant.catalog.acceptance import (
    AcceptanceError,
    exit_code,
    load_routing_set,
    report_to_dict,
    run_acceptance,
    summary_markdown,
)
from assistant.catalog.loader import load_catalog
from assistant.catalog.models import CatalogError
from assistant.config import ConfigError, Settings, load_dotenv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aceptación del catálogo contra el set de enrutamiento."
    )
    parser.add_argument("--routing-file", type=Path, help="JSON con los ítems.")
    parser.add_argument("--json-out", type=Path, help="Reporte JSON.")
    parser.add_argument("--markdown-out", type=Path, help="Reporte Markdown.")
    parser.add_argument("--limit", type=int, help="Primeras N preguntas.")
    parser.add_argument("--today", help="Fecha ISO para simular vigencia.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        load_dotenv()
        settings = Settings.from_env()
        if settings.catalog_dir is None:
            print("Error: define CATALOG_DIR con el directorio del catálogo.", file=sys.stderr)
            return 2
        snapshot = load_catalog(settings.catalog_dir)
        routing_file = args.routing_file or settings.catalog_routing_file
        if routing_file is None:
            print(
                "Error: pasa --routing-file o define CATALOG_ROUTING_FILE.",
                file=sys.stderr,
            )
            return 2
        items = load_routing_set(routing_file)
        if args.limit is not None:
            items = items[: max(0, args.limit)]
        today = date.today()
        raw_today = args.today or settings.catalog_price_today
        if raw_today:
            today = date.fromisoformat(raw_today)
        report = run_acceptance(snapshot, items, today=today)
    except (AcceptanceError, CatalogError, ConfigError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print(summary_markdown(report))
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report_to_dict(report), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.markdown_out is not None:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(summary_markdown(report), encoding="utf-8")
    code = exit_code(report)
    if code != 0:
        print(
            f"Resultado: NO cumple (ruta {report.route_accuracy:.1%}, "
            f"violaciones {report.forbidden_violations}).",
            file=sys.stderr,
        )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
