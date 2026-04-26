# Codex Adversarial Review — `kr-mkt-mcp` 디자인 스펙

- 작성일: 2026-04-26
- 대상 스펙: [`docs/superpowers/specs/2026-04-26-kr-mkt-mcp-design.md`](./2026-04-26-kr-mkt-mcp-design.md)
- 리뷰어: Codex (codex:codex-rescue subagent), GPT-5.4 기반
- 모드: adversarial — 친절하지 않게, 실제 위험 표면화

---

## 1. Verdict

**block.** 스펙의 핵심 온보딩/인증 전제가 검증되지 않았으며, 동봉 리서치 문서와 자체 모순됨. 신선한 Meta 계정으로 실제 토큰 발급/Insights 호출이 동작하는지 확인하기 전까지 구현 시작 금지.

---

## 2. Critical issues (구현 전 반드시 수정)

### C1. `design.md:52` — "no App Review"는 거짓 약속

> "**OAuth 콜백 서버 안 만듦** — Meta App Review 회피. System User Token 방식."

**아마도 잘못됨.** System User Token은 Meta App/액세스 티어 요구사항을 우회하지 않는다. 같은 스펙 line 159에서 "앱 선택"을 요구하고, 리서치 문서 line 285에서 "Dev Tier → Standard: App Review의 Ads Management Standard Access 신청 필요"라고 명시함. "OAuth 없음"과 "App Review 없음"은 서로 다른 문제이며 스펙이 둘을 혼동.

### C2. `design.md:159` — 사용자의 Meta App은 어디서 오는가?

> "**토큰 생성** → 앱 선택 → 권한 `ads_read`, `business_management`, `read_insights` → 만료기간 무기한"

스펙은 Meta App을 누가 만드는지 설명하지 않는다. 사용자가 직접 만들고 Marketing API 추가, BM 연결, 자산 액세스 설정, 가능하면 Standard Access 신청까지 해야 한다면 "5분 영상 1편" 약속은 대부분 한국 마케터에게 거짓.

### C3. `design.md:44` — "누구나 따라 설치"는 거짓

> "**A to Z 영상으로 누구나 따라 설치 가능** — Meta Business Manager 토큰 발급 → MCP 등록까지 영상 1편으로."

**아마도 잘못됨.** Business Manager 미보유, Meta 개발자 앱 미보유, 자산 액세스 미부여, Development Access 단계 사용자는 흐름 완료 불가. 현실적 최소 온보딩은 다단계 app/BM/access 셋업 + 다수 실패 지점.

### C4. `design.md:248` — 숫자로 시작하는 Python 식별자: 진짜 문법 버그 ⚠️

> `3초_이탈률: float`, `25퍼_도달률`, `50퍼_도달률`, `75퍼_도달률` (lines 248-251)

**확실히 잘못됨.** Python 식별자는 숫자로 시작 불가. 한글 식별자는 OK이지만 `25퍼_도달률`은 `SyntaxError` 발생. **Codex가 실제로 검증함.** pydantic 모델 정의 자체가 막히는 블로커 버그.

### C5. `design.md:216` — `ROAS: float | None`은 어트리뷰션 윈도우 데이터 파괴

> `ROAS: float | None`

리서치 문서 자체가 `purchase_roas`를 "action_type별"이라 명시(research.md:53). Meta Python Business SDK는 `purchase_roas`를 `list[AdsActionStats]`로 노출 — action_type, value, attribution window 포함. 단일 float로 평탄화하면 어떤 어트리뷰션 윈도우인지 정보가 묵음 손실.

### C6. `design.md:164` — `/me` 검증은 무의미

> "서버 부팅 시 `GET /me`로 토큰 살아있는지 확인."

토큰이 `/me`는 통과해도 `ads_read`, `read_insights`, 광고 계정 할당, 앱 액세스 티어, insights API 권한에서 실패할 수 있음. 거짓 "건강한" 시작 후 개별 도구에서 silent 실패.

