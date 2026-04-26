# Meta Marketing API v25 조사 보고서 — `kr-mkt-mcp` 설계용

조사일: 2026-04-26 / 기준 버전: Graph API v25.0 / Marketing API v25.0

> 이 문서는 본 MCP 서버 구현 시 1차 참고서. 변경 추적이 잦은 영역이므로 v26 출시 시 재검토 필요.

---

## 1. Insights 필드 전체 목록 (v25)

### 1-1. 기본 비용/노출 (모든 광고 객체에 공통)

| 필드 | 설명 | 한국어 매핑 |
|---|---|---|
| `impressions` | 노출 횟수 | 노출수 |
| `reach` | 도달한 고유 사용자 수 | 도달수 |
| `frequency` | impressions / reach | 빈도 |
| `clicks` | 모든 클릭(반응 포함) | 전체클릭수 |
| `unique_clicks` | 고유 클릭 사용자 | 고유클릭수 |
| `ctr` | clicks / impressions | CTR |
| `unique_ctr` | unique_clicks / reach | 고유CTR |
| `cpc` | spend / clicks | CPC |
| `cpm` | spend / impressions × 1000 | CPM |
| `cpp` | spend / reach × 1000 | 도달당비용(CPP) |
| `spend` | 지출액 (계정 통화) | 지출액 |
| `account_currency` | 계정 통화 코드 | 계정통화 |
| 식별자: `account_id`, `account_name`, `campaign_id`, `campaign_name`, `adset_id`, `adset_name`, `ad_id`, `ad_name` | — | — |

### 1-2. 인게이지먼트(링크 클릭 / 인라인)

| 필드 | 설명 | 한국어 매핑 |
|---|---|---|
| `inline_link_clicks` | 광고 내 링크 클릭만 (반응 제외) | 인라인링크클릭수 |
| `inline_link_click_ctr` | 인라인 링크 CTR | 인라인링크CTR |
| `inline_post_engagement` | 인라인 포스트 참여 | 인라인참여수 |
| `outbound_clicks` | 외부 도메인으로 나가는 클릭 | 외부이동클릭수 |
| `unique_outbound_clicks` | 고유 외부이동 사용자 | 고유외부이동클릭수 |
| `outbound_clicks_ctr`, `unique_outbound_clicks_ctr` | 외부이동 CTR | 외부이동CTR |
| `instant_experience_clicks_to_open` / `_to_start` | 인스턴트 경험 클릭 | 인스턴트경험클릭 |

### 1-3. 전환/액션 (자세한 액션 타입은 §2 참고)

| 필드 | 설명 | 한국어 매핑 |
|---|---|---|
| `actions` | action_type별 합계 배열 | 액션수(타입별) |
| `unique_actions` | 액션의 고유 사용자 수 | 고유액션수 |
| `action_values` | action_type별 가치(원/달러) 배열 | 액션가치(타입별) |
| `cost_per_action_type` | action_type별 단가 | 액션당비용(타입별) |
| `cost_per_unique_action_type` | 일부 항목 2024-10 제거됨 | (사용지양) |
| `conversions` | 전환 수 (action_type별 배열) | 전환수 |
| `conversion_values` | 전환 가치 배열 | 전환가치 |
| `cost_per_conversion` | 전환당 비용 | 전환당비용 |
| `purchase_roas` | 구매가치 / spend, action_type별 | 구매ROAS |
| `mobile_app_purchase_roas` | 앱 구매 ROAS | 앱구매ROAS |
| `cost_per_thruplay` | THRUPLAY당 비용 | THRUPLAY당비용 |
| `cost_per_15_sec_video_view` | 15초시청당 비용 | 15초시청당비용 |
| `objective_results`, `results` | 캠페인 목표에 따른 결과 | 캠페인결과수 |
| `conversion_leads`, `conversion_lead_rate` | 리드 전환 | 리드전환·전환율 |

### 1-4. 진단 신호(Quality Rankings) — 광고(Ad) 레벨에서만

