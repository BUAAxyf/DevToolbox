from devtoolbox.services.json_service import format_text, repair_text


def test_repair_python_literal_text_and_trailing_comma() -> None:
    result = repair_text("{'name': '成长乐', 'items': [1, 2,],}")

    assert result.valid is True
    assert '"name": "成长乐"' in result.formatted
    assert '"items"' in result.formatted


def test_format_valid_json_preserves_chinese() -> None:
    result = format_text('{"name":"成长乐","items":[1,2]}')

    assert result.valid is True
    assert result.formatted == '{\n  "name": "成长乐",\n  "items": [\n    1,\n    2\n  ]\n}'


def test_repair_empty_input_returns_error() -> None:
    result = repair_text("  ")

    assert result.valid is False
    assert result.error == "请输入需要修复的 JSON 内容"

