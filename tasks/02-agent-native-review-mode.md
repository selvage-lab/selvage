# Task 02: 에이전트 네이티브 리뷰 방식 (Agent-Delegated Review)

## 목표

MCP 도구를 통해 **API 키 없이** 호스트 에이전트(Claude Code, Antigravity, Cursor 등)가 자체 LLM으로 코드 리뷰를 수행할 수 있는 경량 모드를 추가한다.

---

## 배경

### 현재 MCP 모드의 허들

```
Agent -> selvage MCP tool 호출
          |
        git diff -> DiffParser -> PromptGenerator -> LLM API 직접 호출 -> 결과 반환
                                                      ^
                                             사용자 API 키 필요 (허들)
```

- 사용자가 별도의 API 키(OpenAI/Anthropic/Google/OpenRouter)를 환경변수로 설정해야 함
- MCP 서버로서의 온보딩 장벽이 높음
- 에이전트가 이미 LLM 능력을 가지고 있는데, 별도 API 호출을 하는 것은 비효율적

### selvage의 진짜 핵심 가치

LLM API 호출 자체가 아니라, **그 앞단의 처리**에 있음:

1. **git diff 추출** - staged/unstaged/branch/commit 모드 지원
2. **DiffParser** - raw diff를 `DiffResult` 구조체로 파싱
3. **Smart Context 추출** - Tree-sitter AST 기반 관련 코드 블록 분석
4. **v4 시스템 프롬프트** - 리뷰 카테고리, 심각도, 출력 형식 정의

---

## 핵심 설계 결정

### 멀티턴 처리: B안 (에이전트에게 위임)

현재 멀티턴 시스템(PromptSplitter, ReviewSynthesizer)은 LLM API 호출과 깊게 결합되어 있음.
에이전트 위임 모드에서는 **프롬프트를 통째로 반환**하고 에이전트가 알아서 처리하도록 한다.

- 현대 에이전트(Claude Code 200k, Cursor 200k+)는 대부분 큰 컨텍스트 처리 가능
- 토큰 추정도 provider별 API 키가 필요하므로 (Claude: Anthropic API, Gemini: Google API), API 키 없는 모드 취지와 모순
- 실제로 문제가 발생하면 그때 tiktoken 기반 로컬 추정 + 사전 분할 로직 추가

### 도구 노출 전략: A+B+C 조합

에이전트가 `review_*`와 `get_review_context` 중 어떤 도구를 사용할지 혼란 방지를 위해:

**A. MCP 서버 시작 시 모드 선택**

```bash
# 에이전트 위임 모드 (API 키 불필요)
selvage mcp --mode agent

# 독립 LLM 모드 (API 키 필요, 기존)
selvage mcp --mode independent

# 자동 감지 (기본값)
selvage mcp
```

**B. API 키 유무 자동 감지 (auto 모드)**

```python
def create_server(mode: str = 'auto'):
    mcp = FastMCP('Selvage')

    if mode == 'auto':
        has_key = _check_api_keys()
        if has_key:
            register_review_tools(mcp)      # 독립 LLM 리뷰
        register_context_tools(mcp)          # 에이전트 위임 (항상)
    elif mode == 'agent':
        register_context_tools(mcp)          # 에이전트 위임만
    elif mode == 'independent':
        register_review_tools(mcp)           # 독립 LLM만

    register_utility_tools(mcp)
    return mcp
```

**C. 명확한 도구 description (auto 모드에서 둘 다 노출될 때 필수)**

```python
@mcp_tool
def get_review_context(...):
    """코드 리뷰 컨텍스트를 반환합니다. API 키가 필요 없습니다.
    에이전트가 직접 리뷰를 수행합니다.
    review_* 도구와 달리 외부 LLM을 호출하지 않습니다."""

@mcp_tool
def review_current_changes(...):
    """독립 LLM으로 코드 리뷰를 수행하고 완성된 결과를 반환합니다.
    API 키가 필요합니다. (OPENAI_API_KEY, ANTHROPIC_API_KEY 등)
    API 키가 없으면 get_review_context를 사용하세요."""
```

### 아키텍처: 3계층 분리

```
[Layer 1: Context Engine] -- 공유 계층
  ReviewRequest -> PromptGenerator -> ReviewPromptWithFileContent
  (diff 파싱, smart context 추출, 프롬프트 생성)

[Layer 2: Execution] -- 분기점
  +-- CLI 모드:                Layer 1 -> LLM Gateway -> 결과 (기존 그대로)
  +-- MCP review_*:            Layer 1 -> LLM Gateway -> 결과 (기존 그대로, API 키 필요)
  +-- MCP get_review_context:  Layer 1 -> 프롬프트 반환 (신규, API 키 불필요)

[Layer 3: Post-processing]
  +-- CLI/MCP review_*:            멀티턴 합성, 로그 저장, 비용 계산
  +-- MCP get_review_context:      없음 (에이전트 책임)
```

