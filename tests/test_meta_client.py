import json
from pathlib import Path

import httpx
import pytest

from kr_mkt_mcp.config import Config
from kr_mkt_mcp.meta_client import MetaClient, ReadOnlyViolation


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def cfg(fake_token) -> Config:
    return Config(access_token=fake_token, api_version="v25.0", base_url="https://graph.facebook.com")


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


@pytest.mark.asyncio
async def test_get_single_page(cfg, httpx_mock):
    httpx_mock.add_response(
        url="https://graph.facebook.com/v25.0/act_123/campaigns?fields=id,name,status",
        json=load_fixture("campaigns_page1.json"),
    )
    # campaigns_page1.json has paging.next → follow-through page returns no more data
    httpx_mock.add_response(
        url="https://graph.facebook.com/v25.0/act_123/campaigns?after=A1",
        json={"data": [], "paging": {}},
    )
    client = MetaClient(cfg)
    rows, meta = await client.get_paginated("/act_123/campaigns", params={"fields": "id,name,status"})
    assert len(rows) == 2
    assert rows[0]["id"] == "c1"
    assert meta["truncated"] is False


@pytest.mark.asyncio
async def test_get_auto_paginate_until_done(cfg, httpx_mock):
    httpx_mock.add_response(
        url="https://graph.facebook.com/v25.0/act_123/campaigns?fields=id",
        json=load_fixture("campaigns_page1.json"),
    )
    httpx_mock.add_response(
        url="https://graph.facebook.com/v25.0/act_123/campaigns?after=A1",
        json=load_fixture("campaigns_page2.json"),
    )
    client = MetaClient(cfg)
    rows, meta = await client.get_paginated("/act_123/campaigns", params={"fields": "id"})
    assert len(rows) == 3
    assert meta["truncated"] is False


@pytest.mark.asyncio
async def test_get_truncates_at_hard_cap(cfg, httpx_mock, monkeypatch):
    monkeypatch.setattr("kr_mkt_mcp.config.PAGINATION_HARD_CAP", 2)
    httpx_mock.add_response(
        url="https://graph.facebook.com/v25.0/act_123/campaigns",
        json=load_fixture("campaigns_page1.json"),  # 2 rows, paging.next 있음
    )
    client = MetaClient(cfg)
    rows, meta = await client.get_paginated("/act_123/campaigns", params={})
    assert len(rows) == 2
    assert meta["truncated"] is True
    assert meta["hard_cap"] == 2


@pytest.mark.asyncio
async def test_no_false_positive_truncated_when_exact_cap(cfg, httpx_mock, monkeypatch):
    """cap과 동일한 row 수 + paging.next 없으면 truncated=False."""
    monkeypatch.setattr("kr_mkt_mcp.config.PAGINATION_HARD_CAP", 2)
    httpx_mock.add_response(
        url="https://graph.facebook.com/v25.0/act_123/campaigns",
        json={"data": [{"id": "c1"}, {"id": "c2"}], "paging": {}},
    )
    client = MetaClient(cfg)
    rows, meta = await client.get_paginated("/act_123/campaigns", params={})
    assert len(rows) == 2
    assert meta["truncated"] is False


@pytest.mark.asyncio
async def test_call_endpoint_raw(cfg, httpx_mock):
    httpx_mock.add_response(
        url="https://graph.facebook.com/v25.0/me",
        json={"id": "user_1", "name": "Tester"},
    )
    client = MetaClient(cfg)
    raw = await client.call_endpoint("/me", params=None)
    assert raw == {"id": "user_1", "name": "Tester"}


@pytest.mark.asyncio
async def test_call_endpoint_supports_version_override(cfg, httpx_mock):
    httpx_mock.add_response(
        url="https://graph.facebook.com/v22.0/me",
        json={"id": "user_2"},
    )
    client = MetaClient(cfg)
    raw = await client.call_endpoint("/v22.0/me", params=None)
    assert raw == {"id": "user_2"}


def test_client_has_no_post_method(cfg):
    client = MetaClient(cfg)
    # MetaClient는 POST/PUT/DELETE/PATCH 메서드를 노출해서는 안 됨 — read-only 강제
    forbidden = {"post", "put", "delete", "patch"}
    public_methods = {m for m in dir(client) if not m.startswith("_")}
    assert public_methods.isdisjoint(forbidden)


def test_readonly_violation_is_module_export():
    """raw passthrough에서 GET 외 시도가 들어오면 던질 예외 타입이 정의되어 있어야 한다."""
    assert ReadOnlyViolation is not None
    assert issubclass(ReadOnlyViolation, Exception)
