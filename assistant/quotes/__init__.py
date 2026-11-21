"""Solicitudes de cotización locales (sin PII)."""

from assistant.quotes.models import QuoteError, QuoteRecord, QuoteRequest
from assistant.quotes.service import create_quote

__all__ = ["QuoteError", "QuoteRecord", "QuoteRequest", "create_quote"]
