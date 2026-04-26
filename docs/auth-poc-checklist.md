# Meta System User Token — Auth POC 체크리스트

- 작성일: 2026-04-26
- 목적: 스펙의 "5분 설치, 누구나 따라 가능" 클레임 검증. Dev Tier로도 read-only Insights API가 충분히 동작하는지, App Review 회피가 정말 가능한지 본인 계정으로 끝-끝 확인
- 예상 시간: 30분 ~ 2시간 (변수가 많음)
- 도구: 터미널 + 브라우저
- 사전 준비: Meta Business Manager 권한 + 본인 광고 계정 (광고 1건 이상 집행 경험 권장)

> 이 체크리스트의 결과로 스펙의 §3, §7, §10이 결정됩니다. 가능한 한 시간을 측정하면서 진행하세요.

---

## 0. 시작 전 측정

- 시작 시각: ____________
- 본인 사전 경험: developers.facebook.com 사용 경험 (있음/없음): ____
- Business Manager 사용 경험: ____ 년

---

## 1. Meta Developer App 생성 (또는 기존 앱 확인)

### 1-1. 기존 앱 있는지 확인

- 브라우저: https://developers.facebook.com/apps/
- 앱 목록 확인. 없으면 1-2로

### 1-2. 새 앱 생성 (없는 경우)

1. "앱 만들기" 클릭
2. 사용 사례: **"기타"** 선택
3. 앱 유형: **"비즈니스"** 선택
4. 앱 이름 (예: `kr-mkt-mcp-test`), 비즈니스 포트폴리오 선택
5. "앱 만들기" 완료
6. 보안 검사 통과 (전화 인증 등)

### 1-3. Marketing API 추가

1. 좌측 메뉴 → "제품 추가"
2. **"마케팅 API"** → 설정
3. 토큰 생성 도구 가능해짐

### ✅ 체크포인트 1

- [ ] 앱 ID 확보: ____________
- [ ] Marketing API 활성화 완료
- 소요 시간: ____ 분
- 막힌 곳: ____________

---

## 2. 액세스 티어 (Standard vs Development) 확인

이게 **가장 중요한 검증 포인트**.

1. 좌측 메뉴 → "앱 검수" → "권한 및 기능"
2. 다음 권한들의 상태 확인:
   - `ads_read` — 상태: ____ (Development Access / Standard Access)
   - `read_insights` — 상태: ____
   - `business_management` — 상태: ____
   - `ads_management` — 상태: ____

### 발견된 사실 기록

- 이 권한들이 기본적으로 Development Access인가? (예/아니오): ____
- Standard Access를 받으려면 App Review가 필요하다고 표시되는가? (예/아니오): ____
- "Advanced Access (구 Standard Access)"로 표기 변경됐는지: ____

### ✅ 체크포인트 2

- [ ] 앱이 Development Access 단계인지 Standard Access인지 명확함
- 결론: ____________________

---

## 3. System User 생성 + 자산 할당

1. https://business.facebook.com → 비즈니스 설정 (좌측 톱니바퀴)
2. **사용자 → 시스템 사용자** → "추가" 클릭
3. 이름: 예 `mcp-server` / 역할: **관리자**
4. 추가된 시스템 사용자 클릭
5. **자산 추가** → 광고 계정 선택 → 권한 **"광고 계정 관리"** (모두) 부여
6. (선택) 페이지도 추가 → "페이지 관리" 부여

### ✅ 체크포인트 3

- [ ] 시스템 사용자 ID: ____________
- [ ] 광고 계정 자산 할당 완료
- 소요 시간: ____ 분

---

## 4. Access Token 발급

1. 시스템 사용자 페이지 → **"새 토큰 생성"**
2. 앱 선택: 1단계에서 만든 앱
3. 권한 선택:
   - ✅ `ads_read`
   - ✅ `read_insights`
   - ✅ `business_management`
4. 만료기간:
   - "60일" / "무기한" 옵션 보이는지 확인
   - **무기한이 안 보이는가? (예/아니오): ____**
   - 무기한을 선택하면 추가 검증(2FA, 최근 비밀번호 등) 요구되는가?: ____
