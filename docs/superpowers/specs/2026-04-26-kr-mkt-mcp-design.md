# `kr-mkt-mcp` — 한국 마케터를 위한 광고 분석 MCP 서버 설계

- 문서 버전: 1.0 (초안)
- 작성일: 2026-04-26
- 본 문서 목적: 구현 계획(implementation plan) 수립 직전의 합의된 설계. 다음 단계는 `superpowers:writing-plans` 스킬로 단계별 구현 플랜 작성.
- 참고: Meta API 필드 상세는 [`/docs/2026-04-26-meta-marketing-api-v25-research.md`](../../2026-04-26-meta-marketing-api-v25-research.md)

---

## 1. 한 줄 정의

**`kr-mkt-mcp`** — Claude Desktop / Codex 등 MCP 호환 클라이언트에 꽂으면 한국어로 본인 Meta(Facebook/Instagram) 광고 데이터를 묻고 분석할 수 있는 1인 OSS Python MCP 서버. V1은 Meta만, 추후 Naver·Kakao·Google·TikTok을 같은 MCP에 모듈로 추가.

---

## 2. 한 페이지 요약

| 항목 | 결정 |
|------|------|
| 프로젝트명 | `kr-mkt-mcp` |
| 언어 | Python 3.11+ |
| 배포 | PyPI 패키지 → `uvx kr-mkt-mcp` |
| 핵심 라이브러리 | 공식 `mcp` Python SDK, `httpx`, `pydantic` |
| V1 플랫폼 | Meta Ads (Facebook/Instagram) |
| 데이터 출처 | 1st-party (사용자 본인 광고 계정) |
| 인증 | Meta System User Access Token (OAuth 미사용) |
| 모드 | Read-only (광고 수정 불가) |
| 도구 수 | **18개** (퍼포먼스 6 + 크리에이티브 4 + 동영상 2 + 분석 3 + 유틸 3) |
| 데이터 모델 | 한국어 통합 스키마 (`광고지표`, `동영상광고지표`) |
| 백엔드/SaaS | 없음. 사용자 PC stdio 실행 |
| 페르소나 | 미고정 — 영상 보고 따라 할 수 있는 사람 누구나 |
| 수익화 | V1에선 안 함. 콘텐츠 + 자연 성장 우선 |
| 영상 시리즈 | 7편 (티저 + 설치 + 토큰 + 시나리오 3 + 트러블슈팅) |

---

## 3. 목표 & 비목표

### 3-1. 목표 (Goals)

1. **수기 가공 제거** — 마케터가 광고 매니저에서 엑셀 다운받아 피벗 돌리던 일을 자연어 질문 한 번으로 끝낸다.
2. **퍼포먼스 + 콘텐츠 동시 분석** — ROAS·CPA·구매 등 숫자뿐 아니라 어떤 크리에이티브가 잘 됐는지(특히 동영상의 3초 이탈률·훅레이트·시청 깔때기)도 한 도구에서.
3. **한국어 친화** — 응답·필드명·예시 프롬프트 모두 한국어 마케팅 용어 기반.
4. **A to Z 영상으로 누구나 따라 설치 가능** — Meta Business Manager 토큰 발급 → MCP 등록까지 영상 1편으로.
5. **확장 가능한 멀티 플랫폼 구조** — 첫날부터 multi-provider 구조로 짜서, V2에서 Naver/Kakao 추가 시 코어 변경 없음.

### 3-2. 비목표 (Non-Goals)

명확히 짚어둠. 향후 유혹이 있어도 안 함:

1. **백엔드/SaaS 운영 안 함** — 호스팅·DB·계정 시스템 없음. MCP는 사용자 PC에서 stdio 실행.
2. **OAuth 콜백 서버 안 만듦** — Meta App Review 회피. System User Token 방식.
3. **V1에선 Meta 외 플랫폼 안 다룸** — Naver/Kakao/Google/TikTok은 V2+ 모듈로 같은 MCP에 추가.
4. **수익화 인프라 안 만듦** — 라이선스 키, 결제, telemetry 없음.
5. **경쟁사 광고 분석 안 함** — 1st-party 데이터로 한정.
6. **자동 캠페인 생성·수정 안 함** — Read-only. 광고 집행 자체를 망칠 위험 차단.
7. **Dynamic Product Ads(DPA) 깊이 분석 안 함** — V1에서 우선순위 낮음.
8. **iOS SKAN 메트릭 별도 처리 안 함** — V1 한국 우선순위 낮음.

