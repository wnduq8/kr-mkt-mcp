# src/kr_mkt_mcp/dates.py
"""date_preset → since/until 변환.

Meta API time_range 파라미터 형식: {"since": "YYYY-MM-DD", "until": "YYYY-MM-DD"}.
preset은 사용자 자연어("지난 7일") → AI가 뽑아내는 슬러그.
since/until이 둘 다 지정되면 preset은 무시.
"""
from __future__ import annotations

from datetime import date, timedelta

from kr_mkt_mcp.config import DATE_PRESET_DEFAULT


def _today() -> date:
    return date.today()


def resolve_date_range(
    *,
    date_preset: str | None,
    since: str | None,
    until: str | None,
    today: date | None = None,
) -> dict[str, str]:
    """preset 또는 since/until로 {since, until} 형태 반환.

    - since와 until이 둘 다 있으면 preset 무시
    - 한쪽만 지정되면 ValueError
    - preset은 yesterday / last_7d / last_14d / last_30d / this_month
    """
    if since and until:
        return {"since": since, "until": until}
    if (since and not until) or (until and not since):
        raise ValueError("since/until은 함께 지정해야 합니다.")

    today = today or _today()
    yesterday = today - timedelta(days=1)

    if date_preset is None:
        date_preset = DATE_PRESET_DEFAULT

    until_iso = yesterday.isoformat()
    if date_preset == "yesterday":
        return {"since": until_iso, "until": until_iso}
    if date_preset == "last_7d":
        return {"since": (yesterday - timedelta(days=6)).isoformat(), "until": until_iso}
    if date_preset == "last_14d":
        return {"since": (yesterday - timedelta(days=13)).isoformat(), "until": until_iso}
    if date_preset == "last_30d":
        return {"since": (yesterday - timedelta(days=29)).isoformat(), "until": until_iso}
    if date_preset == "this_month":
        # 오늘이 1일이면 since(=today)가 yesterday보다 미래 → since/until inversion 방지.
        # 월초엔 since=until=yesterday(전월 말일)로 fallback.
        since_dt = today.replace(day=1)
        if since_dt > yesterday:
            since_dt = yesterday
        return {"since": since_dt.isoformat(), "until": until_iso}

    raise ValueError(f"알 수 없는 date_preset: {date_preset}")
