from devtoolbox.services.markdown_service import render_markdown_text
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


def test_markdown_render_mode_uses_bullet_marker_for_list_items() -> None:
    html = render_markdown_safe("- old\n- new")

    assert html_visible_lines(html) == ["· old", "· new"]


def test_markdown_render_diff_rows_use_bullet_marker_for_list_items() -> None:
    result = compare_texts(left_text="- old", right_text="- new", markdown_render=True)

    assert result.rows[0].kind == "mod"
    assert result.rows[0].left == "· old"
    assert result.rows[0].right == "· new"


def test_markdown_render_safe_matches_markdown_tool_renderer() -> None:
    markdown_text = """# 标题

<p>HTML 段落</p>

> 引用文本

- 无序项

1. 有序项

| 字段 | 值 |
| --- | --- |
| A | B |

`code`

---

[链接](https://example.com)

![图片说明](https://example.com/a.png)
"""

    assert render_markdown_safe(markdown_text) == render_markdown_text(markdown_text)


def test_markdown_render_visible_lines_cover_common_markdown_syntax() -> None:
    markdown_text = """# 一级标题

## 二级标题

<p>HTML 段落</p>

> 引用文本

- 无序项

1. 有序项

| 字段 | 值 |
| --- | --- |
| A | B |

行内 `code`

```python
print("hi")
```

---

[链接](https://example.com)

![图片说明](https://example.com/a.png)

第一行<br>第二行
"""

    html = render_markdown_safe(markdown_text)

    assert html_visible_lines(html) == [
        "一级标题",
        "二级标题",
        "HTML 段落",
        "引用文本",
        "· 无序项",
        "1. 有序项",
        "字段 | 值",
        "A | B",
        "行内 code",
        'print("hi")',
        "---",
        "链接",
        "[图片: 图片说明]",
        "第一行",
        "第二行",
    ]


def test_markdown_render_diff_detects_non_text_markdown_elements() -> None:
    result = compare_texts(
        left_text="![旧图](https://example.com/old.png)\n\n---",
        right_text="![新图](https://example.com/new.png)",
        markdown_render=True,
    )

    assert result.rows[0].kind == "mod"
    assert result.rows[0].left == "[图片: 旧图]"
    assert result.rows[0].right == "[图片: 新图]"
    assert result.rows[1].kind == "del"
    assert result.rows[1].left == "---"


def test_render_markdown_safe_removes_unsafe_attributes() -> None:
    html = render_markdown_safe('[link](javascript:alert(1))')

    assert "javascript:" not in html
