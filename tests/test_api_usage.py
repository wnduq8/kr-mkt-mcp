"""API usage 모니터링 — 헤더 파싱 + gauge + warning level."""
from __future__ import annotations

import json

import pytest

from kr_mkt_mcp.api_usage import (
    compute_warning,
    format_gauge,
    parse_usage_headers,
    summarize_usage,
)
from kr_mkt_mcp.config import Config
from kr_mkt_mcp.meta_client import MetaClient


@pytest.fixture
def cfg(fake_token) -> Config:
    return Config(access_token=fake_token, api_version="v25.0", base_url="https://graph.facebook.com")


# ===== format_gauge =====


@pytest.mark.parametrize(
    "pct, expected_filled",
    [(0, 0), (25, 5), (50, 10), (100, 20), (-5, 0), (150, 20)],
)
def test_format_gauge_filled_blocks(pct, expected_filled):
    """20-width gauge: 25%면 5개, 50%면 10개, 100%면 20개 채워짐."""
    bar = format_gauge(pct)
    filled = bar.count("█")
    assert filled == expected_filled


def test_format_gauge_includes_percent_text():
    assert "28.0%" in format_gauge(28)
    assert "0.0%" in format_gauge(0)
    assert "100.0%" in format_gauge(100)


# ===== compute_warning =====


@pytest.mark.parametrize(
    "pct, expected_level",
    [(0, "ok"), (49, "ok"), (50, "medium"), (75, "high"), (89, "high"), (90, "critical"), (100, "critical")],
)
def test_compute_warning_thresholds(pct, expected_level):
    level, _ = compute_warning(pct)
    assert level == expected_level


def test_compute_warning_messages_korean():
    _, msg = compute_warning(95)
    assert "위험" in msg or "🔴" in msg
    _, msg = compute_warning(80)
    assert "주의" in msg or "🟠" in msg
    _, msg = compute_warning(60)
    assert "알림" in msg or "🟡" in msg
    _, msg = compute_warning(20)
    assert "정상" in msg or "🟢" in msg


# ===== parse_usage_headers =====


def test_parse_usage_headers_dict():
    h = {
        "X-App-Usage": '{"call_count": 50, "total_cputime": 30, "total_time": 25}',
        "X-Ad-Account-Usage": '{"acc_id_util_pct": 10.5}',
    }
    parsed = parse_usage_headers(h)
    assert parsed["app_usage"] == {"call_count": 50, "total_cputime": 30, "total_time": 25}
    assert parsed["ad_account_usage"] == {"acc_id_util_pct": 10.5}
    assert parsed["business_use_case_usage"] is None
    assert parsed["insights_throttle"] is None


def test_parse_usage_headers_case_insensitive():
    h = {"x-app-usage": '{"call_count": 5}'}
    parsed = parse_usage_headers(h)
    assert parsed["app_usage"] == {"call_count": 5}


def test_parse_usage_headers_missing_returns_none():
    parsed = parse_usage_headers({})
    assert parsed == {
        "app_usage": None,
        "ad_account_usage": None,
        "business_use_case_usage": None,
        "insights_throttle": None,
    }


def test_parse_usage_headers_invalid_json_ignored():
    h = {"X-App-Usage": "not valid json"}
    parsed = parse_usage_headers(h)
    assert parsed["app_usage"] is None


def test_parse_insights_throttle_header():
    """X-FB-Ads-Insights-Throttle 헤더 — insights 호출 시에만 옴."""
    h = {
        "X-FB-Ads-Insights-Throttle": '{"app_id_util_pct": 0.01, "acc_id_util_pct": 5.5, "ads_api_access_tier": "development_access"}'
    }
    parsed = parse_usage_headers(h)
    assert parsed["insights_throttle"]["app_id_util_pct"] == 0.01
    assert parsed["insights_throttle"]["acc_id_util_pct"] == 5.5
    assert parsed["insights_throttle"]["ads_api_access_tier"] == "development_access"


