"""토큰 권한 범위 내 광고 계정 목록 조회.

V1에서 account_id가 모든 도구의 필수 파라미터이므로, 사용자가 광고계정 이름을 언급할 때
AI가 이 도구로 ID를 먼저 찾는 흐름을 가능하게 한다.
"""
from __future__ import annotations

from kr_mkt_mcp.meta_client import MetaClient

_FIELDS = "id,account_id,name,currency,account_status,business,timezone_name"


async def list_ad_accounts(client: MetaClient) -> tuple[list[dict], dict]:
    rows, meta = await client.get_paginated("/me/adaccounts", params={"fields": _FIELDS})
    normalized = []
    for r in rows:
        biz = r.get("business") or {}
        normalized.append(
            {
                "id": r.get("id"),
                "account_id": r.get("account_id"),
                "name": r.get("name"),
                "currency": r.get("currency"),
                "account_status": r.get("account_status"),
                "business_id": biz.get("id"),
                "business_name": biz.get("name"),
                "timezone_name": r.get("timezone_name"),
            }
        )
    return normalized, meta
