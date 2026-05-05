"""API 한도/부하/등급 즉시 체크 — 가벼운 1회 GET으로 헤더만 추출.

/me/adaccounts?fields=id&limit=1을 사용. /me 단독 호출은 광고 endpoint가 아니라
X-Business-Use-Case-Usage / ads_api_access_tier 정보가 누락되므로 부적합.
/me/adaccounts?limit=1은 광고 계정 1개만 받아오면서 광고 관련 부하 헤더를 모두 제공.
"""
from __future__ import annotations

from datetime import datetime, timezone

from kr_mkt_mcp.meta_client import MetaClient


async def check_api_health(client: MetaClient) -> dict:
    """Meta API 토큰의 현재 부하/등급/한도 즉시 확인.

    호출은 /me/adaccounts?fields=id&limit=1 1회로 최소화 — 광고 계정 1개만 페치.
    사용자가 광고 데이터 분석을 시작하기 전 등급(development/standard) 및 누적 사용률을
    미리 점검할 때 사용. 응답 자체는 가볍고, 모든 부하 정보는 meta.api_usage에 담김.
    """
    raw = await client.call_endpoint(
        "/me/adaccounts",
        params={"fields": "id", "limit": 1},
    )
    accounts = raw.get("data", []) if isinstance(raw, dict) else []
    return {
        "data": {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "token_can_access_accounts": bool(accounts),
        },
        "meta": {
            "api_usage": client.last_usage,
        },
    }
