from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from json_repair import repair_json


@dataclass(frozen=True)
class RepairResult:
    repaired: str
    formatted: str
    valid: bool
    error: str | None = None


def _to_json_text(value: Any, *, indent: int | None = None) -> str:
    return json.dumps(value, ensure_ascii=False, indent=indent)


def repair_text(raw_text: str) -> RepairResult:
    if not raw_text.strip():
        return RepairResult(repaired="", formatted="", valid=False, error="请输入需要修复的 JSON 内容")

    try:
        repaired_object = repair_json(raw_text, return_objects=True)
        compact_text = _to_json_text(repaired_object, indent=None)
        formatted_text = _to_json_text(repaired_object, indent=2)
        return RepairResult(repaired=compact_text, formatted=formatted_text, valid=True)
    except Exception as exc:
        return RepairResult(repaired="", formatted="", valid=False, error=str(exc))


def format_text(json_text: str) -> RepairResult:
    source = json_text.strip()
    if not source:
        return RepairResult(repaired="", formatted="", valid=False, error="请输入需要格式化的 JSON 内容")

    try:
        parsed_object = json.loads(source)
    except json.JSONDecodeError:
        return repair_text(source)

    compact_text = _to_json_text(parsed_object, indent=None)
    formatted_text = _to_json_text(parsed_object, indent=2)
    return RepairResult(repaired=compact_text, formatted=formatted_text, valid=True)

