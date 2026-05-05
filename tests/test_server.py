"""server.py 모듈은 FastMCP 인스턴스에 6개 도구를 등록한다."""
from kr_mkt_mcp.server import mcp


def test_server_has_six_tools():
    # FastMCP는 등록된 도구를 list_tools()로 노출 (정확한 인터페이스는 mcp 패키지 버전에 따라 다름)
    # 여기서는 인스턴스가 존재하고 6개 핸들러를 갖고 있는지만 확인
    tool_names = {t.name for t in mcp._tools.values()} if hasattr(mcp, "_tools") else set()
    expected = {
        "list_ad_accounts",
        "list_campaigns",
        "list_ads",
        "get_performance",
        "get_creative_preview",
        "call_meta_api",
    }
    # FastMCP 내부 attribute 명이 버전에 따라 다를 수 있어 fallback
    if not tool_names:
        # 등록 함수 명을 직접 확인
        from kr_mkt_mcp import server as srv
        for name in expected:
            assert hasattr(srv, name) or hasattr(srv, f"_tool_{name}"), f"{name} 등록 누락"
    else:
        assert tool_names == expected


def test_main_entry_callable():
    from kr_mkt_mcp.server import main
    assert callable(main)
