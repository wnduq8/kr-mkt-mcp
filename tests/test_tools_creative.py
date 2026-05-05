import json
import re
from pathlib import Path

import pytest

from kr_mkt_mcp.config import Config
from kr_mkt_mcp.meta_client import MetaClient
from kr_mkt_mcp.tools.get_creative_preview import get_creative_preview


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def cfg(fake_token) -> Config:
    return Config(access_token=fake_token, api_version="v25.0", base_url="https://graph.facebook.com")


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


@pytest.mark.asyncio
async def test_creative_image(cfg, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r".*v25\.0/ad1\?.*"),
        json={"id": "ad1", "name": "ad1 name", "creative": {"id": "cr1"}},
    )
    httpx_mock.add_response(
        url=re.compile(r".*v25\.0/cr1\?.*"),
        json=load("creative_image.json"),
    )
    client = MetaClient(cfg)
    result = await get_creative_preview(client, ad_id="ad1")
    assert result["ad_id"] == "ad1"
    assert result["creative_type"] == "IMAGE"
    assert result["headline"] == "봄세일 시작! 최대 50% OFF"
    assert result["body"] == "지금 바로 둘러보세요. 한정 수량."
    assert result["cta"] == "SHOP_NOW"
    assert result["image_url"].startswith("https://")
    assert result["thumbnail_url"].startswith("https://")
    assert result["link_url"].startswith("https://")


@pytest.mark.asyncio
async def test_creative_video(cfg, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r".*v25\.0/ad2\?.*"),
        json={"id": "ad2", "creative": {"id": "cr2"}},
    )
    httpx_mock.add_response(
        url=re.compile(r".*v25\.0/cr2\?.*"),
        json=load("creative_video.json"),
    )
    client = MetaClient(cfg)
    result = await get_creative_preview(client, ad_id="ad2")
    assert result["creative_type"] == "VIDEO"
    assert result["video_id"] == "v123"
    assert result["thumbnail_url"].startswith("https://")
    assert result["cta"] == "WATCH_MORE"


@pytest.mark.asyncio
async def test_creative_carousel(cfg, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r".*v25\.0/ad3\?.*"),
        json={"id": "ad3", "creative": {"id": "cr3"}},
    )
    httpx_mock.add_response(
        url=re.compile(r".*v25\.0/cr3\?.*"),
        json=load("creative_carousel.json"),
    )
    client = MetaClient(cfg)
    result = await get_creative_preview(client, ad_id="ad3")
    assert result["creative_type"] == "CAROUSEL"
    assert len(result["cards"]) == 2
    assert result["cards"][0]["headline"] == "원피스"
    assert result["cards"][0]["body"] == "봄 신상"
    assert result["cards"][0]["cta"] == "SHOP_NOW"
