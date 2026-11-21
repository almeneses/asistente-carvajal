"""Aplicación web del asistente: chat HTMX y estado de salud."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Form, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from assistant.auth import (
    COOKIE_NAME,
    User,
    build_auth_middleware,
    create_session,
    verify_password,
)
from assistant.catalog.answers import build_catalog_answer, city_names
from assistant.catalog.loader import load_catalog
from assistant.catalog.models import CatalogSnapshot
from assistant.catalog.money import format_amount
from assistant.catalog.router import classify
from assistant.config import Settings, load_dotenv
from assistant.corpus import CorpusDocument, load_corpus
from assistant.embeddings import OllamaEmbedder
from assistant.index import QdrantIndex
from assistant.limits import LIMITS
from assistant.llm import build_llm
from assistant.mailer import send_quote_email
from assistant.observability import (
    METRICS,
    configure_logging,
    observability_middleware,
)
from assistant.quotes.models import QuoteError, QuoteRequest
from assistant.quotes.service import create_quote
from assistant.quotes.store import read_quotes
from assistant.rag import Rag, RagService, StreamOutcome
from assistant.retrieval import CorpusRetriever
from assistant.ui.feedback import FeedbackError, read_feedback, record_feedback
from assistant.ui.markdown import render_safe
from assistant.ui.streaming import StreamEvent, encode_event

logger = logging.getLogger("asistente")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.filters["markdown"] = render_safe
templates.env.filters["money"] = format_amount

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


def _rate_limit(request: Request, bucket: str, settings: Settings) -> JSONResponse | None:
    user = getattr(request.state, "user", None)
    username = getattr(user, "username", "anon")
    wait = LIMITS.rate_limited(username, bucket, settings.rate_limit_per_minute)
    if wait is None:
        return None
    METRICS.inc("rate_limited")
    return JSONResponse(
        {"detail": "Demasiadas solicitudes; espera un momento."},
        status_code=429,
        headers={"Retry-After": str(wait)},
    )


def _today(context: AppContext) -> date:
    raw = context.settings.catalog_price_today
    return date.fromisoformat(raw) if raw else date.today()


def _catalog_html(catalog_answer: object) -> str:
    template = templates.get_template("_catalog_stitch.html")
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
    METRICS.inc("sse_streams")
    logger.info("sse_start", extra={"request_id": trace_id, "route": "/ask/stream"})
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
    logger.info(
        "sse_done",
        extra={
            "request_id": trace_id,
            "status": answer.status,
            "provider": answer.provider,
        },
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

    app = FastAPI(title="Asistente Carvajal", version="0.2.0")
    configure_logging(context.settings.log_level, context.settings.log_format)
    app.middleware("http")(build_auth_middleware(context.settings))
    app.middleware("http")(observability_middleware)
    app.state.context = context
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    @app.get("/", response_class=HTMLResponse)
    def welcome(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="welcome.html",
            context={"provider": context.provider},
        )

    @app.get("/chat", response_class=HTMLResponse)
    def chat(request: Request, q: str = "") -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="chat.html",
            context={"provider": context.provider, "initial_question": q.strip()[:2000]},
        )

    @app.get("/chat/empaques")
    def chat_empaques() -> RedirectResponse:
        return RedirectResponse("/chat", status_code=307)

    @app.post("/ask", response_class=HTMLResponse)
    def ask(request: Request, question: str = Form("")) -> Response:
        limited = _rate_limit(request, "ask", context.settings)
        if limited is not None:
            return limited
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
    def ask_stream(request: Request, question: str = Form("")) -> Response:
        limited = _rate_limit(request, "ask_stream", context.settings)
        if limited is not None:
            return limited
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

    @app.post("/quotes")
    def quotes(
        request: Request,
        sku: str = Form(""),
        boxes: int = Form(0),
        city: str = Form(""),
        business: str = Form(""),
        contact_name: str = Form(""),
        contact_email: str = Form(""),
        contact_phone: str = Form(""),
        consent: bool = Form(False),
    ) -> JSONResponse:
        limited = _rate_limit(request, "quotes", context.settings)
        if limited is not None:
            return limited
        user = getattr(request.state, "user", None)
        username = getattr(user, "username", "anon")
        if LIMITS.quote_quota_exceeded(username, context.settings.quote_daily_limit):
            METRICS.inc("quota_exceeded")
            return JSONResponse(
                {"detail": "Cuota diaria de cotizaciones alcanzada."},
                status_code=429,
                headers={"Retry-After": "86400"},
            )
        if context.catalog is None:
            return JSONResponse({"detail": "Catálogo no disponible."}, status_code=503)
        try:
            record = create_quote(
                context.catalog,
                context.settings.quotes_log_path,
                QuoteRequest(
                    sku=sku,
                    boxes=boxes,
                    city=city,
                    business=business,
                    contact_name=contact_name,
                    contact_email=contact_email,
                    contact_phone=contact_phone,
                    consent=consent,
                ),
            )
        except QuoteError as error:
            return JSONResponse({"detail": str(error)}, status_code=422)
        LIMITS.register_quote(username)
        email_status = send_quote_email(record, context.settings)
        METRICS.inc("quotes_registered")
        logger.info("quote_registered", extra={"count": 1})
        return JSONResponse({"ok": True, "quote": record.__dict__, "email_status": email_status})

    @app.post("/feedback")
    def feedback(
        request: Request,
        message_id: str = Form(""),
        rating: str = Form(""),
        comment: str = Form(""),
    ) -> JSONResponse:
        limited = _rate_limit(request, "feedback", context.settings)
        if limited is not None:
            return limited
        try:
            entry = record_feedback(
                context.settings.feedback_log_path,
                message_id=message_id,
                rating=rating,
                comment=comment,
            )
        except FeedbackError as error:
            return JSONResponse({"detail": str(error)}, status_code=422)
        METRICS.inc("feedback_registered")
        logger.info("feedback_registered", extra={"count": 1})
        return JSONResponse({"ok": True, "message_id": entry.message_id, "rating": entry.rating})

    @app.get("/login", response_class=HTMLResponse)
    def login_page(request: Request, next: str = "/") -> Response:
        if not context.settings.auth_enabled:
            return RedirectResponse("/", status_code=303)
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"next": next, "error": None},
        )

    @app.post("/login", response_class=HTMLResponse)
    def login_submit(
        request: Request,
        username: str = Form(""),
        password: str = Form(""),
        next: str = Form("/"),
    ) -> Response:
        settings = context.settings
        if not settings.auth_enabled:
            return RedirectResponse("/", status_code=303)
        encoded = settings.auth_users.get(username)
        if not encoded or not verify_password(password, encoded):
            METRICS.inc("auth_failures")
            logger.info("login_failed", extra={"count": 1})
            return templates.TemplateResponse(
                request=request,
                name="login.html",
                context={"next": next, "error": "Usuario o contraseña incorrectos."},
                status_code=401,
            )
        role = "admin" if username in settings.auth_admins else "user"
        if settings.auth_secret is None:
            return JSONResponse({"detail": "Autenticación mal configurada."}, status_code=503)
        token = create_session(
            User(username, role), settings.auth_secret, settings.session_ttl_seconds
        )
        target = next if next.startswith("/") and not next.startswith("//") else "/"
        response = RedirectResponse(target, status_code=303)
        response.set_cookie(
            COOKIE_NAME,
            token,
            max_age=settings.session_ttl_seconds,
            httponly=True,
            samesite="lax",
            secure=settings.auth_cookie_secure,
            path="/",
        )
        METRICS.inc("auth_logins")
        logger.info("login_ok", extra={"count": 1})
        return response

    @app.get("/logout")
    def logout() -> Response:
        response = RedirectResponse("/login", status_code=303)
        response.delete_cookie(COOKIE_NAME, path="/")
        return response

    @app.get("/admin/summary")
    def admin_summary(request: Request) -> JSONResponse:
        user = getattr(request.state, "user", None)
        if user is None or user.role != "admin":
            return JSONResponse({"detail": "Solo administradores."}, status_code=403)
        feedback = read_feedback(context.settings.feedback_log_path)
        quotes = read_quotes(context.settings.quotes_log_path)
        ratings = {"up": 0, "down": 0}
        for entry in feedback:
            ratings[entry.rating] = ratings.get(entry.rating, 0) + 1
        return JSONResponse(
            {
                "feedback": {"total": len(feedback), **ratings},
                "quotes": {"total": len(quotes)},
            }
        )

    @app.get("/readyz")
    def readyz() -> JSONResponse:
        checks = {"index": context.index_ready, "catalog": context.catalog is not None}
        ok = all(checks.values())
        return JSONResponse(
            {"status": "ok" if ok else "degraded", "checks": checks, "provider": context.provider},
            status_code=200 if ok else 503,
        )

    @app.get("/metrics")
    def metrics() -> Response:
        gauges = {
            "asistente_index_ready": 1 if context.index_ready else 0,
            "asistente_catalog_loaded": 1 if context.catalog is not None else 0,
        }
        if context.catalog is not None:
            gauges["asistente_catalog_references"] = float(context.catalog.references_count)
        return Response(
            METRICS.render(gauges),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

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