| 필드 | 값 | 한국어 매핑 |
|---|---|---|
| `quality_ranking` | ABOVE_AVERAGE / AVERAGE / BELOW_AVERAGE_{35,20,10} / UNKNOWN | 광고품질순위 |
| `engagement_rate_ranking` | 동일 enum | 참여율순위 |
| `conversion_rate_ranking` | 동일 enum | 전환율순위 |
| `estimated_ad_recall_rate` | 추정 광고 회상률(%) | 추정광고회상률 |
| `estimated_ad_recallers` | 추정 회상 사용자 수 | 추정회상자수 |
| `cost_per_estimated_ad_recallers` | 회상자 1명당 비용 | 회상자당비용 |

### 1-5. Attribution Windows (v25 기준)

- **유효:** `1d_click`, `7d_click`, `28d_click`, `1d_view`, `1d_ev`(engaged view), `dda`(데이터 기반), `default`, `skan_click`, `skan_view`, `skan_*_postback`
- **제거:** `7d_view`, `28d_view` — **2026-01-12부로 Ads Insights API 미지원** (2025-10-13 공지)
- **사용:** `action_attribution_windows=['1d_click','7d_click']` (배열)

출처:
- https://developers.facebook.com/docs/marketing-api/insights/
- https://developers.facebook.com/docs/marketing-api/reference/adgroup/insights/
- https://github.com/facebook/facebook-python-business-sdk/blob/main/facebook_business/adobjects/adsinsights.py
- https://developers.facebook.com/blog/post/2025/10/16/ads-insights-api-metric-availability-updates/

---

## 2. Action Types (커머스 중심)

`actions`/`action_values`/`cost_per_action_type` 응답은 `[{action_type, value}, ...]` 형식 + attribution window 키 동봉.

| action_type | 의미 | 한국 마케터 표현 |
|---|---|---|
| `purchase` | 구매(범용) | 구매 |
| `offsite_conversion.fb_pixel_purchase` | 픽셀 기반 웹 구매 | 웹구매(픽셀) |
| `omni_purchase` | 픽셀+앱+오프라인 통합 구매 | 통합구매 |
| `app_custom_event.fb_mobile_purchase` | 앱 SDK 구매 | 앱구매 |
| `onsite_conversion.purchase` | 메타 내부(쇼핑/Shop) 구매 | 메타내구매 |
| `offsite_conversion.fb_pixel_add_to_cart` / `omni_add_to_cart` | 장바구니 | 장바구니담기 |
| `offsite_conversion.fb_pixel_initiate_checkout` / `omni_initiated_checkout` | 결제 시작 | 결제시작 |
| `offsite_conversion.fb_pixel_add_payment_info` | 결제정보 추가 | 결제정보입력 |
| `offsite_conversion.fb_pixel_view_content` / `omni_view_content` | 상세 페이지 조회 | 상품조회 |
| `offsite_conversion.fb_pixel_search` / `omni_search` | 검색 | 검색 |
| `offsite_conversion.fb_pixel_lead` / `lead` / `leadgen_grouped` | 리드 | 리드 |
| `offsite_conversion.fb_pixel_complete_registration` / `omni_complete_registration` | 회원가입 | 회원가입 |
| `subscribe` / `start_trial` / `recurring_subscription_payment` | 구독 시작/체험/반복결제 | 구독·체험·반복결제 |
| `cancel_subscription` | 구독 취소 | 구독취소 |
| `landing_page_view` | 랜딩 페이지 뷰(완전 로드) | 랜딩뷰 |
| `link_click` | 링크 클릭 | 링크클릭 |
| `video_view` | 동영상 시청(범용) | 동영상조회 |
| `post_engagement`, `page_engagement`, `post_reaction`, `comment`, `like`, `post`, `photo_view` | 참여 항목 | 참여 |
| `onsite_conversion.messaging_conversation_started_7d` | 메시지 대화 시작 | 메시지전환 |
| `onsite_conversion.lead_grouped` | 즉시양식 리드 | 즉시양식리드 |
| `offsite_conversion.custom.<id>` | 커스텀 전환 | 커스텀전환 |

**ROAS 계산:**
- `purchase_roas` = sum(`action_values` where action_type=purchase) / `spend` — 메타가 직접 제공
- 자체 계산 시 `omni_purchase`의 `action_values` 권장 (앱+웹+오프라인 통합)

