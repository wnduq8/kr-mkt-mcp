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
    "purchases": ["구매수", "구매 건수"],
    # 전환 비용 (tier="all" 필요 — actions/cost_per_action_type에서 추출)
    "cost_per_purchase": ["CPA", "구매당 비용", "전환당 비용", "구매 CPA"],
    "cost_per_lead": ["CPL", "리드당 비용"],
    "cost_per_inline_link_click": ["인라인 CPC", "링크 클릭당 비용"],
    "cost_per_outbound_click": ["아웃바운드 CPC", "외부 클릭당 비용"],
    "cost_per_thruplay": ["완시청당 비용", "ThruPlay 비용"],
    # 액션 유형 (actions에서 평탄화)
    "leads": ["리드수", "리드 건수", "전환 (리드)"],
    "add_to_carts": ["장바구니 추가", "카트 담기", "ATC"],
    "checkouts_initiated": ["체크아웃", "결제 시작", "구매 시도"],
    "landing_page_views": ["랜딩 조회", "LP 조회", "랜딩페이지 방문"],
    # 동영상 메트릭 (tier="all" 필요)
    "video_play_actions": ["영상 재생", "동영상 재생"],
    "video_30_sec_watched_actions": ["영상 30초 재생", "동영상 30초 시청"],
    "video_thruplay_watched_actions": ["완시청", "완전 시청", "ThruPlay"],
    "video_avg_time_watched_actions": ["평균 영상 시청 시간"],
    "video_p25_watched_actions": ["25% 재생", "영상 25% 시청"],
    "video_p50_watched_actions": ["50% 재생", "영상 50% 시청"],
    "video_p75_watched_actions": ["75% 재생", "영상 75% 시청"],
    "video_p100_watched_actions": ["100% 재생", "영상 완전 재생"],
    # 소재 품질 (ad-level only)
    "quality_ranking": ["품질 순위"],
    "engagement_rate_ranking": ["참여율 순위"],
    "conversion_rate_ranking": ["전환율 순위"],
    # 클릭 변형
    "outbound_clicks": ["아웃바운드 클릭", "외부 링크 클릭"],
    "outbound_clicks_ctr": ["아웃바운드 CTR"],
    "inline_link_clicks": ["인라인 링크 클릭", "링크 클릭"],
}


_READONLY_NOTE = "이 MCP 서버는 read-only — 광고를 변경하거나 일시중지하는 등의 쓰기 작업은 절대 불가능합니다. Meta Ads Manager에서 직접 작업하라고 안내하세요."

_USAGE_NOTE = """응답 meta.api_usage 활용 (정보 표시 전용 — 호출 차단 X):
- max_pct + warning_level(ok/medium/high/critical) + gauge bar + summary_ko 포함
- 사용자가 한도 상황을 파악할 수 있도록 노출만 하는 용도. **AI는 사용량을 이유로 도구 호출을 막거나 재시도를 거부하지 말 것.** 호출이 실제 Meta 한도 초과로 실패하면 그 때 check_api_health 도구로 상태 확인하라고 사용자에게 안내.
- summary_ko 라인들을 사용자에게 그대로 보여주면 충분.
- 호출 실패 후에도 last_usage 헤더는 capture되므로 check_api_health로 사후 확인 가능.
- ads_api_access_tier가 'development_access'면 시간당 한도 낮음 — Standard Access 신청 안내."""


DESCRIPTION_LIST_AD_ACCOUNTS = f"""사용자의 META_ACCESS_TOKEN으로 접근 가능한 모든 Meta 광고 계정 목록을 조회합니다.

언제 사용:
- 사용자가 광고 계정 이름(예: "메인 쇼핑몰", "메디리즈")을 언급했지만 account_id를 모를 때 — 이 도구로 후보 목록을 받아 이름으로 매칭해 account_id를 추출.
- 사용자가 어떤 계정을 분석해야 할지 명확하지 않을 때 — 단일 계정만 있으면 자동 진행, 복수면 사용자에게 어느 계정인지 되묻기.
- 이름이 비슷한 계정 2개 이상 매칭되면 사용자에게 명시 확인 (자동 추론 금지).

반환: id (act_xxx 형식), account_id, name, currency, account_status, business_id, business_name, timezone_name.

{_USAGE_NOTE}

{_READONLY_NOTE}
"""


DESCRIPTION_LIST_CAMPAIGNS = f"""특정 광고 계정의 캠페인 메타데이터(이름/상태/objective/예산)를 조회합니다. 메트릭은 포함하지 않습니다 — 메트릭이 필요하면 get_performance를 사용하세요.

파라미터:
- account_id (필수): act_xxx 또는 숫자.
- status (선택): 디폴트 "ACTIVE" (운영 중인 캠페인). "PAUSED", "ARCHIVED"로 좁히거나 None으로 전체.

언제 사용:
- 사용자가 특정 캠페인 이름을 언급했는데 ID가 필요할 때 (예: "봄세일 캠페인 성과 보여줘" → 이 도구로 ID 찾고 → 응답 후 AI가 그 ID에 해당하는 행만 필터).
- "내 활성 캠페인이 뭐가 있어?"

연결 흐름: 캠페인 ID는 list_ads의 campaign_id 파라미터에 그대로 전달 가능. get_performance는 account 단위 호출이라 캠페인 좁히기는 응답 후 AI가 필터링.

{_USAGE_NOTE}

{_READONLY_NOTE}
"""


