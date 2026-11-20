"""Matriz de variantes de recuperación de la fase 2."""

from __future__ import annotations

from dataclasses import dataclass

MODEL_DIMENSIONS: dict[str, int] = {
    "nomic-embed-text": 768,
    "bge-m3": 1024,
}
_MODEL_SHORT = {"nomic-embed-text": "nomic", "bge-m3": "bge_m3"}
_CHUNKINGS = ((1000, 200, "1000"), (500, 100, "500"))
_WEIGHTS = ((0.6, "hybrid"), (1.0, "vector"))
DEFAULT_MIN_SCORE = 0.2


class VariantError(RuntimeError):
    """Variante desconocida o matriz inconsistente."""


@dataclass(frozen=True)
class VariantConfig:
    """Configuración declarada de una variante."""

    id: str
    embedding_model: str
    embedding_dim: int
    chunk_size: int
    overlap: int
    cosine_weight: float
    lexical_weight: float
    collection: str
    min_score: float = DEFAULT_MIN_SCORE


def _collection(model: str, chunk_size: int) -> str:
    return f"eval_{_MODEL_SHORT[model]}_{chunk_size}"


def build_variants() -> tuple[VariantConfig, ...]:
    """Construye las 8 variantes: 2 modelos x 2 fragmentaciones x 2 mezclas."""
    variants: list[VariantConfig] = []
    for model, dim in MODEL_DIMENSIONS.items():
        for chunk_size, overlap, chunk_tag in _CHUNKINGS:
            for cosine_weight, weight_tag in _WEIGHTS:
                variant_id = f"{_MODEL_SHORT[model].replace('_', '-')}-{chunk_tag}-{weight_tag}"
                variants.append(
                    VariantConfig(
                        id=variant_id,
                        embedding_model=model,
                        embedding_dim=dim,
                        chunk_size=chunk_size,
                        overlap=overlap,
                        cosine_weight=cosine_weight,
                        lexical_weight=round(1.0 - cosine_weight, 1),
                        collection=_collection(model, chunk_size),
                    )
                )
    return tuple(variants)


def variant_ids() -> tuple[str, ...]:
    return tuple(variant.id for variant in build_variants())


def select_variants(spec: str | None = None) -> list[VariantConfig]:
    """Selecciona todas o una lista separada por comas de ids."""
    variants = build_variants()
    if spec is None or spec.strip().lower() == "all":
        return list(variants)
    wanted = [item.strip() for item in spec.split(",") if item.strip()]
    by_id = {variant.id: variant for variant in variants}
    unknown = [item for item in wanted if item not in by_id]
    if unknown:
        raise VariantError(
            f"Variante(s) desconocida(s): {', '.join(unknown)}. "
            f"Disponibles: {', '.join(variant_ids())}."
        )
    return [by_id[item] for item in wanted]


def validate_variants(variants: list[VariantConfig]) -> list[str]:
    """Errores de coherencia de la matriz (para pruebas y CLI)."""
    errors: list[str] = []
    seen: set[str] = set()
    collections: dict[str, tuple[str, int, int]] = {}
    for variant in variants:
        if variant.id in seen:
            errors.append(f"{variant.id}: id duplicado.")
        seen.add(variant.id)
        if variant.embedding_model not in MODEL_DIMENSIONS:
            errors.append(f"{variant.id}: modelo desconocido.")
        elif MODEL_DIMENSIONS[variant.embedding_model] != variant.embedding_dim:
            errors.append(f"{variant.id}: dimensión incoherente con el modelo.")
        if variant.overlap >= variant.chunk_size:
            errors.append(f"{variant.id}: overlap debe ser menor que chunk_size.")
        if round(variant.cosine_weight + variant.lexical_weight, 6) != 1.0:
            errors.append(f"{variant.id}: los pesos deben sumar 1.")
        key = variant.collection
        signature = (variant.embedding_model, variant.embedding_dim, variant.chunk_size)
        if key in collections and collections[key] != signature:
            errors.append(f"{variant.id}: colección compartida con configuración distinta.")
        collections[key] = signature
    return errors
