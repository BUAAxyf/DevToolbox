from __future__ import annotations

import json
import re
from dataclasses import dataclass

from devtoolbox.services.markdown_renderer import render_markdown_html


@dataclass(frozen=True)
class MarkdownRenderResult:
    html: str
    source: str
    decoded: bool
    error: str | None = None


_UNICODE_ESCAPE_RE = re.compile(r"\\u([0-9a-fA-F]{4})")


def render_markdown_text(text: str) -> str:
    return render_markdown_html(text)


def decode_escape_sequences(text: str) -> str:
    if not text:
        return ""

    try:
        return json.loads(f'"{text}"')
    except json.JSONDecodeError:
        return _decode_common_escapes(text)


def render_markdown_payload(text: str, *, decode_escapes: bool = False) -> MarkdownRenderResult:
    source = decode_escape_sequences(text) if decode_escapes else text
    return MarkdownRenderResult(
        html=render_markdown_text(source),
        source=source,
        decoded=decode_escapes,
    )


def _decode_common_escapes(text: str) -> str:
    decoded = _UNICODE_ESCAPE_RE.sub(lambda match: chr(int(match.group(1), 16)), text)
    replacements = {
        r"\n": "\n",
        r"\r": "\r",
        r"\t": "\t",
        r"\b": "\b",
        r"\f": "\f",
        r"\"": '"',
        r"\/": "/",
    }
    for escaped, real_value in replacements.items():
        decoded = decoded.replace(escaped, real_value)
    return decoded.replace(r"\\", "\\")
