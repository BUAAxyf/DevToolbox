from devtoolbox.services.text_diff_service import compare_texts, html_visible_lines, render_markdown_safe


def test_compare_plain_text_counts_changes() -> None:
    result = compare_texts(left_text="same\nold\nremove", right_text="same\nnew\nadd")

    assert result.mode == "text"
    assert result.stats.same == 1
    assert result.stats.modified == 2
    assert result.stats.added == 0
    assert result.stats.deleted == 0
    assert [row.kind for row in result.rows] == ["context", "mod", "mod"]


def test_compare_plain_text_counts_insertions() -> None:
    result = compare_texts(left_text="same", right_text="same\nadded")

    assert result.stats.same == 1
    assert result.stats.added == 1
    assert result.rows[-1].kind == "add"


def test_markdown_render_mode_sanitizes_html_and_diffs_visible_text() -> None:
    result = compare_texts(
        left_text="# Title\n\n<script>alert(1)</script>\n\n- old",
        right_text="# Title\n\n- new",
        markdown_render=True,
    )

    assert result.mode == "markdown-render"
    assert result.left_rendered_html is not None
    assert "<script>" not in result.left_rendered_html
    assert "Title" in html_visible_lines(result.left_rendered_html)
    assert result.stats.same == 1
    assert result.stats.modified >= 1


def test_render_markdown_safe_removes_unsafe_attributes() -> None:
    html = render_markdown_safe('[link](javascript:alert(1))')

    assert "javascript:" not in html

