"""보안 검증 회귀 테스트 — 입력 검증 / token leak 방지."""
from __future__ import annotations

import pytest

from kr_mkt_mcp.config import Config
from kr_mkt_mcp.meta_client import MetaClient, _strip_sensitive_query_params
from kr_mkt_mcp.tools.call_meta_api import call_meta_api
from kr_mkt_mcp.tools.get_creative_preview import get_creative_preview
from kr_mkt_mcp.tools.get_performance import get_performance
from kr_mkt_mcp.tools.list_ads import list_ads
from kr_mkt_mcp.tools.list_campaigns import list_campaigns
from kr_mkt_mcp.validation import (
    validate_field_name,
    validate_id,
    validate_in_set,
    validate_int_range,
)


@pytest.fixture
def cfg(fake_token) -> Config:
    return Config(access_token=fake_token, api_version="v25.0", base_url="https://graph.facebook.com")


# ===== 1. validate_id (path traversal) =====


@pytest.mark.parametrize(
    "bad_id",
    [
        "act_123/../me",        # path traversal
        "act_123/x",             # forward slash
        "act_123\\x",            # backslash
        "act_123?fields=foo",    # query injection
        "act_123&secret=1",      # query separator
        "act_123 with space",    # whitespace
        "act_123\n",             # newline injection
        "act_123#fragment",      # fragment
        "act_123%2F..",          # URL-encoded slash
        "",                       # empty
    ],
)
def test_validate_id_rejects_dangerous_input(bad_id):
    with pytest.raises(ValueError):
        validate_id(bad_id, "account_id")


def test_validate_id_accepts_normal():
    validate_id("act_1508399064276817", "account_id")
    validate_id("123456789", "campaign_id")


# ===== 2. validate_field_name (comma injection) =====


@pytest.mark.parametrize(
    "bad",
    [
        "spend,targeting_spec",  # 컴마 주입
        "spend targeting",        # 공백 주입
        "spend{nested}",          # nested syntax
        "1spend",                 # 숫자 시작
        "Spend",                  # 대문자
        "",                        # 빈
    ],
)
def test_validate_field_name_rejects(bad):
    with pytest.raises(ValueError):
        validate_field_name(bad, "metrics 항목")


def test_validate_field_name_accepts():
    validate_field_name("spend")
    validate_field_name("purchase_roas")
    validate_field_name("video_30_sec_watched_actions")


# ===== 3. validate_in_set (enum) =====


def test_validate_in_set():
    validate_in_set("campaign", ("account", "campaign", "adset", "ad"), "level")
    with pytest.raises(ValueError):
        validate_in_set("invalid_level", ("account", "campaign"), "level")


# ===== 4. validate_int_range =====


def test_validate_int_range():
    validate_int_range(10, lo=1, hi=200, name="top_n")
    with pytest.raises(ValueError):
        validate_int_range(0, lo=1, hi=200, name="top_n")
    with pytest.raises(ValueError):
        validate_int_range(201, lo=1, hi=200, name="top_n")
    with pytest.raises(ValueError):
        validate_int_range(-5, lo=1, hi=200, name="top_n")


# ===== 5. call_meta_api: %3F URL encoding 우회 차단 =====


@pytest.mark.asyncio
async def test_call_meta_api_blocks_urlencoded_question_mark(cfg):
    client = MetaClient(cfg)
    with pytest.raises(ValueError, match="query string"):
        await call_meta_api(client, endpoint="/me%3Fmethod=delete", params=None)


@pytest.mark.asyncio
async def test_call_meta_api_blocks_urlencoded_ampersand(cfg):
    client = MetaClient(cfg)
    with pytest.raises(ValueError, match="query string"):
        await call_meta_api(client, endpoint="/me%26access_token=foo", params=None)


# ===== 6. call_meta_api: access_token in params 차단 =====


@pytest.mark.asyncio
async def test_call_meta_api_blocks_access_token_param(cfg):
    client = MetaClient(cfg)
    with pytest.raises(ValueError, match="금지된 키"):
        await call_meta_api(client, endpoint="/me", params={"access_token": "stolen"})


# ===== 7. tool 진입점에서 path traversal 차단 =====


@pytest.mark.asyncio
async def test_list_campaigns_blocks_traversal(cfg):
    client = MetaClient(cfg)
    with pytest.raises(ValueError):
        await list_campaigns(client, account_id="act_123/../me")


@pytest.mark.asyncio
async def test_list_ads_blocks_traversal(cfg):
    client = MetaClient(cfg)
    with pytest.raises(ValueError):
        await list_ads(client, account_id="act_123", campaign_id="../me")


@pytest.mark.asyncio
async def test_get_creative_preview_blocks_traversal(cfg):
    client = MetaClient(cfg)
    with pytest.raises(ValueError):
        await get_creative_preview(client, ad_id="../me/payment_methods")


# ===== 8. get_performance: 모든 입력 검증 =====


@pytest.mark.asyncio
async def test_get_performance_blocks_account_traversal(cfg):
    client = MetaClient(cfg)
    with pytest.raises(ValueError):
        await get_performance(client, account_id="act_123/../me")


@pytest.mark.asyncio
async def test_get_performance_blocks_invalid_breakdown(cfg):
    client = MetaClient(cfg)
    with pytest.raises(ValueError, match="breakdown"):
        await get_performance(client, account_id="act_123", breakdown="targeting_spec")


@pytest.mark.asyncio
async def test_get_performance_blocks_sort_by_injection(cfg):
    client = MetaClient(cfg)
    with pytest.raises(ValueError, match="sort_by"):
        await get_performance(client, account_id="act_123", sort_by="spend,targeting_spec")


@pytest.mark.asyncio
async def test_get_performance_blocks_metrics_injection(cfg):
    client = MetaClient(cfg)
    with pytest.raises(ValueError, match="metrics"):
        await get_performance(
            client, account_id="act_123", metrics=["spend", "spend,targeting_spec"]
        )


@pytest.mark.asyncio
async def test_get_performance_blocks_top_n_negative(cfg):
    client = MetaClient(cfg)
    with pytest.raises(ValueError, match="top_n"):
        await get_performance(client, account_id="act_123", top_n=-1)


@pytest.mark.asyncio
async def test_get_performance_blocks_top_n_too_large(cfg):
    client = MetaClient(cfg)
    with pytest.raises(ValueError, match="top_n"):
        await get_performance(client, account_id="act_123", top_n=10000)


@pytest.mark.asyncio
async def test_get_performance_blocks_invalid_date_preset(cfg):
    client = MetaClient(cfg)
    with pytest.raises(ValueError, match="date_preset"):
        await get_performance(client, account_id="act_123", date_preset="ever")


# ===== 9. paging.next access_token 제거 =====


def test_strip_access_token_from_paging_next():
    raw = "https://graph.facebook.com/v25.0/act_123/campaigns?after=A1&access_token=EAAxxxx&limit=25"
    cleaned = _strip_sensitive_query_params(raw)
    assert "access_token" not in cleaned
    assert "EAAxxxx" not in cleaned
    assert "after=A1" in cleaned
    assert "limit=25" in cleaned


def test_strip_handles_appsecret_proof():
    raw = "https://graph.facebook.com/me?appsecret_proof=secret123&fields=id"
    cleaned = _strip_sensitive_query_params(raw)
    assert "appsecret_proof" not in cleaned
    assert "secret123" not in cleaned
    assert "fields=id" in cleaned


def test_strip_no_query_unchanged():
    raw = "https://graph.facebook.com/me"
    assert _strip_sensitive_query_params(raw) == raw
