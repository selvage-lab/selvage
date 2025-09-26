### Selvage MCP 서버 연동 가이드 (Cursor, Claude Code)

이 문서는 MCP 클라이언트(Cursor, Claude Code)와 `Selvage MCP Server`를 연동해 코드 리뷰 워크플로우를 사용하는 방법을 안내합니다.

---

## 일반 사용자를 위한 연동 방법 (권장)

### 사전 요구사항

- `uv`가 설치되어 있어야 합니다: [uv 설치 가이드](https://docs.astral.sh/uv/getting-started/installation/)

### A. Cursor와 연동 (mcp.json 설정)

Cursor의 MCP 설정 파일(`~/.cursor/mcp.json`)에 다음과 같이 등록합니다:

```json
{
  "mcpServers": {
    "selvage": {
      "command": "uvx",
      "args": ["selvage", "mcp"],
      "env": {
        "OPENROUTER_API_KEY": "your_openrouter_api_key_here"
      }
    }
  }
}
```

**API 키 설정 방법:**
- `OPENROUTER_API_KEY`: 권장 (모든 모델 지원)
- 또는 개별 프로바이더 API 키: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`

Cursor를 재시작하면 `selvage` MCP 서버가 자동으로 연결되어 도구를 사용할 수 있습니다.

### B. Claude Code와 연동

```bash
# MCP 서버 등록 (환경변수와 함께)
claude mcp add selvage -e OPENROUTER_API_KEY=your_openrouter_api_key_here -- uvx selvage mcp

# 또는 개별 프로바이더 API 키 사용
claude mcp add selvage -e OPENAI_API_KEY=your_openai_key -e ANTHROPIC_API_KEY=your_anthropic_key -- uvx selvage mcp

# 연결 확인
claude mcp list
claude mcp get selvage
```

**대안: 시스템 환경변수 사용**
환경변수를 미리 설정해둔 경우 단순하게 등록할 수도 있습니다:

```bash
# 환경변수 설정
export OPENROUTER_API_KEY="your_openrouter_api_key_here"

# MCP 서버 등록 (환경변수 자동 인식)
claude mcp add selvage -- uvx selvage mcp
```

### 장점

- ✅ Selvage를 미리 설치할 필요 없음
- ✅ 항상 PyPI의 최신 버전 자동 사용
- ✅ 시스템 환경을 오염시키지 않음
- ✅ 간단하고 안정적인 연동

---

#### 2) 연동 이후 코드 리뷰 요청 프롬프트 예시 (3가지+)

아래 프롬프트는 MCP 도구 호출을 유도하는 형태로, 에이전트에게 해당 MCP 서버의 도구를 사용해 리뷰를 수행하도록 요청합니다.

- 예시 1: 현재 변경 사항 리뷰 요청

```
Selvage MCP의 review_current_changes_tool을 사용해 현재 워크스페이스 변경사항을 리뷰해줘.
가능하면 문제점 요약과 수정 제안을 함께 제공해줘.
```

- 예시 2: 스테이징된 변경 사항 리뷰 요청

```
Selvage MCP의 review_staged_changes_tool을 호출해서 스테이징된 변경만 리뷰해줘.
검토 결과를 요약하고, 위험도와 영향을 함께 표로 정리해줘.
```

- 예시 3: 특정 브랜치와 비교해 리뷰

```
Selvage MCP의 review_against_branch_tool을 사용해서 main 브랜치와 비교 리뷰를 실행해줘.
주요 변경 포인트, 잠재적인 회귀, 성능 이슈 가능성을 중점적으로 봐줘.
```

- 예시 4: 특정 커밋과 비교해 리뷰

```
Selvage MCP의 review_against_commit_tool을 이용해 커밋 abc1234와 비교 리뷰를 해줘.
코드 품질/테스트 커버리지/에러 처리 관점에서 개선 제안을 제시해줘.
```

- 예시 5: 서버/모델/히스토리 유틸리티 사용

```
Selvage MCP의 get_server_status_tool, get_available_models_tool, get_review_history_tool을 차례대로 호출해줘.
결과를 간단히 요약하고, 당장 내가 시도할 수 있는 리뷰 플로우를 제안해줘.
```

---

## 개발자/Contributor를 위한 고급 설정

개발 중인 Selvage를 MCP 서버로 테스트하려는 경우 아래 방법을 사용하세요.

### A. 로컬 빌드 테스트 설정

#### 1. 패키지 빌드

```bash
# Selvage 프로젝트 디렉토리에서
python -m build
```

#### 2. Claude Code 연동

```bash
# 로컬 wheel 파일 사용 (환경변수와 함께)
claude mcp add selvage-dev -e OPENROUTER_API_KEY=your_key -- uvx --from ./dist/selvage-0.1.0-py3-none-any.whl selvage mcp

# 연결 확인
claude mcp list
claude mcp get selvage-dev
```

**대안: 시스템 환경변수 사용**
환경변수를 미리 설정해둔 경우 단순하게 등록할 수도 있습니다:

```bash
# 환경변수 설정
export OPENROUTER_API_KEY="your_openrouter_api_key_here"

# MCP 서버 등록 (환경변수 자동 인식)
claude mcp add selvage-dev -- uvx --from ./dist/selvage-0.1.0-py3-none-any.whl selvage mcp
```

#### 3. Cursor 연동

Cursor의 MCP 설정 파일(`~/.cursor/mcp.json`)에 다음과 같이 등록:

```json
{
  "mcpServers": {
    "selvage-dev": {
      "command": "uvx",
      "args": [
        "--from",
        "./dist/selvage-0.1.0-py3-none-any.whl",
        "selvage",
        "mcp"
      ],
      "env": {
        "OPENROUTER_API_KEY": "your_openrouter_api_key_here"
      }
    }
  }
}
```

**주의사항:**

- `./dist/selvage-0.1.0-py3-none-any.whl` 경로는 실제 빌드된 파일명으로 변경
- Cursor 설정 시 Selvage 프로젝트 디렉토리에서 상대 경로 사용

---

#### 참고

- 등록되는 MCP 도구(요약):
  - review_current_changes, review_staged_changes,
    review_against_branch, review_against_commit
  - get_available_models, get_review_history,
    get_review_details, get_server_status, validate_model_config

연동 과정에서 문제가 있으면 uv 설치 상태, 네트워크 연결, 또는 개발 환경의 경우 파이썬 경로와 가상환경 설정을 확인하세요.