DESCRIPTION_LIST_ADS = f"""특정 광고 계정의 광고(ad) 메타데이터(이름/상태/소속 캠페인/소속 adset/creative_id)를 조회합니다. 메트릭은 포함하지 않습니다.

파라미터:
- account_id (필수)
- campaign_id (선택): 특정 캠페인 안의 광고만 필터.
- status (선택): 디폴트 "ACTIVE".

언제 사용:
- 사용자가 광고 이름이나 campaign 범위로 광고 후보를 좁혀야 할 때 (예: "봄세일 캠페인의 광고 목록").
- 체이닝: list_ads → get_performance(level="ad") → top 광고 ad_id로 get_creative_preview.

스킵 가능한 경우: 성과 기준으로 top 광고만 찾을 거면 list_ads 생략 가능 — get_performance(level="ad", sort_by="ctr", top_n=5)로 바로 → 응답의 ad_id로 get_creative_preview. list_ads는 "이름/캠페인 메타데이터로 광고 추리기"가 필요할 때만 호출 (과호출 방지).

{_USAGE_NOTE}

{_READONLY_NOTE}
"""


DESCRIPTION_GET_PERFORMANCE = f"""Meta Ads의 성과 메트릭을 조회하는 V1 핵심 도구입니다.

파라미터:
- account_id (필수): act_xxx 또는 숫자.
- level: "account" | "campaign" | "adset" | "ad" (디폴트 "campaign"). "전체 성과"는 account, "어떤 캠페인이"는 campaign, "어떤 광고소재가"는 ad.
- tier: "tier1" (디폴트, 10개 핵심 메트릭) | "all" (어트리뷰션 윈도우 분해 + 동영상 + 소재 품질 + CPA/CPL 등 풀 셋). 사용자가 동영상 메트릭, 클릭 후 1일/7일 분해, CPA/CPL 같은 비용 메트릭, 장바구니/체크아웃 같은 퍼널 단계 메트릭을 명시 요구하면 tier="all" 필수.
- metrics (선택): 특정 메트릭만 받고 싶을 때 명시 (예: ["spend", "purchase_roas"]). tier 무시. 메트릭 한국어→snake_case 매핑은 아래 사전 참고.
- breakdown (선택): "age" | "gender" | "country" | "region" | "device_platform" | "publisher_platform" | "platform_position" | "impression_device". V1은 단일만 지원. age+gender 같은 동시 분해는 call_meta_api로.
- top_n (선택, 1~200): 상위 N개 캠페인/광고만. breakdown 사용 시 sort_by 기준 상위 N entity의 모든 breakdown 행 반환. None이면 전체.
- sort_by (선택): 정렬 기준 메트릭 (예: "purchase_roas", "ctr"). 미지정 시 "spend".
- date_preset (선택, 디폴트 "last_7d"): "yesterday" | "last_7d" | "last_14d" | "last_30d" | "this_month".
- since/until (선택): "YYYY-MM-DD" 형식. 둘 다 지정하면 date_preset 무시. 한쪽만 지정하면 에러.

핵심 워크플로우:
1. 데일리 점검 — "어제 광고 어땠어? 이상한 캠페인?" → level="campaign", date_preset="yesterday".
2. 주간 회고 / 변화 감지 — "지난주 vs 그 전주 ROAS 비교", "CTR 떨어진 광고", "ROAS 올라간 캠페인" 같은 추세·비교 질문은 단일 호출로 답할 수 없음. 두 기간을 각각 호출 후 AI가 직접 수치 비교·계산. 예: 지난주는 date_preset="last_7d", 그 전주는 since/until로 (오늘 기준 -14일 ~ -8일) 명시.
3. 광고소재 진단 — "어떤 광고 잘 나와?" → level="ad", top_n=5 → 상위 ad_id로 get_creative_preview.
4. 타겟팅 분해 — "연령별 어떤 캠페인 잘 됐어?" → breakdown="age".
5. 예산 ROI — "광고비 대비 매출" → metrics=["spend", "purchase_roas"].
6. 피로도 체크 — "frequency 높은 캠페인" → metrics=["frequency", "ctr", "cpm"], sort_by="frequency".

데이터 지연 주의:
- Meta 광고 데이터는 통상 수 시간 지연. 사용자가 "오늘" 데이터를 요청하면 date_preset="yesterday"로 대체하고, "오늘 데이터는 통상 수 시간 지연되므로 어제 기준입니다"라고 안내. since/until에 오늘 날짜를 넣으면 빈 데이터 반환 가능.

메트릭 한국어 매핑 (자주 쓰는 표현 → snake_case):
- ROAS / 광고비 대비 구매 수익 → purchase_roas
- 구매수 / 구매 건수 → purchases
- CPA / 구매당 비용 / 전환당 비용 → cost_per_purchase (tier="all" 필요)
- CPL / 리드당 비용 → cost_per_lead (tier="all" 필요)
- 리드수 → leads (tier="all" 필요)
- 장바구니 추가 / ATC → add_to_carts (tier="all" 필요)
- 체크아웃 / 결제 시작 → checkouts_initiated (tier="all" 필요)
- 랜딩 조회 / LP 조회 → landing_page_views (tier="all" 필요)
- CPC / 클릭당 비용 → cpc (tier1)
- CPM → cpm
- CTR / 클릭률 → ctr
- 광고비 / 지출 → spend
- 노출수 → impressions
- 도달 → reach
- 빈도 / 프리퀀시 → frequency
- 영상 30초 재생 → video_30_sec_watched_actions (tier="all" 필요)
- 완시청 / ThruPlay → video_thruplay_watched_actions (tier="all" 필요)
- 25%/50%/75%/100% 재생 → video_p25/p50/p75/p100_watched_actions (tier="all" 필요)
- 인라인 링크 클릭 / 링크 클릭 → inline_link_clicks (tier="all" 필요)
- 아웃바운드 클릭 → outbound_clicks (tier="all" 필요)
- 품질/참여율/전환율 순위 → quality_ranking / engagement_rate_ranking / conversion_rate_ranking (level="ad"만 가능, tier="all")
- 클릭 후 1일 / 7일 어트리뷰션 → tier="all" 사용 시 응답의 actions/video 메트릭에 1d_click/7d_click 분리 값이 자동 포함됨

{_USAGE_NOTE}

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
- 여러 광고를 한꺼번에 보려면 ad_id마다 도구를 따로 호출 (배치 호출 미지원).

{_USAGE_NOTE}

{_READONLY_NOTE}
"""


