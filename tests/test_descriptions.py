from kr_mkt_mcp.descriptions import (
    DESCRIPTION_LIST_AD_ACCOUNTS,
    DESCRIPTION_LIST_CAMPAIGNS,
    DESCRIPTION_LIST_ADS,
    DESCRIPTION_GET_PERFORMANCE,
    DESCRIPTION_GET_CREATIVE_PREVIEW,
    DESCRIPTION_CALL_META_API,
    METRIC_ALIAS_TABLE,
)


def test_all_descriptions_mention_read_only():
    for desc in [
        DESCRIPTION_LIST_AD_ACCOUNTS,
        DESCRIPTION_LIST_CAMPAIGNS,
        DESCRIPTION_LIST_ADS,
        DESCRIPTION_GET_PERFORMANCE,
        DESCRIPTION_GET_CREATIVE_PREVIEW,
        DESCRIPTION_CALL_META_API,
    ]:
        assert "read-only" in desc.lower() or "조회 전용" in desc or "읽기 전용" in desc


def test_metric_alias_includes_korean_for_tier1():
    # tier1 메트릭 모두 한국어 alias가 사전에 있어야 함
    for m in ("spend", "purchase_roas", "cpc", "ctr", "purchases", "frequency"):
        assert m in METRIC_ALIAS_TABLE
        assert len(METRIC_ALIAS_TABLE[m]) > 0


def test_get_performance_description_mentions_workflows():
    desc = DESCRIPTION_GET_PERFORMANCE
    assert "데일리 점검" in desc or "어제" in desc
    assert "주간" in desc
    assert "breakdown" in desc.lower() or "연령" in desc


def test_call_meta_api_description_warns_about_escape_hatch():
    desc = DESCRIPTION_CALL_META_API
    assert "묶음" in desc or "다른 도구" in desc
    assert "GET" in desc
