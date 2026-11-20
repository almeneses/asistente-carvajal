"""Aplicación web del asistente: chat HTMX y estado de salud."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from assistant.config import Settings, load_dotenv
from assistant.corpus import CorpusDocument, load_corpus
from assistant.embeddings import OllamaEmbedder
from assistant.index import QdrantIndex
from assistant.llm import build_llm
from assistant.rag import Rag, RagService
from assistant.retrieval import CorpusRetriever

logger = logging.getLogger("asistente")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

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
    return AppContext(
        settings=settings,
        rag=rag,
        documents=documents,
        index_ready=True,
        provider=settings.llm_provider,
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

    @app.get("/healthz")
    def healthz() -> JSONResponse:
        payload = {
            "status": "ok" if context.index_ready else "degraded",
            "corpus_documents": len(context.documents),
            "collection": context.settings.qdrant_collection,
            "provider": context.provider,
        }
        return JSONResponse(payload, status_code=200 if context.index_ready else 503)

    return app
