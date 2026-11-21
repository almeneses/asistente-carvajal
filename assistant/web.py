"""Aplicación web del asistente: chat HTMX y estado de salud."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from assistant.catalog.answers import build_catalog_answer, city_names
from assistant.catalog.loader import load_catalog
from assistant.catalog.models import CatalogSnapshot
from assistant.catalog.router import classify
from assistant.config import Settings, load_dotenv
from assistant.corpus import CorpusDocument, load_corpus
from assistant.embeddings import OllamaEmbedder
from assistant.index import QdrantIndex
from assistant.llm import build_llm
from assistant.rag import Rag, RagService, StreamOutcome
from assistant.retrieval import CorpusRetriever
from assistant.ui.feedback import FeedbackError, record_feedback
from assistant.ui.markdown import render_safe
from assistant.ui.streaming import StreamEvent, encode_event

logger = logging.getLogger("asistente")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.filters["markdown"] = render_safe

INDEX_HINT = (
    "El índice Qdrant está vacío o no existe. "
    "Ejecuta: uv run python scripts/index_corpus.py --recreate"
)


@dataclass
class AppContext:
    """Dependencias resueltas de la aplicación."""

    settings: Settings
    rag: Rag
    documents: list[CorpusDocument]
    index_ready: bool
    provider: str
    catalog: CatalogSnapshot | None = None


def build_context(settings: Settings) -> AppContext:
    """Carga corpus, índice, embedder y LLM; falla temprano si algo no está listo."""
    documents = load_corpus(settings.corpus_gold_dir)
    index = QdrantIndex.open(settings)
    if not index.is_ready():
        raise RuntimeError(INDEX_HINT)
    embedder = OllamaEmbedder(
        settings.ollama_base_url, settings.embedding_model, dim=settings.embedding_dim
    )
    embedder.check()
    retriever = CorpusRetriever(embedder, index)
    llm = build_llm(settings)
    rag = RagService(retriever, llm, top_k=settings.top_k)
    if settings.catalog_dir is None:
        raise RuntimeError(
            "Define CATALOG_DIR con el directorio del catálogo de empaques "
            "(referencias.csv, precios.csv, materiales.csv, distribuidores.csv)."
        )
    catalog = load_catalog(settings.catalog_dir)
    return AppContext(
        settings=settings,
        rag=rag,
        documents=documents,
        index_ready=True,
        provider=settings.llm_provider,
        catalog=catalog,
    )


def _today(context: AppContext) -> date:
    raw = context.settings.catalog_price_today
    return date.fromisoformat(raw) if raw else date.today()


def _catalog_html(catalog_answer: object) -> str:
    template = templates.get_template("_catalog_section.html")
    return template.render(
        section=getattr(catalog_answer, "section", None),
        warnings=getattr(catalog_answer, "warnings", ()),
    )


def _sources_html(sources: object) -> str:
    template = templates.get_template("_sources.html")
    return template.render(sources=sources)


def _answer_text_html(text: str) -> str:
    return render_safe(text)


def _stream_events(context: AppContext, question: str) -> Iterator[str]:
    """Generador SSE para una pregunta documental, comercial o mixta."""
    trace_id = uuid4().hex
    catalog = context.catalog
    cities = city_names(catalog) if catalog is not None else ()
    query = classify(question, cities=cities)
    yield encode_event(StreamEvent("start", {"request_id": trace_id, "intent": query.intent}))

    if catalog is not None and query.intent in {"commercial", "mixed", "ambiguous"}:
        try:
            catalog_answer = build_catalog_answer(query, snapshot=catalog, today=_today(context))
        except Exception:
            logger.exception("fallo_catalogo", extra={"request_id": trace_id})
            yield encode_event(
                StreamEvent(
                    "error",
                    {
                        "message": "No se pudo consultar el catálogo.",
                        "request_id": trace_id,
                        "retryable": True,
                    },
                )
            )
            return
        if not (
            query.intent == "mixed"
            and catalog_answer.section is not None
            and catalog_answer.section.kind == "no_match"
        ):
            yield encode_event(StreamEvent("catalog", {"html": _catalog_html(catalog_answer)}))
            yield encode_event(
                StreamEvent(
                    "done",
                    {
                        "message_id": uuid4().hex,
                        "status": "answered",
                        "provider": None,
                        "latency_ms": 0,
                        "final_html": "",
                    },
                )
            )
            return

    yield encode_event(StreamEvent("status", {"phase": "retrieving"}))
    outcome = StreamOutcome()
    stream = getattr(context.rag, "stream_tokens", None)
    try:
        if callable(stream):
            generating = False
            for token in stream(question, trace_id, outcome):
                if not generating:
                    yield encode_event(StreamEvent("status", {"phase": "generating"}))
                    generating = True
                yield encode_event(StreamEvent("token", {"text": token}))
            if not generating:
                yield encode_event(StreamEvent("status", {"phase": "generating"}))
        else:
            answer = context.rag.answer(question, request_id=trace_id)
            outcome.answer = answer
            yield encode_event(StreamEvent("status", {"phase": "generating"}))
            yield encode_event(StreamEvent("token", {"text": answer.text}))
    except Exception:
        logger.exception("fallo_stream", extra={"request_id": trace_id})
        yield encode_event(
            StreamEvent(
                "error",
                {
                    "message": (
                        "No se pudo responder en este momento. "
                        "Revisa el proveedor de lenguaje o inténtalo de nuevo."
                    ),
                    "request_id": trace_id,
                    "retryable": True,
                },
            )
        )
        return

    answer = outcome.answer
    if answer is None:
        return
    if answer.sources:
        yield encode_event(
            StreamEvent(
                "sources",
                {"count": len(answer.sources), "html": _sources_html(answer.sources)},
            )
        )
    yield encode_event(
        StreamEvent(
            "done",
            {
                "message_id": uuid4().hex,
                "status": answer.status,
                "provider": answer.provider,
                "latency_ms": answer.latency_ms,
                "final_html": _answer_text_html(answer.text),
            },
        )
    )


def create_app(
    *,
    settings: Settings | None = None,
    context: AppContext | None = None,
) -> FastAPI:
    """Crea la aplicación; en producción resuelve el contexto al construirse."""
    if context is None:
        if settings is None:
            load_dotenv()
            settings = Settings.from_env()
        context = build_context(settings)

    app = FastAPI(title="Asistente Carvajal", version="0.1.0")
    app.state.context = context
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    @app.get("/", response_class=HTMLResponse)
    def chat(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"provider": context.provider},
        )

    @app.post("/ask", response_class=HTMLResponse)
    def ask(request: Request, question: str = Form("")) -> HTMLResponse:
        trace_id = uuid4().hex
        if not question.strip() or len(question) > 2000:
            return templates.TemplateResponse(
                request=request,
                name="_exchange.html",
                context={
                    "error": "La pregunta debe tener entre 1 y 2000 caracteres.",
                    "request_id": trace_id,
                    "question": question,
                },
                status_code=422,
            )

        catalog = context.catalog
        cities = city_names(catalog) if catalog is not None else ()
        query = classify(question, cities=cities)
        if catalog is not None and query.intent in {"commercial", "mixed", "ambiguous"}:
            today = date.today()
            if context.settings.catalog_price_today:
                today = date.fromisoformat(context.settings.catalog_price_today)
            catalog_answer = build_catalog_answer(query, snapshot=catalog, today=today)
            if not (
                query.intent == "mixed"
                and catalog_answer.section is not None
                and catalog_answer.section.kind == "no_match"
            ):
                logger.info(
                    "respuesta_catalogo",
                    extra={
                        "request_id": trace_id,
                        "intent": query.intent,
                        "kind": catalog_answer.section.kind if catalog_answer.section else None,
                    },
                )
                return templates.TemplateResponse(
                    request=request,
                    name="_catalog_exchange.html",
                    context={"answer": catalog_answer, "question": question},
                )

        try:
            answer = context.rag.answer(question, request_id=trace_id)
        except ValueError as error:
            return templates.TemplateResponse(
                request=request,
                name="_exchange.html",
                context={"error": str(error), "request_id": trace_id, "question": question},
                status_code=422,
            )
        except Exception:
            logger.exception("Fallo al responder", extra={"request_id": trace_id})
            return templates.TemplateResponse(
                request=request,
                name="_exchange.html",
                context={
                    "error": (
                        "No se pudo responder en este momento. "
                        "Revisa el proveedor de lenguaje o inténtalo de nuevo."
                    ),
                    "request_id": trace_id,
                    "question": question,
                },
                status_code=503,
            )
        logger.info(
            "respuesta",
            extra={
                "request_id": trace_id,
                "status": answer.status,
                "provider": answer.provider,
                "latency_ms": answer.latency_ms,
                "sources": [source.slug for source in answer.sources],
            },
        )
        return templates.TemplateResponse(
            request=request,
            name="_exchange.html",
            context={"answer": answer, "question": question},
        )

    @app.post("/ask/stream")
    def ask_stream(question: str = Form("")) -> Response:
        if not question.strip() or len(question) > 2000:
            return JSONResponse(
                {"detail": "La pregunta debe tener entre 1 y 2000 caracteres."},
                status_code=422,
            )
        return StreamingResponse(
            _stream_events(context, question),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    @app.post("/feedback")
    def feedback(
        message_id: str = Form(""),
        rating: str = Form(""),
        comment: str = Form(""),
    ) -> JSONResponse:
        try:
            entry = record_feedback(
                context.settings.feedback_log_path,
                message_id=message_id,
                rating=rating,
                comment=comment,
            )
        except FeedbackError as error:
            return JSONResponse({"detail": str(error)}, status_code=422)
        return JSONResponse({"ok": True, "message_id": entry.message_id, "rating": entry.rating})

    @app.get("/healthz")
    def healthz() -> JSONResponse:
        payload = {
            "status": "ok" if context.index_ready else "degraded",
            "corpus_documents": len(context.documents),
            "collection": context.settings.qdrant_collection,
            "provider": context.provider,
        }
        if context.catalog is not None:
            payload["catalog"] = {
                "references": context.catalog.references_count,
                "prices": context.catalog.prices_count,
                "distributors": context.catalog.distributors_count,
                "fingerprint": context.catalog.fingerprint,
            }
        return JSONResponse(payload, status_code=200 if context.index_ready else 503)

    return app