5. "토큰 생성" → 표시된 토큰 즉시 복사 (다시 못 봄)

### ✅ 체크포인트 4

- [ ] 토큰 발급 성공
- [ ] 토큰 만료기간 확정: ____________
- 토큰 일부 (앞 10자): `EAA________` (전체는 안전한 곳에)

---

## 5. 토큰 동작 검증 (터미널)

다음을 본인 환경에서 실행. **`$TOKEN` 부분에 발급받은 토큰 입력**.

### 5-1. 기본 검증 (`/me`)

```bash
TOKEN="EAAxxxxx..."  # 본인 토큰 입력
curl -s "https://graph.facebook.com/v25.0/me?access_token=$TOKEN" | jq
```

기대 응답:
```json
{ "name": "...", "id": "..." }
```

### ✅ 체크포인트 5-1

- [ ] `/me` 응답 정상
- 응답: ____________

### 5-2. 광고 계정 목록

```bash
curl -s "https://graph.facebook.com/v25.0/me/adaccounts?fields=id,name,currency,timezone_name,account_status&access_token=$TOKEN" | jq
```

기대 응답: 광고 계정 배열. 각 항목에 `id` (예: `act_123456...`), `name`, `currency`, `account_status`

### ✅ 체크포인트 5-2

- [ ] 광고 계정 목록 받음
- 계정 개수: ____
- 계정 통화: ____ (KRW일 가능성, 다를 수도 있음 — 스펙에 영향)
- 계정 ID 1개 (테스트용): ____________

### 5-3. 실제 Insights 호출 (the killer test)

```bash
ACCOUNT="act_xxxxx"  # 위에서 확인한 계정
curl -s "https://graph.facebook.com/v25.0/$ACCOUNT/insights?fields=spend,impressions,clicks,ctr,cpm,reach,frequency,actions,action_values,purchase_roas&date_preset=last_7d&level=account&access_token=$TOKEN" | jq
```

### ✅ 체크포인트 5-3 ⭐

- [ ] **Insights 응답이 정상으로 옴 (data 배열에 값)**: ____
- [ ] 또는 빈 응답이지만 에러는 없음: ____
- [ ] 또는 권한 에러 발생: ____ (이 경우 결과 기록)
- `purchase_roas` 응답 구조: `[{"action_type":"omni_purchase","value":"..."}]` 형태인가?: ____
- `spend` 값의 타입: 숫자(int)인가 문자열("원" 단위)인가?: **____**
- `actions` 응답에 `attribution_window` 정보가 어떻게 표현되는가?: ____

### 5-4. Rate limit 헤더 확인

```bash
curl -sI "https://graph.facebook.com/v25.0/$ACCOUNT/insights?fields=spend&date_preset=last_7d&level=account&access_token=$TOKEN" | grep -i "business-use-case-usage"
```

### ✅ 체크포인트 5-4

- [ ] `X-Business-Use-Case-Usage` 헤더 존재
- 헤더 값 (JSON): ____________
- BUC 버킷 종류 (ads_management / ads_insights / 둘 다 / 다른 이름): ____

### 5-5. 캠페인/광고세트/광고 객체 호출

```bash
# 캠페인
curl -s "https://graph.facebook.com/v25.0/$ACCOUNT/campaigns?fields=id,name,objective,status,daily_budget,lifetime_budget&access_token=$TOKEN" | jq '.data[0]'

# 광고
curl -s "https://graph.facebook.com/v25.0/$ACCOUNT/ads?fields=id,name,creative,status&limit=3&access_token=$TOKEN" | jq
```

### ✅ 체크포인트 5-5

- [ ] 캠페인 목록 정상
- 캠페인 `objective` 실제 값 (ODAX인가 레거시인가): ____________
- [ ] 광고 목록 정상

---

## 6. 동영상 광고 메트릭 검증 (있는 경우)

본인 계정에 동영상 광고가 있다면:

