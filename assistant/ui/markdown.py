"""Render de Markdown seguro para respuestas del asistente."""

from __future__ import annotations

from typing import Any

from markdown_it import MarkdownIt
from markdown_it.token import Token


def _link_open(_self: Any, tokens: list[Token], index: int, _options: Any, _env: Any) -> str:
    token = tokens[index]
    href = str(token.attrGet("href") or "")
    if href.lower().startswith(("javascript:", "vbscript:", "data:")):
        token.attrSet("href", "#")
    token.attrSet("target", "_blank")
    token.attrSet("rel", "noopener noreferrer")
    return _self.renderToken(tokens, index, _options, _env)


_MARKDOWN = MarkdownIt(
    "commonmark", {"html": False, "linkify": False, "typographer": False}
).enable(["table", "strikethrough"])
_MARKDOWN.add_render_rule("link_open", _link_open)


def render_safe(text: str) -> str:
    """Renderiza Markdown sin HTML crudo y con enlaces seguros."""
    return _MARKDOWN.render(text)
