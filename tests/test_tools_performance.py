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
    return Config(access_token=fake_token, api_version="v25.0", base_url="https://graph.facebook.com")


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


@pytest.mark.asyncio
async def test_get_performance_default_tier1_campaign_level(cfg, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r".*v25\.0/act_111/insights.*"),
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
        url=re.compile(r".*v25\.0/act_111/insights.*"),
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


@pytest.mark.asyncio
async def test_get_performance_breakdown_returns_per_value_rows(cfg, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r".*insights.*"),
        json=load("insights_breakdown_age.json"),
    )
    client = MetaClient(cfg)
    result = await get_performance(
        client,
        account_id="act_111",
        level="campaign",
        breakdown="age",
        today=date(2026, 5, 5),
    )
    rows = result["data"]
    assert len(rows) == 2
    assert {r["age"] for r in rows} == {"25-34", "35-44"}
    assert result["meta"]["breakdown"] == "age"


@pytest.mark.asyncio
async def test_get_performance_breakdown_top_n_filters_to_top_campaigns(cfg, httpx_mock):
    """breakdown 사용 시 top_n=2이고 응답에 캠페인 c1/c2/c3가 있으면 sort_by 기준 상위 2개 캠페인의 행만 반환."""
    raw = {
        "data": [
            {"campaign_id": "c1", "age": "25-34", "spend": "20000"},
            {"campaign_id": "c1", "age": "35-44", "spend": "25000"},
            {"campaign_id": "c2", "age": "25-34", "spend": "10000"},
            {"campaign_id": "c2", "age": "35-44", "spend": "15000"},
            {"campaign_id": "c3", "age": "25-34", "spend": "5000"},
            {"campaign_id": "c3", "age": "35-44", "spend": "8000"},
        ]
    }
    httpx_mock.add_response(url=re.compile(r".*insights.*"), json=raw)
    client = MetaClient(cfg)
    result = await get_performance(
        client,
        account_id="act_111",
        level="campaign",
        breakdown="age",
        top_n=2,
        today=date(2026, 5, 5),
    )
    rows = result["data"]
    campaign_ids = {r["campaign_id"] for r in rows}
    # c1, c2 합계 spend가 c3보다 크므로 상위 2개로 필터됨
    assert campaign_ids == {"c1", "c2"}
    assert len(rows) == 4  # 2 캠페인 × 2 연령대


@pytest.mark.asyncio
async def test_get_performance_sort_by_ctr_overrides_default(cfg, httpx_mock):
    raw = {
        "data": [
            {"campaign_id": "c1", "age": "25-34", "spend": "100000", "ctr": "0.5"},
            {"campaign_id": "c2", "age": "25-34", "spend": "10000", "ctr": "3.0"},
        ]
    }
    httpx_mock.add_response(url=re.compile(r".*insights.*"), json=raw)
    client = MetaClient(cfg)
    result = await get_performance(
        client,
        account_id="act_111",
        level="campaign",
        breakdown="age",
        top_n=1,
        sort_by="ctr",
        today=date(2026, 5, 5),
    )
    # CTR 기준 top1은 c2
    assert {r["campaign_id"] for r in result["data"]} == {"c2"}


@pytest.mark.asyncio
async def test_get_performance_no_breakdown_top_n_clips_rows(cfg, httpx_mock):
    raw = {
        "data": [
            {"campaign_id": f"c{i}", "spend": str(1000 - i * 50)} for i in range(20)
        ]
    }
    httpx_mock.add_response(url=re.compile(r".*insights.*"), json=raw)
    client = MetaClient(cfg)
    result = await get_performance(
        client,
        account_id="act_111",
        level="campaign",
        top_n=5,
        today=date(2026, 5, 5),
    )
    assert len(result["data"]) == 5
    assert result["data"][0]["campaign_id"] == "c0"  # spend 가장 높음
