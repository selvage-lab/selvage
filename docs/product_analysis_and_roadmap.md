# Selvage 제품 분석 및 로드맵

## 1. 현재 상태 요약

### 1.1 제품 개요
Selvage는 LLM 기반 코드 리뷰 도구로, Git diff를 분석하여 AI 모델로부터 코드 리뷰를 받는 CLI 애플리케이션입니다.

| 항목 | 내용 |
|------|------|
| **버전** | 0.2.x (현재), Beta 상태 |
| **타겟 사용자** | 개발자, DevOps 엔지니어, 코드 리뷰어 |
| **라이선스** | Apache 2.0 |
| **Python 지원** | 3.10, 3.11, 3.12, 3.13 |
| **저장소** | https://github.com/selvage-lab/selvage |

### 1.2 핵심 강점
| 강점 | 설명 | 경쟁 우위 |
|------|------|----------|
| **다중 LLM 지원** | OpenAI, Anthropic, Google, OpenRouter 4개 제공자 | 벤더 종속 없음 |
| **OpenRouter First** | 단일 API 키로 모든 모델 접근 | 설정 간소화 |
| **AST 기반 컨텍스트** | Tree-sitter로 9개 언어 지원 | 정확한 관련 코드 추출 |
| **Multiturn 시스템** | Context limit 자동 분할/합성 | 대규모 diff 처리 |
| **MCP 통합** | Claude Code 네이티브 연동 | AI 도구 체인 |
| **비용 추정** | 실시간 토큰 기반 비용 계산 | 비용 투명성 |

### 1.3 기술 스택 및 의존성
```
Core:        pydantic 2.11+, click 8.1.8, PyYAML 6.0.1
LLM:         openai 1.95+, anthropic 0.49, google-genai 1.13, instructor 1.8
AST:         tree-sitter-language-pack 0.9.0
UI:          streamlit 1.43.2, rich 13.9+
HTTP:        httpx 0.28.1, requests 2.32.3
MCP:         fastmcp 2.12+
Token:       tiktoken 0.9.0
Retry:       tenacity 9.0+
```

### 1.4 테스트 현황
| 카테고리 | 파일 수 | 주요 영역 |
|---------|--------|----------|
| Unit Tests | 85개 | diff_parser, llm_gateway, context_extractor |
| Context Extractor | 23개 | Python, TypeScript, Java, Kotlin, Go, Swift, C#, C |
| Multiturn | 4개 | prompt_splitter, executor, synthesizer |
| MCP | 6개 | server, tools, config |
| E2E | 5개 | Docker 기반 통합 테스트 |
| LLM Eval | - | DeepEval 기반 품질 평가 |

---

## 2. 코드 수준 분석 및 개선점

### 2.1 아키텍처 이슈

#### 2.1.1 `cli.py` 모놀리식 구조 (789 라인)
**위치**: `selvage/cli.py`
**문제**:
- 단일 파일에 명령어 핸들러, 비즈니스 로직, 에러 처리 혼재
- `review_code()` 함수가 145라인으로 과도하게 복잡
- 테스트 시 모킹 범위가 넓어짐

**작업량**: 3-5일 (중)
**제안**: 책임 분리
```
selvage/
  cli/
    __init__.py          # 메인 CLI 그룹
    review_command.py    # review 관련 로직 (~200 라인)
    config_command.py    # config 관련 로직 (~150 라인)
    view_command.py      # UI 실행 (~50 라인)
    error_handlers.py    # 에러 처리 통합 (~100 라인)
```

#### 2.1.2 설정 관리 분산
**위치**: `selvage/src/config.py`, `selvage/src/model_config.py`
**문제**:
- `config.py`: INI 파일 기반 일반 설정 (357 라인)
- `model_config.py`: YAML 기반 모델 설정
- 환경변수 우선순위가 코드에 분산되어 있음

**작업량**: 2-3일 (소)
**제안**: 통합 설정 계층
```python
class ConfigManager:
    def __init__(self):
        self.env = EnvConfig()          # 환경변수 (최우선)
        self.project = ProjectConfig()  # .selvage.yml
        self.user = UserConfig()        # ~/.config/selvage/config.ini
        self.default = DefaultConfig()  # 기본값

    def get(self, key: str) -> Any:
        for source in [self.env, self.project, self.user, self.default]:
            if (value := source.get(key)) is not None:
                return value
        return None
```

