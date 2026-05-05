"""check_api_health 도구 테스트."""
from __future__ import annotations

import pytest

from kr_mkt_mcp.config import Config
from kr_mkt_mcp.meta_client import MetaClient
from kr_mkt_mcp.tools.check_api_health import check_api_health


@pytest.fixture
def cfg(fake_token) -> Config:
    return Config(
        access_token=fake_token,
        api_version="v25.0",
        base_url="https://graph.facebook.com",
    )


@pytest.mark.asyncio
async def test_check_api_health_returns_token_status_and_usage(cfg, httpx_mock):
    httpx_mock.add_response(
        url="https://graph.facebook.com/v25.0/me/adaccounts?fields=id&limit=1",
        json={"data": [{"id": "act_111"}]},
        headers={
            "X-Business-Use-Case-Usage": (
                '{"123": [{"type": "ads_management", "call_count": 5, '
                '"total_cputime": 3, "total_time": 2, '
                '"ads_api_access_tier": "development_access", '
                '"estimated_time_to_regain_access": 0}]}'
            ),
        },
    )
    client = MetaClient(cfg)
    result = await check_api_health(client)

    assert result["data"]["token_can_access_accounts"] is True
    assert "checked_at" in result["data"]
    usage = result["meta"]["api_usage"]
    assert usage is not None
    assert usage["max_pct"] == 5.0
    assert usage["access_tier"] == "development_access"
    assert "개발자 등급" in usage["access_tier_ko"]


@pytest.mark.asyncio
async def test_check_api_health_handles_no_account_access(cfg, httpx_mock):
    """토큰에 광고 계정 권한 없으면 token_can_access_accounts=False."""
    httpx_mock.add_response(
        url="https://graph.facebook.com/v25.0/me/adaccounts?fields=id&limit=1",
        json={"data": []},
    )
    client = MetaClient(cfg)
    result = await check_api_health(client)
    assert result["data"]["token_can_access_accounts"] is False
    assert result["meta"]["api_usage"] is None


@pytest.mark.asyncio
async def test_check_api_health_lightweight_call_only(cfg, httpx_mock):
    """가장 가벼운 endpoint 1회만 호출 — 무거운 광고 데이터 안 받음."""
    httpx_mock.add_response(
        url="https://graph.facebook.com/v25.0/me/adaccounts?fields=id&limit=1",
        json={"data": [{"id": "act_111"}]},
    )
    client = MetaClient(cfg)
    await check_api_health(client)

    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    url_str = str(requests[0].url)
    assert "/me/adaccounts" in url_str
    assert "limit=1" in url_str
    # 캠페인/insights 등 무거운 endpoint 호출 안 함
    assert "campaigns" not in url_str
    assert "insights" not in url_str
