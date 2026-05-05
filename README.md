# kr-mkt-mcp

한국 마케터를 위한 Meta Ads 분석 MCP 서버.

Claude Desktop, Codex CLI 등 MCP 호스트에 연결하면 Facebook/Instagram 광고 데이터를 자연어로 질문하고 AI가 분석·리포트를 생성합니다.

V1: **Meta Ads only**, **read-only** (광고 변경 불가). V2+에서 네이버/카카오 등 한국 플랫폼 추가 예정.

## 설치

### 1. uvx로 즉시 실행 (권장)

`uvx`가 설치되어 있다면 별도 설치 없이 바로 사용 가능:

```bash
uvx kr-mkt-mcp
```

### 2. pip 설치

```bash
pip install kr-mkt-mcp
kr-mkt-mcp  # stdio 서버 실행
```

### 3. 소스에서 설치 (개발자용)

```bash
git clone https://github.com/<owner>/kr-mkt-mcp
cd kr-mkt-mcp
pip install -e ".[dev]"
```

## Meta API 토큰 발급 (5–10분)

1. [Meta for Developers](https://developers.facebook.com/) 로그인.
2. [Business Manager](https://business.facebook.com/) → 비즈니스 설정 → "사용자" → "시스템 사용자" → 새 시스템 사용자 생성 (이름: 예 `kr-mkt-mcp`).
3. 시스템 사용자에게 광고 계정 권한 할당 — **분석(분석가)** 권한만(read-only). "광고 게재" 권한 부여 금지.
4. 시스템 사용자에서 "토큰 생성" → 앱 선택 → **`ads_read` 권한만 체크** (다른 권한 불필요). 만료일 영구 토큰 권장.
5. 생성된 토큰 복사. 다음 단계에서 사용.

> 보안 노트: 본 MCP 서버는 read-only로 동작하지만 토큰 자체에 추가 권한을 부여하면 다른 도구·코드가 그 권한을 쓸 수 있습니다. `ads_read`만 발급해서 위험을 원천 차단하세요.

> Meta API 버전 노트: 디폴트 버전은 `v21.0`. Meta가 새 버전을 deprecate하면 `META_API_VERSION=v22.0` env 추가로 override 가능. 또는 `call_meta_api`의 `endpoint`에 `/v22.0/...` 형식으로 직접 명시.

## Claude Desktop 연결

Claude Desktop의 mcp config(`claude_desktop_config.json`)에 다음 항목 추가:

```json
{
  "mcpServers": {
    "kr-mkt-mcp": {
      "command": "uvx",
      "args": ["kr-mkt-mcp"],
      "env": {
        "META_ACCESS_TOKEN": "발급한_토큰_여기에"
      }
    }
  }
}
```

또는 pip 설치 시:

```json
{
  "mcpServers": {
    "kr-mkt-mcp": {
      "command": "kr-mkt-mcp",
      "env": {
        "META_ACCESS_TOKEN": "발급한_토큰_여기에"
      }
    }
  }
}
```

Claude Desktop 재시작 후 채팅에 "내 광고 계정 알려줘"라고 물어보세요.

## Codex CLI / 다른 MCP 호스트

호스트의 MCP 설정 형식에 따라 동일하게 `command` + `args` + `env` 지정.

## V1 도구 6개

| 도구 | 역할 |
|------|------|
| `list_ad_accounts` | 토큰 권한 내 모든 광고 계정 목록 |
| `list_campaigns` | 캠페인 메타데이터 (이름·상태·예산·objective) |
| `list_ads` | 광고 메타데이터 (이름·상태·creative_id) |
| `get_performance` | 성과 메트릭 조회 (level × 기간 × breakdown × tier) |
| `get_creative_preview` | 광고 본문 (헤드라인·CTA·이미지/동영상 URL) |
| `call_meta_api` | Meta Graph API GET 직접 호출 (escape hatch) |

자세한 파라미터·사용법은 각 도구의 description에서 AI가 자동으로 인지합니다.

## 자주 묻는 질문

### "이 MCP는 광고를 변경할 수 있나요?"

**아니요.** HTTP GET만 호출하고, write method를 호출할 수 있는 코드 자체가 없습니다. 토큰을 `ads_read`로만 발급하면 추가 안전장치가 됩니다.

### "토큰 발급이 5분 만에 가능한가요?"

Meta 비즈니스 매니저가 이미 설정되어 있고 광고 계정이 그 안에 있으면 5분 가능. 신규 계정/비즈니스라면 검수 단계 없이 시스템 사용자만으로도 ads_read 토큰 발급 가능합니다 (Standard Access App Review 불필요).

### "다른 광고 플랫폼은 언제?"

V2+. 네이버 검색광고, 카카오모먼트, Google Ads, TikTok 등을 같은 MCP 안에 모듈로 추가할 계획. V1 출시 후 영상 피드백 보고 우선순위 결정.

## 라이선스

MIT.
