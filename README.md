# kr-mkt-mcp

한국 마케터를 위한 **Meta Ads 분석 MCP 서버**.

Claude Desktop / Codex CLI 등 MCP 호스트에 연결하면 Facebook + Instagram 광고 데이터를 자연어로 질문하고 AI가 분석·리포트·액션 제안을 자동 생성합니다.

V1 범위: **Meta Ads only**, **read-only** (광고 변경·일시중지 등 쓰기 작업 절대 불가능). V2+에서 네이버 검색광고/카카오모먼트/Google Ads/TikTok 등 추가 예정.

---

## 📑 목차

1. [⚡ 5분 설치 (직접 따라하기)](#-5분-설치-직접-따라하기)
2. [🤖 AI에게 설치 부탁하기](#-ai에게-설치-부탁하기)
3. [Meta API 토큰 발급 (5–10분)](#meta-api-토큰-발급-510분)
4. [첫 사용 — 핵심 워크플로우 6개](#첫-사용--핵심-워크플로우-6개)
5. [트러블슈팅](#트러블슈팅)
6. [업데이트 / 삭제](#업데이트--삭제)
7. [V1 도구 6개 (참고)](#v1-도구-6개-참고)
8. [FAQ](#faq)
9. [개발자용](#개발자용)

---

## ⚡ 5분 설치 (직접 따라하기)

### 준비물 체크

| 항목 | 확인 방법 |
|---|---|
| **Claude Desktop** | [claude.ai/download](https://claude.ai/download) 설치되어 있어야 함 |
| **Meta API 토큰** | 아직 없으면 → [Meta API 토큰 발급](#meta-api-토큰-발급-510분) 먼저 |
| **uv** (Python 패키지 매니저) | 1단계에서 설치 |

---

### 1. uv 설치

[uv](https://docs.astral.sh/uv/)는 Python 패키지를 자동 격리·다운로드해주는 도구입니다. 본 MCP 서버를 별도 설치 없이 실행하기 위해 필요합니다.

#### macOS / Linux

터미널에서 한 줄:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

또는 Homebrew:

```bash
brew install uv
```

#### Windows

PowerShell에서 한 줄:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### ✅ 설치 확인 (양쪽 OS 공통)

**새 터미널/PowerShell 창을 열고** (PATH 갱신을 위해 필수):

```bash
uvx --version
```

`uv-x.x.x` 같은 버전 문자열이 보이면 성공.

---

### 2. Claude Desktop config 파일 열기

config 파일 위치는 OS별로 다릅니다.

| OS | 경로 |
|---|---|
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |

#### 빠르게 여는 방법

**macOS** — 터미널에서:

```bash
open -e "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
```

파일이 없다는 에러가 나면 먼저 생성:

```bash
mkdir -p "$HOME/Library/Application Support/Claude"
echo '{"mcpServers":{}}' > "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
open -e "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
```

**Windows** — PowerShell에서:

```powershell
notepad $env:APPDATA\Claude\claude_desktop_config.json
```

파일이 없으면 새로 만들겠다고 묻는 창에 "예" → 빈 메모장이 열림 → 일단 `{"mcpServers":{}}` 입력 후 저장하고 재오픈.

---

### 3. config에 kr-mkt-mcp 항목 추가

#### 처음 설치하는 경우 (다른 MCP 없음)

파일 내용 전체를 다음으로 교체:

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
        "META_ACCESS_TOKEN": "여기에_발급한_토큰_붙여넣기"
      }
    }
  }
}
```

#### 다른 MCP가 이미 있는 경우 (cafe24-catalog-mcp 등)

기존 `mcpServers` 객체 안에 `kr-mkt-mcp` 항목만 추가. 예시:

```json
{
  "mcpServers": {
    "cafe24-catalog-mcp": {
      "command": "npx",
      "args": ["mcp-remote", "https://mcp-catalog.cafe24.com/api/mcp"]
    },
    "kr-mkt-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/wnduq8/kr-mkt-mcp",
        "kr-mkt-mcp"
      ],
      "env": {
        "META_ACCESS_TOKEN": "여기에_발급한_토큰_붙여넣기"
      }
    }
  }
}
```

> **중요**: `여기에_발급한_토큰_붙여넣기` 부분만 본인 Meta API 토큰으로 교체. 다른 부분은 그대로.

#### ✅ JSON 문법 검증

저장 후 콤마(`,`)·따옴표(`"`)·중괄호(`{}`)가 잘 닫혔는지 확인. 의심스러우면 [JSONLint](https://jsonlint.com/)에 붙여넣어 검증.

---

### 4. Claude Desktop 완전 재시작

**창 닫기만으로는 안 됩니다.** 완전 종료 후 재실행:

| OS | 종료 방법 |
|---|---|
| **macOS** | `cmd + Q` 또는 dock 아이콘 우클릭 → "종료" |
| **Windows** | 시스템 트레이(우측 하단) Claude 아이콘 우클릭 → "Quit" |

종료 후 다시 실행.

---

### 5. ✅ 설치 확인

Claude Desktop 새 채팅 창에서:

```
내 Meta 광고 계정 알려줘
```

AI가 도구 호출 승인을 요청하면(권한 팝업) **승인** → `kr-mkt-mcp`의 `list_ad_accounts` 도구가 실행되어 광고 계정 목록 반환.

설정 화면(`Settings → Developer → 로컬 MCP 서버`)에서 `kr-mkt-mcp` 항목이 **녹색/connected**로 표시되면 정상.

문제 발생 시 → [트러블슈팅](#트러블슈팅) 섹션 참고.

---

## 🤖 AI에게 설치 부탁하기

`Claude Code` 또는 `Claude Desktop + filesystem MCP`가 켜져 있으면, 아래 프롬프트를 그대로 복사해서 Claude에게 보내세요. AI가 README를 읽고 config 편집까지 자동 처리합니다.

### macOS 사용자

```
이 GitHub 저장소의 MCP 서버를 내 Claude Desktop에 설치해줘:
https://github.com/wnduq8/kr-mkt-mcp

조건:
- 내 META_ACCESS_TOKEN: <여기에_발급한_토큰>
- 운영체제: macOS
- ~/Library/Application Support/Claude/claude_desktop_config.json 의 mcpServers 항목에 kr-mkt-mcp 추가
- 기존 다른 MCP 항목은 보존
- 설치 끝나면 Claude Desktop 재시작 안내
```

### Windows 사용자

```
이 GitHub 저장소의 MCP 서버를 내 Claude Desktop에 설치해줘:
https://github.com/wnduq8/kr-mkt-mcp

조건:
- 내 META_ACCESS_TOKEN: <여기에_발급한_토큰>
- 운영체제: Windows
- %APPDATA%\Claude\claude_desktop_config.json 의 mcpServers 항목에 kr-mkt-mcp 추가
- 기존 다른 MCP 항목은 보존
- 설치 끝나면 Claude Desktop 재시작 안내
```

> **주의**: 일반 Claude.ai 웹 버전은 사용자 PC의 파일을 편집할 수 없으므로 위 프롬프트만 단독으로는 설치 못 함. 답변으로 가이드만 받음. 실제 자동 설치는 Claude Code 또는 filesystem MCP가 활성화된 Claude Desktop에서만 가능.

---

## Meta API 토큰 발급 (5–10분)

### 1단계. Meta for Developers 계정

[Meta for Developers](https://developers.facebook.com/) 로그인. (Facebook 계정으로 가입)

### 2단계. Business Manager 진입

[Business Manager](https://business.facebook.com/) → **비즈니스 설정** (Business Settings).

비즈니스 매니저가 없으면 새로 생성. 광고 계정이 이 비즈니스 매니저에 속해 있어야 합니다.

### 3단계. 시스템 사용자 생성

좌측 메뉴 **사용자 → 시스템 사용자** → **새 시스템 사용자 추가**:

- 이름: 예 `kr-mkt-mcp` (자유)
- 시스템 사용자 역할: **직원** (관리자 X)

### 4단계. 광고 계정 권한 할당

생성한 시스템 사용자 → **자산 추가** → **광고 계정** → 분석할 계정 선택 → **분석가** 권한만 체크.

> ⚠️ **광고 게재** 권한은 부여하지 마세요. 본 MCP는 read-only이지만 토큰 자체에 추가 권한이 있으면 다른 도구가 그 권한을 쓸 수 있습니다.

### 5단계. 토큰 생성

시스템 사용자 화면 → **토큰 생성** → 앱 선택 → **권한 체크**:

- ✅ `ads_read` (필수, 그리고 이것만)
- ❌ `ads_management` (체크하지 마세요)
- ❌ `business_management` (체크하지 마세요)

만료일: **영구 토큰** 권장.

### 6단계. 토큰 복사

생성된 토큰 문자열을 복사. **이 화면을 닫으면 다시 볼 수 없으므로** 안전한 곳에 임시 보관.

이 토큰을 [3단계 config](#3-config에-kr-mkt-mcp-항목-추가)의 `META_ACCESS_TOKEN` 값으로 사용.

---

## 첫 사용 — 핵심 워크플로우 6개

설치 후 Claude에 다음 패턴으로 질문해보세요:

| # | 워크플로우 | 예시 질문 |
|---|---|---|
| 1 | **데일리 점검** | "어제 광고 성과 어땠어? 이상한 캠페인 있어?" |
| 2 | **주간 회고** | "지난주 vs 그 전주 ROAS 비교해줘" |
| 3 | **광고소재 진단** | "지난 7일 ROAS 가장 높은 캠페인 5개 찾아주고, 1위 캠페인의 광고 카피 보여줘" |
| 4 | **타겟팅 분해** | "연령별로 어떤 캠페인 잘 됐어?" |
| 5 | **예산 ROI 점검** | "광고비 대비 매출 어디에 더 투자해야 해?" |
| 6 | **피로도 체크** | "frequency 너무 높은 캠페인 있어? CTR 떨어지는 거?" |

광고 계정이 여러 개면 먼저 "내 광고 계정 알려줘" → AI가 계정 목록 받은 후 → 위 질문 시 자연스럽게 어떤 계정인지 되묻거나 추론합니다.

---

## 트러블슈팅

### 공통 문제

| 증상 | 원인 / 해결 |
|---|---|
| **로컬 MCP 서버에 kr-mkt-mcp가 안 보임** | config JSON 문법 오류. [JSONLint](https://jsonlint.com/)로 검증. 또는 Claude Desktop 미재시작 |
| **kr-mkt-mcp 옆에 ⚠️ failed 표시** | 로그 확인 (아래 "로그 보기" 섹션) |
| **`META_ACCESS_TOKEN 환경 변수가 필요합니다`** | config의 token 값을 본인 토큰으로 교체 안 함. `여기에_발급한_토큰_붙여넣기` 그대로 두면 안 됨 |
| **`(401) Invalid OAuth access token`** | 토큰 만료/오타. Meta for Developers에서 재발급 후 config 업데이트 |
| **`(403) ads_read permission required`** | 시스템 사용자에 ads_read 권한 미할당. Business Manager에서 자산 추가 다시 |
| **`(190) Unsupported get request`** | 광고 계정 ID가 잘못됐거나 토큰이 그 계정 권한 없음 |
| **도구 호출은 시작되는데 응답 없음 / 타임아웃** | Meta API rate limit (Dev Tier 시간당 300). 잠시 대기 후 재시도 |

---

### macOS 특정

| 증상 | 해결 |
|---|---|
| **`uvx: command not found`** (Claude Desktop이 spawn 시) | uv가 PATH에 있지만 Claude Desktop이 못 찾는 케이스. config의 `"command": "uvx"`를 절대경로로 교체. 터미널에서 `which uvx` 실행 후 그 경로 (예: `/Users/yourname/.local/bin/uvx` 또는 `/opt/homebrew/bin/uvx`)로 |
| **재시작했는데 변경 미반영** | dock에서 우클릭 → 종료. activity monitor에서 Claude 프로세스 잔존 시 강제 종료 |

---

### Windows 특정

| 증상 | 해결 |
|---|---|
| **`uvx is not recognized`** | uv 설치 후 PowerShell 미재시작. 새 PowerShell 창에서 `uvx --version` 확인 |
| **Defender / SmartScreen 차단** | uv 또는 Python 실행 차단 시 "추가 정보 → 실행" 선택. 또는 정책 따라 예외 추가 |
| **사용자 폴더 한글 경로 (예: `C:\Users\한글이름`)** | 일부 Python 패키지가 한글 경로 미지원. 영문 사용자 계정 사용 권장 |
| **재시작했는데 변경 미반영** | 시스템 트레이에서 Quit. 작업 관리자에서 Claude 프로세스 잔존 시 강제 종료 |

---

### 로그 보기

문제 진단에 가장 중요. Claude Desktop은 MCP 서버별 로그를 자동 저장합니다.

| OS | 경로 |
|---|---|
| **macOS** | `~/Library/Logs/Claude/mcp-server-kr-mkt-mcp.log` |
| **Windows** | `%APPDATA%\Claude\logs\mcp-server-kr-mkt-mcp.log` |

#### 빠르게 보기

**macOS**:

```bash
tail -50 "$HOME/Library/Logs/Claude/mcp-server-kr-mkt-mcp.log"
```

**Windows** (PowerShell):

```powershell
Get-Content "$env:APPDATA\Claude\logs\mcp-server-kr-mkt-mcp.log" -Tail 50
```

로그의 마지막 30~50줄에 실제 에러 메시지가 있습니다. 그 메시지를 그대로 [GitHub Issues](https://github.com/wnduq8/kr-mkt-mcp/issues)에 올리거나 Claude에 보여주면 빠른 진단 가능.

---

## 업데이트 / 삭제

### 업데이트

`uvx`가 매 호출마다 git+ URL을 fetch하지만 캐시를 씁니다. 강제 갱신:

**macOS / Linux**:

```bash
uvx --refresh --from git+https://github.com/wnduq8/kr-mkt-mcp kr-mkt-mcp --help
```

**Windows** (PowerShell):

```powershell
uvx --refresh --from git+https://github.com/wnduq8/kr-mkt-mcp kr-mkt-mcp --help
```

(끝의 `--help`는 빠른 종료용. 캐시만 갱신.)

이후 Claude Desktop 재시작.

#### 특정 버전 고정

```json
"args": [
  "--from",
  "git+https://github.com/wnduq8/kr-mkt-mcp@v0.1.0",
  "kr-mkt-mcp"
]
```

`@v0.1.0` 부분을 원하는 git tag 또는 commit SHA로.

---

### 삭제

#### 1. config에서 항목 제거

`claude_desktop_config.json` 열고 `kr-mkt-mcp` 객체 삭제 (앞뒤 콤마 정리).

#### 2. Claude Desktop 재시작

#### 3. uvx 캐시 정리 (선택)

```bash
uv cache prune
```

토큰 자체는 Meta for Developers의 시스템 사용자 화면에서 별도 폐기 가능 (보안상 권장).

---

## V1 도구 6개 (참고)

| 도구 | 역할 | 주요 사용 케이스 |
|---|---|---|
| `list_ad_accounts` | 토큰 권한 내 모든 광고 계정 목록 | 계정 ID 모를 때 첫 호출 |
| `list_campaigns` | 캠페인 메타데이터 (이름·상태·예산·objective) | 특정 캠페인 ID 찾기 |
| `list_ads` | 광고 메타데이터 (이름·상태·소속 캠페인/adset/creative_id) | 광고소재 진단 전단계 |
| `get_performance` | 성과 메트릭 조회 (level × 기간 × breakdown × tier) | **메인 분석 도구** |
| `get_creative_preview` | 광고 본문 (헤드라인·CTA·이미지/동영상 URL) | 광고 카피 분석 |
| `call_meta_api` | Meta Graph API GET 직접 호출 (escape hatch) | 위 5개로 안 되는 edge case |

자세한 파라미터·사용법은 각 도구의 description에서 AI가 자동으로 인지합니다. 사용자는 자연어 질문만 하면 됨.

---

## FAQ

### "이 MCP는 광고를 변경할 수 있나요?"

**아니요.** 코드 자체에 HTTP GET 호출만 있고 POST/PUT/DELETE/PATCH 메서드 자체가 없습니다. 토큰을 `ads_read`로만 발급하면 추가 안전장치가 됩니다.

### "토큰 발급이 진짜 5분 만에 가능한가요?"

이미 Meta 비즈니스 매니저 + 광고 계정이 있으면 5분 가능. 신규라면 비즈니스 매니저 생성 + 광고 계정 추가까지 30분~1시간. 단 Standard Access App Review는 불필요 (시스템 사용자만으로 ads_read 토큰 발급 가능).

### "uvx 외에 다른 설치 방법은?"

가능합니다 — `pip install`로 글로벌 설치 후 절대경로 사용:

```bash
pip install git+https://github.com/wnduq8/kr-mkt-mcp
which kr-mkt-mcp  # 결과 path 복사
```

config:

```json
{
  "mcpServers": {
    "kr-mkt-mcp": {
      "command": "/path/from/which/kr-mkt-mcp",
      "env": { "META_ACCESS_TOKEN": "..." }
    }
  }
}
```

단 가상환경 의존성 격리가 안 되므로 **uvx 권장**.

### "다른 광고 플랫폼은 언제?"

V2+. 네이버 검색광고, 카카오모먼트, Google Ads, TikTok 등을 같은 MCP 안에 모듈로 추가할 계획. V1 출시 후 사용자 피드백 보고 우선순위 결정.

### "내 광고 데이터가 어디로 가나요?"

본 MCP는 stdio로 Claude Desktop과만 통신합니다. **외부 서버에 데이터를 보내지 않습니다.** Meta API 호출 응답은 Claude Desktop에서 AI가 분석하고, 그 분석 결과만 사용자에게 보입니다. AI 호스트(Claude)의 데이터 처리는 Anthropic 정책 따름 (Claude는 학습에 사용하지 않음 옵션 가능).

### "여러 광고 계정 관리 가능한가요?"

네. 토큰에 권한 부여한 모든 계정을 `list_ad_accounts`로 조회 가능. 사용자가 "X 계정의 어제 성과"라고 하면 AI가 ID 매칭해서 호출.

---

## 개발자용

### 소스에서 설치

```bash
git clone https://github.com/wnduq8/kr-mkt-mcp
cd kr-mkt-mcp
uv venv .venv --python 3.12
uv pip install -e ".[dev]" --python .venv/bin/python
.venv/bin/pytest  # 60 tests pass
```

### 로컬 dev로 Claude Desktop 연결 (publish 전 검증용)

```json
{
  "mcpServers": {
    "kr-mkt-mcp-dev": {
      "command": "/path/to/kr-mkt-mcp/.venv/bin/python",
      "args": ["-m", "kr_mkt_mcp.server"],
      "env": {
        "PYTHONPATH": "/path/to/kr-mkt-mcp/src",
        "META_ACCESS_TOKEN": "..."
      }
    }
  }
}
```

`PYTHONPATH=src/`가 핵심 — editable install 상태에 무관하게 src 직접 참조.

### stdio 핸드셰이크 빠른 검증

```bash
.venv/bin/python scripts/verify_stdio.py
```

Meta 토큰 없이 6개 도구 등록 + MCP 프로토콜 응답 확인.

### 구조

```
src/kr_mkt_mcp/
├── config.py              # env 로딩 + V1 상수
├── meta_client.py         # GET-only HTTP wrapper + 페이지네이션
├── normalize.py           # Meta API → flat list[dict]
├── dates.py               # date_preset → since/until
├── descriptions.py        # 한국어 tool description + alias 사전
├── server.py              # FastMCP stdio entry
└── tools/                 # 6개 도구
```

### 기여

PR 환영. 단 V1 sticky 결정 사항(`docs/superpowers/plans/2026-05-05-kr-mkt-mcp-v1.md` 참고)은 변경 시 plan 갱신 필요.

---

## 라이선스

MIT — `LICENSE` 참고.
