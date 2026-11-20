"""Ejecuta variantes de recuperación y evaluación end-to-end."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from time import perf_counter
from typing import Protocol

from qdrant_client import QdrantClient

from assistant.chunking import chunk_corpus
from assistant.config import Settings
from assistant.corpus import CorpusDocument
from assistant.embeddings import Embedder, EmbeddingError, OllamaEmbedder
from assistant.evaluation import metrics
from assistant.evaluation.dataset import EvaluationQuestion, EvaluationSet
from assistant.evaluation.fingerprint import corpus_fingerprint, index_jsonl_sha256
from assistant.evaluation.reports import QuestionRow, RunReport, VariantReport
from assistant.evaluation.variants import VariantConfig
from assistant.index import IndexError, QdrantIndex
from assistant.llm import LLM, build_llm
from assistant.rag import RagService
from assistant.retrieval import CorpusRetriever

Progress = Callable[[str], None]
EmbedderFactory = Callable[[str, int], Embedder]
LLMFactory = Callable[[], LLM]
BATCH_SIZE = 32
RETRIEVAL_TOP_K = 10


class Closable(Protocol):
    def close(self) -> None: ...


def _noop(_message: str) -> None:
    return None


def _client(settings: Settings) -> QdrantClient:
    if settings.qdrant_url:
        return QdrantClient(url=settings.qdrant_url)
    return QdrantClient(path=str(settings.eval_qdrant_path))


def _default_embedder_factory(settings: Settings) -> EmbedderFactory:
    def factory(model: str, dim: int) -> Embedder:
        return OllamaEmbedder(settings.ollama_base_url, model, dim=dim)

    return factory


def _close(resource: object) -> None:
    close = getattr(resource, "close", None)
    if callable(close):
        close()


def _build_collection(
    client: QdrantClient,
    variant: VariantConfig,
    documents: list[CorpusDocument],
    *,
    recreate: bool,
    embedder_factory: EmbedderFactory,
) -> int:
    """Asegura la colección de la variante y devuelve el número de fragmentos."""
    fragments = chunk_corpus(documents, chunk_size=variant.chunk_size, overlap=variant.overlap)
    index = QdrantIndex(client, variant.collection, variant.embedding_dim)
    index.ensure_collection(recreate=recreate)
    if index.count() == 0:
        embedder = embedder_factory(variant.embedding_model, variant.embedding_dim)
        try:
            vectors: list[list[float]] = []
            for start in range(0, len(fragments), BATCH_SIZE):
                batch = fragments[start : start + BATCH_SIZE]
                vectors.extend(embedder.embed([fragment.text for fragment in batch]))
        finally:
            _close(embedder)
        if len(vectors) != len(fragments):
            raise RuntimeError("El embedder no devolvió un vector por fragmento.")
        index.upsert(fragments, vectors)
    return index.count()


def _unique_slugs(slugs: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    unique: list[str] = []
    for slug in slugs:
        if slug not in seen:
            seen.add(slug)
            unique.append(slug)
    return tuple(unique)


def _rank_first_expected(retrieved: tuple[str, ...], expected: tuple[str, ...]) -> int | None:
    expected_set = set(expected)
    for position, slug in enumerate(retrieved, start=1):
        if slug in expected_set:
            return position
    return None


def _retrieval_rows(
    retriever: CorpusRetriever, questions: Sequence[EvaluationQuestion]
) -> tuple[QuestionRow, ...]:
    rows: list[QuestionRow] = []
    for question in questions:
        started = perf_counter()
        fragments = retriever.search(question.question, RETRIEVAL_TOP_K)
        latency_ms = max(0, int((perf_counter() - started) * 1000))
        retrieved = _unique_slugs([fragment.slug for fragment in fragments])
        rows.append(
            QuestionRow(
                id=question.id,
                question=question.question,
                expected_slugs=question.expected_slugs,
                expected_status=question.expected_status,
                retrieved_slugs=retrieved,
                rank_first_expected=_rank_first_expected(retrieved, question.expected_slugs),
                status=None,
                sources=(),
                source_slugs=(),
                citations_invalid=0,
                latency_ms=latency_ms,
            )
        )
    return tuple(sorted(rows, key=lambda row: row.id))


def _migration_recommendation(variants: Sequence[VariantReport]) -> str | None:
    by_model: dict[str, float] = {}
    for variant in variants:
        model = variant.config.embedding_model
        recall = float(variant.metrics.get("hit_at_5") or 0.0)
        by_model[model] = max(by_model.get(model, 0.0), recall)
    if "nomic-embed-text" not in by_model or "bge-m3" not in by_model:
        return None
    delta = by_model["bge-m3"] - by_model["nomic-embed-text"]
    if delta >= 0.05:
        return f"migrar a bge-m3 (mejora de {delta * 100:.1f} pp en acierto@5)"
    return f"mantener nomic-embed-text (mejora de bge-m3: {delta * 100:.1f} pp en acierto@5)"


def _base_report(
    settings: Settings,
    documents: list[CorpusDocument],
    mode: str,
    variants: tuple[VariantReport, ...],
    indexed: dict[str, int],
    winner: str | None,
    provider: str | None,
    *,
    omitted: tuple[dict[str, str], ...] = (),
) -> RunReport:
    index_path = settings.corpus_gold_dir / "index.jsonl"
    return RunReport(
        generated_at=datetime.now(UTC).isoformat(),
        mode=mode,
        corpus_fingerprint=corpus_fingerprint(documents),
        index_jsonl_sha256=index_jsonl_sha256(index_path),
        indexed_fragments=indexed,
        provider=provider,
        variants=variants,
        winner=winner,
        omitted=omitted,
        migration_recommendation=(
            _migration_recommendation(variants) if mode == "retrieval" else None
        ),
    )


def _questions(evaluation_set: EvaluationSet, limit: int | None) -> list[EvaluationQuestion]:
    questions = list(evaluation_set.questions)
    if limit is not None:
        questions = questions[: max(0, limit)]
    return questions


def run_retrieval(
    settings: Settings,
    documents: list[CorpusDocument],
    evaluation_set: EvaluationSet,
    variants: Sequence[VariantConfig],
    *,
    limit: int | None = None,
    recreate: bool = False,
    progress: Progress = _noop,
    embedder_factory: EmbedderFactory | None = None,
) -> RunReport:
    """Ejecuta la matriz de recuperación (sin LLM)."""
    questions = _questions(evaluation_set, limit)
    factory = embedder_factory or _default_embedder_factory(settings)
    client = _client(settings)
    grouped: dict[tuple[str, int, int, int], list[VariantConfig]] = {}
    for variant in variants:
        key = (
            variant.embedding_model,
            variant.embedding_dim,
            variant.chunk_size,
            variant.overlap,
        )
        grouped.setdefault(key, []).append(variant)
    indexed: dict[str, int] = {}
    variant_reports: list[VariantReport] = []
    omitted: list[dict[str, str]] = []
    try:
        for (model, dim, _chunk, _overlap), group in grouped.items():
            representative = group[0]
            progress(
                f"indexando {representative.collection} "
                f"({model}, {representative.chunk_size}/{representative.overlap})"
            )
            try:
                indexed[representative.collection] = _build_collection(
                    client,
                    representative,
                    documents,
                    recreate=recreate,
                    embedder_factory=factory,
                )
            except (EmbeddingError, IndexError, RuntimeError) as error:
                reason = str(error)
                progress(f"variante omitida: {reason}")
                omitted.extend({"id": variant.id, "reason": reason} for variant in group)
                continue
            embedder = factory(model, dim)
            try:
                for variant in group:
                    progress(f"evaluando {variant.id}")
                    retriever = CorpusRetriever(
                        embedder,
                        QdrantIndex(client, variant.collection, variant.embedding_dim),
                        cosine_weight=variant.cosine_weight,
                        lexical_weight=variant.lexical_weight,
                    )
                    rows = _retrieval_rows(retriever, questions)
                    variant_reports.append(
                        VariantReport(
                            config=variant,
                            metrics=metrics.compute_metrics(rows, "retrieval"),
                            rows=rows,
                        )
                    )
            finally:
                _close(embedder)
    finally:
        client.close()
    ordered = tuple(sorted(variant_reports, key=lambda item: item.config.id))
    winner = metrics.pick_winner([(item.config.id, item.metrics) for item in ordered])
    return _base_report(
        settings,
        documents,
        "retrieval",
        ordered,
        indexed,
        winner,
        provider=None,
        omitted=tuple(sorted(omitted, key=lambda item: item["id"])),
    )


def _documents_by_url(
    documents: Sequence[CorpusDocument],
) -> dict[str, CorpusDocument]:
    return {document.url: document for document in documents}


def _source_is_valid(source: object, documents_by_url: dict[str, CorpusDocument]) -> bool:
    url = getattr(source, "url", "")
    document = documents_by_url.get(url)
    return (
        document is not None
        and document.title == getattr(source, "title", "")
        and document.source_type == getattr(source, "source_type", "")
    )


def _e2e_rows(
    settings: Settings,
    documents: list[CorpusDocument],
    evaluation_set: EvaluationSet,
    variant: VariantConfig,
    index: QdrantIndex,
    embedder: Embedder,
    *,
    limit: int | None,
    llm_factory: LLMFactory,
) -> tuple[QuestionRow, ...]:
    questions = _questions(evaluation_set, limit)
    documents_by_url = _documents_by_url(documents)
    retriever = CorpusRetriever(
        embedder,
        index,
        cosine_weight=variant.cosine_weight,
        lexical_weight=variant.lexical_weight,
    )
    llm = llm_factory()
    rag = RagService(retriever, llm, top_k=settings.top_k, min_score=variant.min_score)
    rows: list[QuestionRow] = []
    try:
        for question in questions:
            try:
                fragments = retriever.search(question.question, RETRIEVAL_TOP_K)
                retrieved = _unique_slugs([fragment.slug for fragment in fragments])
                answer = rag.answer(question.question)
                sources = tuple(source.url for source in answer.sources)
                source_slugs = tuple(source.slug for source in answer.sources)
                invalid = sum(
                    1 for source in answer.sources if not _source_is_valid(source, documents_by_url)
                )
                row = QuestionRow(
                    id=question.id,
                    question=question.question,
                    expected_slugs=question.expected_slugs,
                    expected_status=question.expected_status,
                    retrieved_slugs=retrieved,
                    rank_first_expected=_rank_first_expected(retrieved, question.expected_slugs),
                    status=answer.status,
                    sources=sources,
                    source_slugs=source_slugs,
                    citations_invalid=invalid,
                    latency_ms=answer.latency_ms,
                )
            except Exception as error:
                row = QuestionRow(
                    id=question.id,
                    question=question.question,
                    expected_slugs=question.expected_slugs,
                    expected_status=question.expected_status,
                    retrieved_slugs=(),
                    rank_first_expected=None,
                    status="error",
                    sources=(),
                    source_slugs=(),
                    citations_invalid=0,
                    latency_ms=0,
                    error=str(error),
                )
            rows.append(row)
    finally:
        _close(llm)
    return tuple(sorted(rows, key=lambda row: row.id))


def run_end_to_end(
    settings: Settings,
    documents: list[CorpusDocument],
    evaluation_set: EvaluationSet,
    variant: VariantConfig,
    *,
    limit: int | None = None,
    recreate: bool = False,
    progress: Progress = _noop,
    embedder_factory: EmbedderFactory | None = None,
    llm_factory: LLMFactory | None = None,
) -> RunReport:
    """Ejecuta una variante con generación y citas."""
    factory = embedder_factory or _default_embedder_factory(settings)
    client = _client(settings)
    try:
        progress(f"indexando {variant.collection}")
        count = _build_collection(
            client,
            variant,
            documents,
            recreate=recreate,
            embedder_factory=factory,
        )
        embedder = factory(variant.embedding_model, variant.embedding_dim)
        try:
            index = QdrantIndex(client, variant.collection, variant.embedding_dim)
            rows = _e2e_rows(
                settings,
                documents,
                evaluation_set,
                variant,
                index,
                embedder,
                limit=limit,
                llm_factory=llm_factory or (lambda: build_llm(settings)),
            )
        finally:
            _close(embedder)
    finally:
        client.close()
    variant_report = VariantReport(
        config=variant,
        metrics=metrics.compute_metrics(rows, "e2e"),
        rows=rows,
    )
    return _base_report(
        settings,
        documents,
        "e2e",
        (variant_report,),
        {variant.collection: count},
        winner=variant.id,
        provider=settings.llm_provider,
    )