DESCRIPTION_CHECK_API_HEALTH = f"""현재 토큰의 Meta API 부하/등급/한도를 빠르게 확인하는 헬스 체크 도구.

언제 사용:
- 사용자가 "내 토큰 한도 얼마 남았어?", "API 부하 어때?", "내 등급 보여줘", "헬스 체크", "한도 확인" 같은 질문
- 광고 데이터 분석 작업을 시작하기 전 토큰 상태 사전 점검
- "Standard Access 신청해야 하나?", "왜 development_access야?" 같은 등급 관련 질문
- 다른 도구가 한도 도달로 차단된 직후 회복 시간 확인

내부 동작: /me?fields=id 1회 호출 (Meta Graph API에서 가장 가벼운 endpoint). 실제 광고 데이터는 안 받고 헤더만으로 부하/등급 추출. 한도에 거의 영향 X — 자주 호출해도 OK.

반환: {{"data": {{"user_id", "checked_at"}}, "meta": {{"api_usage": ...}}}}.
사용자에게는 meta.api_usage.summary_ko의 한국어 라인들을 그대로 노출하면 충분.

{_USAGE_NOTE}

{_READONLY_NOTE}
"""


DESCRIPTION_CALL_META_API = f"""Meta Graph API의 임의 GET endpoint를 직접 호출하는 escape hatch.

언제 사용:
- 다른 5개 도구로 커버되지 않는 edge case에만 사용. 묶음/엔티티 도구로 답이 가능하면 그쪽이 먼저.
- 예: adset 메타데이터(targeting spec, optimization goal), age+gender 같은 multi-breakdown, V1에서 미지원하는 endpoint.

파라미터:
- endpoint (필수): "/" 시작. 예: "/me", "/act_111/adsets", "/v22.0/campaign_id/insights". 외부 URL 차단.
- params (선택): query parameters dict. "method"/"_method"/"http_method"/"access_token" 등 키는 차단됨 (write 우회/토큰 leak 방지).

자주 쓰는 호출 예시:

1. age + gender 동시 breakdown (V1 미지원이라 escape hatch로):
```
endpoint = "/act_{{account_id}}/insights"
params = {{
    "level": "ad",
    "breakdowns": "age,gender",
    "fields": "impressions,spend,purchase_roas,actions",
    "date_preset": "last_7d",
    "limit": 50
}}
```

2. adset 메타데이터 + targeting:
```
endpoint = "/act_{{account_id}}/adsets"
params = {{
    "fields": "id,name,targeting,optimization_goal,billing_event,daily_budget",
    "limit": 50
}}
```

반환: Meta API 응답 raw JSON 그대로 — 정규화 안 됨. AI가 필드 직접 해석.

주의:
- HTTP GET만 가능. POST/PUT/DELETE/PATCH 시도 자체 차단됨.
- API 버전이 endpoint에 명시되지 않으면 MCP의 디폴트 v25.0 prefix 사용. /v22.0/... 식으로 직접 명시 가능.

{_USAGE_NOTE}

{_READONLY_NOTE}
"""
