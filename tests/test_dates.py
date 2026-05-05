# tests/test_dates.py
from datetime import date

import pytest

from kr_mkt_mcp.dates import resolve_date_range


@pytest.fixture
def today():
    return date(2026, 5, 5)


def test_explicit_since_until_overrides_preset(today):
    result = resolve_date_range(
        date_preset="last_7d",
        since="2026-04-01",
        until="2026-04-15",
        today=today,
    )
    assert result == {"since": "2026-04-01", "until": "2026-04-15"}


def test_yesterday(today):
    result = resolve_date_range(date_preset="yesterday", since=None, until=None, today=today)
    assert result == {"since": "2026-05-04", "until": "2026-05-04"}


def test_last_7d(today):
    result = resolve_date_range(date_preset="last_7d", since=None, until=None, today=today)
    # last_7d: 어제까지 7일
    assert result == {"since": "2026-04-28", "until": "2026-05-04"}


def test_last_30d(today):
    result = resolve_date_range(date_preset="last_30d", since=None, until=None, today=today)
    assert result == {"since": "2026-04-05", "until": "2026-05-04"}


def test_this_month(today):
    result = resolve_date_range(date_preset="this_month", since=None, until=None, today=today)
    assert result == {"since": "2026-05-01", "until": "2026-05-04"}


def test_unknown_preset_raises():
    with pytest.raises(ValueError, match="알 수 없는 date_preset"):
        resolve_date_range(date_preset="nonexistent", since=None, until=None)


def test_only_since_raises():
    with pytest.raises(ValueError, match="since/until은 함께 지정"):
        resolve_date_range(date_preset=None, since="2026-04-01", until=None)


def test_this_month_at_month_start_no_inversion():
    """today가 월 1일이면 since(=today)가 yesterday보다 미래라 inversion 발생.
    fallback으로 since=until=yesterday(전월 말일)."""
    result = resolve_date_range(
        date_preset="this_month",
        since=None,
        until=None,
        today=date(2026, 5, 1),
    )
    assert result == {"since": "2026-04-30", "until": "2026-04-30"}


def test_last_14d():
    result = resolve_date_range(
        date_preset="last_14d",
        since=None,
        until=None,
        today=date(2026, 5, 5),
    )
    assert result == {"since": "2026-04-21", "until": "2026-05-04"}