---

## 4. 페르소나 & 사용자 시나리오

### 4-1. 페르소나

**미고정** — 영상 가이드를 보고 따라 할 수 있는 사람 누구나. 이상적으로는:
- ChatGPT/Claude를 일상적으로 쓰는 사람
- Meta Business Manager 권한이 있고 본인 광고 계정을 운영
- macOS 또는 Windows 사용

### 4-2. 핵심 사용자 시나리오

1. **주간 보고서 자연어 작성**: "지난주 캠페인별 ROAS와 CPA 알려줘"
2. **이상 진단**: "지난 14일간 ROAS가 갑자기 떨어진 날 있어?"
3. **동영상 광고 진단**: "이 광고 3초 이탈률이 너무 높은데 어디서 떨어져?"
4. **크리에이티브 비교**: "이번 달 상위 5개 광고 비교해줘"
5. **게재 위치 진단**: "Reels와 Feed 중 어느 쪽이 ROAS 높아?"
6. **구매 깔때기 진단**: "상품 조회 → 장바구니 → 결제시작 → 구매 단계별 손실률 보여줘"

---

## 5. 시스템 아키텍처

```
┌─────────────────────────────────────┐
│  Claude Desktop / Codex / Cursor    │  ← 사용자
└──────────────┬──────────────────────┘
               │ stdio (MCP)
┌──────────────▼──────────────────────┐
│  kr-mkt-mcp (이 프로젝트)             │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  MCP server (tool router)    │    │
│  └────────┬────────────────────┘    │
│           │                          │
│  ┌────────▼─────────────────────┐   │
│  │  Provider registry            │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐   │   │
│  │  │ meta │ │naver │ │kakao │   │   │
│  │  │ ✅ V1│ │  ⏳  │ │  ⏳  │   │   │
│  │  └───┬──┘ └──────┘ └──────┘   │   │
│  └──────┼────────────────────────┘   │
│         │                            │
│  ┌──────▼────────────┐               │
│  │  Normalizer        │ ← 모든 플랫폼 │
│  │  (한국어 통합 스키마)│   동일 필드명 │
│  └──────┬─────────────┘              │
│         │                            │
│  ┌──────▼────────────┐               │
│  │  운영 가드          │ rate limit, │
│  │                    │ async 전환,  │
│  │                    │ breakdown   │
│  │                    │ 화이트리스트  │
│  └──────┬─────────────┘              │
└──────────┼──────────────────────────┘
           │ HTTPS
┌──────────▼──────────────────────────┐
│  Meta Marketing API v25.0            │
└─────────────────────────────────────┘
```

### 5-1. 핵심 설계 원칙

1. **Provider plugin 구조** — `providers/meta.py`, (V2) `providers/naver.py`, `providers/kakao.py` 등. 각 provider는 동일 인터페이스 구현.
2. **Normalizer 레이어** — 플랫폼별 응답 → 공통 한국어 스키마. LLM이 플랫폼 차이를 신경 쓰지 않음.
3. **운영 가드 분리** — rate limit·async 전환·breakdown 검증을 도구 코드와 분리.
4. **stdio 전용** — 원격 호스팅 없음.
5. **읽기 전용 강제** — provider 인터페이스에 read 메서드만 정의. 쓰기 메서드 없음.

---

## 6. 기술 스택

| 영역 | 선택 | 이유 |
|------|------|------|
| 언어 | Python 3.11+ | 마케팅·데이터 분석 생태계, MCP SDK 공식 지원 |
| MCP | 공식 `mcp` Python SDK | 안정성, 표준 호환 |
| HTTP | `httpx` (async) | Meta API 호출 다수 병렬 처리 |
| 데이터 검증 | `pydantic` v2 | 한국어 필드 모델링·직렬화 |
| 패키징 | `pyproject.toml` + uv build | PyPI 배포 |
| 배포·실행 | `uvx` | 사용자 환경 격리, 1줄 설치 |
| CSV 출력 | `pandas` (선택) 또는 stdlib `csv` | 가벼우면 stdlib 우선 |
| 테스트 | `pytest`, `respx` (httpx mocking) | 표준 |
| 린트 | `ruff` + `pyright` | 모던 표준 |

