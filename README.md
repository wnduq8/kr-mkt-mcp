# kr-mkt-mcp

한국 마케터를 위한 Meta Ads 분석 MCP 서버.

Claude Desktop, Codex CLI 등 MCP 호스트에 연결하면 Facebook/Instagram 광고 데이터를 자연어로 질문하고 AI가 분석·리포트를 생성합니다.

V1: **Meta Ads only**, **read-only** (광고 변경 불가). V2+에서 네이버/카카오 등 한국 플랫폼 추가 예정.

---

## ⚡ AI에게 설치 시키기 (가장 빠름)

`Claude Code` 또는 `Claude Desktop + filesystem MCP`가 켜져 있으면, 아래 프롬프트를 그대로 복사해서 Claude에게 보내세요. AI가 README를 읽고 config 편집까지 자동으로 처리합니다.

```
이 GitHub 저장소의 MCP 서버를 내 Claude Desktop에 설치해줘:
https://github.com/wnduq8/kr-mkt-mcp

조건:
- 내 META_ACCESS_TOKEN: <여기에_발급한_토큰_붙여넣기>
- ~/Library/Application Support/Claude/claude_desktop_config.json 의 mcpServers 항목에 추가
- 기존 다른 MCP 항목은 보존
- 설치 끝나면 Claude Desktop 재시작 안내
```

토큰이 없으면 먼저 [Meta API 토큰 발급](#meta-api-토큰-발급-510분) 단계부터.

---

## 🛠 수동 설치 (3가지 방법)

### A. uvx로 PyPI에서 설치 (권장 — 1줄)

[uv](https://docs.astral.sh/uv/) 설치 후:

```bash
uvx kr-mkt-mcp
```

자동 격리 환경에 최신 버전 다운로드 + stdio 서버 실행. Claude Desktop config:

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

### B. uvx로 GitHub에서 직접 설치 (PyPI 미경유)

PyPI를 거치지 않고 GitHub에서 바로 받고 싶으면:

```json
{
  "mcpServers": {
    "kr-mkt-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/wnduq8/kr-mkt-mcp",
        "kr-mkt-mcp"
      ],
      "env": {
        "META_ACCESS_TOKEN": "발급한_토큰_여기에"
      }
    }
  }
}
```

특정 버전 고정은 `git+https://github.com/wnduq8/kr-mkt-mcp@v0.1.0` 형식.

### C. pip 설치 (uvx 없는 환경)

```bash
pip install kr-mkt-mcp
```

config:

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

> Claude Desktop이 `kr-mkt-mcp` 명령을 PATH에서 못 찾으면 절대경로로 지정 (`/Users/.../bin/kr-mkt-mcp`).

---

## Meta API 토큰 발급 (5–10분)

1. [Meta for Developers](https://developers.facebook.com/) 로그인.
2. [Business Manager](https://business.facebook.com/) → 비즈니스 설정 → "사용자" → "시스템 사용자" → 새 시스템 사용자 생성 (이름: 예 `kr-mkt-mcp`).
3. 시스템 사용자에게 광고 계정 권한 할당 — **분석(분석가)** 권한만(read-only). "광고 게재" 권한 부여 금지.
4. 시스템 사용자에서 "토큰 생성" → 앱 선택 → **`ads_read` 권한만 체크** (다른 권한 불필요). 만료일 영구 토큰 권장.
5. 생성된 토큰 복사. 다음 단계에서 사용.

> 보안 노트: 본 MCP 서버는 read-only로 동작하지만 토큰 자체에 추가 권한을 부여하면 다른 도구·코드가 그 권한을 쓸 수 있습니다. `ads_read`만 발급해서 위험을 원천 차단하세요.

> Meta API 버전 노트: 디폴트 버전은 `v21.0`. Meta가 새 버전을 deprecate하면 `META_API_VERSION=v22.0` env 추가로 override 가능. 또는 `call_meta_api`의 `endpoint`에 `/v22.0/...` 형식으로 직접 명시.

---

## Claude Desktop config 위치

| OS | 경로 |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

수정 후 Claude Desktop **완전 종료 후 재시작**해야 반영됩니다.

---

## Codex CLI / 다른 MCP 호스트

호스트의 MCP 설정 형식에 따라 동일하게 `command` + `args` + `env` 지정.

---

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

---

## 첫 사용 — 핵심 워크플로우 6개

설치 후 Claude에 다음 패턴으로 질문:

| 워크플로우 | 예시 질문 |
|---|---|
| 데일리 점검 | "어제 광고 성과 어땠어? 이상한 캠페인 있어?" |
| 주간 회고 | "지난주 vs 그 전주 ROAS 비교해줘" |
| 광고소재 진단 | "어떤 광고 카피가 가장 잘 나와?" |
| 타겟팅 분해 | "연령별로 어떤 캠페인 잘 됐어?" |
| 예산 ROI | "광고비 대비 매출 어디에 더 투자해야 해?" |
| 피로도 체크 | "frequency 너무 높은 캠페인 있어?" |

---

## 자주 묻는 질문

### "이 MCP는 광고를 변경할 수 있나요?"

**아니요.** HTTP GET만 호출하고, write method를 호출할 수 있는 코드 자체가 없습니다. 토큰을 `ads_read`로만 발급하면 추가 안전장치가 됩니다.

### "토큰 발급이 5분 만에 가능한가요?"

Meta 비즈니스 매니저가 이미 설정되어 있고 광고 계정이 그 안에 있으면 5분 가능. 신규 계정/비즈니스라면 검수 단계 없이 시스템 사용자만으로도 ads_read 토큰 발급 가능합니다 (Standard Access App Review 불필요).

### "다른 광고 플랫폼은 언제?"

V2+. 네이버 검색광고, 카카오모먼트, Google Ads, TikTok 등을 같은 MCP 안에 모듈로 추가할 계획. V1 출시 후 영상 피드백 보고 우선순위 결정.

### "에러 트러블슈팅"

| 증상 | 원인 / fix |
|---|---|
| 도구가 안 보임 | 1) config JSON 문법 오류 2) Claude Desktop 미재시작 3) `uvx`가 PATH에 없음 |
| `META_ACCESS_TOKEN 환경 변수가 필요합니다` | env에 토큰 추가 안 했거나 오타 |
| `(401) Invalid OAuth access token` | 토큰 만료/오타 — Meta for Developers에서 재발급 |
| `(403) ads_read permission required` | 시스템 사용자에 ads_read 권한 미할당 |
| 도구 호출 시 멈춤 | 로그 확인: macOS `~/Library/Logs/Claude/mcp*.log` |

---

## 개발자용

### 소스에서 설치

```bash
git clone https://github.com/wnduq8/kr-mkt-mcp
cd kr-mkt-mcp
uv venv .venv --python 3.12
uv pip install -e ".[dev]" --python .venv/bin/python
.venv/bin/pytest
```

### 구조

```
src/kr_mkt_mcp/
├── config.py              # env 로딩 + V1 상수
├── meta_client.py         # GET-only HTTP wrapper + 페이지네이션
├── normalize.py           # Meta API → flat list[dict]
├── dates.py               # date_preset → since/until
├── descriptions.py        # 한국어 tool description
├── server.py              # FastMCP stdio entry
└── tools/                 # 6개 도구
```

### 기여

PR 환영. 단 V1 sticky 결정 사항(`docs/superpowers/plans/2026-05-05-kr-mkt-mcp-v1.md` 참고)은 변경 시 plan 갱신 필요.

---

## 라이선스

MIT — `LICENSE` 참고.
