### Selvage MCP 서버 연동 가이드 (Cursor, Claude Code)

이 문서는 실제 MCP 클라이언트(예: Cursor, Claude Code)와 `Selvage MCP Server`를 연동해 로컬에서 코드 리뷰 워크플로우를 테스트하는 방법을 안내합니다.

---

#### 1) 연동 방법

##### A. Cursor와 연동 (mcp.json 설정)

1. Selvage MCP 서버는 `python -m selvage.src.mcp.server`로 stdio 기반 실행이 가능합니다.
2. Cursor의 MCP 설정 파일(`~/.cursor/mcp.json` 혹은 워크스페이스 설정 위치)에 다음과 같이 등록합니다.

```json
{
  "mcpServers": {
    "selvage": {
      "command": "/Users/USER/.pyenv/versions/3.11.9/bin/python",
      "args": ["-m", "selvage.src.mcp.server"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

- command: 로컬 Python 실행 경로로 바꿔주세요. 예) `/Users/you/.venv/bin/python` 또는 프로젝트 venv의 `python` 경로
- args: `-m selvage.src.mcp.server` 그대로 유지 (stdio)
- env(PYTHONUNBUFFERED): 로그 출력 버퍼링 방지에 유용

Cursor를 재시작하면 `selvage` MCP 서버가 자동으로 연결되어 도구를 탐색할 수 있습니다.

##### B. Claude Code와 연동 (Terminal 명령)

Claude Code(데스크톱 앱)에서 로컬 MCP 서버를 연결할 때는 `claude mcp add <name> <command> [args...]` 형식을 사용합니다. 예시:

```bash
# 사용자 환경에 맞춰 python 경로를 바꾸세요
claude mcp add -t stdio -- selvage \
  /Users/demin_coder/Dev/selvage/venv/bin/python -- -m selvage.src.mcp.server

# 연결 확인
claude mcp list
claude mcp get selvage
```

이 저장소 경로 기준(현재 워크스페이스) 절대 경로 예시:

```bash
claude mcp add -t stdio -e PYTHONUNBUFFERED=1 selvage \
  /Users/demin_coder/Dev/selvage/venv/bin/python -m selvage.src.mcp.server
```

핵심은 로컬 가상환경의 `python` 바이너리 경로와 `-m selvage.src.mcp.server`를 정확히 전달하는 것입니다.

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

#### 참고

- 서버 엔트리포인트: `python -m selvage.src.mcp.server` (stdio)
- 등록되는 도구(요약):
  - review_current_changes_tool, review_staged_changes_tool,
    review_against_branch_tool, review_against_commit_tool
  - get_available_models_tool, get_review_history_tool,
    get_review_details_tool, get_server_status_tool, validate_model_config_tool

연동 과정에서 문제가 있으면 파이썬 경로, 가상환경 활성화, `PYTHONUNBUFFERED=1` 설정을 우선 확인하세요.
