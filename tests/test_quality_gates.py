"""Pruebas de los gates de calidad."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from assistant.quality import check_reports, evaluate

ROOT = Path(__file__).resolve().parents[1]


def test_gates_actuales_pasan() -> None:
    # Arrange / Act
    failures = check_reports(ROOT)

    # Assert
    assert failures == []


def test_gate_falla_si_baja_hit_at_5() -> None:
    # Arrange
    ganadora = json.loads(
        (ROOT / "specs/002-evaluacion-recuperacion/reports/ganadora.json").read_text(
            encoding="utf-8"
        )
    )
    acceptance = json.loads(
        (ROOT / "specs/003-catalogo-empaques/reports/acceptance.json").read_text(encoding="utf-8")
    )
    roto = copy.deepcopy(ganadora)
    for variant in roto["variants"]:
        if variant["config"]["id"] == roto["winner"]:
            variant["metrics"]["hit_at_5"] = 0.1

    # Act
    failures = evaluate(roto, acceptance)

    # Assert
    assert any("hit_at_5" in failure for failure in failures)


def test_gate_falla_con_violacion_prohibida() -> None:
    # Arrange
    ganadora = json.loads(
        (ROOT / "specs/002-evaluacion-recuperacion/reports/ganadora.json").read_text(
            encoding="utf-8"
        )
    )
    acceptance = json.loads(
        (ROOT / "specs/003-catalogo-empaques/reports/acceptance.json").read_text(encoding="utf-8")
    )
    roto = copy.deepcopy(acceptance)
    roto["forbidden_violations"] = 1

    # Act
    failures = evaluate(ganadora, roto)

    # Assert
    assert any("forbidden_violations" in failure for failure in failures)
