"""AI에게 노출되는 한국어 tool description.

각 description은:
- 도구가 무엇을 하는지 (1줄)
- read-only 명시
- 사용자 자연어 → 파라미터 매핑 가이드
- PM Seed 6개 워크플로우 예시
- 다른 도구와의 결정 위계 (tier1 → all → call_meta_api)
"""

METRIC_ALIAS_TABLE: dict[str, list[str]] = {
    # tier1 (10개)
    "impressions": ["노출수", "노출", "임프레션"],
    "reach": ["도달", "도달수"],
    "frequency": ["빈도", "프리퀀시"],
    "clicks": ["클릭수", "클릭"],
    "spend": ["지출", "광고비", "사용액"],
    "cpm": ["CPM", "1000회 노출당 비용"],
    "cpc": ["CPC", "클릭당 비용"],
    "ctr": ["CTR", "클릭률"],
    "purchase_roas": ["ROAS", "광고비 대비 구매 수익", "구매 ROAS"],
    "purchases": ["구매수", "전환수", "구매 건수"],
    # tier=all 추가 일부
    "video_3_sec_watched_actions": ["영상 3초 재생", "동영상 3초 시청"],
    "video_thruplay_watched_actions": ["완전 시청 (ThruPlay)"],
    "quality_ranking": ["품질 순위"],
    "engagement_rate_ranking": ["참여율 순위"],
    "outbound_clicks": ["외부 링크 클릭"],
    "landing_page_views": ["랜딩페이지 방문"],
}


_READONLY_NOTE = "이 MCP 서버는 read-only — 광고를 변경하거나 일시중지하는 등의 쓰기 작업은 절대 불가능합니다. Meta Ads Manager에서 직접 작업하라고 안내하세요."


DESCRIPTION_LIST_AD_ACCOUNTS = f"""사용자의 META_ACCESS_TOKEN으로 접근 가능한 모든 Meta 광고 계정 목록을 조회합니다.

언제 사용:
- 사용자가 광고 계정 이름(예: "메인 쇼핑몰", "서브 브랜드")을 언급했지만 account_id를 모를 때 — 이 도구로 후보 목록을 받아 이름으로 매칭해 account_id를 추출.
- 사용자가 어떤 계정을 분석해야 할지 명확하지 않을 때 — 단일 계정만 있으면 자동 진행, 복수면 사용자에게 어느 계정인지 되묻기.

반환: id (act_xxx 형식), account_id, name, currency, account_status, business_id, business_name, timezone_name.

{_READONLY_NOTE}
"""


DESCRIPTION_LIST_CAMPAIGNS = f"""특정 광고 계정의 캠페인 메타데이터(이름/상태/objective/예산)를 조회합니다. 메트릭은 포함하지 않습니다 — 메트릭이 필요하면 get_performance를 사용하세요.

파라미터:
- account_id (필수): act_xxx 또는 숫자.
- status (선택): 디폴트 "ACTIVE" (운영 중인 캠페인). "PAUSED", "ARCHIVED"로 좁히거나 None으로 전체.

언제 사용:
- 사용자가 특정 캠페인 이름을 언급했는데 ID가 필요할 때 (예: "봄세일 캠페인 성과 보여줘" → 이 도구로 ID 찾고 → get_performance에 campaign 필터 적용).
- "내 활성 캠페인이 뭐가 있어?"

{_READONLY_NOTE}
"""


DESCRIPTION_LIST_ADS = f"""특정 광고 계정의 광고(ad) 메타데이터(이름/상태/소속 캠페인/소속 adset/creative_id)를 조회합니다. 메트릭은 포함하지 않습니다.

파라미터:
- account_id (필수)
- campaign_id (선택): 특정 캠페인 안의 광고만 필터.
- status (선택): 디폴트 "ACTIVE".

언제 사용:
- 사용자가 광고 소재 분석을 원할 때 (예: "어떤 광고 카피가 가장 잘 나와?") — 이 도구로 ad_id 후보를 좁히고 → get_performance(level="ad")로 성과를 받고 → top performers의 get_creative_preview로 본문을 받음.

{_READONLY_NOTE}
"""