### C7. `design.md:418-433` — `SAFE_BREAKDOWN_COMBOS`가 metric-level 제약 무시

> `SAFE_BREAKDOWN_COMBOS = [...] ["region"] ...`

화이트리스트가 metric-aware하지 않다. 리서치 문서에서 비디오 % watched action들은 `region`을 지원하지 않음(research.md:163). 글로벌 화이트리스트는 metric과 무관하게 region 허용. 비디오 도구는 여전히 invalid API 호출 생성, 가드가 잡지 못함.

### C8. `design.md:387-388` — `get_data_spec` 첫 턴 호출은 강제 불가

> "사용자가 첫 인사를 한 후 LLM이 자동 호출"

**확실히 잘못됨.** MCP는 도구 설명만 제공. 모델이 특정 도구를 첫 턴에 호출하도록 강제하는 라이프사이클 훅 없음. 이 호출이 일어난다는 가정 위에 정확성을 쌓는 건 design theater.

---

## 3. Major risks (가능성 높은 문제)

### M1. Rate limit 숫자 모순 (research.md:328 vs research.md:283)

> `100K + 40 × active_ads` vs `100000 if Standard tier else 300`

App Review 회피로 Dev Tier 가능성 높은데, 베이스가 300이지 100,000 아님. 스펙의 async/rate-limit 가드는 Standard Tier 기준으로 calibrated되어 있어 Dev Tier 사용자 보호 못 함.

### M2. `X-Business-Use-Case-Usage` 헤더 파싱 underspecified

여러 BUC 버킷 존재(ads_management, ads_insights, custom_audience + 계정/앱 레벨 nesting). 어떤 버킷을 게이트하는지 미명시. 단일 임계값으로 한 버킷만 보면 다른 버킷 고갈 놓침.

### M3. `design.md:236` — 2초 메트릭을 3초로 라벨링은 의미 위험

> `동영상_3초_조회수: int  # video_continuous_2_sec_watched_actions`

**불확실.** `video_continuous_2_sec_watched_actions`가 현재 Meta Ads Manager UI(한국어)의 "3초 조회"와 product-equivalent인지 미검증. 2초 metric을 3초로 잘못 라벨링하면 모든 비디오 진단이 misleading.

### M4. 라우팅 디자인이 구현 단계로 deferred

> "나머지 15개 도구의 docstring은 구현 단계에서…"

스펙이 "가장 강력한 장치"라 부르는 라우팅 문제가 18개 중 15개에서 미해결. 의미 겹치는 도구 페어들(compare_creatives vs top_performing_creatives; get_account_summary vs get_campaign_insights vs find_anomalies)이 런타임에 충돌.

### M5. plaintext 영구 토큰을 config 파일에

> `"META_ACCESS_TOKEN": "EAAxxx..."`

영구 또는 long-lived 비즈니스 토큰을 `claude_desktop_config.json`에 plaintext 저장. 경고, 회전 가이드, least-privilege 가이드 없음. System User 토큰이 BM 모든 광고 계정을 커버하면 이 파일 유출 = 심각한 비즈니스 위험.

### M6. `design.md:205` — 통화를 정수 KRW로 가정

> `지출액: int  # 원`

Meta는 `spend`를 계정 통화의 string decimal로 반환. 모든 한국 마케터 계정이 KRW가 아니며, KRW라도 `account_currency` 보존 없이 스키마 레벨에서 가정 금지.

### M7. async 임계값이 days/ad count만 본다

> `return time_range_days >= 30 or ad_count >= 500`

응답 크기는 breakdowns, level, time_increment, action 필드, attribution windows, pagination에도 의존. hourly breakdown + 다수 action 필드 있는 1일 pull이 30일 quiet pull보다 클 수 있음.

### M8. 수동 통합 테스트 + CI 없음 = 회귀 못 잡음

> "Integration | 수동 (CI 미포함)" + "**E2E 자동화는 안 함**"

Meta API drift, fixture rot, normalizer 변경 발생 시 3주 후 리팩터링에서 도구 깨져도 자동 신호 없음.

