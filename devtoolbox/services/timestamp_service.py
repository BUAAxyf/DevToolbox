from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

SUPPORTED_TIMEZONES = (
    "Asia/Shanghai",
    "UTC",
    "America/New_York",
    "Europe/London",
    "Asia/Tokyo",
)
SUPPORTED_UNITS = ("seconds", "milliseconds")
SUPPORTED_BATCH_MODES = ("to-datetime", "from-datetime")


@dataclass(frozen=True)
class TimestampNowResult:
    timestamp: str
    unit: str
    datetime_text: str
    timezone: str
    valid: bool
    error: str | None = None


@dataclass(frozen=True)
class TimestampConvertResult:
    result: str
    unit: str
    timezone: str
    valid: bool
    error: str | None = None


@dataclass(frozen=True)
class TimestampBatchRow:
    line_no: int
    source: str
    result: str
    valid: bool
    error: str | None = None


@dataclass(frozen=True)
class TimestampBatchResult:
    mode: str
    unit: str
    timezone: str
    rows: list[TimestampBatchRow]
    valid: bool
    error: str | None = None


def current_timestamp(
    *,
    timezone: str = "Asia/Shanghai",
    unit: str = "seconds",
    now: datetime | None = None,
) -> TimestampNowResult:
    try:
        zone = _resolve_timezone(timezone)
        normalized_unit = _resolve_unit(unit)
    except ValueError as exc:
        return TimestampNowResult(timestamp="", unit=unit, datetime_text="", timezone=timezone, valid=False, error=str(exc))

    instant = now or datetime.now(UTC)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=UTC)
    local_dt = instant.astimezone(zone)
    return TimestampNowResult(
        timestamp=_timestamp_for_unit(local_dt, normalized_unit),
        unit=normalized_unit,
        datetime_text=format_datetime(local_dt),
        timezone=timezone,
        valid=True,
    )


def datetime_to_timestamp(
    *,
    datetime_text: str,
    timezone: str = "Asia/Shanghai",
    unit: str = "seconds",
) -> TimestampConvertResult:
    try:
        zone = _resolve_timezone(timezone)
        normalized_unit = _resolve_unit(unit)
        parsed = parse_datetime_text(datetime_text, zone)
        result = _timestamp_for_unit(parsed, normalized_unit)
        return TimestampConvertResult(result=result, unit=normalized_unit, timezone=timezone, valid=True)
    except ValueError as exc:
        return TimestampConvertResult(result="", unit=unit, timezone=timezone, valid=False, error=str(exc))


def timestamp_to_datetime(
    *,
    timestamp: str,
    timezone: str = "Asia/Shanghai",
    unit: str = "seconds",
) -> TimestampConvertResult:
    try:
        zone = _resolve_timezone(timezone)
        normalized_unit = _resolve_unit(unit)
        parsed = parse_timestamp_text(timestamp, normalized_unit)
        local_dt = parsed.astimezone(zone)
        return TimestampConvertResult(
            result=format_datetime(local_dt),
            unit=normalized_unit,
            timezone=timezone,
            valid=True,
        )
    except ValueError as exc:
        return TimestampConvertResult(result="", unit=unit, timezone=timezone, valid=False, error=str(exc))


def batch_convert(
    *,
    text: str,
    mode: str,
    timezone: str = "Asia/Shanghai",
    unit: str = "seconds",
) -> TimestampBatchResult:
    try:
        normalized_mode = _resolve_batch_mode(mode)
        _resolve_timezone(timezone)
        _resolve_unit(unit)
    except ValueError as exc:
        return TimestampBatchResult(mode=mode, unit=unit, timezone=timezone, rows=[], valid=False, error=str(exc))

    rows: list[TimestampBatchRow] = []
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        source = raw_line.strip()
        if not source:
            continue

        if normalized_mode == "to-datetime":
            converted = timestamp_to_datetime(timestamp=source, timezone=timezone, unit=unit)
        else:
            converted = datetime_to_timestamp(datetime_text=source, timezone=timezone, unit=unit)
        rows.append(
            TimestampBatchRow(
                line_no=line_no,
                source=source,
                result=converted.result,
                valid=converted.valid,
                error=converted.error,
            )
        )

    if not rows:
        return TimestampBatchResult(
            mode=normalized_mode,
            unit=unit,
            timezone=timezone,
            rows=[],
            valid=False,
            error="请输入需要批量转换的内容",
        )

    return TimestampBatchResult(
        mode=normalized_mode,
        unit=unit,
        timezone=timezone,
        rows=rows,
        valid=all(row.valid for row in rows),
    )


def parse_datetime_text(datetime_text: str, zone: ZoneInfo) -> datetime:
    source = datetime_text.strip()
    if not source:
        raise ValueError("请输入日期时间")

    formats = (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    )
    for fmt in formats:
        try:
            parsed = datetime.strptime(source, fmt)
            return parsed.replace(tzinfo=zone)
        except ValueError:
            continue
    raise ValueError("日期时间格式不正确，请使用 YYYY-MM-DD HH:mm:ss 或 YYYY-MM-DD HH:mm:ss.SSS")


def parse_timestamp_text(timestamp: str, unit: str) -> datetime:
    source = timestamp.strip()
    if not source:
        raise ValueError("请输入时间戳")
    if not source.isdigit():
        raise ValueError("时间戳只能包含数字")

    value = int(source)
    if unit == "seconds":
        seconds = value
    else:
        seconds = value / 1000

    try:
        return datetime.fromtimestamp(seconds, tz=UTC)
    except (OverflowError, OSError, ValueError) as exc:
        raise ValueError("时间戳超出可转换范围") from exc


def format_datetime(value: datetime) -> str:
    base = value.strftime("%Y-%m-%d %H:%M:%S")
    milliseconds = value.microsecond // 1000
    if milliseconds:
        return f"{base}.{milliseconds:03d}"
    return base


def _timestamp_for_unit(value: datetime, unit: str) -> str:
    seconds = value.timestamp()
    if unit == "seconds":
        return str(int(seconds))
    return str(int(seconds * 1000))


def _resolve_timezone(timezone: str) -> ZoneInfo:
    if timezone not in SUPPORTED_TIMEZONES:
        raise ValueError("不支持的时区")
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("当前系统缺少时区数据") from exc


def _resolve_unit(unit: str) -> str:
    if unit not in SUPPORTED_UNITS:
        raise ValueError("不支持的时间戳单位")
    return unit


def _resolve_batch_mode(mode: str) -> str:
    if mode not in SUPPORTED_BATCH_MODES:
        raise ValueError("不支持的批量转换模式")
    return mode
