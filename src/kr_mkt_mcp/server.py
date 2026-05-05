"""FastMCP stdio 서버. V1의 7개 도구를 등록한다.

NOTE: MCP Python SDK의 FastMCP 인터페이스는 버전에 따라 변할 수 있음. 본 구현은
mcp>=1.2.0 기준. 실패 시 mcp 패키지 docstring/예제 참고해서 어댑트.
"""
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from kr_mkt_mcp.config import load_config
from kr_mkt_mcp.descriptions import (
    DESCRIPTION_CALL_META_API,
    DESCRIPTION_CHECK_API_HEALTH,
    DESCRIPTION_GET_CREATIVE_PREVIEW,
    DESCRIPTION_GET_PERFORMANCE,
    DESCRIPTION_LIST_AD_ACCOUNTS,
    DESCRIPTION_LIST_ADS,
    DESCRIPTION_LIST_CAMPAIGNS,
)
from kr_mkt_mcp.meta_client import MetaClient
from kr_mkt_mcp.tools.call_meta_api import call_meta_api as _call_meta_api
from kr_mkt_mcp.tools.check_api_health import check_api_health as _check_api_health
from kr_mkt_mcp.tools.get_creative_preview import get_creative_preview as _get_creative_preview
from kr_mkt_mcp.tools.get_performance import get_performance as _get_performance
from kr_mkt_mcp.tools.list_ad_accounts import list_ad_accounts as _list_ad_accounts
from kr_mkt_mcp.tools.list_ads import list_ads as _list_ads
from kr_mkt_mcp.tools.list_campaigns import list_campaigns as _list_campaigns


mcp = FastMCP("kr-mkt-mcp")

_CLIENT: MetaClient | None = None


def _client() -> MetaClient:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = MetaClient(load_config())
    return _CLIENT


@mcp.tool(description=DESCRIPTION_LIST_AD_ACCOUNTS)
async def list_ad_accounts() -> dict:
    rows, meta = await _list_ad_accounts(_client())
    return {"data": rows, "meta": meta}


@mcp.tool(description=DESCRIPTION_LIST_CAMPAIGNS)
async def list_campaigns(account_id: str, status: str | None = "ACTIVE") -> dict:
    rows, meta = await _list_campaigns(_client(), account_id=account_id, status=status)
    return {"data": rows, "meta": meta}


@mcp.tool(description=DESCRIPTION_LIST_ADS)
async def list_ads(
    account_id: str,
    campaign_id: str | None = None,
    status: str | None = "ACTIVE",
) -> dict:
    rows, meta = await _list_ads(
        _client(), account_id=account_id, campaign_id=campaign_id, status=status
    )
    return {"data": rows, "meta": meta}


@mcp.tool(description=DESCRIPTION_GET_PERFORMANCE)
async def get_performance(
    account_id: str,
    level: str = "campaign",
    tier: str = "tier1",
    metrics: list[str] | None = None,
    breakdown: str | None = None,
    sort_by: str | None = None,
    top_n: int | None = 10,
    date_preset: str | None = "last_7d",
    since: str | None = None,
    until: str | None = None,
) -> dict:
    return await _get_performance(
        _client(),
        account_id=account_id,
        level=level,
        tier=tier,
        metrics=metrics,
        breakdown=breakdown,
        sort_by=sort_by,
        top_n=top_n,
        date_preset=date_preset,
        since=since,
        until=until,
    )


@mcp.tool(description=DESCRIPTION_GET_CREATIVE_PREVIEW)
async def get_creative_preview(ad_id: str) -> dict:
    return await _get_creative_preview(_client(), ad_id=ad_id)


@mcp.tool(description=DESCRIPTION_CHECK_API_HEALTH)
async def check_api_health() -> dict:
    return await _check_api_health(_client())


@mcp.tool(description=DESCRIPTION_CALL_META_API)
async def call_meta_api(endpoint: str, params: dict[str, Any] | None = None) -> dict:
    return await _call_meta_api(_client(), endpoint=endpoint, params=params)


def main() -> None:
    """stdio entry — pyproject scripts에서 호출."""
    mcp.run()


if __name__ == "__main__":
    main()
