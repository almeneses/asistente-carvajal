"""Pruebas de tokens visuales y contraste WCAG."""

from __future__ import annotations

from assistant.ui.tokens import CONTRAST_PAIRS, TOKENS, contrast_ratio


def test_pares_de_contraste_cumplen_su_minimo() -> None:
    # Arrange / Act / Assert
    for foreground, background, minimum in CONTRAST_PAIRS:
        ratio = contrast_ratio(foreground, background)
        assert ratio >= minimum, f"{foreground} sobre {background}: {ratio:.2f} < {minimum}"


def test_texto_principal_alcanza_aaa() -> None:
    # Arrange / Act / Assert
    assert contrast_ratio(TOKENS.ink, TOKENS.surface) >= 7.0
    assert contrast_ratio(TOKENS.ink, TOKENS.background) >= 7.0


def test_primario_y_secundario_son_los_de_la_identidad() -> None:
    # Arrange / Act / Assert
    assert TOKENS.primary == "#003A5D"
    assert TOKENS.secondary == "#00B5E5"
    assert TOKENS.font_family.startswith('"DM Sans"')
