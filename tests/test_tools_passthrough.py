import pytest

from kr_mkt_mcp.config import Config
from kr_mkt_mcp.meta_client import MetaClient
from kr_mkt_mcp.tools.call_meta_api import call_meta_api


@pytest.fixture
def cfg(fake_token) -> Config:
    return Config(access_token=fake_token, api_version="v21.0", base_url="https://graph.facebook.com")


@pytest.mark.asyncio
async def test_call_meta_api_returns_raw(cfg, httpx_mock):
    httpx_mock.add_response(
        url="https://graph.facebook.com/v21.0/me?fields=id,name",
        json={"id": "user_1", "name": "테스터"},
    )
    client = MetaClient(cfg)
    result = await call_meta_api(client, endpoint="/me", params={"fields": "id,name"})
    assert result == {"id": "user_1", "name": "테스터"}


@pytest.mark.asyncio
async def test_call_meta_api_endpoint_with_explicit_version(cfg, httpx_mock):
    httpx_mock.add_response(
        url="https://graph.facebook.com/v22.0/me",
        json={"id": "user_2"},
    )
    client = MetaClient(cfg)
    result = await call_meta_api(client, endpoint="/v22.0/me", params=None)
    assert result == {"id": "user_2"}


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
