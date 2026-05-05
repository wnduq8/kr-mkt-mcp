import json
import re
from datetime import date
from pathlib import Path

import pytest

from kr_mkt_mcp.config import Config
from kr_mkt_mcp.meta_client import MetaClient
from kr_mkt_mcp.tools.get_performance import get_performance


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def cfg(fake_token) -> Config:
    return Config(access_token=fake_token, api_version="v21.0", base_url="https://graph.facebook.com")


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


@pytest.mark.asyncio
async def test_get_performance_default_tier1_campaign_level(cfg, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r".*v21\.0/act_111/insights.*"),
        json=load("insights_campaign_tier1.json"),
    )
    client = MetaClient(cfg)
    result = await get_performance(
        client,
        account_id="act_111",
        level="campaign",
        today=date(2026, 5, 5),
    )
    assert "data" in result
    assert "meta" in result
    assert len(result["data"]) == 1
    row = result["data"][0]
    assert row["spend"] == 45000
    assert row["purchase_roas"] == 3.2
    assert row["purchases"] == 12
    # tier1 메트릭 모두 포함
    for m in ["impressions", "reach", "frequency", "clicks", "spend", "cpm", "cpc", "ctr"]:
        assert m in row, f"tier1 metric {m} missing"


@pytest.mark.asyncio
async def test_get_performance_metrics_override(cfg, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r".*insights.*"),
        json={"data": [{"campaign_id": "c1", "spend": "1000", "purchase_roas": [{"value": "2.0"}]}]},
    )
    client = MetaClient(cfg)
    await get_performance(
        client,
        account_id="act_111",
        level="campaign",
        metrics=["spend", "purchase_roas"],
        today=date(2026, 5, 5),
    )
    requests = httpx_mock.get_requests()
    assert any("spend" in str(r.url) and "purchase_roas" in str(r.url) for r in requests)


@pytest.mark.asyncio
async def test_get_performance_tier_all_includes_video_metrics(cfg, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r".*insights.*"),
        json={"data": [{"campaign_id": "c1", "spend": "1000"}]},
    )
    client = MetaClient(cfg)
    await get_performance(
        client,
        account_id="act_111",
        level="campaign",
        tier="all",
        today=date(2026, 5, 5),
    )
    requests = httpx_mock.get_requests()
    request_url = str(requests[-1].url)
    assert "video_3_sec_watched_actions" in request_url
    assert "quality_ranking" in request_url


@pytest.mark.asyncio
async def test_get_performance_account_level(cfg, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r".*v21\.0/act_111/insights.*"),
        json={"data": [{"account_id": "111", "spend": "100000", "purchase_roas": [{"value": "2.5"}]}]},
    )
    client = MetaClient(cfg)
    result = await get_performance(
        client,
        account_id="act_111",
        level="account",
        today=date(2026, 5, 5),
    )
    assert len(result["data"]) == 1
    assert result["data"][0]["spend"] == 100000


@pytest.mark.asyncio
async def test_get_performance_since_until_overrides_preset(cfg, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r".*insights.*"),
        json={"data": []},
    )
    client = MetaClient(cfg)
    await get_performance(
        client,
        account_id="act_111",
        level="campaign",
        since="2026-03-01",
        until="2026-03-15",
    )
    requests = httpx_mock.get_requests()
    request_url = str(requests[-1].url)
    assert "2026-03-01" in request_url
    assert "2026-03-15" in request_url
