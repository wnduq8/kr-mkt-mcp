"""실 Meta API 통합 테스트 — claude_desktop_config.json의 token으로 6 도구 호출.

⚠️ 토큰은 절대 stdout/stderr에 출력하지 않음.
- 파일에서 직접 읽어 subprocess env로 통과
- 모든 출력은 token 문자열을 [REDACTED]로 치환

사용:
    .venv/bin/python scripts/integration_test.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


def load_token_from_claude_config() -> str | None:
    cfg_path = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    if not cfg_path.exists():
        return None
    try:
        cfg = json.loads(cfg_path.read_text())
        return cfg["mcpServers"]["kr-mkt-mcp"]["env"]["META_ACCESS_TOKEN"]
    except (KeyError, json.JSONDecodeError):
        return None


def redact(text: str, token: str) -> str:
    """token 문자열을 [REDACTED]로 치환."""
    if not token or not text:
        return text
    return text.replace(token, "[REDACTED]")


def parse_tool_result(result: Any) -> dict:
    """CallToolResult.content[0].text(JSON) → dict."""
    if not result.content:
        return {}
    text = result.content[0].text
    return json.loads(text)


async def main() -> int:
    token = load_token_from_claude_config()
    if not token:
        print("❌ claude_desktop_config.json에서 META_ACCESS_TOKEN을 찾을 수 없음")
        return 1
    if token.startswith("REPLACE_") or token == "여기에_발급한_토큰_붙여넣기":
        print("❌ token이 placeholder. 실 토큰으로 교체 후 재시도")
        return 1

    repo_root = Path(__file__).resolve().parents[1]
    params = StdioServerParameters(
        command=str(repo_root / ".venv" / "bin" / "python"),
        args=["-m", "kr_mkt_mcp.server"],
        env={
            "PYTHONPATH": str(repo_root / "src"),
            "META_ACCESS_TOKEN": token,
        },
    )

    print("⏳ 서버 기동 + initialize...")
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ initialize 통과\n")

            # ===== 1. list_ad_accounts =====
            print("[1/6] list_ad_accounts")
            try:
                r = await session.call_tool("list_ad_accounts", {})
                data = parse_tool_result(r)
                accounts = data.get("data", [])
                print(f"   ✅ {len(accounts)} 광고 계정 발견")
                for a in accounts[:5]:
                    name = a.get("name", "?")
                    currency = a.get("currency", "?")
                    status = a.get("account_status", "?")
                    print(f"      • {a.get('id')}  {name}  [{currency}, status={status}]")
            except Exception as e:
                print(f"   ❌ {redact(str(e), token)[:300]}")
                return 2

            if not accounts:
                print("\n⚠️ 광고 계정 0개 — 시스템 사용자에 광고 계정 권한 미할당 추정")
                return 3

            account_id = accounts[0]["id"]
            print(f"\n   → 이후 테스트 대상 account_id: {account_id}\n")

            # ===== 2. list_campaigns =====
            print("[2/6] list_campaigns")
            try:
                r = await session.call_tool("list_campaigns", {"account_id": account_id})
                data = parse_tool_result(r)
                campaigns = data.get("data", [])
                meta = data.get("meta", {})
                print(f"   ✅ {len(campaigns)} 활성 캠페인 (truncated={meta.get('truncated')})")
                for c in campaigns[:5]:
                    obj = c.get("objective", "?")
                    daily = c.get("daily_budget")
                    life = c.get("lifetime_budget")
                    budget = f"daily={daily}" if daily else f"lifetime={life}" if life else "no-budget"
                    print(f"      • {c.get('id')}  {c.get('name')}  [{obj}, {budget}]")
            except Exception as e:
                print(f"   ❌ {redact(str(e), token)[:300]}")
                campaigns = []

            # ===== 3. get_performance (account level) =====
            print("\n[3/6] get_performance(level=account, last_7d)")
            try:
                r = await session.call_tool(
                    "get_performance",
                    {"account_id": account_id, "level": "account", "date_preset": "last_7d"},
                )
                data = parse_tool_result(r)
                rows = data.get("data", [])
                meta = data.get("meta", {})
                print(f"   ✅ {len(rows)} row, date_range={meta.get('date_range')}")
                for row in rows[:1]:
                    print(f"      spend={row.get('spend')}  impressions={row.get('impressions')}")
                    print(f"      clicks={row.get('clicks')}  ctr={row.get('ctr')}  purchase_roas={row.get('purchase_roas')}")
                    print(f"      purchases={row.get('purchases')}")
            except Exception as e:
                print(f"   ❌ {redact(str(e), token)[:300]}")

            # ===== 4. get_performance (campaign + breakdown=age) =====
            print("\n[4/6] get_performance(level=campaign, breakdown=age, top_n=3)")
            try:
                r = await session.call_tool(
                    "get_performance",
                    {
                        "account_id": account_id,
                        "level": "campaign",
                        "breakdown": "age",
                        "top_n": 3,
                        "date_preset": "last_30d",
                    },
                )
                data = parse_tool_result(r)
                rows = data.get("data", [])
                ages = sorted({r.get("age") for r in rows if r.get("age")})
                campaigns_in_result = sorted({r.get("campaign_id") for r in rows if r.get("campaign_id")})
                print(f"   ✅ {len(rows)} rows, {len(campaigns_in_result)} 캠페인 × {len(ages)} 연령대")
                print(f"      ages: {ages}")
            except Exception as e:
                print(f"   ❌ {redact(str(e), token)[:300]}")

            # ===== 5. list_ads + get_creative_preview =====
            print("\n[5/6] list_ads + get_creative_preview")
            try:
                r = await session.call_tool("list_ads", {"account_id": account_id})
                data = parse_tool_result(r)
                ads = data.get("data", [])
                print(f"   ✅ list_ads: {len(ads)} 광고")
                if ads:
                    ad_id = ads[0]["id"]
                    print(f"      첫 광고 {ad_id} ({ads[0].get('name')}) — get_creative_preview...")
                    r2 = await session.call_tool("get_creative_preview", {"ad_id": ad_id})
                    cdata = parse_tool_result(r2)
                    ctype = cdata.get("creative_type")
                    headline = (cdata.get("headline") or "")[:50]
                    cta = cdata.get("cta")
                    print(f"      ✅ creative_type={ctype}  cta={cta}  headline={headline!r}")
                else:
                    print("      (광고 0개 — 시연 스킵)")
            except Exception as e:
                print(f"   ❌ {redact(str(e), token)[:300]}")

            # ===== 6. call_meta_api (escape hatch) =====
            print("\n[6/6] call_meta_api(/me)")
            try:
                r = await session.call_tool(
                    "call_meta_api",
                    {"endpoint": "/me", "params": {"fields": "id,name"}},
                )
                data = parse_tool_result(r)
                print(f"   ✅ user_id={data.get('id')}  name={data.get('name')}")
            except Exception as e:
                print(f"   ❌ {redact(str(e), token)[:300]}")

            print("\n✅ 통합 테스트 완료")
            return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