---

## 7. 인증 — Meta System User Token

### 7-1. 결정

**OAuth 안 씀**. Meta Business Manager의 시스템 사용자 토큰을 사용자가 직접 발급해서 환경변수로 주입.

### 7-2. 사용자 절차 (영상 1편의 핵심 챕터)

1. business.facebook.com → 비즈니스 설정
2. 사용자 → **시스템 사용자** → 추가 → 역할: 관리자
3. **자산 추가** → 광고 계정 + 페이지 → 모든 권한 부여
4. **토큰 생성** → 앱 선택 → 권한 `ads_read`, `business_management`, `read_insights` → 만료기간 무기한
5. 생성된 토큰 복사 → Claude Desktop 설정의 `env.META_ACCESS_TOKEN`에 붙여넣기

### 7-3. 토큰 검증

서버 부팅 시 `GET /me`로 토큰 살아있는지 확인. 죽었으면 한국어 명확한 에러:

```
META_ACCESS_TOKEN이 만료됐거나 권한이 부족합니다.
business.facebook.com → 시스템 사용자 → 토큰 재발급 후 환경변수 갱신 → Claude Desktop 재시작.
```

LLM이 이 메시지를 그대로 사용자에게 전달 가능.

---

## 8. 데이터 모델 — 한국어 통합 스키마

### 8-1. `광고지표` (모든 광고 객체 공통)

```python
class 광고지표(BaseModel):
    # 식별자
    플랫폼: Literal["meta", "naver", "kakao", "google", "tiktok"]
    계정ID: str
    캠페인ID: str | None
    광고세트ID: str | None
    광고ID: str | None
    날짜: date

    # 노출/도달
    노출수: int
    도달수: int                      # reach
    빈도: float                      # frequency

    # 클릭
    클릭수: int                      # 전체 클릭
    고유클릭수: int | None
    인라인링크클릭수: int            # 반응 제외 진짜 링크
    외부이동클릭수: int              # outbound_clicks
    CTR: float
    고유CTR: float | None

    # 비용
    CPC: float
    CPM: float
    지출액: int                      # 원

    # 커머스 깔때기 (있을 때만)
    상품조회수: int | None           # omni_view_content
    장바구니수: int | None           # omni_add_to_cart
    결제시작수: int | None           # omni_initiated_checkout
    구매수: int | None               # omni_purchase
    구매가치: int | None             # 원
    랜딩뷰수: int | None             # landing_page_view (클릭 → 랜딩 손실 진단)

    # 핵심 지표
    ROAS: float | None
    CPA: float | None

    # 진단 신호 (Ad 레벨에서만)
    광고품질순위: str | None         # ABOVE_AVERAGE / AVERAGE / BELOW_AVERAGE_{35,20,10} / UNKNOWN
    참여율순위: str | None
    전환율순위: str | None
    추정광고회상률: float | None     # estimated_ad_recall_rate

    # 응답 메타 (매우 중요 — LLM이 답할 때 출처 표기)
    어트리뷰션윈도우: list[str]      # 예: ["1d_click", "7d_click"]
    플랫폼별_원본: dict              # 플랫폼 고유 필드 보존
```

### 8-2. `동영상광고지표` (동영상 광고 한정)

