"""로컬 stdio 검증 — Meta 토큰 없이 서버가 MCP 프로토콜을 정상 수행하는지 확인.

다음을 검증:
1. 서버 subprocess 기동 (`python -m kr_mkt_mcp.server`)
2. MCP initialize 핸드셰이크 응답
3. tools/list가 6개 도구 반환
4. 각 도구에 description + read-only 표기 포함

사용:
    .venv/bin/python scripts/verify_stdio.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


EXPECTED_TOOLS = {
    "list_ad_accounts",
    "list_campaigns",
    "list_ads",
    "get_performance",
    "get_creative_preview",
    "call_meta_api",
}


async def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    venv_python = repo_root / ".venv" / "bin" / "python"
    if not venv_python.exists():
        print(f"❌ venv python을 찾을 수 없음: {venv_python}", file=sys.stderr)
        return 1

    params = StdioServerParameters(
        command=str(venv_python),
        args=["-m", "kr_mkt_mcp.server"],
        env={"META_ACCESS_TOKEN": "FAKE_TOKEN_FOR_HANDSHAKE_ONLY"},
    )

    print("⏳ 서버 subprocess 기동 + MCP initialize...")
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init_result = await session.initialize()
            print(f"✅ initialize 응답 수신")
            print(f"   server: {init_result.serverInfo.name} v{init_result.serverInfo.version}")
            print(f"   protocol: {init_result.protocolVersion}")

            tools_result = await session.list_tools()
            tool_names = {t.name for t in tools_result.tools}

            missing = EXPECTED_TOOLS - tool_names
            extra = tool_names - EXPECTED_TOOLS

            print(f"\n📋 등록된 도구: {len(tool_names)}개")
            for t in tools_result.tools:
                desc_preview = (t.description or "").split("\n")[0][:60]
                read_only_ok = "read-only" in (t.description or "").lower() or "조회 전용" in (t.description or "") or "읽기 전용" in (t.description or "")
                marker = "✅" if read_only_ok else "⚠️"
                print(f"   {marker} {t.name:<24} {desc_preview}")

            print()
            if missing:
                print(f"❌ 누락 도구: {sorted(missing)}")
                return 2
            if extra:
                print(f"⚠️ 예상 외 도구: {sorted(extra)}")

            print("✅ 6개 도구 모두 등록됨, MCP 프로토콜 핸드셰이크 정상")
            print()
            print("📌 이 검증은 Meta API 호출은 하지 않습니다.")
            print("   실제 도구 동작 검증은 Claude Desktop 또는 MCP Inspector로 진행하세요.")
            return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
