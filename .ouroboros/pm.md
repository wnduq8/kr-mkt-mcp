# kr-mkt-mcp

*Created At: 2026-05-05T09:22:16.183464+00:00*

## Goal

한국 마케터의 '엑셀 복붙 노가다 + 수동 분석' 워크플로우를 MCP 데이터 인출 레이어로 대체하여, AI(Claude/Codex)가 자연어 질문에 대해 광고 성과 분석·리포트를 자동 생성할 수 있게 한다.

## User Stories

1. **As a** 인하우스 마케터 (primary), **I want to** 매일 아침 Meta 광고 성과를 자연어로 질문, **so that** 광고관리자 로그인 → CSV 다운 → 엑셀 분석 루틴을 AI 한 줄 질문으로 대체.
2. **As a** 1인 사업자 (primary), **I want to** ROAS/CPA 등 핵심 지표를 AI에게 물어봄, **so that** 광고 성과 파악에 전문 분석 능력 없이도 원인/결과/액션 형태의 인사이트 획득.
3. **As a** 대행사 AE (secondary), **I want to** 여러 클라이언트 광고 계정의 성과를 계정 전환 없이 조회, **so that** 멀티 계정 데일리 점검 시간 단축, 이상 캠페인 즉시 탐지.
4. **As a** 마케터 (공통), **I want to** 광고소재(카피/이미지/CTA) 성과를 AI에게 진단 요청, **so that** 소재별 성과 비교 + 개선 제안을 한 대화에서 완결.
5. **As a** 마케터 (공통), **I want to** 연령/성별/지면별 성과 분해를 자연어로 요청, **so that** breakdown 분석을 위해 별도 피벗 테이블 만들 필요 없음.
6. **As a** 마케터 (공통), **I want to** 주간/월간 기간 비교 성과 리포트 요청, **so that** AI가 두 기간 데이터를 비교해 변화 원인과 액션 제안.

## Constraints

- 1인 OSS 개발자: SaaS·백엔드·DB·결제·라이선스·계정 시스템 모두 거부. 코드 + 콘텐츠 IP만 자산
- 운영 부담 0: 서버 운영, 사용자 관리, 인프라 유지 일체 없음
- MCP 전체 read-only: 모든 도구(raw passthrough 포함) HTTP GET only 강제. 광고 변경 불가
- V1 플랫폼: Meta Ads(Facebook+Instagram) only. 네이버/카카오 등은 V2+
- 인증: META_ACCESS_TOKEN env var만. OAuth flow·계정 시스템 없음
- AI 컨텍스트 토큰 한계: MCP 데이터에 할당 가능한 공간 ~50-100k tokens
- Meta API rate limit 준수 (Dev Tier 시간당 300 호출)
- Python 구현 (데이터 분석 생태계 고려)
- stdio 연결 (Claude Desktop/Codex 등 MCP 호스트)
- 페이지네이션 자동 fetch + 200건 hard cap (토큰 폭발 방지)
- 수익화 후순위: 라이선스/구독/Open Core 거부

## Success Criteria

1. 데일리 점검 워크플로우가 get_performance 1회 호출로 완결됨
2. 6개 핵심 워크플로우(데일리 점검, 주간 회고, 소재 진단, 타겟팅 분해, 예산 ROI, 피로도 체크) 모두 V1 도구 조합으로 커버
3. 인하우스/1인 마케터(캠페인 5-50개)의 일상 질문 80%+가 디폴트 파라미터만으로 답변 가능
4. YouTube 영상 따라하면 설치+토큰 발급+첫 질문까지 완료 가능한 온보딩 UX
5. 토큰 효율: tier1(10개 메트릭) + top-N(디폴트 10) + last_7d 디폴트로 단일 호출 응답이 50k tokens 이내
6. 멀티 계정 대행사 AE도 list_ad_accounts → account_id 지정으로 자연스럽게 지원
7. raw passthrough(call_meta_api)로 V1 비커버 edge case에도 도망구 제공

## Assumptions

