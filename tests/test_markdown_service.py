from devtoolbox.services.markdown_service import (
    decode_escape_sequences,
    render_markdown_payload,
    render_markdown_text,
)


def test_render_markdown_text_supports_headings_html_and_tables() -> None:
    html = render_markdown_text("# 标题\n\n<p>正文</p>\n\n| 字段 | 值 |\n| --- | --- |\n| A | B |")

    assert "<h1>标题</h1>" in html
    assert "<p>正文</p>" in html
    assert "<table>" in html
    assert "<td>A</td>" in html


def test_decode_escape_sequences_turns_literal_newlines_into_real_newlines() -> None:
    decoded = decode_escape_sequences(r"# 标题\n\n<p>正文</p>")

    assert decoded == "# 标题\n\n<p>正文</p>"


def test_decode_escape_sequences_preserves_markdown_escape() -> None:
    decoded = decode_escape_sequences(r"已交保费\\*给付比例")

    assert decoded == r"已交保费\*给付比例"


def test_render_markdown_text_sanitizes_script_and_dangerous_url() -> None:
    html = render_markdown_text('<script>alert(1)</script>\n\n[bad](javascript:alert(1))')

    assert "<script>" not in html
    assert "javascript:" not in html


def test_render_markdown_payload_decodes_before_rendering() -> None:
    result = render_markdown_payload(r"# 标题\n\n- 列表", decode_escapes=True)

    assert result.decoded is True
    assert result.source == "# 标题\n\n- 列表"
    assert "<h1>标题</h1>" in result.html
    assert "<li>列表</li>" in result.html

