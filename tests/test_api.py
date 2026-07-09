from fastapi.testclient import TestClient

from devtoolbox.main import app
from devtoolbox.services.markdown_service import render_markdown_text

client = TestClient(app)


def test_pages_are_served() -> None:
    for path, marker in [
        ("/", "DevToolbox"),
        ("/tools/json", "JSON 自动修复与格式化"),
        ("/tools/text-diff", "文本对比"),
        ("/tools/markdown", "Markdown 渲染"),
        ("/tools/timestamp", "时间戳转换"),
    ]:
        response = client.get(path)

        assert response.status_code == 200
        assert marker in response.text


def test_home_page_does_not_show_service_overview_card() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "工具状态概览" not in response.text
    assert "本地服务" not in response.text
    assert "FastAPI + 原生前端" not in response.text


def test_json_api_repair_and_format() -> None:
    repair_response = client.post("/api/json/repair", json={"text": "{'a': 1, 'b': [2,]}"})
    format_response = client.post("/api/json/format", json={"text": '{"a":1}'})

    assert repair_response.status_code == 200
    assert repair_response.json()["valid"] is True
    assert format_response.status_code == 200
    assert format_response.json()["formatted"] == '{\n  "a": 1\n}'


def test_text_diff_api_plain_text() -> None:
    response = client.post(
        "/api/text-diff/compare",
        json={"left_text": "a\nb", "right_text": "a\nc\nd", "markdown_render": False},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["mode"] == "text"
    assert payload["stats"]["same"] == 1
    assert payload["stats"]["modified"] == 1
    assert payload["stats"]["added"] == 1


def test_text_diff_api_markdown_render() -> None:
    response = client.post(
        "/api/text-diff/compare",
        json={
            "left_text": "# A\n\n<script>alert(1)</script>\n\nold",
            "right_text": "# A\n\nnew",
            "markdown_render": True,
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["mode"] == "markdown-render"
    assert "<script>" not in payload["left_rendered_html"]
    assert payload["stats"]["same"] == 1


def test_text_diff_api_markdown_render_uses_bullet_marker() -> None:
    response = client.post(
        "/api/text-diff/compare",
        json={"left_text": "- old", "right_text": "- new", "markdown_render": True},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["rows"][0]["left"] == "· old"
    assert payload["rows"][0]["right"] == "· new"


def test_text_diff_api_markdown_render_matches_markdown_tool_html() -> None:
    markdown_text = """# 标题

<p>正文</p>

- 无序项

| 字段 | 值 |
| --- | --- |
| A | B |
"""
    response = client.post(
        "/api/text-diff/compare",
        json={"left_text": markdown_text, "right_text": markdown_text, "markdown_render": True},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["left_rendered_html"] == render_markdown_text(markdown_text)
    assert payload["right_rendered_html"] == render_markdown_text(markdown_text)
    assert any(row["left"] == "字段 | 值" for row in payload["rows"])


def test_markdown_page_contains_editor_and_preview() -> None:
    response = client.get("/tools/markdown")

    assert response.status_code == 200
    assert 'id="markdownInput"' in response.text
    assert 'id="markdownPreview"' in response.text
    assert 'id="decodeEscapesButton"' in response.text


def test_markdown_render_api() -> None:
    response = client.post(
        "/api/markdown/render",
        json={"text": "# 标题\n\n<p>正文</p>", "decode_escapes": False},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["decoded"] is False
    assert payload["source"] == "# 标题\n\n<p>正文</p>"
    assert "<h1>标题</h1>" in payload["html"]
    assert "<p>正文</p>" in payload["html"]


def test_markdown_render_api_decodes_escapes() -> None:
    response = client.post(
        "/api/markdown/render",
        json={"text": r"# 标题\n\n<p>正文</p>", "decode_escapes": True},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["decoded"] is True
    assert payload["source"] == "# 标题\n\n<p>正文</p>"
    assert "<h1>标题</h1>" in payload["html"]


def test_timestamp_page_contains_expected_controls() -> None:
    response = client.get("/tools/timestamp")

    assert response.status_code == 200
    for marker in [
        'class="timestamp-workbench"',
        'class="workspace-card timestamp-card timestamp-now-card"',
        'class="workspace-card timestamp-card timestamp-converter-card"',
        "当前时间",
        "日期时间 -&gt; 时间戳",
        "时间戳 -&gt; 日期时间",
        'id="currentTimestamp"',
        'id="toggleUnitButton"',
        'id="copyCurrentButton"',
        'id="pauseNowButton"',
        'id="timestampToDateButton"',
        'id="dateToTimestampButton"',
    ]:
        assert marker in response.text


def test_timestamp_page_hides_batch_conversion_controls() -> None:
    response = client.get("/tools/timestamp")

    assert response.status_code == 200
    for marker in [
        'id="batchTab"',
        'id="batchPanel"',
        'id="batchConvertButton"',
        'id="batchInput"',
        "批量转换",
    ]:
        assert marker not in response.text


def test_home_page_links_to_timestamp_tool() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "/tools/timestamp" in response.text
    assert "时间戳转换" in response.text


def test_timestamp_now_api() -> None:
    response = client.get("/api/timestamp/now", params={"timezone": "Asia/Shanghai", "unit": "milliseconds"})

    payload = response.json()
    assert response.status_code == 200
    assert payload["valid"] is True
    assert payload["unit"] == "milliseconds"
    assert payload["timezone"] == "Asia/Shanghai"
    assert payload["timestamp"].isdigit()
    assert len(payload["timestamp"]) >= 13


def test_timestamp_conversion_apis() -> None:
    to_datetime = client.post(
        "/api/timestamp/to-datetime",
        json={"timestamp": "1782180714232", "timezone": "Asia/Shanghai", "unit": "milliseconds"},
    )
    from_datetime = client.post(
        "/api/timestamp/from-datetime",
        json={"datetime_text": "2026-06-23 10:11:54", "timezone": "Asia/Shanghai", "unit": "seconds"},
    )

    assert to_datetime.status_code == 200
    assert to_datetime.json()["result"] == "2026-06-23 10:11:54.232"
    assert from_datetime.status_code == 200
    assert from_datetime.json()["result"] == "1782180714"


def test_timestamp_batch_api_allows_partial_failures() -> None:
    response = client.post(
        "/api/timestamp/batch",
        json={
            "text": "1782180714232\ninvalid\n1782180715000",
            "mode": "to-datetime",
            "timezone": "Asia/Shanghai",
            "unit": "milliseconds",
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["valid"] is False
    assert payload["rows"][0]["result"] == "2026-06-23 10:11:54.232"
    assert payload["rows"][1]["valid"] is False
    assert payload["rows"][2]["result"] == "2026-06-23 10:11:55"


def test_timestamp_api_returns_readable_errors() -> None:
    response = client.post(
        "/api/timestamp/from-datetime",
        json={"datetime_text": "", "timezone": "Asia/Shanghai", "unit": "seconds"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["valid"] is False
    assert "请输入日期时间" in payload["error"]
