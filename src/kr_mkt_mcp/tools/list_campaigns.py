# src/kr_mkt_mcp/tools/list_campaigns.py
"""account 단위 캠페인 목록 (메타데이터만, 메트릭 X)."""
from __future__ import annotations

import json

from kr_mkt_mcp.meta_client import MetaClient
from kr_mkt_mcp.normalize import parse_metric_value
from kr_mkt_mcp.validation import validate_id

_FIELDS = "id,name,status,effective_status,objective,daily_budget,lifetime_budget,start_time,stop_time"


async def list_campaigns(
    client: MetaClient,
    *,
    account_id: str,
    status: str | None = "ACTIVE",
) -> tuple[list[dict], dict]:
    """Meta Ads의 캠페인 메타데이터 조회.

    Args:
        account_id: act_xxx 형식 또는 숫자 ID. act_ prefix 없으면 자동 추가.
        status: effective_status 필터 (디폴트 ACTIVE — "최근 운영 캠페인" 의미). None이면 전체.
    """
    validate_id(account_id, "account_id")
    acc = account_id if account_id.startswith("act_") else f"act_{account_id}"
    params: dict[str, object] = {"fields": _FIELDS}
    if status:
        params["effective_status"] = json.dumps([status])
    rows, meta = await client.get_paginated(f"/{acc}/campaigns", params=params)
    normalized = [
        {
            "id": r.get("id"),
            "name": r.get("name"),
            "status": r.get("status"),
            "effective_status": r.get("effective_status"),
            "objective": r.get("objective"),
            "daily_budget": parse_metric_value(r.get("daily_budget")),
            "lifetime_budget": parse_metric_value(r.get("lifetime_budget")),
            "start_time": r.get("start_time"),
            "stop_time": r.get("stop_time"),
        }
        for r in rows
    ]
    return normalized, meta
