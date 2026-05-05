"""tier='all' 400 원인 진단 — Meta v25에서 invalid한 필드 + 대체 후보 확인."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx


def load_token() -> str:
    cfg = json.loads((Path.home() / "Library/Application Support/Claude/claude_desktop_config.json").read_text())
    return cfg["mcpServers"]["kr-mkt-mcp"]["env"]["META_ACCESS_TOKEN"]


async def test_fields(token: str, fields: list[str]) -> tuple[bool, str]:
    url = "https://graph.facebook.com/v25.0/act_634718569695860/insights"
    params = {
        "level": "account",
        "fields": ",".join(["account_id"] + fields),
        "time_range": json.dumps({"since": "2026-05-04", "until": "2026-05-04"}),
        "action_attribution_windows": json.dumps(["1d_click", "7d_click"]),
    }
    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.get(url, params=params, headers={"Authorization": f"Bearer {token}"})
        if r.status_code == 200:
            return True, "OK"
        try:
            err = r.json().get("error", {})
            return False, f"{r.status_code}: {err.get('message', '')[:200]}"
        except Exception:
            return False, f"{r.status_code}: {r.text[:200]}"


async def main() -> int:
    token = load_token()

    # 의심 + 대체 후보 단일 테스트
    candidates = [
        "video_3_sec_watched_actions",
        "video_30_sec_watched_actions",
        "link_clicks",
        "inline_link_clicks",
        "outbound_clicks",
        "outbound_clicks_ctr",
        "landing_page_views",
        "actions",  # actions로부터 link_click/landing_page_view 추출 가능 검증
        "action_values",
        "video_play_actions",
        "video_thruplay_watched_actions",
        "video_avg_time_watched_actions",
        "video_p25_watched_actions",
        "cost_per_action_type",
        "cost_per_inline_link_click",
        "cost_per_outbound_click",
        "cost_per_thruplay",
    ]

    for c in candidates:
        ok, msg = await test_fields(token, ["impressions", c])
        flag = "✅" if ok else "❌"
        print(f"  {flag} {c:<45} {msg if not ok else ''}")

    print("\n--- 대체 후보 조합 테스트 ---")
    # link_click, landing_page_view는 actions[]에서 추출 가능한지 확인
    ok, msg = await test_fields(token, ["actions", "action_values"])
    print(f"  {'✅' if ok else '❌'} actions+action_values  {msg if not ok else ''}")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