리팩토링 포인트: 기존 `_execute_review_workflow()`에서 Layer 1 부분을 `_prepare_review_context()`로 추출

```python
# Layer 1 (공유) - 새 함수로 추출
def _prepare_review_context(repo_path, staged, target_commit, target_branch):
    diff_result = get_diff_content_result(repo_path, staged, target_commit, target_branch)
    review_request = _create_review_request(diff_result.diff_content, repo_path)
    prompt = PromptGenerator().create_code_review_prompt(review_request)
    return prompt, review_request

# Layer 2a (기존 review_*) - LLM 호출
def _execute_review_workflow(model, repo_path, ...):
    prompt, request = _prepare_review_context(repo_path, ...)
    return _perform_review_and_save_log(request, model)

# Layer 2b (신규 get_review_context) - 프롬프트만 반환
def get_review_context(repo_path, mode, ...):
    prompt, request = _prepare_review_context(repo_path, ...)
    return prompt.to_messages()
```

---

## 제안: 에이전트 위임 방식

```
Agent -> selvage "get_review_context" 호출
          |
        git diff -> DiffParser -> PromptGenerator -> 구조화된 프롬프트 반환
                                                      |
                                             Agent가 자체 LLM으로 리뷰 수행
                                             (API 키 불필요)
```

---

## 구현 설계

### 새 MCP 도구: `get_review_context`

```python
@mcp_tool
def get_review_context(
    repo_path: str,
    mode: str = 'unstaged',           # unstaged | staged | branch | commit
    target_branch: str | None = None,  # mode=branch일 때 대상 브랜치
    target_commit: str | None = None,  # mode=commit일 때 대상 커밋
) -> dict:
    """
    코드 리뷰를 위한 구조화된 컨텍스트를 생성하여 반환한다.
    LLM API를 호출하지 않으므로 API 키가 필요 없다.
    반환된 프롬프트를 호스트 에이전트가 직접 처리하여 리뷰를 수행한다.
    review_* 도구와 달리 외부 LLM을 호출하지 않으며,
    에이전트가 자체 모델로 리뷰를 수행할 수 있도록 시스템 프롬프트와
    파일별 컨텍스트를 구조화하여 제공한다.
    """
    # 1. Git diff 추출
    diff = get_diff_content(repo_path, mode, target_branch, target_commit)

    # 2. Diff 파싱
    diff_result = parse_git_diff(diff)

    # 3. 프롬프트 생성 (Smart Context 포함)
    prompt = PromptGenerator.create_code_review_prompt(diff_result)

    # 4. 구조화된 컨텍스트 반환 (LLM 호출 없음)
    return {
        'system_prompt': prompt.system_prompt,
        'review_targets': prompt.to_messages(),
        'output_format': EXPECTED_JSON_SCHEMA,
        'metadata': {
            'files_count': len(diff_result.files),
            'total_changes': sum(f.changes for f in diff_result.files),
        }
    }
```

### 반환 데이터 구조

```json
{
  "system_prompt": "You are Selvage, a senior-level software engineer...",
  "review_targets": [
    {
      "role": "user",
      "content": {
        "file_name": "src/app.py",
        "file_context": {
          "context_type": "smart_context",
          "context": "관련 코드 블록...",
          "description": "Tree-sitter AST 기반 추출"
        },
        "formatted_hunks": [
          {
            "hunk_idx": "1",
            "before_code": "변경 전 코드",
            "after_code": "변경 후 코드"
          }
        ]
      }
    }
  ],
  "output_format": {
    "type": "json_schema",
    "schema": {
      "issues": [
        {
          "type": "bug|security|performance|style|design",
          "file": "string",
          "description": "string",
          "suggestion": "string",
          "severity": "info|warning|error",
          "target_code": "string",
          "suggested_code": "string"
        }
      ],
      "summary": "string",
      "score": "0-10",
      "recommendations": ["string"]
    }
  },
  "metadata": {
    "files_count": 3,
    "total_changes": 42
  }
}
```

---

## Claude Code Plugin 연동 (추가 트랙)

큰 프롬프트가 메인 대화 컨텍스트를 소모하는 문제를 해결하기 위해,
Claude Code plugin의 서브에이전트 기능을 활용할 수 있다.