출처: https://developers.facebook.com/docs/marketing-api/reference/ads-action-stats/

---

## 3. 동영상 메트릭 상세 (v25)

### 3-1. 정확한 필드명

| 필드 | 정의 | 한국어 매핑 |
|---|---|---|
| `video_play_actions` | 재생 시작(자동/수동) | 재생수 |
| `video_continuous_2_sec_watched_actions` | **연속 2초 시청** = 현재 표준 "3초 시청" | 3초시청수 |
| `video_15_sec_watched_actions` | 15초 시청 | 15초시청수 |
| `video_30_sec_watched_actions` | **deprecated** (2024-10 정리) | (사용지양) |
| `video_p25_watched_actions` / `_p50_` / `_p75_` / `_p95_` / `_p100_` | 25/50/75/95/100% 도달 | 25·50·75·95·100%시청수 |
| `video_avg_time_watched_actions` | 평균 시청 시간(초) | 평균시청시간 |
| `video_thruplay_watched_actions` | THRUPLAY: 15초 이상 또는 끝까지 | THRUPLAY수 |
| `video_play_curve_actions` | 1초 단위 시청 곡선(0-60s 배열) | 시청곡선 |
| `video_play_retention_0_to_15s_actions` | 0–15s 보존 곡선 | 초기보존(0–15s) |
| `video_play_retention_20_to_60s_actions` | 20–60s 보존 곡선 | 후기보존(20–60s) |
| `video_time_watched_actions` | 총 시청 초수 | 총시청초 |
| `cost_per_thruplay`, `cost_per_15_sec_video_view` | 단가 | THRUPLAY/15초당비용 |

### 3-2. 3초 시청 측정 방식

- 2024년 정리 후 Meta는 "3-second video views"를 **연속 2초** 시청으로 정의 — 필드명 `video_continuous_2_sec_watched_actions`. 화면 75% 이상 표시 + 2초 연속.
- 옛 `video_3_sec_watched_actions` deprecated.

### 3-3. 훅레이트 / 홀드레이트 (Meta 공식 정의 부재)

Meta API에 `hook_rate` 필드 **없음**. 업계 표준 공식 (MCP에서 산식 명시 권장):

- **Hook Rate (%)** = `video_continuous_2_sec_watched_actions` / `impressions` × 100
- **Hold Rate (%)** = `video_15_sec_watched_actions` / `video_continuous_2_sec_watched_actions` × 100
- **Play Rate (%)** = `video_play_actions` / `impressions` × 100
- **3초 이탈률** = 100 − Hook Rate
- **THRUPLAY율** = `video_thruplay_watched_actions` / `impressions` × 100
- **시청완료율** = `video_p100_watched_actions` / `video_play_actions` × 100

### 3-4. Reels 전용 필드

- 광고 동영상(`/insights`)에는 **Reels 전용 필드 없음**. `platform_position` breakdown으로 `feed`, `instagram_reels`, `facebook_reels`, `instagram_stories` 등 분리 조회.
- 오가닉 Reels는 별도 엔드포인트 — V1 범위 외.

### 3-5. Breakdown 제약

- `video_p25/50/75/95/100_watched_actions`: **region** breakdown 미지원
- `video_thruplay_watched_actions`, `estimated_ad_recall_rate`: **dma** breakdown 미지원

출처:
- https://developers.facebook.com/docs/marketing-api/reference/adgroup/insights/
- https://developers.facebook.com/docs/marketing-api/insights/breakdowns/

---

## 4. Breakdowns 매트릭스

### 4-1. 사용 가능 값 (v25 SDK enum)

**인구통계:** `age`, `gender`, `country`, `region`, `dma`

**플랫폼/디바이스:** `publisher_platform` (facebook/instagram/audience_network/messenger), `platform_position` (feed/instagram_reels/facebook_reels/instagram_stories/facebook_stories/instream_video/marketplace/search/...), `device_platform` (mobile/desktop), `impression_device` (iphone/android_smartphone/desktop/...)

**시간:** `hourly_stats_aggregated_by_advertiser_time_zone`, `hourly_stats_aggregated_by_audience_time_zone`