#### 2.1.3 Gateway Factory 확장성
**위치**: `selvage/src/llm_gateway/gateway_factory.py:37-54`
**문제**: if-elif 체인으로 새 제공자 추가 시 코드 수정 필요

**작업량**: 1일 (소)
**제안**: 레지스트리 패턴
```python
GATEWAY_REGISTRY: dict[ModelProvider, type[BaseGateway]] = {
    ModelProvider.OPENAI: OpenAIGateway,
    ModelProvider.ANTHROPIC: ClaudeGateway,
    ModelProvider.GOOGLE: GoogleGateway,
    ModelProvider.OPENROUTER: OpenRouterGateway,
}

@staticmethod
def create(model: str) -> BaseGateway:
    gateway_class = GATEWAY_REGISTRY.get(provider)
    if not gateway_class:
        raise ValueError(f"Unsupported provider: {provider}")
    return gateway_class(model_info=model_info)
```

### 2.2 코드 품질 이슈

#### 2.2.1 전역 상태 사용
**위치**: `selvage/src/config.py:21-23`
```python
_MCP_MODE = False
_mcp_mode_set = False
```
**문제**: 테스트 격리 어려움, 멀티스레드 안전성 부재
**작업량**: 2일 (소)
**제안**: 컨텍스트 객체 또는 `contextvars` 활용

#### 2.2.2 중복 프롬프트 생성
**위치**: `selvage/cli.py:353, 473, 496, 522`
```python
review_prompt = PromptGenerator().create_code_review_prompt(review_request)
```
**문제**: 동일한 `review_request`에 대해 최대 4번 프롬프트 생성
**작업량**: 0.5일 (소)
**제안**: 한 번 생성 후 재사용

#### 2.2.3 예외 처리 일관성
**위치**: `selvage/cli.py:290-341`
**문제**:
- `_handle_api_error`에서 `raise Exception()`으로 재발생 (305라인)
- 상위에서 다시 `except Exception`으로 포착 (546라인)
- 예외 체인 정보 손실

**작업량**: 1일 (소)
**제안**: 커스텀 예외 체인 활용
```python
class ReviewError(SelvageError):
    """리뷰 실행 중 발생한 에러"""
    pass

# 사용
raise ReviewError("API error occurred") from error_response.exception
```

### 2.3 성능 이슈

#### 2.3.1 토큰 계산 중복
**위치**:
- `selvage/cli.py:358` - `ProactiveTokenChecker.calculate_total_tokens()`
- `selvage/src/utils/prompts/prompt_generator.py` - 프롬프트 생성 시 내부 계산

**문제**: 토큰 계산 중복으로 CPU 낭비
**작업량**: 1일 (소)
**제안**: `ReviewPromptWithFileContent`에 `cached_token_count` 속성 추가

#### 2.3.2 Tree-sitter 파서 인스턴스화
**위치**: `selvage/src/context_extractor/context_extractor.py`
**문제**: 파일별로 Parser 생성 가능성
**작업량**: 0.5일 (소)
**제안**: 언어별 Parser 싱글톤 캐시 (이미 일부 구현됨, 검증 필요)

### 2.4 사용성 이슈

#### 2.4.1 에러 메시지 개선 필요
**현재**:
```
API error (OpenRouter): context_length_exceeded
```
**작업량**: 2일 (소)
**제안**:
```
[Context Limit Exceeded]
Your diff contains 250,000 tokens but the model limit is 200,000.

Solutions:
1. Use a model with larger context (e.g., gemini-3-pro: 1M tokens)
2. Review smaller changes using --staged
3. Selvage will automatically split the review (multiturn mode)

Run 'selvage models' to see available models and their context limits.
```

#### 2.4.2 진행 상태 세분화
**현재**: 단순 스피너
**작업량**: 1일 (소)
**제안**:
```
[1/4] Parsing git diff... (15 files, 342 changes)
[2/4] Extracting context... (Python: 8, TypeScript: 7)
[3/4] Sending to claude-sonnet-4...
[4/4] Processing response...

Review complete! Estimated cost: $0.0234
```

---

## 3. 추가 기능 제안

### 3.1 단기 (v0.3.x) - 2026 Q1

#### 3.1.1 프로젝트별 설정 파일
**우선순위**: 높음 (사용자 요청 빈번)
**작업량**: 3일

