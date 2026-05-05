import pytest

from kr_mkt_mcp.config import Config
from kr_mkt_mcp.meta_client import MetaClient
from kr_mkt_mcp.tools.call_meta_api import call_meta_api


@pytest.fixture
def cfg(fake_token) -> Config:
    return Config(access_token=fake_token, api_version="v25.0", base_url="https://graph.facebook.com")


@pytest.mark.asyncio
async def test_call_meta_api_returns_raw(cfg, httpx_mock):
    httpx_mock.add_response(
        url="https://graph.facebook.com/v25.0/me?fields=id,name",
        json={"id": "user_1", "name": "테스터"},
    )
    client = MetaClient(cfg)
    result = await call_meta_api(client, endpoint="/me", params={"fields": "id,name"})
    # 응답은 {"data": <원본>, "meta": {"api_usage": ...}} 형태로 wrapping됨
    assert result["data"] == {"id": "user_1", "name": "테스터"}
    assert "api_usage" in result["meta"]
    # mock 응답에 X-*-Usage 헤더 없으므로 None
    assert result["meta"]["api_usage"] is None


@pytest.mark.asyncio
async def test_call_meta_api_endpoint_with_explicit_version(cfg, httpx_mock):
    httpx_mock.add_response(
        url="https://graph.facebook.com/v22.0/me",
        json={"id": "user_2"},
    )
    client = MetaClient(cfg)
    result = await call_meta_api(client, endpoint="/v22.0/me", params=None)
    assert result["data"] == {"id": "user_2"}


@pytest.mark.asyncio
async def test_call_meta_api_includes_api_usage_when_headers_present(cfg, httpx_mock):
    httpx_mock.add_response(
        url="https://graph.facebook.com/v25.0/me",
        json={"id": "user"},
        headers={
            "X-App-Usage": '{"call_count": 28, "total_cputime": 25, "total_time": 25}',
            "X-Ad-Account-Usage": '{"acc_id_util_pct": 9.85}',
        },
    )
    client = MetaClient(cfg)
    result = await call_meta_api(client, endpoint="/me", params=None)
    usage = result["meta"]["api_usage"]
    assert usage is not None
    assert usage["max_pct"] == 28.0
    assert usage["warning_level"] == "ok"
    assert "█" in usage["gauge"]


@pytest.mark.parametrize(
    "bad_endpoint",
    [
        "https://example.com/abuse",  # 외부 URL
        "/me/feed?method=POST",  # query string에 method 강제 시도
        "//etc/passwd",  # 경로 traversal 시도
    ],
)
@pytest.mark.asyncio
async def test_call_meta_api_rejects_dangerous_endpoint(cfg, bad_endpoint):
    client = MetaClient(cfg)
    with pytest.raises(ValueError):
        await call_meta_api(client, endpoint=bad_endpoint, params=None)


@pytest.mark.asyncio
async def test_call_meta_api_rejects_method_param(cfg):
    client = MetaClient(cfg)
    with pytest.raises(ValueError, match="method"):
        await call_meta_api(client, endpoint="/me", params={"method": "POST"})