**프로덕트/카탈로그(DPA):** `product_id`, `product_brand`, `product_category`, `product_custom_labels` — V1 제외

**크리에이티브 자산(Advantage+):** `creative_relaxation_asset_type` 외

**전환:** `conversion_destination`, `landing_destination`, `signal_source_bucket`, `app_id`, `placement`

**액션 브레이크다운(`action_breakdowns`):** `action_type`, `action_target_id`, `action_destination`, `action_device`, `action_carousel_card_id`, `action_carousel_card_name`, `action_canvas_component_name`, `action_video_type`, `action_video_sound`, `action_reaction`, `standard_event_content_type`

### 4-2. 호환 규칙

- 한 번에 **breakdowns 최대 2개** 권장 (3개 이상 invalid 빈번)
- 알려진 invalid: `(action_type, publisher_platform, region)` 동시 사용 불가
- `region` 미지원: `video_p25/50/75/95/100_watched_actions`
- `dma` 미지원: `video_thruplay_watched_actions`, `estimated_ad_recall_rate`
- 오프-페이스북 전환 + 인구통계 breakdown 결합 시 일부 metric 누락
- **MCP에서는 화이트리스트 방식 강제** — 사전 정의한 안전한 조합만 노출

출처: https://developers.facebook.com/docs/marketing-api/insights/breakdowns/

---

## 5. 크리에이티브 객체 (`/adcreatives`)

### 5-1. 핵심 필드 (v25)

- 식별: `id`, `name`, `account_id`, `actor_id`, `status` (ACTIVE/IN_PROCESS/WITH_ISSUES/DELETED), `effective_object_story_id`
- 콘텐츠: `body`, `title`, `image_hash`, `image_url`, `video_id`, `thumbnail_url`, `link_url`
- CTA: `call_to_action_type` (SHOP_NOW/LEARN_MORE/SIGN_UP/INSTALL_APP/BOOK_TRAVEL/...) , `call_to_action`(객체)
- 게시물 참조: `object_story_id`, `object_story_spec`, `object_type`
- 다이내믹/카루셀: `asset_feed_spec`, `object_story_spec.link_data.child_attachments[]`
- 인스타: `instagram_actor_id`, `instagram_permalink_url`
- Threads: `threads_media_id`, `threads_user_id`
- 플랫폼 커스터마이즈: `platform_customizations`
- 정치광고: `authorization_category`

### 5-2. 광고 포맷별 데이터 추출

- **단일 이미지:** `image_url` 또는 `image_hash` → `/act_{id}/adimages?hashes=[...]` 로 원본 URL
- **단일 동영상:** `video_id` → `GET /{video_id}?fields=source,permalink_url,length,picture,format,thumbnails`
- **카루셀:** `object_story_spec.link_data.child_attachments[]` 또는 `effective_object_story_id` → `/{post_id}?fields=attachments{...}`
- **컬렉션(Instant Experience):** `object_story_spec.video_data` 또는 `template_url_spec`
- **Advantage+ Creative:** `asset_feed_spec.images[]`, `videos[]`, `bodies[]`, `titles[]`, `descriptions[]`, `call_to_action_types[]`, `link_urls[]`

### 5-3. Ad → Creative 가져오기

`GET /{ad_id}?fields=creative{...}` 또는 `GET /{ad_id}/adcreatives` (ad는 보통 1개 creative).

출처: https://developers.facebook.com/docs/graph-api/reference/ad-creative/

---

## 6. 객체 메타데이터

### 6-1. AdAccount (`/act_{id}`)

| 필드 | 설명 |
|---|---|
| `id`, `account_id`, `name` | 계정 식별 |
| `currency` | KRW 등 |
| `timezone_name`, `timezone_offset_hours_utc` | 계정 타임존 |
| `account_status` | 1=ACTIVE, 2=DISABLED, 3=UNSETTLED, 7=PENDING_RISK_REVIEW, 8=PENDING_SETTLEMENT, 9=IN_GRACE_PERIOD, 100=PENDING_CLOSURE, 101=CLOSED |
| `disable_reason` | 비활성화 사유 |
| `business`, `business_name` | 소속 비즈니스 |
| `amount_spent`, `balance`, `spend_cap` | 누적/잔액/한도 |
| `funding_source_details` | 결제수단 |
| `min_daily_budget`, `min_campaign_group_spend_cap` | 일예산 최소치 |