```python
class 동영상광고지표(광고지표):
    # 시청 깔때기 (Meta v25 정확한 필드명)
    재생수: int                          # video_play_actions
    동영상_3초_조회수: int               # video_continuous_2_sec_watched_actions
    동영상_15초_조회수: int | None
    동영상_25퍼_조회수: int
    동영상_50퍼_조회수: int
    동영상_75퍼_조회수: int
    동영상_95퍼_조회수: int | None
    동영상_100퍼_완주수: int

    # 파생 지표 (LLM이 명세서로 산식 확인 가능)
    플레이레이트: float                  # 재생수 / 노출수 × 100
    훅레이트: float                      # 3초 조회수 / 노출수 × 100
    홀드레이트: float                    # 15초 조회수 / 3초 조회수 × 100
    3초_이탈률: float                    # 100 - 훅레이트
    25퍼_도달률: float
    50퍼_도달률: float
    75퍼_도달률: float
    완주율: float                        # 100퍼 완주수 / 노출수 × 100
    시청완료율: float                    # 100퍼 완주수 / 재생수 × 100
    THRUPLAY율: float                    # THRUPLAY수 / 노출수 × 100

    # 시청 시간
    동영상_평균_시청시간_초: float
    THRUPLAY수: int                      # video_thruplay_watched_actions
    THRUPLAY당_비용: int                 # 원

    # 곡선 (선택적, 도구가 요청 시만 채움)
    시청곡선: list[int] | None           # video_play_curve_actions (1초 단위 0-60s)
    초기보존곡선: dict | None            # video_play_retention_0_to_15s_actions
```

### 8-3. Deprecated 필드 차단

스키마에서 받지도, 보내지도 않을 필드:
- `video_30_sec_watched_actions` (deprecated 2024-10)
- `video_3_sec_watched_actions` (deprecated 2024-10, 대신 continuous_2_sec)
- `7d_view`, `28d_view` 어트리뷰션 (제거 2026-01-12)
- `cost_per_unique_action_type` 일부 (확인 필요 항목)

---

## 9. MCP 도구 18개

### 9-1. 카테고리별 일람

| # | 도구 | 카테고리 | 핵심 반환 |
|---|------|---------|---------|
| 1 | `list_ad_accounts` | 퍼포먼스 | 토큰으로 접근 가능한 광고 계정 목록 |
| 2 | `get_account_summary` | 퍼포먼스 | 계정 전체 요약 |
| 3 | `list_campaigns` | 퍼포먼스 | 캠페인 목록 + 핵심 지표 |
| 4 | `get_campaign_insights` | 퍼포먼스 | 캠페인 상세 (일별·breakdown) |
| 5 | `list_ad_sets` | 퍼포먼스 | 광고 세트 + 지표 |
| 6 | `list_ads` | 퍼포먼스 | 광고 + 지표 + 진단 신호 |
| 7 | `get_ad_creative` | 크리에이티브 | 광고 크리에이티브 콘텐츠 |
| 8 | `compare_creatives` | 크리에이티브 | 다수 광고 나란히 비교 |
| 9 | `get_creative_breakdown` | 크리에이티브 | 같은 광고를 인구통계·디바이스별 분리 |
| 10 | `top_performing_creatives` | 크리에이티브 | 상위 N개 광고 |
| 11 | `get_video_metrics` | 동영상 | 단일 동영상 시청 깔때기 |
| 12 | `compare_video_dropoff` | 동영상 | 다수 동영상 시청 깔때기 비교 |
| 13 | `find_anomalies` | 분석 | 이상치 탐지 (ROAS 급락 등) |
| 14 | `get_placement_breakdown` | 분석 | Reels vs Feed vs Stories 등 |
| 15 | `get_purchase_funnel` | 분석 | 조회→장바구니→결제시작→구매 |
| 16 | `export_to_csv` | 유틸 | 직전 결과를 `~/Downloads/`에 CSV |
| 17 | `get_korean_glossary` | 유틸 | 마케팅 용어 사전 (LLM이 사용자 질문 해석 시) |
| 18 | `get_data_spec` | 유틸 | 데이터 명세서 — LLM이 첫 호출 권장 |

### 9-2. 도구 설명 작성 표준

모든 도구의 docstring은 **4부 구조**를 따른다 (한국어):

```
[1] 한 줄 목적
[2] 호출해야 하는 경우 (3-5개 bullet, 사용자 질문 패턴 포함)
[3] 호출하지 말아야 하는 경우 (혼동 도구 명시 — "이건 X 도구가 더 적합")
[4] 인자 + 반환 형태 (스키마명 명시)
```

이 표준이 중요한 이유: 18개 도구가 있을 때 LLM이 잘못된 도구를 호출하는 일을 막는 가장 강력한 장치.

### 9-3. 도구 docstring 예시 — 3개

#### 예시 A: `get_video_metrics`

