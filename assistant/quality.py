"""Gates de calidad sobre los reportes de evaluación."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

THRESHOLDS: dict[str, float] = {
    "hit_at_5": 0.90,
    "citation_precision": 0.95,
    "abstention_accuracy": 0.95,
    "expected_citation_coverage": 0.90,
    "route_accuracy": 0.95,
    "attributes_accuracy": 0.95,
    "quote_accuracy": 0.95,
}

_GANADORA = Path("specs/002-evaluacion-recuperacion/reports/ganadora.json")
_ACCEPTANCE = Path("specs/003-catalogo-empaques/reports/acceptance.json")


def _load(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"No se pudo leer {path}: {error}") from error


def _winner_metrics(report: dict[str, Any]) -> dict[str, Any]:
    winner = report.get("winner")
    for variant in report.get("variants", []):
        if variant.get("config", {}).get("id") == winner:
            return variant.get("metrics", {})
    raise ValueError(f"No se encontró la variante ganadora {winner!r}")


def evaluate(
    ganadora: dict[str, Any], acceptance: dict[str, Any], thresholds: dict[str, float] | None = None
) -> list[str]:
    """Devuelve la lista de fallos; vacía si todo cumple."""
    limits = thresholds or THRESHOLDS
    failures: list[str] = []
    try:
        metrics = _winner_metrics(ganadora)
    except ValueError as error:
        return [str(error)]
    for key in (
        "hit_at_5",
        "citation_precision",
        "abstention_accuracy",
        "expected_citation_coverage",
    ):
        value = metrics.get(key)
        minimum = limits[key]
        if value is None or float(value) < minimum:
            failures.append(f"{key}={value} < {minimum}")
    total = acceptance.get("total", 0)
    if total < 100:
        failures.append(f"acceptance.total={total} < 100")
    for key in ("route_accuracy", "attributes_accuracy", "quote_accuracy"):
        value = acceptance.get(key)
        minimum = limits[key]
        if value is None or float(value) < minimum:
            failures.append(f"acceptance.{key}={value} < {minimum}")
    if acceptance.get("forbidden_violations", 1) != 0:
        failures.append(f"forbidden_violations={acceptance.get('forbidden_violations')} != 0")
    return failures


def check_reports(root: Path = Path(".")) -> list[str]:
    """Carga los reportes del repositorio y evalúa los gates."""
    try:
        ganadora = _load(root / _GANADORA)
        acceptance = _load(root / _ACCEPTANCE)
    except ValueError as error:
        return [str(error)]
    return evaluate(ganadora, acceptance)


def main(root: Path = Path(".")) -> int:
    failures = check_reports(root)
    if failures:
        print("Gates de calidad: FALLÓ")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print("Gates de calidad: OK")
    return 0