### M9. 5주 part-time 스코프 비현실적

18 도구 + multi-provider 아키텍처 + 4 운영 가드 + 한국어 스키마 + CSV export + 테스트 + PyPI 패키징 + 7개 영상 in 5주 part-time. 가장 슬립 가능성 높은 것: tool docstring(이미 deferred), integration test 커버리지, 토큰 온보딩 정확성 — 정확히 제품 약속이 의존하는 부분.

---

## 4. Minor issues (nitpicks)

### N1. `design.md:33` — 영상 개수 불일치

> "영상 시리즈 | 7편" 이지만 line 529-536에 #0 ~ #7 (8개 항목, 미래 #8 제외해도)

### N2. `design.md:656` — BOM 결정은 open으로 둘 수 없음

> "CSV 출력 시 BOM 추가 여부 — Excel 한글 깨짐 방지"

한국어 Excel export가 V1 사용자 약속이라면 UTF-8 BOM은 V1 acceptance criterion이지 open question 아님.

### N3. `design.md:124` — Multi-provider 아키텍처는 premature (YAGNI)

> "첫날부터 multi-provider 구조"

Meta 인증·Insights 정확성 자체가 어려움. 첫 provider도 안 되는데 Naver/Kakao/TikTok/Google placeholder가 아키텍처 표면을 더함. abstraction이 Naver의 완전히 다른 인증·메트릭 모델과 첫 만남에서 살아남을 증거 없음.

### N4. `design.md:635` — "매핑만 추가"는 순진

> "각 plat 추가는 코어 변경 없이 `providers/` 아래 파일 추가 + `normalizer.py`에 매핑만 추가."

Google Ads, Naver, Kakao, TikTok은 attribution model, creative schema, currency, account hierarchy, auth flow가 모두 다름. flat "mapping-only" claim은 비현실적.

---

## 5. 검증 불가능한 부분 (불확실성 명시)

- 무기한 System User 토큰을 2026년 미인증 또는 소규모 한국 비즈니스 계정 누구나 발급 가능한가? **불확실**
- `7d_view`/`28d_view`가 live v25 Insights API에서 완전 거부되는지(deprecated이지만 반환됨 vs) — research.md:134 제거 주장; SDK enum은 여전히 등재. **불확실**
- `video_30_sec_watched_actions`가 거부 / deprecation 경고와 반환 / 정상 수용 중 어느 것? **불확실**
- `video_continuous_2_sec_watched_actions`가 현재 Meta Ads Manager UI(한국어 로케일)의 "3초 조회"와 product-equivalent인가? **불확실**
- `quality_ranking` enum 값 `BELOW_AVERAGE_35`, `BELOW_AVERAGE_20`, `BELOW_AVERAGE_10`이 live API 반환 정확한 문자열과 일치하는가? Live response로 미확인. **불확실**
- `video_p95_watched_actions`가 v25 실제 필드인가 보간인가? 대부분 공개 소스는 p25/50/75/100만 등재. **불확실 — 잘못일 가능성 높음**

---

## 6. 마무리 — 가장 큰 단일 위험

저자가 18개 도구 + multi-provider 아키텍처를 짓기 시작하는 것은, **prior Meta 개발 경험이 없는 실제 한국 마케터가 처음부터 read-only Insights 액세스 토큰을 성공적으로 만들 수 있는지** 검증하기 전이라는 것. 스펙의 모든 제품 약속("5분 설치, 누구나 따라 가능")은 System User 토큰 접근성, BM 사전 요구사항, App Review를 Standard Access rate limit에서 회피 가능한지에 대한 검증 안 된 가정 위에 서있음. 답이 "아니오, 사용자는 본인 Meta App + Standard Access review 필요"라면 첫 도구 호출 전에 온보딩 스토리가 깨짐. **단일 신선 계정으로 이걸 증명/반증하는 것이 — 한 줄의 구현 코드를 쓰기 전에 — 지금 가장 중요한 일.**