- 타겟 사용자는 Meta Business Manager 접근 권한이 있어 System User Token 발급 가능
- 인하우스/1인 마케터의 활성 캠페인 수는 대부분 5-50개 범위
- AI(Claude/Codex)가 자연어 → Meta API snake_case 메트릭 매핑을 tool description 사전만으로 정확히 수행 가능
- Meta Marketing API v21.0이 V1 개발·출시 기간 동안 안정적으로 유지됨
- MCP 호스트(Claude Desktop 등)가 env var 주입 메커니즘(mcp config JSON)을 제공함
- 사용자가 YouTube 영상을 보고 Meta API 토큰 발급을 5-10분 내 완료할 수 있음
- tier1 메트릭 10개(impressions, reach, frequency, clicks, spend, cpm, cpc, ctr, purchase_roas, purchases)로 일상 질문 80% 커버 가능
- Meta API GET 요청만으로는 광고 계정에 변경이 불가능 (read-only 안전 보장)
- MCP의 역할은 데이터 인출에 한정, 분석/인사이트/리포트 생성은 AI 호스트 책임
- 정규화된 flat list[dict] 응답 포맷이 AI의 후속 계산·비교·정렬에 최적

## Decide Later

The following items were deferred or identified as premature at this stage. They should be revisited when more context is available:

- '최근 운영 캠페인(active/recent)' 정의: effective_status ACTIVE? 최근 N일 내 spend > 0? Meta API 어떤 필드로 판단?
- tier='all' 풀 필드셋의 정확한 목록 (어트리뷰션 윈도우 분해, 동영상 메트릭, 소재 품질 등급 포함 범위)
- 어트리뷰션 윈도우 디폴트 (예: ['1d_click','7d_click']) 및 응답 평탄화 규칙
- ALL_COMMON 필드셋이 level별(account/campaign/adset/ad)로 다르게 정의되는지
- top-N 디폴트 N값 (5? 10? — 현재 10으로 잠정)
- list_ad_accounts 반환 필드 범위 (id, name, currency, status 외 business_id, timezone 등)
- 사용자가 계정 이름을 아예 안 말했을 때 AI 동작 (단일 계정 자동 진행? 되묻기?)
- 디폴트 필터로도 토큰 예산 초과(활성 캠페인 500+) 시 동작 (페이지네이션? 에러 메시지? truncate?)
- raw passthrough(call_meta_api) 안전장치 상세 명세 (params validation 수준, rate limit 카운터)
- AI에게 'tier1 → 디테일 → raw' 결정 위계를 가르치는 description 가이드라인 상세
- Meta App permission을 ads_read만 요청할지 (토큰 발급 단계 UX/난이도 영향)
- '이 MCP는 read-only' 사실을 사용자에게 노출하는 위치 (README? 설치 영상? tool description?)
- override metrics 시 허용 풀 — tier1만? 디테일 도구 영역(동영상/어트리뷰션) 메트릭까지?
- breakdown 사용 시 top-N 정렬 기준이 breakdown value 내인지 캠페인 전체 기준인지
- CAROUSEL creative의 cards nested 구조 정확한 스키마
- V2+ 플랫폼 확장: 네이버 검색광고, 카카오모먼트, Google Ads, TikTok, X 등 (같은 MCP 안에 추가)
- Multi-breakdown 지원 (age+gender 교차 분석 등) — V1은 단일 breakdown만
- 별도 list_adsets 도구 (V1에서는 get_performance(level='adset') + call_meta_api로 커버)
- Write 기능 (캠페인 일시중지, 예산 변경 등) — read-only 원칙 유지
- 분석 도구 (analyze_performance) — AI가 직접 비교·이상치 판단 담당
- 리포트 생성 도구 (generate_report) — AI가 마크다운 포맷 직접 생성
- 수익 모델 구체화 (운영 부담 0 제약 내에서)
- 한국어 alias 매핑 레이어를 MCP 코드에 내장하는 옵션 (V1은 tool description + AI 번역)

---
*PM ID: pm_seed_interview_20260505_072056*
*Interview ID: interview_20260505_072056*