```bash
# 동영상 광고 ID 1개 확보 후
AD="..."
curl -s "https://graph.facebook.com/v25.0/$AD/insights?fields=video_play_actions,video_continuous_2_sec_watched_actions,video_15_sec_watched_actions,video_p25_watched_actions,video_p50_watched_actions,video_p75_watched_actions,video_p100_watched_actions,video_avg_time_watched_actions,video_thruplay_watched_actions&date_preset=last_30d&access_token=$TOKEN" | jq
```

### ✅ 체크포인트 6

- [ ] 동영상 메트릭 호출 성공
- `video_continuous_2_sec_watched_actions` 응답: ____________
- `video_p95_watched_actions` 시도해보면 어떻게 됨? (있음/없음/에러): ____________
- `video_30_sec_watched_actions` 시도해보면? (deprecated 경고/에러/조용히 동작): ____________
- 실제 응답 형태 (action_type + value 배열인가, 단일 값인가): ____

---

## 7. Quality Ranking enum 검증 (광고 1주 이상 집행한 경우)

```bash
curl -s "https://graph.facebook.com/v25.0/$AD/insights?fields=quality_ranking,engagement_rate_ranking,conversion_rate_ranking&date_preset=last_30d&access_token=$TOKEN" | jq
```

### ✅ 체크포인트 7

- 실제 반환된 `quality_ranking` 값: ____________
- `BELOW_AVERAGE_35` / `BELOW_AVERAGE_20` / `BELOW_AVERAGE_10` 형태가 맞는가, 아니면 `BELOW_AVERAGE` 등 다른 형태인가?: ____

---

## 8. 끝 — 종합

### 8-1. 시간 측정

- 시작 시각 (0번): ____________
- 종료 시각: ____________
- **총 소요 시간**: ____ 분
- 가장 시간 많이 걸린 단계: ____________

### 8-2. 핵심 결론

다음 질문에 본인 답변 기록:

1. **"5분 설치 영상"으로 최종 사용자가 따라 할 수 있는가?**
   - 가능 / 불가능 (10분 이상 필요) / 가능하지만 영상 여러 편 분할 필요
   - 결론: ____________

2. **본인 같이 마케팅 분야 사람이 developer.facebook.com을 처음 쓴다면 가장 막힐 곳은?**
   - ____________

3. **Dev Tier로도 본 프로젝트가 약속하는 분석이 다 가능한가?**
   - 가능 / Insights API 일부만 / 아예 안 됨
   - 결론: ____________

4. **App Review가 정말 회피 가능한가?**
   - 회피 가능 (Dev Tier로 충분) / 회피 불가 (rate limit 부족) / 일부 기능만 회피 가능
   - 결론: ____________

5. **토큰 만료기간 무기한이 정말 가능한가?**
   - 가능 / 60일이 최대 / 비즈니스 인증 필요
   - 결론: ____________

6. **`spend` 값의 타입은 무엇인가?**
   - int / string decimal / 다른 형태
   - 결론: ____________ (스펙의 `지출액: int` 수정 여부 결정)

7. **`purchase_roas` 응답 구조는 어떤가?**
   - 단일 값 / action_type 배열 / attribution window 별 다름
   - 결론: ____________ (스펙의 `ROAS: float | None` 수정 여부 결정)

### 8-3. 발견한 추가 이슈

리스트:
- ____________
- ____________

---

## POC 결과 처리

이 체크리스트 마치면 다음 단계:

1. 본 문서 채워넣기 (커밋)
2. 결과를 봐서 스펙 v2의 §3, §7, §10에 반영
3. 그래도 5분 설치 불가능하다면:
   - 옵션 (a) 페르소나 재조정 (테크 친화 사용자만 타겟)
   - 옵션 (b) 영상 시리즈 재구성 (설치 영상을 1편 → 3편으로 분할)
   - 옵션 (c) 원클릭 인스톨러 추가 검토
   - 옵션 (d) 프로젝트 전제 자체 재검토

체크리스트 결과 채워주시면 다음 작업 (스펙 v2 작성)으로 진행합니다.
