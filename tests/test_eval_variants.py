"""Pruebas de la matriz de variantes."""

from __future__ import annotations

from dataclasses import replace

import pytest
from assistant.evaluation.variants import (
    MODEL_DIMENSIONS,
    VariantError,
    build_variants,
    select_variants,
    validate_variants,
)


def test_matriz_de_ocho_variantes() -> None:
    # Arrange / Act
    variants = build_variants()

    # Assert
    assert len(variants) == 8
    assert len({variant.id for variant in variants}) == 8
    assert validate_variants(list(variants)) == []


def test_dimensiones_y_pesos_coherentes() -> None:
    # Arrange / Act
    variants = build_variants()

    # Assert
    for variant in variants:
        assert variant.embedding_dim == MODEL_DIMENSIONS[variant.embedding_model]
        assert round(variant.cosine_weight + variant.lexical_weight, 6) == 1.0
        assert variant.overlap < variant.chunk_size


def test_colecciones_compartidas_por_modelo_y_fragmentacion() -> None:
    # Arrange
    by_id = {variant.id: variant for variant in build_variants()}

    # Act / Assert
    assert by_id["nomic-1000-hybrid"].collection == by_id["nomic-1000-vector"].collection
    assert by_id["bge-m3-500-hybrid"].collection == by_id["bge-m3-500-vector"].collection
    assert by_id["nomic-1000-hybrid"].collection != by_id["nomic-500-hybrid"].collection


def test_seleccion_all_y_por_id() -> None:
    # Arrange / Act / Assert
    assert len(select_variants("all")) == 8
    assert [variant.id for variant in select_variants("nomic-1000-hybrid")] == ["nomic-1000-hybrid"]
    with pytest.raises(VariantError, match="desconocida"):
        select_variants("no-existe")


def test_valida_dimension_incoherente() -> None:
    # Arrange
    variants = list(build_variants())
    variants[0] = replace(variants[0], embedding_dim=999)

    # Act
    errors = validate_variants(variants)

    # Assert
    assert any("dimensión" in error for error in errors)


def test_valida_pesos_que_no_suman() -> None:
    # Arrange
    variants = list(build_variants())
    variants[0] = replace(variants[0], cosine_weight=0.5, lexical_weight=0.2)

    # Act
    errors = validate_variants(variants)

    # Assert
    assert any("pesos" in error for error in errors)
