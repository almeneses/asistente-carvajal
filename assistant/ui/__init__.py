"""Capa de presentación: tokens, Markdown seguro, SSE y feedback."""

from assistant.ui.markdown import render_safe
from assistant.ui.streaming import StreamEvent, encode_event
from assistant.ui.tokens import CONTRAST_PAIRS, contrast_ratio

__all__ = ["CONTRAST_PAIRS", "StreamEvent", "contrast_ratio", "encode_event", "render_safe"]
