"""Tokens visuales de la identidad Carvajal y utilidades de contraste."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DesignTokens:
    """Tokens del sistema visual documentado en docs/design/DESIGN.md."""

    primary: str = "#003A5D"
    primary_strong: str = "#00243C"
    secondary: str = "#00B5E5"
    tertiary: str = "#C89B6A"
    ink: str = "#072B46"
    background: str = "#F3F6F8"
    surface: str = "#FFFFFF"
    border: str = "#DCE5EA"
    success: str = "#1E7A57"
    warning: str = "#8A5415"
    radius_card: str = "24px"
    radius_button: str = "18px"
    radius_input: str = "16px"
    font_family: str = '"DM Sans", system-ui, sans-serif'


TOKENS = DesignTokens()

# (primer plano, fondo, ratio mínimo) de los pares realmente usados en la UI.
CONTRAST_PAIRS: tuple[tuple[str, str, float], ...] = (
    (TOKENS.ink, TOKENS.surface, 7.0),
    (TOKENS.ink, TOKENS.background, 7.0),
    (TOKENS.primary, TOKENS.surface, 4.5),
    (TOKENS.surface, TOKENS.primary, 4.5),
    (TOKENS.warning, TOKENS.surface, 4.5),
    (TOKENS.success, TOKENS.surface, 4.5),
    (TOKENS.border, TOKENS.surface, 1.0),
)


def _channel(value: int) -> float:
    normalized = value / 255.0
    if normalized <= 0.03928:
        return normalized / 12.92
    return ((normalized + 0.055) / 1.055) ** 2.4


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    raw = color.lstrip("#")
    if len(raw) != 6:
        raise ValueError(f"Color inválido: {color!r}")
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def relative_luminance(color: str) -> float:
    red, green, blue = hex_to_rgb(color)
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def contrast_ratio(foreground: str, background: str) -> float:
    """Ratio WCAG entre dos colores hex."""
    first = relative_luminance(foreground)
    second = relative_luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)