def test_summarize_includes_korean_summary():
    h = {
        "X-Business-Use-Case-Usage": json.dumps({
            "634718569695860": [
                {
                    "type": "ads_insights",
                    "call_count": 65,
                    "total_cputime": 30,
                    "total_time": 30,
                    "estimated_time_to_regain_access": 0,
                    "ads_api_access_tier": "development_access",
                }
            ]
        }),
        "X-FB-Ads-Insights-Throttle": '{"app_id_util_pct": 0.01, "acc_id_util_pct": 0, "ads_api_access_tier": "development_access"}',
    }
    result = summarize_usage(h)
    assert result["max_pct"] == 65.0
    assert result["warning_level"] == "medium"
    assert result["access_tier"] == "development_access"
    assert "개발자 등급" in result["access_tier_ko"]
    # summary_ko 라인들에 사용자 친화 표현 포함
    summary_text = "\n".join(result["summary_ko"])
    assert "광고 분석" in summary_text  # ads_insights → 한국어
    assert "%" in summary_text
    assert "권장" in summary_text


def test_summarize_critical_level_recommends_immediate_stop():
    h = {"X-App-Usage": '{"call_count": 95}'}
    result = summarize_usage(h)
    assert result["warning_level"] == "critical"
    summary = "\n".join(result["summary_ko"])
    assert "중단" in summary or "🔴" in summary


def test_summarize_etr_visible_when_blocked():
    """estimated_time_to_regain_access > 0이면 차단 정보 노출."""
    h = {
        "X-Business-Use-Case-Usage": json.dumps({
            "biz1": [{"type": "ads_management", "call_count": 100, "estimated_time_to_regain_access": 1800}]
        })
    }
    result = summarize_usage(h)
    summary = "\n".join(result["summary_ko"])
    assert "1800" in summary
    assert "차단" in summary or "대기" in summary


# ===== summarize_usage =====


def test_summarize_usage_max_pct_picks_highest():
    h = {
        "X-App-Usage": '{"call_count": 30, "total_cputime": 75, "total_time": 25}',
        "X-Ad-Account-Usage": '{"acc_id_util_pct": 10}',
    }
    result = summarize_usage(h)
    assert result["max_pct"] == 75.0
    assert result["warning_level"] == "high"


def test_summarize_usage_business_use_case_flat():
    h = {
        "X-Business-Use-Case-Usage": json.dumps({
            "biz123": [
                {"type": "ads_management", "call_count": 95, "total_cputime": 50, "total_time": 30}
            ]
        })
    }
    result = summarize_usage(h)
    assert result["max_pct"] == 95.0
    assert result["warning_level"] == "critical"


def test_summarize_usage_returns_none_if_no_headers():
    assert summarize_usage({}) is None


def test_summarize_usage_includes_gauge():
    h = {"X-App-Usage": '{"call_count": 60}'}
    result = summarize_usage(h)
    assert "█" in result["gauge"]
    assert "60" in result["gauge"]


# ===== integration: MetaClient.last_usage 갱신 =====


@pytest.mark.asyncio
async def test_meta_client_captures_usage_on_call(cfg, httpx_mock):
    httpx_mock.add_response(
        url="https://graph.facebook.com/v25.0/me",
        json={"id": "u"},
        headers={"X-App-Usage": '{"call_count": 35}'},
    )
    client = MetaClient(cfg)
    assert client.last_usage is None
    await client.call_endpoint("/me", params=None)
    assert client.last_usage is not None
    assert client.last_usage["max_pct"] == 35.0


@pytest.mark.asyncio
async def test_get_paginated_meta_includes_api_usage(cfg, httpx_mock):
    httpx_mock.add_response(
        url="https://graph.facebook.com/v25.0/act_111/campaigns",
        json={"data": [{"id": "c1"}], "paging": {}},
        headers={
            "X-App-Usage": '{"call_count": 42}',
            "X-Ad-Account-Usage": '{"acc_id_util_pct": 12.5}',
        },
    )
    client = MetaClient(cfg)
    rows, meta = await client.get_paginated("/act_111/campaigns", params={})
    assert "api_usage" in meta
    assert meta["api_usage"]["max_pct"] == 42.0
    assert meta["api_usage"]["warning_level"] == "ok"


@pytest.mark.asyncio
async def test_get_paginated_meta_api_usage_none_when_no_headers(cfg, httpx_mock):
    httpx_mock.add_response(
        url="https://graph.facebook.com/v25.0/act_111/campaigns",
        json={"data": [], "paging": {}},
    )
    client = MetaClient(cfg)
    _, meta = await client.get_paginated("/act_111/campaigns", params={})
    assert meta["api_usage"] is None