```python
@mcp.tool()
def get_video_metrics(ad_id: str, date_range: str = "지난 7일") -> 동영상광고지표:
    """
    동영상 광고 한 개의 시청 깔때기와 이탈 지표를 가져옵니다.

    호출해야 하는 경우:
    - 사용자가 "3초 이탈률" "훅레이트" "홀드레이트" "완주율" "시청률" 등 동영상 전용 지표를 물을 때
    - "이 영상 어디서 사람들이 떨어져 나가?" 같은 시청 깔때기 분석
    - 동영상 광고 단일 진단

    호출하지 말아야 하는 경우:
    - 이미지/카루셀 광고는 동영상 지표 없음 → 먼저 get_ad_creative로 광고 형식 확인
    - 광고 여러 개 비교는 → compare_video_dropoff 사용
    - 캠페인/광고세트 단위 동영상 통합 보기는 → get_campaign_insights에 video breakdown 옵션 사용

    인자:
    - ad_id (str): list_ads로 먼저 ID 확보. ad_set_id나 campaign_id 아님.
    - date_range (str): 자연어 가능. 예: "지난 7일", "이번 달", "2026-04-01~2026-04-15"

    반환 (동영상광고지표 스키마):
    - 노출수, 재생수, 3초/15초 조회수, 25/50/75/95/100% 도달수
    - 플레이레이트, 훅레이트, 홀드레이트, THRUPLAY율, 시청완료율 (모두 %)
    - 평균 시청시간(초), THRUPLAY수, THRUPLAY당 비용(원)
    - 어트리뷰션윈도우 메타 포함
    """
```

#### 예시 B: `find_anomalies`

```python
@mcp.tool()
def find_anomalies(
    account_id: str,
    metric: Literal["ROAS", "CPA", "CTR", "지출액", "구매수"] = "ROAS",
    date_range: str = "지난 30일",
    sensitivity: Literal["낮음", "보통", "높음"] = "보통",
) -> list[dict]:
    """
    지정 기간 내 특정 지표가 갑자기 변한 날짜를 탐지합니다 (z-score 기반).

    호출해야 하는 경우:
    - 사용자가 "갑자기 ROAS 떨어진 날" "CPA 튄 날" "이상한 날" 등을 물을 때
    - 정기 진단/주간 리포트의 일부로 비정상 탐지

    호출하지 말아야 하는 경우:
    - 이상치 없이 "전반적인 흐름"만 보고 싶다 → get_account_summary 또는 get_campaign_insights
    - 특정 캠페인 단위 진단 → get_campaign_insights에 time_increment=1 사용

    인자:
    - account_id (str): list_ad_accounts로 먼저 확인
    - metric (str): "ROAS" | "CPA" | "CTR" | "지출액" | "구매수"
    - date_range (str): "지난 30일" 등 자연어
    - sensitivity (str): 임계 z-score (낮음=±2.5, 보통=±2.0, 높음=±1.5)

    반환:
    - list[{"날짜", "값", "기간_평균", "z_score", "방향": "급등|급락"}]
    - 어트리뷰션윈도우 메타 포함
    """
```

#### 예시 C: `get_data_spec`

```python
@mcp.tool()
def get_data_spec() -> dict:
    """
    이 MCP가 다루는 모든 데이터의 명세서를 반환합니다 — 필드 정의, 산식, 한국어 매핑, 사용 가능 breakdown 조합 등.

    호출해야 하는 경우:
    - 사용자가 첫 인사를 한 후 LLM이 자동 호출 (세션 컨텍스트 확보용)
    - 사용자가 "어떤 데이터가 있어?" "ROAS가 뭐야?" "훅레이트는 어떻게 계산해?" 등을 물을 때
    - LLM이 다른 도구를 호출하기 전, 적합한 필드명을 확인하고 싶을 때

    호출하지 말아야 하는 경우:
    - 단순 한국어 마케팅 용어 정의는 → get_korean_glossary 사용

    인자: 없음

    반환 (dict):
    - 한국어_필드사전: 모든 한국어 필드명 + 영문 원본 + 정의
    - 파생지표_산식: 훅레이트·홀드레이트·플레이레이트·시청완료율·랜딩손실률 등 공식
    - 어트리뷰션윈도우_의미: 1d_click vs 7d_click 차이 설명
    - quality_ranking_의미: ABOVE_AVERAGE → BELOW_AVERAGE_10 5단계 의미
    - 사용가능_breakdown_조합: 화이트리스트
    - 알려진_제약: region이 video_p25 안 됨 등
    - 한국어_표현_매핑: 한국 마케터 표현 ↔ Meta 영문 매핑 사전
    """
```

