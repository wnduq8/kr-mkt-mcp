"""사용자 원래 시나리오 재현 — tier=all, level=account, yesterday, account_id=메디리즈."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main() -> int:
    cfg = json.loads((Path.home() / "Library/Application Support/Claude/claude_desktop_config.json").read_text())
    token = cfg["mcpServers"]["kr-mkt-mcp"]["env"]["META_ACCESS_TOKEN"]

    repo = Path(__file__).resolve().parents[1]
    params = StdioServerParameters(
        command=str(repo / ".venv" / "bin" / "python"),
        args=["-m", "kr_mkt_mcp.server"],
        env={"PYTHONPATH": str(repo / "src"), "META_ACCESS_TOKEN": token},
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("⏳ 사용자 시나리오: tier=all + level=account + yesterday\n")
            r = await session.call_tool(
                "get_performance",
                {
                    "account_id": "act_634718569695860",
                    "level": "account",
                    "date_preset": "yesterday",
                    "tier": "all",
                },
            )
            data = json.loads(r.content[0].text)
            rows = data.get("data", [])
            meta = data.get("meta", {})
            print(f"✅ status: 200, {len(rows)} row(s)")
            print(f"   metrics_used 개수: {len(meta.get('metrics_used', []))}")
            if rows:
                row = rows[0]
                print(f"\n📊 어제(2026-05-04) 메디리즈 계정 성과:")
                print(f"   spend: {row.get('spend')} 원")
                print(f"   impressions: {row.get('impressions')}")
                print(f"   clicks: {row.get('clicks')}")
                print(f"   ctr: {row.get('ctr')}")
                print(f"   cpc: {row.get('cpc')}")
                print(f"   cpm: {row.get('cpm')}")
                print(f"   purchases: {row.get('purchases')}")
                print(f"   purchase_roas (1d_click+7d_click 합산): {row.get('purchase_roas')}")
                print(f"\n📹 동영상/링크 메트릭:")
                print(f"   video_play_actions: {row.get('video_play_actions', 0)}")
                print(f"   video_30_sec_watched: {row.get('video_30_sec_watched_actions', 0)}")
                print(f"   video_thruplay: {row.get('video_thruplay_watched_actions', 0)}")
                print(f"   inline_link_clicks: {row.get('inline_link_clicks', 0)}")
                print(f"   outbound_clicks: {row.get('outbound_clicks', 0)}")
                print(f"   landing_page_views: {row.get('landing_page_views', 0)}")
            return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
