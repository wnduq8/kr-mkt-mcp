# src/kr_mkt_mcp/dates.py
"""date_preset → since/until 변환.

Meta API time_range 파라미터 형식: {"since": "YYYY-MM-DD", "until": "YYYY-MM-DD"}.
preset은 사용자 자연어("지난 7일") → AI가 뽑아내는 슬러그.
since/until이 둘 다 지정되면 preset은 무시.
"""
from __future__ import annotations

from datetime import date, timedelta


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
        date_preset = "last_7d"  # config.DATE_PRESET_DEFAULT — 순환 import 회피해 인라인

    if date_preset == "yesterday":
        return {"since": yesterday.isoformat(), "until": yesterday.isoformat()}
    if date_preset == "last_7d":
        return {"since": (yesterday - timedelta(days=6)).isoformat(), "until": yesterday.isoformat()}
    if date_preset == "last_14d":
        return {"since": (yesterday - timedelta(days=13)).isoformat(), "until": yesterday.isoformat()}
    if date_preset == "last_30d":
        return {"since": (yesterday - timedelta(days=29)).isoformat(), "until": yesterday.isoformat()}
    if date_preset == "this_month":
        return {"since": today.replace(day=1).isoformat(), "until": yesterday.isoformat()}

    raise ValueError(f"알 수 없는 date_preset: {date_preset}")
