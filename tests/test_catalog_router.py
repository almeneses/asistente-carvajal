"""Pruebas del router determinista."""

from __future__ import annotations

from assistant.catalog.router import classify, normalize

CITIES = ("Bogotá", "Medellín")


def test_intencion_documental() -> None:
    # Arrange / Act
    query = classify("¿Qué es Carvajal y a qué sectores se dedica?", cities=CITIES)

    # Assert
    assert query.intent == "documental"


def test_intencion_comercial_caliente() -> None:
    # Arrange / Act
    query = classify("necesito vasos para café caliente de 12 oz", cities=CITIES)

    # Assert
    assert query.intent == "commercial"
    assert query.family == "vaso"
    assert query.capacity_oz == 12.0
    assert query.use == "bebida_caliente"
    assert query.temperature == "caliente"


def test_extrae_cantidad_y_ciudad() -> None:
    # Arrange / Act
    query = classify("necesito 5.000 vasos de 9 oz para jugos en Bogotá", cities=CITIES)

    # Assert
    assert query.intent == "commercial"
    assert query.quantity == 5000
    assert query.city == "Bogotá"
    assert query.country == "CO"
    assert query.use == "bebida_fria"


def test_consulta_de_distribuidor() -> None:
    # Arrange / Act
    query = classify("¿quién distribuye en Medellín?", cities=CITIES)

    # Assert
    assert query.intent == "commercial"
    assert query.asks_distributor is True
    assert query.city == "Medellín"


def test_pregunta_ambigua() -> None:
    # Arrange / Act
    query = classify("   ", cities=CITIES)

    # Assert
    assert query.intent == "ambiguous"


def test_saludo_cae_en_documental() -> None:
    # Arrange / Act
    query = classify("Hola", cities=CITIES)

    # Assert
    assert query.intent == "documental"


def test_pregunta_mixta() -> None:
    # Arrange / Act
    query = classify("¿qué empaques sostenibles ofrece Carvajal y cuánto cuestan?", cities=CITIES)

    # Assert
    assert query.intent == "mixed"
    assert query.residual_documental is True


def test_normaliza_acentos() -> None:
    # Arrange / Act / Assert
    assert normalize("Café caliente en Bogotá") == "cafe caliente en bogota"
