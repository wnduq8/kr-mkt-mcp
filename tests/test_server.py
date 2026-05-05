"""server.py 모듈은 FastMCP 인스턴스에 6개 도구를 등록한다."""
import pytest

from kr_mkt_mcp.server import mcp


@pytest.mark.asyncio
async def test_server_has_six_tools():
    """FastMCP의 list_tools()로 실제 등록 검증."""
    tools = await mcp.list_tools()
    tool_names = {t.name for t in tools}
    expected = {
        "list_ad_accounts",
        "list_campaigns",
        "list_ads",
        "get_performance",
        "get_creative_preview",
        "call_meta_api",
    }
    assert tool_names == expected


def test_main_entry_callable():
    from kr_mkt_mcp.server import main
    assert callable(main)


@pytest.mark.asyncio
async def test_each_tool_has_description():
    """등록된 모든 도구에 description이 부착됨."""
    tools = await mcp.list_tools()
    for t in tools:
        assert t.description, f"{t.name}에 description 누락"
        assert "read-only" in t.description.lower() or "조회 전용" in t.description or "읽기 전용" in t.description, \
            f"{t.name} description에 read-only 표기 누락"