### 6-2. Campaign (`/{campaign_id}`)

| 필드 | 설명 |
|---|---|
| `id`, `name` | 식별 |
| `objective` | (v25 ODAX) `OUTCOME_AWARENESS`, `OUTCOME_TRAFFIC`, `OUTCOME_ENGAGEMENT`, `OUTCOME_LEADS`, `OUTCOME_APP_PROMOTION`, `OUTCOME_SALES`. 레거시는 v22+ 신규 캠페인에서 거부 |
| `status`, `effective_status` | ACTIVE/PAUSED/DELETED/ARCHIVED + 효력 상태 |
| `buying_type` | AUCTION / RESERVED |
| `bid_strategy` | LOWEST_COST_WITHOUT_CAP, LOWEST_COST_WITH_BID_CAP, COST_CAP, LOWEST_COST_WITH_MIN_ROAS |
| `daily_budget`, `lifetime_budget`, `budget_remaining` | 예산(account currency 최소단위) |
| `special_ad_categories[]` | HOUSING/EMPLOYMENT/CREDIT/ISSUES_ELECTIONS_POLITICS/ONLINE_GAMBLING_AND_GAMING |
| `start_time`, `stop_time`, `created_time`, `updated_time` | 시간 |
| `smart_promotion_type` | Advantage+ 종류 |
| `is_skadnetwork_attribution` | iOS SKAN 여부 |

### 6-3. AdSet (`/{adset_id}`)

`id`, `name`, `campaign_id`, `status`, `effective_status`, `daily_budget`, `lifetime_budget`, `budget_remaining`, `bid_amount`, `bid_strategy`, `billing_event` (IMPRESSIONS/LINK_CLICKS/THRUPLAY 등), `optimization_goal`, `destination_type`, `targeting`, `promoted_object` (pixel_id, custom_event_type), `attribution_spec`, `start_time`, `end_time`, `pacing_type`, `learning_stage_info`.

### 6-4. Ad (`/{ad_id}`)

`id`, `name`, `adset_id`, `campaign_id`, `creative` (또는 `creative.id`), `status`, `effective_status`, `configured_status`, `created_time`, `updated_time`, `bid_amount`, `tracking_specs`, `conversion_specs`, `preview_shareable_link`, `issues_info` (반려/이슈), `recommendations`.

출처:
- https://developers.facebook.com/docs/marketing-api/reference/ad-campaign-group/
- https://developers.facebook.com/docs/marketing-api/reference/ad-campaign/
- https://developers.facebook.com/docs/marketing-api/reference/adgroup/

---

## 7. Rate limits & Pagination

### 7-1. Business Use Case (BUC) Rate Limits — `ads_management`

- **공식 공식값:** `Calls within one hour = (100000 if Standard tier else 300) + 40 × Active Ads count` (per ad account)
- 헤더 `X-Business-Use-Case-Usage`에 `call_count`, `total_cputime`, `total_time` (각 0–100%)
- Dev Tier → Standard: App Review의 Ads Management Standard Access 신청 필요

### 7-2. Insights 호출 모드

- **동기:** `GET /{object}/insights?...` — 빠르지만 큰 결과는 timeout 위험
- **비동기 (권장):** `POST /{object}/insights` → `report_run_id` → polling `GET /{report_run_id}` (status: Job Started → Running → Completed) → `GET /{report_run_id}/insights`
- v25.0(2026-02-18) 비동기에 상세 에러 필드 추가

### 7-3. Pagination & 한도

- **Cursor 기반:** `paging.cursors.before/after`, `paging.next` URL
- 페이지당 기본 25행, `limit` 파라미터로 증가 (권장 100–500)
- **time_range:** `since`/`until` (YYYY-MM-DD). 타임존 = 계정 timezone 기본
- **데이터 보존:** 2026-01-12 이후 일부 메트릭 historical retention 단축
- `time_increment`: 1=일별, 7, 28, 'monthly', 'all_days'

