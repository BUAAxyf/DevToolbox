from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser

from devtoolbox.services.markdown_service import render_markdown_text


@dataclass(frozen=True)
class DiffStats:
    added: int
    deleted: int
    modified: int
    same: int


@dataclass(frozen=True)
class DiffRow:
    kind: str
    left_no: int | None = None
    right_no: int | None = None
    left: str = ""
    right: str = ""


@dataclass(frozen=True)
class TextDiffResult:
    schema_version: str
    mode: str
    left_name: str
    right_name: str
    rows: list[DiffRow]
    stats: DiffStats
    left_rendered_html: str | None = None
    right_rendered_html: str | None = None


_BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "dd",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
}


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._lines: list[str] = []
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "br":
            self._flush_line()
            return
        if tag in _BLOCK_TAGS:
            self._flush_line()
        if tag == "li":
            self._parts.append("- ")

    def handle_endtag(self, tag: str) -> None:
        if tag in _BLOCK_TAGS:
            self._flush_line()

    def handle_data(self, data: str) -> None:
        pieces = data.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        for index, piece in enumerate(pieces):
            if index > 0:
                self._flush_line()
            if piece:
                self._parts.append(piece)

    def lines(self) -> list[str]:
        self._flush_line()
        return [line for line in self._lines if line]

    def _flush_line(self) -> None:
        if not self._parts:
            return
        line = _normalize_visible_text("".join(self._parts))
        if line:
            self._lines.append(line)
        self._parts = []


def compare_texts(
    *,
    left_text: str,
    right_text: str,
    left_name: str | None = None,
    right_name: str | None = None,
    markdown_render: bool = False,
) -> TextDiffResult:
    left_label = left_name or "左侧文本"
    right_label = right_name or "右侧文本"
    left_rendered_html = None
    right_rendered_html = None

    if markdown_render:
        left_rendered_html = render_markdown_safe(left_text)
        right_rendered_html = render_markdown_safe(right_text)
        left_lines = html_visible_lines(left_rendered_html)
        right_lines = html_visible_lines(right_rendered_html)
        mode = "markdown-render"
    else:
        left_lines = split_text_lines(left_text)
        right_lines = split_text_lines(right_text)
        mode = "text"

    rows = build_diff_rows(left_lines, right_lines)
    stats = summarize_rows(rows)
    return TextDiffResult(
        schema_version="1.0",
        mode=mode,
        left_name=left_label,
        right_name=right_label,
        rows=rows,
        stats=stats,
        left_rendered_html=left_rendered_html,
        right_rendered_html=right_rendered_html,
    )


def render_markdown_safe(text: str) -> str:
    return render_markdown_text(text)


def html_visible_lines(html_text: str) -> list[str]:
    parser = VisibleTextParser()
    parser.feed(html_text)
    parser.close()
    return parser.lines()


def split_text_lines(text: str) -> list[str]:
    if text == "":
        return []
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def build_diff_rows(left_lines: list[str], right_lines: list[str]) -> list[DiffRow]:
    ops = _diff_lines(left_lines, right_lines)
    rows: list[DiffRow] = []
    left_no = 1
    right_no = 1

    for index, op in enumerate(ops):
        if op["kind"] == "same":
            rows.append(
                DiffRow(kind="context", left_no=left_no, right_no=right_no, left=op["text"], right=op["text"])
            )
            left_no += 1
            right_no += 1
            continue

        deletes: list[str] = []
        adds: list[str] = []
        lookahead = index
        while lookahead < len(ops) and ops[lookahead]["kind"] != "same":
            if ops[lookahead]["kind"] == "del":
                deletes.append(ops[lookahead]["text"])
            if ops[lookahead]["kind"] == "add":
                adds.append(ops[lookahead]["text"])
            lookahead += 1

        if index > 0 and ops[index - 1]["kind"] != "same":
            continue

        paired_count = max(len(deletes), len(adds))
        for pair_index in range(paired_count):
            deleted = deletes[pair_index] if pair_index < len(deletes) else None
            added = adds[pair_index] if pair_index < len(adds) else None
            if deleted is not None and added is not None:
                rows.append(DiffRow(kind="mod", left_no=left_no, right_no=right_no, left=deleted, right=added))
                left_no += 1
                right_no += 1
            elif deleted is not None:
                rows.append(DiffRow(kind="del", left_no=left_no, left=deleted))
                left_no += 1
            elif added is not None:
                rows.append(DiffRow(kind="add", right_no=right_no, right=added))
                right_no += 1

    return rows


def summarize_rows(rows: list[DiffRow]) -> DiffStats:
    return DiffStats(
        added=sum(1 for row in rows if row.kind == "add"),
        deleted=sum(1 for row in rows if row.kind == "del"),
        modified=sum(1 for row in rows if row.kind == "mod"),
        same=sum(1 for row in rows if row.kind == "context"),
    )


def _diff_lines(left: list[str], right: list[str]) -> list[dict[str, str]]:
    left_count = len(left)
    right_count = len(right)
    dp = [[0] * (right_count + 1) for _ in range(left_count + 1)]
    for left_index in range(left_count - 1, -1, -1):
        for right_index in range(right_count - 1, -1, -1):
            if left[left_index] == right[right_index]:
                dp[left_index][right_index] = dp[left_index + 1][right_index + 1] + 1
            else:
                dp[left_index][right_index] = max(dp[left_index + 1][right_index], dp[left_index][right_index + 1])

    ops: list[dict[str, str]] = []
    left_index = 0
    right_index = 0
    while left_index < left_count and right_index < right_count:
        if left[left_index] == right[right_index]:
            ops.append({"kind": "same", "text": left[left_index]})
            left_index += 1
            right_index += 1
        elif dp[left_index + 1][right_index] >= dp[left_index][right_index + 1]:
            ops.append({"kind": "del", "text": left[left_index]})
            left_index += 1
        else:
            ops.append({"kind": "add", "text": right[right_index]})
            right_index += 1
    while left_index < left_count:
        ops.append({"kind": "del", "text": left[left_index]})
        left_index += 1
    while right_index < right_count:
        ops.append({"kind": "add", "text": right[right_index]})
        right_index += 1
    return ops


def _normalize_visible_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
