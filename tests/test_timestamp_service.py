from datetime import datetime
from zoneinfo import ZoneInfo

from devtoolbox.services.timestamp_service import (
    batch_convert,
    current_timestamp,
    datetime_to_timestamp,
    timestamp_to_datetime,
)


def test_datetime_to_seconds_and_milliseconds_timestamp() -> None:
    seconds = datetime_to_timestamp(
        datetime_text="2026-06-23 10:11:54",
        timezone="Asia/Shanghai",
        unit="seconds",
    )
    milliseconds = datetime_to_timestamp(
        datetime_text="2026-06-23 10:11:54",
        timezone="Asia/Shanghai",
        unit="milliseconds",
    )

    assert seconds.valid is True
    assert seconds.result == "1782180714"
    assert milliseconds.valid is True
    assert milliseconds.result == "1782180714000"


def test_timestamp_to_datetime_for_seconds_and_milliseconds() -> None:
    seconds = timestamp_to_datetime(timestamp="1782180714", timezone="Asia/Shanghai", unit="seconds")
    milliseconds = timestamp_to_datetime(timestamp="1782180714232", timezone="Asia/Shanghai", unit="milliseconds")

    assert seconds.valid is True
    assert seconds.result == "2026-06-23 10:11:54"
    assert milliseconds.valid is True
    assert milliseconds.result == "2026-06-23 10:11:54.232"


def test_timestamp_to_datetime_respects_timezone() -> None:
    result = timestamp_to_datetime(timestamp="1782180714", timezone="UTC", unit="seconds")

    assert result.valid is True
    assert result.result == "2026-06-23 02:11:54"


def test_millisecond_timestamp_can_be_near_unix_epoch() -> None:
    result = timestamp_to_datetime(timestamp="0", timezone="UTC", unit="milliseconds")

    assert result.valid is True
    assert result.result == "1970-01-01 00:00:00"


def test_current_timestamp_supports_seconds_and_milliseconds() -> None:
    fixed_now = datetime(2026, 6, 23, 10, 11, 54, 123000, tzinfo=ZoneInfo("Asia/Shanghai"))

    seconds = current_timestamp(timezone="Asia/Shanghai", unit="seconds", now=fixed_now)
    milliseconds = current_timestamp(timezone="Asia/Shanghai", unit="milliseconds", now=fixed_now)

    assert seconds.timestamp == "1782180714"
    assert seconds.datetime_text == "2026-06-23 10:11:54.123"
    assert milliseconds.timestamp == "1782180714123"
    assert milliseconds.datetime_text == "2026-06-23 10:11:54.123"


def test_batch_convert_allows_partial_failures() -> None:
    result = batch_convert(
        text="1782180714232\ninvalid\n\n1782180715000",
        mode="to-datetime",
        timezone="Asia/Shanghai",
        unit="milliseconds",
    )

    assert result.valid is False
    assert len(result.rows) == 3
    assert result.rows[0].result == "2026-06-23 10:11:54.232"
    assert result.rows[1].valid is False
    assert result.rows[2].line_no == 4
    assert result.rows[2].result == "2026-06-23 10:11:55"


def test_invalid_inputs_return_clear_errors() -> None:
    empty_datetime = datetime_to_timestamp(datetime_text="", timezone="Asia/Shanghai", unit="seconds")
    invalid_timestamp = timestamp_to_datetime(timestamp="abc", timezone="Asia/Shanghai", unit="seconds")
    invalid_timezone = timestamp_to_datetime(timestamp="1782180714", timezone="Mars/Base", unit="seconds")
    invalid_unit = datetime_to_timestamp(datetime_text="2026-06-23 10:11:54", timezone="Asia/Shanghai", unit="minute")

    assert empty_datetime.valid is False
    assert "请输入日期时间" in empty_datetime.error
    assert invalid_timestamp.valid is False
    assert "只能包含数字" in invalid_timestamp.error
    assert invalid_timezone.valid is False
    assert "不支持的时区" in invalid_timezone.error
    assert invalid_unit.valid is False
    assert "不支持的时间戳单位" in invalid_unit.error
