import json
from pathlib import Path

import pytest

from kr_mkt_mcp.config import Config
from kr_mkt_mcp.meta_client import MetaClient
from kr_mkt_mcp.tools.list_ad_accounts import list_ad_accounts


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
