# src/kr_mkt_mcp/tools/list_ads.py
"""account 단위 광고(ad) 목록. campaign_id로 필터 가능. 메트릭 X."""
from __future__ import annotations

import json

from kr_mkt_mcp.meta_client import MetaClient
from kr_mkt_mcp.validation import validate_id


_FIELDS = "id,name,status,effective_status,campaign_id,adset_id,creative"


async def list_ads(
    client: MetaClient,
    *,
    account_id: str,
    campaign_id: str | None = None,
    status: str | None = "ACTIVE",
) -> tuple[list[dict], dict]:
    validate_id(account_id, "account_id")
    if campaign_id is not None:
        validate_id(campaign_id, "campaign_id")
    acc = account_id if account_id.startswith("act_") else f"act_{account_id}"
    params: dict[str, object] = {"fields": _FIELDS}
    if status:
        params["effective_status"] = json.dumps([status])
    if campaign_id:
        params["filtering"] = json.dumps(
            [{"field": "campaign.id", "operator": "IN", "value": [campaign_id]}]
        )
    rows, meta = await client.get_paginated(f"/{acc}/ads", params=params)
    normalized = [
        {
            "id": r.get("id"),
            "name": r.get("name"),
            "status": r.get("status"),
            "effective_status": r.get("effective_status"),
            "campaign_id": r.get("campaign_id"),
            "adset_id": r.get("adset_id"),
            "creative_id": (r.get("creative") or {}).get("id"),
        }
        for r in rows
    ]
    return normalized, meta