DESCRIPTION_GET_PERFORMANCE = f"""Meta Ads의 성과 메트릭을 조회하는 V1 핵심 도구입니다.

파라미터:
- account_id (필수): act_xxx 또는 숫자.
- level: "account" | "campaign" | "adset" | "ad" (디폴트 "campaign"). "전체 성과"는 account, "어떤 캠페인이"는 campaign, "어떤 광고소재가"는 ad.
- tier: "tier1" (디폴트, 10개 핵심 메트릭) | "all" (어트리뷰션 윈도우 분해 + 동영상 + 소재 품질 등 풀 셋). 사용자가 동영상 메트릭이나 클릭 후 1일 같은 어트리뷰션 분해를 명시 요구하면 tier="all".
- metrics (선택): 특정 메트릭만 받고 싶을 때 명시 (예: ["spend", "purchase_roas"]). tier 무시. 메트릭 한국어→snake_case 매핑은 아래 사전 참고.
- breakdown (선택): "age" | "gender" | "country" | "region" | "device_platform" | "publisher_platform" | "platform_position" | "impression_device". V1은 단일만 지원. age+gender 같은 동시 분해는 call_meta_api로.
- top_n (선택, 디폴트 10): 상위 N개 캠페인/광고만. breakdown 사용 시 sort_by 기준 상위 N entity의 모든 breakdown 행 반환.
- sort_by (선택): 정렬 기준 메트릭 (예: "purchase_roas", "ctr"). 미지정 시 "spend".
- date_preset (선택, 디폴트 "last_7d"): "yesterday" | "last_7d" | "last_14d" | "last_30d" | "this_month".
- since/until (선택): "YYYY-MM-DD" 형식. 둘 다 지정하면 date_preset 무시. 한쪽만 지정하면 에러.

핵심 워크플로우 6개:
1. 데일리 점검 — "어제 광고 어땠어? 이상한 캠페인?" → level="campaign", date_preset="yesterday".
2. 주간 회고 — "지난주 vs 그 전주" → 두 윈도우 호출(date_preset="last_7d", 그리고 since/until로 그 전주).
3. 광고소재 진단 — "어떤 광고 잘 나와?" → level="ad", top_n=5 → 상위 ad_id로 get_creative_preview.
4. 타겟팅 분해 — "연령별 어떤 캠페인 잘 됐어?" → breakdown="age".
5. 예산 ROI — "광고비 대비 매출" → metrics=["spend", "purchase_roas"].
6. 피로도 체크 — "frequency 높은 캠페인" → metrics=["frequency", "ctr", "cpm"], sort_by="frequency".

메트릭 한국어 매핑:
- ROAS / 광고비 대비 구매 수익 → purchase_roas
- 구매수 / 전환수 → purchases
- CPC / 클릭당 비용 → cpc
- CPM → cpm
- CTR / 클릭률 → ctr
- 광고비 / 지출 → spend
- 노출수 → impressions
- 도달 → reach
- 빈도 / frequency → frequency
- 영상 3초 재생 → video_3_sec_watched_actions (tier="all" 필요)
- 클릭 후 1일 / 7일 → tier="all"로 전환 후 응답에서 어트리뷰션 윈도우 분해

{_READONLY_NOTE}
"""


DESCRIPTION_GET_CREATIVE_PREVIEW = f"""특정 광고(ad)의 크리에이티브 본문(헤드라인/본문/CTA/이미지·동영상 URL)을 조회합니다.

파라미터:
- ad_id (필수)

반환은 creative_type에 따라 다름:
- IMAGE: image_url, headline, body, cta, link_url, thumbnail_url
- VIDEO: video_id, headline, body, cta, link_url, thumbnail_url
- CAROUSEL: cards (각 카드의 image_url/headline/body/link/cta 리스트)

언제 사용:
- get_performance(level="ad")로 top performer ad_id를 받은 후, "이 광고 카피 분석해줘" 같은 질문에 답하기 위해.
- "어떤 광고 소재가 가장 좋아?" → list_ads로 후보 → get_performance로 성과 → 이 도구로 본문.

{_READONLY_NOTE}
"""


DESCRIPTION_CALL_META_API = f"""Meta Graph API의 임의 GET endpoint를 직접 호출하는 escape hatch.

언제 사용:
- 다른 5개 도구로 커버되지 않는 edge case에만 사용. 묶음/엔티티 도구로 답이 가능하면 그쪽이 먼저.
- 예: adset 메타데이터(targeting spec, optimization goal), age+gender 같은 multi-breakdown, V1에서 미지원하는 endpoint.

파라미터:
- endpoint (필수): "/" 시작. 예: "/me", "/act_111/adsets", "/v22.0/campaign_id/insights". 외부 URL 차단.
- params (선택): query parameters dict. "method"/"_method"/"http_method" 키는 차단됨 (write 우회 시도 방지).

반환: Meta API 응답 raw JSON 그대로.

주의:
- HTTP GET만 가능. POST/PUT/DELETE/PATCH 시도 자체 차단됨.
- API 버전이 endpoint에 명시되지 않으면 MCP의 디폴트 v25.0 prefix 사용. /v22.0/... 식으로 직접 명시 가능.

{_READONLY_NOTE}
"""