나머지 15개 도구의 docstring은 구현 단계에서 동일한 4부 구조로 작성.

---

## 10. 운영 가드 (구현 시 강제)

### 10-1. Breakdown 화이트리스트

Meta가 invalid 조합을 silent로 막거나 잘못된 결과를 줌. MCP는 사전 정의된 안전 조합만 노출.

```python
SAFE_BREAKDOWN_COMBOS = [
    [],
    ["age"],
    ["gender"],
    ["age", "gender"],
    ["country"],
    ["region"],
    ["device_platform"],
    ["publisher_platform"],
    ["platform_position"],
    ["publisher_platform", "platform_position"],
    ["impression_device"],
    ["hourly_stats_aggregated_by_advertiser_time_zone"],
]
# 도구가 위 리스트 외 조합을 받으면 KoreanError 반환
```

### 10-2. Async 자동 전환

```python
def should_use_async(time_range_days: int, ad_count: int) -> bool:
    return time_range_days >= 30 or ad_count >= 500
```

대용량 호출은 자동으로 `POST /insights` async 모드 + `report_run_id` polling.

### 10-3. Rate Limit 가드

- `X-Business-Use-Case-Usage` 헤더 파싱
- `call_count`, `total_cputime`, `total_time` 중 가장 높은 값 기준
- 80% 도달: 요청 throttle (지연)
- 100% 도달: exponential backoff (5s → 30s → 5min)
- 503/429 응답: 자동 재시도 최대 3회

### 10-4. Deprecated 필드 차단

`server.py` 시작 시 schema validator로 강제. 다음 필드를 요청하면 즉시 에러:
- `video_30_sec_watched_actions`
- `video_3_sec_watched_actions`
- `7d_view`, `28d_view` (attribution windows)

---

## 11. 에러 처리

| 에러 | 한국어 메시지 | LLM 전달 |
|------|------------|--------|
| 토큰 만료/권한 부족 | "META_ACCESS_TOKEN이 만료됐거나 권한이 부족합니다. ..." | 그대로 |
| Rate limit 초과 | "요청이 한도를 초과했습니다. 잠시 후 다시 시도해주세요. (남은 한도 회복까지 약 X분)" | 그대로 |
| 광고 계정 접근 불가 | "이 광고 계정에 접근 권한이 없습니다. 시스템 사용자 자산 할당을 확인해주세요." | 그대로 |
| 빈 결과 | "지정 기간 동안 데이터 없음. 캠페인 일시중지 또는 날짜 범위를 확인해주세요." | 그대로 |
| Invalid breakdown 조합 | "이 breakdown 조합은 Meta가 지원하지 않습니다. 사용 가능 조합: ..." | 그대로 |
| 네트워크 오류 | "Meta API에 접근할 수 없습니다. 네트워크 상태를 확인해주세요." | 그대로 |

원칙: 모든 에러 메시지는 **LLM이 그대로 사용자에게 전달해도 자연스럽게**. 영문 stack trace 노출 금지.

---

## 12. 배포 & 설치 흐름

### 12-1. 배포

- PyPI에 `kr-mkt-mcp` 패키지로 publish
- 버전 관리: SemVer (`0.1.0` 시작)
- 릴리즈: GitHub Actions로 PyPI 자동 publish

### 12-2. 사용자 설치 (영상 1편)

```bash
# 사전 요구: uv 설치
brew install uv  # 또는 Windows 공식 설치
```

Claude Desktop 설정 파일 (`~/Library/Application Support/Claude/claude_desktop_config.json` 또는 Windows 동등):

```json
{
  "mcpServers": {
    "kr-mkt-mcp": {
      "command": "uvx",
      "args": ["kr-mkt-mcp"],
      "env": {
        "META_ACCESS_TOKEN": "EAAxxx..."
      }
    }
  }
}
```

Claude Desktop 재시작 → 끝.

---

## 13. 테스트 전략