**파일**: `.selvage.yml`
```yaml
# .selvage.yml
version: 1

model: claude-sonnet-4
language: ko

ignore:
  - "*.generated.ts"
  - "vendor/**"
  - "**/*.min.js"
  - "package-lock.json"

focus:
  - security
  - performance
  - error-handling

rules:
  max_file_size: 10000  # 라인
  require_tests: true
  severity_threshold: warning  # info, warning, critical
```

**테스트 전략**:
- `tests/test_project_config.py`: 설정 파싱 및 우선순위 테스트
- `tests/test_ignore_patterns.py`: glob 패턴 매칭 테스트

#### 3.1.2 출력 포맷 다양화
**우선순위**: 중간
**작업량**: 2일

```bash
selvage review --format json > review.json
selvage review --format sarif > review.sarif  # IDE 통합
selvage review --format github  # PR 코멘트 형식
selvage review --format markdown  # 기본값
```

**테스트 전략**:
- `tests/test_output_formats.py`: 각 포맷 출력 검증

#### 3.1.3 CI/CD 통합
**우선순위**: 높음
**작업량**: 5일

**GitHub Actions**:
```yaml
# .github/workflows/selvage-review.yml
name: Code Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: selvage-lab/selvage-action@v1
        with:
          model: claude-sonnet-4
          target-branch: ${{ github.base_ref }}
          fail-on: critical
          github-token: ${{ secrets.GITHUB_TOKEN }}
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

**테스트 전략**:
- `e2e/test_github_action.py`: Docker 기반 액션 테스트

#### 3.1.4 대화형 리뷰 모드
**우선순위**: 중간
**작업량**: 5일

```bash
selvage review --interactive

# 리뷰 결과 출력 후
[Interactive Mode] Type 'help' for commands, 'exit' to quit.

