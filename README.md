# kr-mkt-mcp

한국 마케터를 위한 **Meta Ads 분석 MCP 서버**.

Claude Desktop / Codex CLI 등에 연결하면 Facebook + Instagram 광고 데이터를 자연어로 질문하고 AI가 분석·리포트·액션 제안을 자동 생성합니다.

V1 범위: **Meta Ads only**, **read-only** (광고 변경·일시중지 등 쓰기 작업 절대 불가).

---

## 🤖 가장 빠른 설치 — AI에게 부탁하기

`Claude Code`나 `Claude Desktop + filesystem MCP`가 활성화된 환경이면 아래 프롬프트를 그대로 복사해 보내면 됩니다. AI가 README를 읽고 uv 설치 여부 확인 + config 편집까지 자동 처리합니다.

### Windows 사용자

```
이 GitHub 저장소의 MCP 서버를 내 Claude Desktop에 설치해줘:
https://github.com/wnduq8/kr-mkt-mcp

내 환경:
- 운영체제: Windows
- META_ACCESS_TOKEN: <여기에_발급한_토큰_붙여넣기>

설치 순서:
1. PowerShell에서 `uv --version`을 실행해 uv가 설치돼 있는지 확인
2. 없으면 다음 명령으로 먼저 설치하라고 안내:
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   설치 후 PowerShell을 닫고 새로 열어야 PATH 반영됨
3. %APPDATA%\Claude\claude_desktop_config.json 파일을 메모장으로 열어
   mcpServers 객체에 kr-mkt-mcp 항목 추가 (기존 항목 있으면 보존)
4. 시스템 트레이의 Claude 아이콘 우클릭 → Quit → 재실행으로 완전 재시작
5. 새 채팅에서 "내 Meta 광고 계정 알려줘"로 동작 확인
```

### macOS 사용자

```
이 GitHub 저장소의 MCP 서버를 내 Claude Desktop에 설치해줘:
https://github.com/wnduq8/kr-mkt-mcp

내 환경:
- 운영체제: macOS
- META_ACCESS_TOKEN: <여기에_발급한_토큰_붙여넣기>

설치 순서:
1. Terminal에서 `uv --version`으로 uv 설치 확인
2. 없으면 `curl -LsSf https://astral.sh/uv/install.sh | sh`로 설치 후 새 터미널 오픈
3. ~/Library/Application Support/Claude/claude_desktop_config.json의 mcpServers에
   kr-mkt-mcp 항목 추가 (기존 항목 보존)