출처:
- https://developers.facebook.com/docs/marketing-api/overview/rate-limiting/
- https://developers.facebook.com/docs/marketing-api/insights/best-practices/

---

## 8. 한국 마케터용 추가 분석 신호

| 영문 필드 | 한국어 매핑 | 사용 시나리오 |
|---|---|---|
| `quality_ranking` | 광고품질순위 | "내 광고 품질 어디쯤?" |
| `engagement_rate_ranking` | 참여율순위 | 크리에이티브 진단 |
| `conversion_rate_ranking` | 전환율순위 | 랜딩/오퍼 진단 |
| `estimated_ad_recall_rate` | 추정광고회상률 | 인지도 캠페인 KPI |
| `estimated_ad_recallers` | 추정회상자수 | 인지도 캠페인 |
| `landing_page_view` (action) | 랜딩뷰수 | 클릭→랜딩 손실률 = link_clicks − landing_page_view |
| `inline_link_clicks` | 인라인링크클릭수 | 반응 클릭과 분리 |
| `outbound_clicks` | 외부이동클릭수 | "정말 사이트로 간 사람" |
| `frequency` | 빈도 | 광고 피로도 판단 |
| Placement-별 ROAS (`platform_position`) | 게재위치별ROAS | Reels vs Feed 비교 |
| Hourly breakdown | 시간대별성과 | 입찰/예산 시간대 최적화 |

---

## 9. 개발 단계 주의사항

1. **Attribution window를 모든 응답 메타에 박을 것** — 같은 ROAS 숫자도 1d_click vs 7d_click이면 의미가 다름. 한국 마케터는 "어떤 기준이지?" 질문 잦음
2. **Rate limit 가드** — 계정당 시간당 호출량 = `100K + 40 × active_ads`. MCP 내부 토큰 버킷 + `X-Business-Use-Case-Usage` 헤더 모니터링 필수
3. **Breakdown 안전 화이트리스트** — Meta가 invalid 조합을 silent로 막으므로 사전 정의한 안전 조합만 노출. 사용자 임의 조합 받지 말 것
4. **Deprecated 윈도우 제거** — `7d_view`, `28d_view`는 2026-01-12부터 거부. v1 기본값 `1d_click`,`7d_click`,`1d_view` 권장
5. **`video_30_sec_watched_actions` 사용 금지** — 2024-10 정리. 대신 `video_thruplay_watched_actions`
6. **Async insights 자동 전환** — 시간 범위 ≥ 30일 또는 광고 ≥ 500개일 때 자동 async

---

## 출처 (정리)

- Insights 메인: https://developers.facebook.com/docs/marketing-api/insights/
- AdGroup Insights v25: https://developers.facebook.com/docs/marketing-api/reference/adgroup/insights/
- Breakdowns: https://developers.facebook.com/docs/marketing-api/insights/breakdowns/
- AdsActionStats: https://developers.facebook.com/docs/marketing-api/reference/ads-action-stats/
- AdCreative: https://developers.facebook.com/docs/graph-api/reference/ad-creative/
- Marketing API 버전: https://developers.facebook.com/docs/marketing-api/marketing-api-changelog/versions/
- Rate Limiting: https://developers.facebook.com/docs/marketing-api/overview/rate-limiting/
- Best Practices: https://developers.facebook.com/docs/marketing-api/insights/best-practices/
- 메트릭 변경 2025-10: https://developers.facebook.com/blog/post/2025/10/16/ads-insights-api-metric-availability-updates/
- Out-of-Cycle Changes 2025: https://developers.facebook.com/docs/marketing-api/out-of-cycle-changes/occ-2025/
- Python SDK (필드 enum 권위 소스): https://github.com/facebook/facebook-python-business-sdk/blob/main/facebook_business/adobjects/adsinsights.py

## 확인 필요 항목

- v25.0 정확한 changelog 본문 (WebFetch 잘림) — 신규 추가 필드 여부
- breakdown × 메트릭 호환 풀 매트릭스 (공식 표 비완전)
- `cost_per_unique_action_type` 등 2024-10 정리 필드의 v25 잔존 여부
- iOS SKAN 메트릭 스키마(SKAdNetwork postback) — V1 한국 우선순위 낮음
