"""환경 변수 로딩 + V1 상수.

V1 상수는 PM Seed에서 굳혀진 결정 사항을 표현한다. 변경 시 plan 갱신 필요.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Tier1 디폴트 메트릭 — PM Seed Round 13 결정
TIER1_METRICS: tuple[str, ...] = (
    "impressions",
    "reach",
    "frequency",
    "clicks",
    "spend",
    "cpm",
    "cpc",
    "ctr",
    "purchase_roas",
    "purchases",  # actions 중 purchase 평탄화
)

# tier="all" 풀 필드셋 — Meta Marketing API v25 valid 필드만
# - landing_page_views는 actions[landing_page_view]에서 추출 (normalize.py 매핑)
# - link_clicks는 inline_link_clicks로 (Meta v25 rename)
# - video_3_sec_watched_actions는 v25 deprecated → video_30_sec_watched_actions로
TIER_ALL_EXTRA_METRICS: tuple[str, ...] = (
    "actions",
    "action_values",
    "cost_per_action_type",
    "video_play_actions",
    "video_30_sec_watched_actions",
    "video_thruplay_watched_actions",
    "video_avg_time_watched_actions",
    "video_p25_watched_actions",
    "video_p50_watched_actions",
    "video_p75_watched_actions",
    "video_p100_watched_actions",
    "quality_ranking",
    "engagement_rate_ranking",
    "conversion_rate_ranking",
    "outbound_clicks",
    "outbound_clicks_ctr",
    "inline_link_clicks",
    "cost_per_inline_link_click",
    "cost_per_outbound_click",
    "cost_per_thruplay",
)

# 어트리뷰션 윈도우 디폴트 — Meta 표준
ATTRIBUTION_WINDOWS_DEFAULT: tuple[str, ...] = ("1d_click", "7d_click")

# 페이지네이션 / top-N
PAGINATION_HARD_CAP: int = 200
TOP_N_DEFAULT: int = 10

# 날짜 preset enum 멤버
DATE_PRESETS: tuple[str, ...] = (
    "yesterday",
    "last_7d",
    "last_14d",
    "last_30d",
    "this_month",
)
DATE_PRESET_DEFAULT: str = "last_7d"

# Breakdown enum 멤버 — V1은 단일만
BREAKDOWNS_ALLOWED: tuple[str, ...] = (
    "age",
    "gender",
    "country",
    "region",
    "device_platform",
    "publisher_platform",
    "platform_position",
    "impression_device",
)


@dataclass(frozen=True)
class Config:
    access_token: str
    api_version: str
    base_url: str

    @property
    def graph_url(self) -> str:
        return f"{self.base_url}/{self.api_version}"


def load_config() -> Config:
    """환경 변수에서 설정을 로딩한다. .env 파일 자동 인식."""
    load_dotenv(override=False)
    token = os.environ.get("META_ACCESS_TOKEN")
    if not token:
        raise RuntimeError(
            "META_ACCESS_TOKEN 환경 변수가 필요합니다. "
            "MCP 호스트의 mcp config JSON `env` 필드 또는 .env 파일에 설정하세요."
        )
    api_version = os.environ.get("META_API_VERSION", "v25.0")
    base_url = os.environ.get("META_GRAPH_BASE_URL", "https://graph.facebook.com")
    return Config(access_token=token, api_version=api_version, base_url=base_url)