> explain 3
[Issue #3: SQL Injection Vulnerability]
This code directly concatenates user input into SQL query...

> fix 3
[Suggested Fix for Issue #3]
```python
# Before
query = f"SELECT * FROM users WHERE id = {user_id}"

# After
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```

> ignore 2 --reason "false positive"
Issue #2 marked as ignored.

> exit
```

### 3.2 중기 (v0.4.x - v0.5.x) - 2026 Q2-Q3

#### 3.2.1 증분 리뷰
**작업량**: 7일
- 이전 리뷰 결과 추적 (SQLite 로컬 DB)
- 해결된 이슈 자동 제거
- 새 이슈만 하이라이트
- `--since-last-review` 옵션

#### 3.2.2 팀 기능 (로컬 서버)
**작업량**: 14일
```bash
selvage server start --port 8080 --data-dir ~/.selvage/team
selvage review --server http://localhost:8080
```
- 리뷰 결과 중앙 저장
- 팀원 간 공유
- 통계 대시보드

#### 3.2.3 보안 검사 강화
**작업량**: 7일
- OWASP Top 10 체크리스트 통합
- 시크릿 탐지 (API 키, 비밀번호 패턴)
- 의존성 취약점 경고 (Safety/pip-audit 연동)

### 3.3 장기 (v1.0.0+) - 2026 Q4

#### 3.3.1 VS Code 확장
**작업량**: 21일
- 실시간 리뷰 피드백
- 인라인 코멘트
- 원클릭 수정 적용

#### 3.3.2 자동 수정 제안
**작업량**: 14일
```bash
selvage review --auto-fix

# 출력
[Fix Available] Issue #3: SQL Injection vulnerability
  Apply fix? [y/N/diff] d

--- a/db/queries.py
+++ b/db/queries.py
@@ -15,2 +15,3 @@
- query = f"SELECT * FROM users WHERE id = {user_id}"
+ query = "SELECT * FROM users WHERE id = ?"
+ cursor.execute(query, (user_id,))

Apply this fix? [y/N]
```

---

## 4. 제품 로드맵

### 4.1 Phase 1: 안정화 (v0.3.x) - 2026 Q1

| 버전 | 목표 | 작업량 | 상태 |
|------|------|--------|------|
| v0.3.1 | 에러 메시지 개선, 진행 상황 세분화 | 3일 | 계획 |
| v0.3.2 | 프로젝트별 설정 파일 (`.selvage.yml`) | 3일 | 계획 |
| v0.3.3 | CI/CD 통합 (GitHub Actions) | 5일 | 계획 |
| v0.3.4 | 출력 포맷 다양화 (JSON, SARIF, GitHub) | 2일 | 계획 |

**Phase 1 총 작업량**: 약 13일 (3주)

### 4.2 Phase 2: 확장 (v0.4.x - v0.5.x) - 2026 Q2-Q3

| 버전 | 목표 | 작업량 | 상태 |
|------|------|--------|------|
| v0.4.0 | 대화형 리뷰 모드 | 5일 | 계획 |
| v0.4.1 | 증분 리뷰 | 7일 | 계획 |
| v0.5.0 | 팀 기능 (로컬 서버) | 14일 | 계획 |
| v0.5.1 | 보안 검사 강화 | 7일 | 계획 |

**Phase 2 총 작업량**: 약 33일 (7주)

### 4.3 Phase 3: 성숙 (v1.0.0+) - 2026 Q4

| 버전 | 목표 | 작업량 | 상태 |
|------|------|--------|------|
| v0.9.0 | 베타 안정화, 성능 최적화 | 7일 | 계획 |
| v1.0.0 | 프로덕션 릴리스 | 3일 | 계획 |
| v1.1.0 | VS Code 확장 | 21일 | 계획 |
| v1.2.0 | 자동 수정 제안 | 14일 | 계획 |

**Phase 3 총 작업량**: 약 45일 (9주)

### 4.4 로드맵 다이어그램

```
2026 Q1              2026 Q2              2026 Q3              2026 Q4
|------------------| |------------------| |------------------| |------------------|
  [Phase 1: 안정화]   [Phase 2: 확장]       [Phase 2: 확장]      [Phase 3: 성숙]

v0.3.1 (3d) --+
              |
v0.3.2 (3d) --+      v0.4.0 (5d) --+
              |                     |
v0.3.3 (5d) --+      v0.4.1 (7d) --+      v0.5.0 (14d) --+    v0.9.0 (7d) --+
              |                                          |                   |
v0.3.4 (2d) --+                          v0.5.1 (7d) ---+    v1.0.0 (3d) --+
                                                                            |
                                                             v1.1.0 (21d) --+
                                                             (VS Code)

총 작업량: ~91일 (~18주)
```

---

## 5. 기술 부채 및 리팩토링 계획

### 5.1 높은 우선순위 (v0.3.x와 병행)

| 항목 | 위치 | 작업량 | 영향 | 테스트 전략 |
|------|------|--------|------|------------|
| CLI 모듈 분리 | `cli.py` | 3-5일 | 테스트 용이성 | 기존 CLI 테스트 유지, 모듈별 단위 테스트 추가 |
| 설정 검증 추가 | `config.py` | 1일 | 런타임 에러 방지 | `test_config_validation.py` 추가 |
| 에러 체인 정리 | `cli.py`, `exceptions/` | 1일 | 디버깅 효율 | 에러 시나리오 테스트 보강 |
| 프롬프트 중복 제거 | `cli.py` | 0.5일 | 성능 | 기존 테스트로 검증 |

### 5.2 중간 우선순위 (v0.4.x와 병행)

| 항목 | 위치 | 작업량 | 영향 | 테스트 전략 |
|------|------|--------|------|------------|
| Gateway 레지스트리 패턴 | `gateway_factory.py` | 1일 | 확장성 | 팩토리 테스트 리팩토링 |
| 토큰 캐싱 | `prompt_generator.py` | 1일 | 성능 | 토큰 계산 테스트 추가 |
| Tree-sitter 파서 캐시 검증 | `context_extractor.py` | 0.5일 | 성능 | 성능 벤치마크 추가 |

### 5.3 낮은 우선순위 (v1.0.0 전)

| 항목 | 위치 | 작업량 | 영향 | 테스트 전략 |
|------|------|--------|------|------------|
| mypy strict 모드 | 전체 | 5일 | 타입 안전성 | CI에 mypy 검사 추가 |
| 전역 상태 제거 | `config.py` | 2일 | 테스트 격리 | 격리된 테스트 환경 구성 |
| 로깅 표준화 | 전체 | 3일 | 디버깅 | 로그 출력 테스트 |

---

## 6. 리스크 분석

### 6.1 기술적 리스크

| 리스크 | 확률 | 영향 | 완화 전략 |
|--------|------|------|----------|
| LLM API 가격 변동 | 높음 | 중간 | OpenRouter First로 대체 모델 즉시 전환 가능 |
| Tree-sitter 언어팩 버전 호환성 | 중간 | 낮음 | 버전 고정 및 E2E 테스트 |
| Context limit 정책 변경 | 중간 | 중간 | Multiturn 시스템으로 대응 |
| MCP 프로토콜 변경 | 낮음 | 높음 | FastMCP 업데이트 추적 |

### 6.2 비즈니스 리스크

| 리스크 | 확률 | 영향 | 완화 전략 |
|--------|------|------|----------|
| GitHub Copilot 기능 확대 | 높음 | 높음 | 다중 LLM, 로컬 실행, MCP 통합으로 차별화 |
| 오픈소스 유지보수 부담 | 중간 | 중간 | 커뮤니티 기여 장려, 문서화 강화 |
| 사용자 피드백 부족 | 중간 | 중간 | 사용량 통계 (opt-in), GitHub Discussions 활성화 |

### 6.3 리스크 대응 계획

1. **LLM API 의존성**: OpenRouter를 통한 다중 제공자 지원으로 단일 제공자 의존도 감소
2. **경쟁 심화**: MCP 통합과 로컬 실행이라는 고유 가치 강화
3. **유지보수**: CLI 모듈화로 기여 장벽 낮추기

---

## 7. 성공 메트릭

### 7.1 사용자 지표

| 메트릭 | 현재 | v0.3 목표 | v1.0 목표 | 측정 방법 |
|--------|------|----------|----------|----------|
| PyPI 월간 다운로드 | - | 500 | 5,000 | PyPI Stats |
| GitHub Stars | - | 100 | 1,000 | GitHub API |
| 활성 사용자 (opt-in) | - | 50 | 500 | 익명 통계 |

### 7.2 품질 지표

| 메트릭 | 현재 | v0.3 목표 | v1.0 목표 | 측정 방법 |
|--------|------|----------|----------|----------|
| 테스트 커버리지 | ~70% | 80% | 90% | pytest-cov |
| E2E 테스트 통과율 | ~95% | 99% | 99.9% | CI 보고서 |
| 버그 수정 시간 (P1) | - | 7일 | 3일 | GitHub Issues |

### 7.3 성능 지표

| 메트릭 | 현재 | v0.3 목표 | v1.0 목표 | 측정 방법 |
|--------|------|----------|----------|----------|
| 평균 리뷰 시간 (100 라인) | ~15초 | ~10초 | ~5초 | 벤치마크 |
| 메모리 사용량 | ~200MB | ~150MB | ~100MB | 프로파일링 |
| 시작 시간 | ~2초 | ~1초 | ~0.5초 | 벤치마크 |

---

## 8. 경쟁 분석

### 8.1 직접 경쟁자

| 도구 | 가격 | LLM | 특징 | Selvage 차별점 |
|------|------|-----|------|---------------|
| **GitHub Copilot PR** | $19/월 | GPT-4 | GitHub 완전 통합 | 다중 LLM, 로컬 실행, 오픈소스 |
| **CodeRabbit** | $15/월 | GPT-4, Claude | 상세 리뷰, 학습 | 자체 호스팅, MCP 통합 |
| **Sourcery** | 무료~$30/월 | 자체 모델 | 자동 수정 | 다중 언어, 비용 투명성 |
| **DeepSource** | 무료~커스텀 | 규칙 기반 | CI 통합 | LLM 컨텍스트 이해 |

### 8.2 Selvage 고유 가치 제안 (UVP)

1. **LLM 제공자 독립성**: 벤더 종속 없이 최적 모델 선택
2. **로컬 우선**: 코드가 외부 서버에 영구 저장되지 않음
3. **MCP 네이티브**: Claude Code와 원클릭 통합
4. **투명한 비용**: 리뷰당 비용 실시간 표시
5. **오픈소스**: 커스터마이징 및 자체 호스팅 가능

---

## 9. 액션 아이템 (우선순위순)

### 9.1 즉시 실행 (1-2주)

- [ ] `selvage config validate` 명령어 추가
- [ ] 에러 메시지 개선 (해결 가이드 포함)
- [ ] 프롬프트 생성 중복 제거 (`cli.py`)
- [ ] 진행 상황 세분화 (Rich progress bar)

### 9.2 단기 (1개월)

- [ ] `.selvage.yml` 프로젝트 설정 파일 지원
- [ ] CLI 모듈 분리 (`cli/` 디렉토리 구조)
- [ ] `--format` 옵션 추가 (JSON, SARIF)
- [ ] 테스트 커버리지 80% 달성

### 9.3 중기 (3개월)

- [ ] GitHub Actions 액션 개발 및 배포
- [ ] 대화형 리뷰 모드 프로토타입
- [ ] 증분 리뷰 기능 설계 및 구현
- [ ] mypy strict 모드 적용

---

## 10. 결론

Selvage는 다중 LLM 지원, AST 기반 컨텍스트 추출, Multiturn 시스템 등 기술적으로 탄탄한 기반을 갖추고 있습니다.

**강점을 극대화할 영역**:
- OpenRouter First 전략으로 "단일 API 키, 모든 모델" 경험
- MCP 통합으로 AI 도구 체인의 핵심 컴포넌트 위치

**개선이 필요한 영역**:
- 개발자 경험 (에러 메시지, 진행 표시)
- CI/CD 통합 (GitHub Actions)
- 프로젝트별 커스터마이징

**총 예상 작업량**: 약 91일 (18주)
**목표 릴리스**: v1.0.0 - 2026 Q4

2026년 내 v1.0.0 출시를 목표로, Phase 1(안정화) -> Phase 2(확장) -> Phase 3(성숙) 단계를 밟아 나가는 것이 적절합니다.

---

## 11. 의존성 관리 전략

### 11.1 버전 고정 정책

| 카테고리 | 정책 | 이유 |
|---------|------|------|
| **LLM SDK** | 마이너 버전 범위 (`>=1.95,<2.0`) | API 호환성 유지 |
| **Core** | 패치 버전 범위 (`>=2.11.7,<3.0`) | 안정성 우선 |
| **Tree-sitter** | 정확한 버전 (`==0.9.0`) | AST 호환성 보장 |
| **UI** | 정확한 버전 (`==1.43.2`) | 렌더링 일관성 |

### 11.2 업데이트 주기

- **보안 패치**: 즉시 (dependabot alerts)
- **마이너 업데이트**: 월 1회 검토
- **메이저 업데이트**: 분기 1회 검토 및 테스트

### 11.3 호환성 테스트

```bash
# Python 버전별 테스트 (CI에서 자동 실행)
tox -e py310,py311,py312,py313

# 의존성 업데이트 후 E2E 테스트
pytest e2e/ --timeout=300
```

---

## 12. 국제화 (i18n) 전략

### 12.1 현재 상태
- 프롬프트 언어: 설정 가능 (`selvage config language ko`)
- CLI 메시지: 영어 고정
- 문서: 한국어/영어 병행

### 12.2 향후 계획 (v0.5.x+)

| 항목 | 작업량 | 우선순위 |
|------|--------|---------|
| CLI 메시지 i18n (gettext) | 3일 | 낮음 |
| 리뷰 결과 템플릿 다국어화 | 2일 | 중간 |
| 문서 다국어 자동화 | 5일 | 낮음 |

**지원 예정 언어**: 한국어, 영어, 일본어, 중국어 (간체)

---

## 13. 커뮤니티 기여 가이드

### 13.1 기여 영역

| 영역 | 난이도 | 가이드 |
|------|--------|--------|
| 버그 리포트 | 낮음 | GitHub Issues 템플릿 |
| 문서 개선 | 낮음 | `docs/` 디렉토리 |
| 새 언어 컨텍스트 추출 | 중간 | `context_extractor/` + 테스트 |
| 새 LLM 제공자 | 중간 | `BaseGateway` 상속 |
| 코어 기능 | 높음 | PR 전 Issue 논의 필수 |

### 13.2 개발 환경 설정

```bash
# 1. 저장소 클론
git clone https://github.com/selvage-lab/selvage.git
cd selvage

# 2. 개발 의존성 설치
pip install -e ".[dev,e2e]"

# 3. pre-commit 설정
pre-commit install

# 4. 테스트 실행
pytest tests/ -v

# 5. 린팅
ruff check .
ruff format .
```

### 13.3 PR 체크리스트

- [ ] 테스트 추가/수정
- [ ] 문서 업데이트 (필요시)
- [ ] `ruff check` 통과
- [ ] 기존 테스트 통과
- [ ] CHANGELOG.md 업데이트

---

*문서 버전: 4.0*
*최종 수정: 2026-01-28*
*작성자: Claude Code*