```
[메인 대화 컨텍스트]
  사용자: "코드 리뷰해줘"
      |
  Claude Code: selvage 스킬/에이전트 호출
      |
  [서브에이전트 컨텍스트 (독립)]      <-- 별도 컨텍스트 윈도우
    1. selvage MCP -> get_review_context() 호출
    2. 큰 프롬프트 전체를 받음
    3. 이 컨텍스트 안에서 리뷰 수행
    4. 압축된 리뷰 결과만 반환
      |
  [메인 대화 컨텍스트]
  Claude Code: "리뷰 결과입니다: ..."   <-- 요약만 전달
```

- 메인 대화 컨텍스트를 소모하지 않음
- 서브에이전트가 독립 컨텍스트(200k)를 온전히 사용
- MCP 도구(`get_review_context`)와 같은 기반 공유

---

## 에이전트 사용 시나리오

### Claude Code에서의 사용 예시

```
사용자: "현재 변경사항 리뷰해줘"

Claude Code:
  1. selvage의 get_review_context 도구 호출 (repo_path=현재 경로)
  2. 반환된 system_prompt + review_targets를 기반으로 직접 리뷰 수행
  3. output_format에 맞춰 구조화된 결과 생성
  4. 사용자에게 리뷰 결과 제시
```

### Antigravity에서의 사용 예시

```
사용자: "PR 올리기 전에 코드 리뷰 부탁해"

Antigravity:
  1. selvage의 get_review_context(mode='staged') 호출
  2. 자체 LLM으로 리뷰 수행
  3. 결과를 UI에 표시
```

---

## 장단점 비교

|  | 현재 방식 (API 직접 호출) | 에이전트 위임 방식 |
|---|---|---|
| **API 키** | 사용자가 별도 설정 필요 | 불필요 (에이전트 자체 모델 사용) |
| **온보딩 허들** | 높음 | 매우 낮음 |
| **모델 선택** | 사용자가 지정 | 호스트 에이전트의 모델에 의존 |
| **비용** | selvage 사용량으로 과금 | 에이전트 세션 토큰에 포함 |
| **리뷰 품질 제어** | 모델/프롬프트 완전 제어 | 프롬프트는 제어, 모델은 에이전트 의존 |
| **Structured Output** | Instructor/JSON Schema로 보장 | 에이전트가 JSON 파싱해야 함 |
| **마켓 차별화** | selvage가 end-to-end 처리 | selvage는 "컨텍스트 엔진" 역할 |

---

## 결론: 두 모드 병행 제공

1. **`review_*` 도구들** (기존 유지) -- API 키가 있는 사용자를 위한 end-to-end 리뷰
2. **`get_review_context` 도구** (신규 추가) -- API 키 없이 에이전트에게 위임하는 경량 모드

도구 노출은 `--mode` 옵션 + API 키 자동 감지 + 명확한 description으로 제어.

### 기대 효과

- MCP 마켓플레이스에서 **"API 키 없이도 사용 가능"**이라는 강력한 USP 확보
- Claude Code, Antigravity, Cursor 등 어떤 에이전트에서든 즉시 사용 가능
- 기존 사용자의 워크플로우도 그대로 유지

---

## 구현 계획

### Phase 1: 아키텍처 리팩토링

1. `_execute_review_workflow()`에서 Layer 1(`_prepare_review_context()`) 추출
2. MCP 서버에 `--mode` 옵션 추가 (auto/agent/independent)
3. API 키 자동 감지 로직 구현

### Phase 2: 핵심 도구 구현

1. `get_review_context` MCP 도구 함수 작성
   - 기존 `review_tools.py`의 로직에서 LLM 호출 부분만 제거
   - diff 파싱 + smart context 추출 + 프롬프트 생성까지만 수행
   - mode 파라미터로 staged/unstaged/branch/commit 통합
2. 반환 데이터 모델 정의 (Pydantic)
3. MCP 서버에 도구 등록

### Phase 3: 도구 description 정비

1. `get_review_context` description: API 키 불필요, 에이전트 직접 리뷰용
2. 기존 `review_*` description: API 키 필요, 독립 LLM 리뷰용, API 키 없으면 get_review_context 안내
3. auto 모드에서 두 종류 동시 노출 시 에이전트가 올바르게 선택할 수 있도록 차별화

### Phase 4: 테스트 및 문서화

1. 단위 테스트 작성 (LLM 호출 없이 프롬프트 생성만 검증)
2. 각 mode별 도구 등록 검증 (auto/agent/independent)
3. README에 에이전트 위임 모드 사용법 문서화

### Phase 5: Claude Code Plugin (선택)

1. `.claude-plugin/plugin.json` 구조 생성
2. 서브에이전트 기반 리뷰 스킬 정의
3. Claude Code에서 실제 사용 테스트