4. cmd+Q로 Claude Desktop 완전 종료 후 재실행
5. 새 채팅에서 "내 Meta 광고 계정 알려줘"로 동작 확인
```

토큰이 없으면 → 아래 [Meta API 토큰 발급](#meta-api-토큰-발급-510분) 먼저.

---

## 🪟 Windows 직접 설치 (수동)

### 1. uv 설치 (한 번만)

**PowerShell**을 관리자 권한 없이 새로 열어서:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

설치 끝나면 **PowerShell을 닫고 새로 열어야** PATH가 갱신됩니다. 새 PowerShell에서 확인:

```powershell
uv --version
```

`uv 0.x.x` 같은 버전이 보이면 OK. `'uv'은(는) 내부 또는 외부 명령... 으로 인식되지 않습니다` 에러가 나면 PowerShell을 다시 열거나, 아래 절대경로 방법 참고.

> **PowerShell 미숙자**: 시작 메뉴 → "Windows PowerShell" 검색 → 클릭. 관리자 권한 불필요.

### 2. 토큰 준비

[Meta API 토큰 발급](#meta-api-토큰-발급-510분) 섹션 참고. **`ads_read` 권한만** 발급.

### 3. Claude Desktop config 편집

**PowerShell**에서:

```powershell
notepad $env:APPDATA\Claude\claude_desktop_config.json
```

파일이 없다고 메모장이 새로 만들겠다고 물으면 "예" → 빈 메모장이 열림.

다음 내용으로 저장:

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

> 이미 다른 MCP 서버(예: cafe24-catalog-mcp)가 들어있으면 `mcpServers` 객체 안에 **`kr-mkt-mcp` 항목만 추가**하고 기존 항목은 그대로 둘 것.

> **`여기에_발급한_토큰_붙여넣기`** 부분만 본인 토큰으로 교체.

저장 후 메모장 닫기.

### 4. Claude Desktop 완전 재시작

**창 X 버튼만 눌러선 안 됩니다.** 트레이 아이콘에서 종료해야 함:

1. 화면 우측 하단 시스템 트레이의 **^** (위로 화살표) 클릭 → 숨겨진 아이콘 펼치기
2. **Claude 아이콘 우클릭** → **Quit** 선택
3. 다시 시작 메뉴에서 Claude 실행

작업 관리자(Ctrl+Shift+Esc)에서 "Claude" 프로세스가 모두 사라졌는지 확인하면 더 확실.

### 5. 동작 확인

새 채팅 창에 입력:

```
내 Meta 광고 계정 알려줘
```

AI가 도구 호출 권한 승인을 요청 → **승인** → 광고 계정 목록이 표시되면 ✅

---

## 🍎 macOS 직접 설치 (수동)

### 1. uv 설치

Terminal에서:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

또는 Homebrew:

```bash
brew install uv
```

설치 후 새 터미널 열어서 `uv --version` 확인.

### 2. config 편집

Terminal에서:

```bash
open -e "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
```

파일 없다고 에러나면:

```bash
mkdir -p "$HOME/Library/Application Support/Claude"
echo '{"mcpServers":{}}' > "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
open -e "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
```

내용은 위 [Windows 3단계 JSON](#3-claude-desktop-config-편집)과 동일.

### 3. 재시작

`cmd + Q`로 Claude Desktop 종료 후 재실행.

### 4. 동작 확인

`내 Meta 광고 계정 알려줘`

---

## Meta API 토큰 발급 (5–10분)

1. [Meta for Developers](https://developers.facebook.com/) 로그인
2. [Business Manager](https://business.facebook.com/) → **비즈니스 설정** → **사용자** → **시스템 사용자** → 새로 생성
3. 시스템 사용자에게 광고 계정 권한 할당 — **분석가** 권한만 (광고 게재 권한 부여 X)
4. **토큰 생성** → 앱 선택 → 권한은 **`ads_read`만 체크** → 만료일 영구 권장
5. 생성된 토큰 복사 → config의 `META_ACCESS_TOKEN` 값으로 사용

> 보안: `ads_read`만 발급해야 토큰 노출 시에도 광고 변경/계정 정보 유출 위험 차단.

---

## 🔧 Windows 트러블슈팅

| 증상 | 해결 |
|---|---|
| **`'uv'은(는) ... 인식되지 않습니다`** | PowerShell을 닫고 새로 열기 (PATH 갱신). 그래도 안 되면 절대경로: `command`를 `"%USERPROFILE%\.local\bin\uvx.exe"`로 |
| **Claude Desktop에서 kr-mkt-mcp가 안 보임** | 1) JSON 문법 오류 — [JSONLint](https://jsonlint.com/)로 검증 2) Claude Desktop 미재시작 (트레이 Quit 필수) |
| **"failed" / "Server disconnected"** | 로그 확인: PowerShell에서 `Get-Content "$env:APPDATA\Claude\logs\mcp-server-kr-mkt-mcp.log" -Tail 30` |
| **`META_ACCESS_TOKEN 환경 변수가 필요합니다`** | config의 토큰 자리에 `여기에_발급한_토큰_붙여넣기`가 그대로 남아있음. 본인 토큰으로 교체 |
| **`(401) Invalid OAuth access token`** | 토큰 만료/오타. Meta for Developers에서 재발급 후 config 업데이트 |
| **`(403) ads_read permission required`** | 시스템 사용자에 ads_read 권한 미할당. Business Manager에서 자산 추가 다시 |
| **사용자 폴더 한글 (예: `C:\Users\한글이름`)** | Python 일부 환경에서 한글 경로 미지원. 영문 사용자 계정으로 재설치 권장 |
| **Defender / SmartScreen 차단** | uv/Python 첫 실행 시 차단되면 "추가 정보 → 실행" 선택. 또는 정책 따라 예외 추가 |

---

## 라이선스

MIT — `LICENSE` 참고.
