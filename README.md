# kr-mkt-mcp

한국 마케터를 위한 **Meta Ads 분석 MCP 서버**.

Claude Desktop / Codex CLI 등에 연결하면 Facebook + Instagram 광고 데이터를 자연어로 질문하고 AI가 분석·리포트·액션 제안을 자동 생성합니다.

V1 범위: **Meta Ads only**, **read-only** (광고 변경·일시중지 등 쓰기 작업 절대 불가).

---

## 🤖 가장 빠른 설치 — AI에게 부탁하기

Claude Code, 또는 filesystem MCP가 켜진 Claude Desktop에 아래 프롬프트를 그대로 복사해 보내면 끝.

```
이 GitHub 저장소의 MCP 서버를 내 Claude Desktop에 설치해줘:
https://github.com/wnduq8/kr-mkt-mcp

내 META_ACCESS_TOKEN: <여기에_발급한_토큰>
```

토큰이 아직 없으면 → 아래 [Meta API 토큰 발급](#meta-api-토큰-발급-510분) 먼저 진행.

---

## 🛠 직접 설치

### 1. uv 설치 (한 번만)

**macOS / Linux**:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows** (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

설치 후 새 터미널 열어 `uvx --version` 확인.

### 2. Claude Desktop config 편집

config 파일 위치:

| OS | 경로 |
|---|---|
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |

`mcpServers` 객체에 다음 항목 추가 (기존 다른 MCP 항목이 있으면 그대로 두고 옆에 붙이기):

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

> `여기에_발급한_토큰_붙여넣기` 부분만 본인 토큰으로 교체.

### 3. Claude Desktop 완전 재시작

- **macOS**: `cmd + Q` 후 재실행
- **Windows**: 시스템 트레이 Claude 아이콘 우클릭 → Quit 후 재실행

(창 닫기만으론 안 됨)

### 4. 확인

새 채팅 창에 입력:

```
내 Meta 광고 계정 알려줘
```

AI가 도구 호출 권한 승인 요청 → 승인 → 광고 계정 목록이 보이면 ✅

---

## Meta API 토큰 발급 (5–10분)

1. [Meta for Developers](https://developers.facebook.com/) 로그인
2. [Business Manager](https://business.facebook.com/) → **비즈니스 설정** → **사용자** → **시스템 사용자** → 새로 생성
3. 시스템 사용자에게 광고 계정 권한 할당 — **분석가** 권한만 (광고 게재 권한 부여 X)
4. **토큰 생성** → 앱 선택 → 권한은 **`ads_read`만 체크** → 만료일 영구 권장
5. 생성된 토큰 복사 → 위 [config의 `META_ACCESS_TOKEN`](#2-claude-desktop-config-편집) 값으로 사용

> 보안: `ads_read`만 발급해야 토큰이 노출돼도 광고 변경/계정 정보 유출 위험을 원천 차단.

---

## 라이선스

MIT — `LICENSE` 참고.
