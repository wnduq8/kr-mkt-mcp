import json
import re
from pathlib import Path

import pytest

from kr_mkt_mcp.config import Config
from kr_mkt_mcp.meta_client import MetaClient
from kr_mkt_mcp.tools.list_ad_accounts import list_ad_accounts
from kr_mkt_mcp.tools.list_campaigns import list_campaigns
from kr_mkt_mcp.tools.list_ads import list_ads


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def cfg(fake_token) -> Config:
    return Config(access_token=fake_token, api_version="v21.0", base_url="https://graph.facebook.com")


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


@pytest.mark.asyncio
async def test_list_ad_accounts_returns_normalized(cfg, httpx_mock):
    httpx_mock.add_response(
        url="https://graph.facebook.com/v21.0/me/adaccounts?fields=id,account_id,name,currency,account_status,business,timezone_name",
        json=load("ad_accounts.json"),
    )
    client = MetaClient(cfg)
    rows, meta = await list_ad_accounts(client)
    assert len(rows) == 2
    assert rows[0]["id"] == "act_111"
    assert rows[0]["name"] == "메인 쇼핑몰 광고계정"
    assert rows[0]["currency"] == "KRW"
    assert rows[0]["business_id"] == "biz_1"
    assert rows[0]["business_name"] == "메인 비즈"
    assert rows[0]["timezone_name"] == "Asia/Seoul"
    assert "account_status" in rows[0]
    assert meta["truncated"] is False


@pytest.mark.asyncio
async def test_list_campaigns_default_filter_active(cfg, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r"https://graph\.facebook\.com/v21\.0/act_111/campaigns"),
        json=load("campaigns.json"),
    )
    client = MetaClient(cfg)
    rows, meta = await list_campaigns(client, account_id="act_111")
    assert len(rows) == 2
    assert rows[0]["id"] == "c1"
    assert rows[0]["objective"] == "OUTCOME_SALES"
    assert rows[0]["daily_budget"] == 50000
    assert rows[1]["lifetime_budget"] == 1000000


@pytest.mark.asyncio
async def test_list_campaigns_status_override(cfg, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r"https://graph\.facebook\.com/v21\.0/act_111/campaigns"),
        json=load("campaigns.json"),
    )
    client = MetaClient(cfg)
    rows, _ = await list_campaigns(client, account_id="act_111", status="PAUSED")
    # 응답 자체는 fixture라 필터가 동작하진 않지만, 호출 시 effective_status=PAUSED로 query 들어가야 함
    requests = httpx_mock.get_requests()
    assert any("PAUSED" in str(req.url) for req in requests)


@pytest.mark.asyncio
async def test_list_ads_with_campaign_filter(cfg, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r"https://graph\.facebook\.com/v21\.0/act_111/ads"),
        json=load("ads.json"),
    )
    client = MetaClient(cfg)
    rows, _ = await list_ads(client, account_id="act_111", campaign_id="c1")
    assert len(rows) == 1
    assert rows[0]["id"] == "ad1"
    assert rows[0]["campaign_id"] == "c1"
    assert rows[0]["creative_id"] == "cr1"
