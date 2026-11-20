"""Validación técnica de materiales y temperaturas."""

from __future__ import annotations

from assistant.catalog.models import MaterialRule, Reference

USE_TO_APPLICATION = {
    "bebida_caliente": "comida_caliente",
    "bebida_fria": "comida_fria",
    "comida_caliente": "comida_caliente",
    "comida_fria": "comida_fria",
    "sopas": "sopas",
}

HOT_MIN_C = 60.0


def check_compatibility(
    reference: Reference,
    rule: MaterialRule | None,
    *,
    use: str | None,
    temperature: str | None,
    needs_microwave: bool = False,
    needs_freezing: bool = False,
) -> tuple[bool, tuple[str, ...]]:
    """Devuelve (compatible, avisos) para una referencia y una consulta."""
    warnings: list[str] = []
    if rule is None:
        warnings.append("material sin regla; se usa el rango de la ficha")
        if needs_microwave or needs_freezing:
            return False, tuple(warnings)
        if (
            temperature == "caliente"
            and reference.temp_max_c is not None
            and reference.temp_max_c < HOT_MIN_C
        ):
            return False, tuple(warnings)
        return True, tuple(warnings)
    application = USE_TO_APPLICATION.get(use or "")
    if application is not None:
        value = rule.applications.get(application)
        if value == "no_apto":
            return False, ()
        if value is None:
            warnings.append(f"sin regla de material para {application}")
    if temperature == "caliente":
        if rule.hot_content is False and application == "comida_caliente":
            warnings.append("la guía no declara contenido caliente para el material")
        if reference.temp_max_c is not None and reference.temp_max_c < HOT_MIN_C:
            return False, ()
    if needs_microwave and not rule.microwave:
        return False, ()
    if needs_freezing and not rule.freezing:
        return False, ()
    return True, tuple(warnings)


def is_microwave_use(use: str | None) -> bool:
    return use in {"microondas", "microonda"}


def is_freezing_use(use: str | None) -> bool:
    return use in {"congelacion", "congelación", "congelado"}