| 레이어 | 도구 | 범위 |
|------|------|------|
| Unit | `pytest` | normalizer 정규화 로직, 파생 지표 산식 |
| Contract | `pytest` + `respx` | 18개 도구 각각 mock Meta API로 정상 호출 시 정의된 스키마 반환 |
| Integration | 수동 (CI 미포함) | 본인 광고 계정 + 테스트 캠페인(예산 ₩1,000)으로 실제 API → fixtures 갱신 |
| LLM evals (선택) | Claude API + 시나리오 케이스 | 18개 도구 description 품질 평가, 첫 영상 출시 전 1회 |

**E2E 자동화는 안 함** — Meta 광고 계정 위험.

---

## 14. 영상 콘텐츠 시리즈

| # | 영상 | 길이 | 형식 | 우선순위 |
|---|------|------|------|--------|
| 0 | "엑셀 다운받기 그만, AI에게 물어봐" — Hook | 30초 | 인스타 릴스/쇼츠 | P0 |
| 1 | 설치 A to Z (uv → MCP → Claude Desktop) | 8-10분 | 유튜브 | P0 |
| 2 | Meta System User Token 발급 가이드 | 5분 | 유튜브 | P0 |
| 3 | "주간 보고서 자연어로 만들기" 시나리오 | 6분 | 유튜브 + 쇼츠 컷 | P1 |
| 4 | "3초 이탈률·훅레이트로 영상 광고 진단" | 8분 | 유튜브 | P1 |
| 5 | "이상 탐지 — 왜 ROAS가 떨어졌나?" 시나리오 | 6분 | 유튜브 | P1 |
| 6 | 자주 묻는 에러 / 트러블슈팅 모음 | 10분 | 유튜브 | P2 |
| 7 | (V2 출시 시) 다른 광고 플랫폼 연동 | 미정 | 유튜브 | 미래 |

영상 #0~#2는 **진입 깔때기**, #3~#5는 **재방문 깔때기**, #6은 **CS 비용 절감**.

---

## 15. 디렉터리 구조

```
kr-mkt-mcp/
├── pyproject.toml              # PyPI 패키지 메타
├── README.md                   # 한국어, 영상 링크 포함
├── docs/
│   ├── superpowers/specs/
│   │   └── 2026-04-26-kr-mkt-mcp-design.md   # 본 문서
│   ├── 2026-04-26-meta-marketing-api-v25-research.md  # API 리서치
│   ├── 2026-04-25-google-cloud-multi-agent-a2a-mcp.md # 참고 자료
│   └── data-spec.md            # 사용자용 데이터 명세
├── src/kr_mkt_mcp/
│   ├── __main__.py             # uvx 실행 진입점
│   ├── server.py               # MCP server + tool router
│   ├── providers/
│   │   ├── _base.py            # Provider 추상 인터페이스
│   │   ├── _schema.py          # 한국어 통합 스키마
│   │   ├── meta.py             # V1 — Meta 구현
│   │   ├── naver.py            # V2 — placeholder (NotImplementedError)
│   │   └── kakao.py            # V3 — placeholder
│   ├── normalizer.py           # 플랫폼별 → 통합 스키마
│   ├── guards/
│   │   ├── breakdown.py        # 화이트리스트
│   │   ├── async_switch.py     # async 자동 전환
│   │   ├── rate_limit.py       # 토큰 버킷
│   │   └── deprecated.py       # 차단 리스트
│   ├── tools/                  # 18개 도구 (카테고리별 파일)
│   │   ├── accounts.py         # list_ad_accounts, get_account_summary
│   │   ├── campaigns.py        # list_campaigns, get_campaign_insights, list_ad_sets, list_ads
│   │   ├── creatives.py        # get_ad_creative, compare_creatives, get_creative_breakdown, top_performing_creatives
│   │   ├── video.py            # get_video_metrics, compare_video_dropoff
│   │   ├── analytics.py        # find_anomalies, get_placement_breakdown, get_purchase_funnel
│   │   └── utils.py            # export_to_csv, get_korean_glossary, get_data_spec
│   ├── errors.py               # 한국어 에러 메시지
│   └── glossary.py             # 마케팅 용어 사전
└── tests/
    ├── fixtures/               # Meta API 응답 샘플 (마스킹)
    ├── unit/
    ├── contract/
    └── integration/            # 수동 실행, CI 제외
```

