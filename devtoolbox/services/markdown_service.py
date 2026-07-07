from __future__ import annotations

import json
import re
from dataclasses import dataclass

import bleach
import markdown


@dataclass(frozen=True)
class MarkdownRenderResult:
    html: str
    source: str
    decoded: bool
    error: str | None = None


_MARKDOWN_EXTENSIONS = ["extra", "sane_lists", "smarty"]
_ALLOWED_TAGS = [
    "a",
    "abbr",
    "blockquote",
    "br",
    "code",
    "dd",
    "del",
    "div",
    "dl",
    "dt",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "img",
    "ins",
    "li",
    "ol",
    "p",
    "pre",
    "span",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
]
_ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
    "abbr": ["title"],
    "code": ["class"],
    "img": ["alt", "src", "title"],
    "span": ["class"],
    "th": ["align"],
    "td": ["align"],
}
_ALLOWED_PROTOCOLS = ["http", "https", "mailto"]
_UNICODE_ESCAPE_RE = re.compile(r"\\u([0-9a-fA-F]{4})")


def render_markdown_text(text: str) -> str:
    raw_html = markdown.markdown(text or "", extensions=_MARKDOWN_EXTENSIONS, output_format="html5")
    return bleach.clean(
        raw_html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )


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