---

## 16. 구현 우선순위 (마일스톤)

### M1: 코어 인프라 (1주차)

- [ ] `pyproject.toml`, `pre-commit`, `pytest`, `ruff`, `pyright` 셋업
- [ ] `providers/_base.py`, `providers/_schema.py` (광고지표·동영상광고지표)
- [ ] `providers/meta.py` 기본 클라이언트 (httpx + token 검증)
- [ ] `guards/` 4종 (breakdown / async / rate_limit / deprecated)
- [ ] `normalizer.py` Meta → 한국어 스키마 변환
- [ ] `errors.py` 한국어 에러 메시지

### M2: 핵심 도구 7개 (2주차)

P0 시나리오에 필요한 도구 우선:
- [ ] `list_ad_accounts`, `get_account_summary`, `list_campaigns`, `list_ads`
- [ ] `get_ad_creative`, `get_video_metrics`, `get_data_spec`

→ 이 시점에 **영상 #0, #1, #2 촬영 가능**.

### M3: 분석 도구 6개 (3주차)

- [ ] `get_campaign_insights`, `list_ad_sets`, `find_anomalies`
- [ ] `compare_creatives`, `top_performing_creatives`, `get_creative_breakdown`

→ 이 시점에 **영상 #3, #4, #5 촬영 가능**.

### M4: 동영상·분석 도구 + 유틸 5개 (4주차)

- [ ] `compare_video_dropoff`, `get_placement_breakdown`, `get_purchase_funnel`
- [ ] `export_to_csv`, `get_korean_glossary`

### M5: 출시 (5주차)

- [ ] PyPI publish (`0.1.0`)
- [ ] README 한국어 + 영상 임베드
- [ ] 영상 #0~#2 게시
- [ ] 영상 #6 (트러블슈팅) — 사용자 댓글 누적되면 추가

---

## 17. 미래 확장 (V2+)

- **V2**: Naver 검색광고 + Naver GFA provider 추가. 같은 한국어 통합 스키마 재사용.
- **V3**: Kakao 모먼트 provider.
- **V4**: Google Ads (GA4 separate) provider.
- **V5**: TikTok Ads provider.
- **부수**: 사용자 요청 시 Coupang Ads / 11번가 등 커머스 플랫폼 (스크래핑 영역, 별도 Apify 액터로 빠질 가능성).

각 plat 추가는 코어 변경 없이 `providers/` 아래 파일 추가 + `normalizer.py`에 매핑만 추가.

---

## 18. 확정된 결정 / 보류 사항

### 18-1. 확정 (Confirmed)

- 언어: Python 3.11+
- V1 플랫폼: Meta only (FB/IG)
- 인증: System User Token
- Read-only
- 도구 18개
- 한국어 통합 스키마
- 백엔드 없음 (stdio 전용)
- 페르소나 미고정
- V1 수익화 안 함

### 18-2. 보류 / 추후 결정 (Open Questions)

- TypeScript 포팅 여부 (사용자 요청 시)
- 한국어 글꼴 처리 (CSV 출력 시 BOM 추가 여부 — Excel 한글 깨짐 방지)
- Telemetry/사용 통계 수집 여부 (현재 안 함, 향후 옵트인 검토 가능)
- 다중 광고 계정 동시 처리 시 토큰 vs 계정ID 분리 (V2에서 검토)

---

## 19. 참고 자료

- 본 프로젝트 리서치:
  - [`docs/2026-04-26-meta-marketing-api-v25-research.md`](../../2026-04-26-meta-marketing-api-v25-research.md) — Meta API v25 필드 상세
  - [`docs/2026-04-25-google-cloud-multi-agent-a2a-mcp.md`](../../2026-04-25-google-cloud-multi-agent-a2a-mcp.md) — A2A·MCP 패턴
- 외부:
  - Meta Marketing API: https://developers.facebook.com/docs/marketing-api/
  - MCP 공식: https://modelcontextprotocol.io/
  - MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk

---

## 20. 다음 단계

본 스펙에 대한 사용자 검토 후, `superpowers:writing-plans` 스킬로 마일스톤별 구현 계획 수립.
