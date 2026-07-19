# Sprint 0c — 자체 경량 Eval 인프라 재구축 계획

> 기준일: 2026-07-17 · 대상: `selvage` 리포 · 상태: 설계 제안

## 1. Executive summary

방치된 `llm_eval/`과 별도 `selvage-eval-agent`를 폐기·흡수하고, `ReviewRun` manifest와 Pydantic golden fixture를 중심으로 한 결정론적 eval을 `selvage`에 구축한다. PR에서는 저장된 run을 재생해 finding precision/recall, 오탐, severity, caller/wrong-def 회귀를 차단하고 결과를 코멘트한다. 실제 LLM 호출과 LLM-as-judge는 비차단·선택 경로로 격리한다.

## 2. 현재 `selvage/llm_eval/` 진단

### 2.1 구조와 동작 상태

| 자산 | 실제 상태 | 판단 |
|---|---|---|
| `README_DEEPEVAL.md` | Python 3.13.2 및 DeepEval 설치/CLI 사용법만 설명 | 역사 참고 후 제거 |
| `test_deepeval_hello_world.py` | 일반 질의용 2개 테스트가 모두 `@pytest.mark.skip` | 제품 eval로 재사용 불가 |
| `test_deepeval_advanced.py` | mock 응답용 2개 테스트가 모두 skip | 제품 eval로 재사용 불가 |
| `test_reviewer_eval.py` | import 시 GEval 3종과 JSON metric을 생성하고 JSON 1개를 parameterize | 평가 관점만 참고 |
| `data_set/*.json` | 11개 DeepEval 입력/출력 snapshot | golden 후보 탐색용 원자료 |
| `pytest.ini` | `env`, `timeout=900`, `--maxfail=1` 설정 | 루트 pytest 설정으로 통합 |

2026-07-17에 60초 외부 timeout으로 실행했다. 기본 `uv` 환경에는 DeepEval이 없으며, DeepEval 3.3.9가 있는 기존 eval-agent venv와 현재 리포 의존성을 조합한 최종 실행은 **4개 수집 후 1개 collection error**로 종료했다. `test_reviewer_eval.py:50`에서 `GEval(model="gemini-2.5-pro")`를 import 시 생성하지만 해당 DeepEval 버전은 이를 GPT 모델로 해석해 “Invalid model”을 발생시킨다. 테스트 본문은 실행되지 않았다. `pytest.ini`의 `env`와 `timeout`도 대응 플러그인이 없어 경고가 났다. 즉 현재 디렉터리는 CI에서 독립 실행할 수 없다.

실제 평가 기준에는 보존 가치가 있다. 예를 들어 다음은 completeness, 위치, 유형, severity, 사실성이라는 finding 축을 이미 표현한다.

```python
# llm_eval/test_reviewer_eval.py:53-63
evaluation_steps=[
    "Verify that all pertinent issues ... are reported in the 'issues' array.",
    "If issues are reported, check if their specified filenames and line numbers are accurate.",
    "If issues are reported, confirm if their severity levels ... are assigned ...",
]
```

다만 이 문장을 judge prompt로 그대로 이식하지 않고, 아래의 golden 필드와 deterministic metric으로 분해한다. `JsonCorrectnessMetric`도 버리고 `ReviewRun.model_validate_json()`으로 대체한다.

### 2.2 현재 제품 코드와 통합 지점

실행 경로는 `cli.review()` → `review_code()` → `ReviewRequest` → `PromptGenerator` → `GatewayFactory`/`BaseGateway.review_code()` → `ReviewResponse` → `ReviewLogManager.save()`이다.

```python
# selvage/cli.py:451-467
diff_content = get_diff_content(repo_path, staged, target_commit, target_branch)
diff_result = parse_git_diff(diff_content, repo_path)
review_request = ReviewRequest(
    diff_content=diff_content, processed_diff=diff_result,
    file_paths=[file.filename for file in diff_result.files],
    model=model, repo_path=repo_path,
)
```

`PromptGenerator`는 `VERSION = "v4"`이고, 파일별 smart/fallback/full context를 선택해 `ReviewPromptWithFileContent`를 만든다(`selvage/src/utils/prompts/prompt_generator.py:24-27, 100-162`). `BaseGateway`는 이를 messages로 바꾸고 provider별 호출 후 `StructuredReviewResponse`를 검증하며 비용을 계산한다(`base_gateway.py:185-195, 231-256`). 결과 모델은 이미 `ReviewIssue(file, line_number, type, severity, target_code, ...)`와 `ReviewResponse`를 제공한다(`token/models.py:77-136`).

가장 가까운 manifest 전신은 review log다.

```python
# selvage/src/utils/logging/review_log_manager.py:77-96
review_log = {
    "id": log_id, "model": {"provider": provider.value, "name": model_name},
    "created_at": now.isoformat(), "prompt": prompt_data,
    "review_request": review_request.model_dump(mode="json"),
    "review_response": response_data, "prompt_version": "v4",
}
```

여기에 없는 diff digest/snapshot 경계, skill version, 실제 context chunks, tool calls, 시간·토큰 budget, 종료 상태를 Sprint 2 `ReviewRun`으로 승격한다. Sprint 0c에서는 스키마와 serializer protocol을 먼저 고정하고, `ReviewLogManager.save()`에는 임시 adapter를 둔다. CLI와 gateway가 eval을 직접 알게 하지 말고 `RunRecorder` protocol을 주입해 단계별 event를 기록한다. 이 경계는 normal/multiturn/cache 경로를 모두 동일 manifest로 관찰하게 한다.

## 3. `selvage-eval-agent` 마이그레이션 자산

| 원본 파일/디렉터리 | 가져올 내용 | 목적지/처리 |
|---|---|---|
| `configs/selvage-eval-config.yml` | cline, fastapi, ecommerce-microservices, ktor, aider의 기술 스택과 readonly 의도; 모델 목록 | `eval/config/repositories.yml`; 절대 경로·구형 모델명·binary path 제거, URL+commit SHA로 고정 |
| `src/selvage_eval/config/commit-collection-config.yml` | XS/S/M/L/XL 기준(10/100/500/9999), 비율(15/50/20/13/2), 최소 품질/재분배 정책 | `eval/config/commit-selection.yml`; 근거와 버전을 명시 |
| `commit_collection/{commit_stats,commit_data,commit_score,commit_size_category,diversity_selector}.py` | 변경량 모델, 경계값, 크기별 quota와 deterministic quality sort | `selvage/src/eval/collection/`; dataclass를 Pydantic으로 정리 |
| `commit_collection/commit_collector.py` | non-code 감점, positive/negative keyword, core/config path 분류 | 휴리스틱만 포팅; shell 문자열 조립과 checkout은 제외 |
| `tests/commit_collection/test_commit_collection.py` | git numstat 파싱, 필터·점수·직렬화 케이스 | 새 collection 단위 테스트로 축약 이식 |
| `tests/commit_collection/test_commit_size_category.py`, `test_diversity_selector.py` | 경계값, 파일 수 보정, quota/shortage/quality 검증 | 거의 그대로 포팅할 최우선 테스트 |
| `sample/*.json` 3개 | 동일 시점 Gemini Flash/Pro, Claude review log 구조 | golden 저작 시 비교 샘플; 정답으로 자동 승격 금지 |
| `sample/deepEval/*.json` | 기존 input/actual output | 후보 finding 수동 라벨링 후 새 fixture로 변환 |
| `tools/review_executor_tool.py` 및 관련 tests | commit×model 실행 행렬, 성공/실패 summary, 원 브랜치 복구 의도 | subprocess 구현은 폐기; `git show SHA^!` 기반 read-only runner와 summary test만 재작성 |
| `analysis/metric_aggregator.py`, `version_comparison_analyzer.py` 및 tests | 모델/버전별 집계, regression trend, 빈 입력 처리 | NumPy/DeepEval 타입 제거 후 표준 라이브러리 집계로 포팅 |
| `analysis/tech_stack_analyzer.py` | repository→tech stack grouping | deterministic 결과 grouping만 포팅 |
| DeepEval executor/parser/engine, ReAct agent, Gemini failure analyzer | DeepEval·외부 judge·에이전트 결합 | 이식하지 않음 |

사용자가 언급한 142개와 달리 현재 `selvage-eval-results/` 실파일은 **137개, 984KB**다(67 session metadata + 67 session state + `session_state.json`, `meaningful_commits.json`, `file_change_commit2.json`; 2025-07-02~2025-11-17). 숫자 차이를 migration record에 남긴다. 대부분 실행 제어 상태라 golden은 아니다. `docs/historical-evals/index.md`에 원본 commit, 파일 수, SHA-256, 기간, 스키마, 알려진 결손을 기록하고, 원본 JSON은 `docs/historical-evals/archive/`에 읽기 전용으로 보존하되 PR metric 입력에서는 제외한다. 개인정보·로컬 절대 경로를 검사/마스킹한 뒤 이동하며 3개 sample log도 동일 정책을 적용한다.

## 4. 자체 경량 eval 설계

### 4.1 디렉터리 구조

```text
selvage/src/eval/
  models.py          # ReviewRun, GoldenFixture, DiffSource, EvalReport
  recorder.py        # RunRecorder protocol / JSONL event recorder
  extractor.py       # ReviewResponse -> normalized Finding
  matcher.py         # deterministic bipartite matching
  metrics.py         # 순수 함수
  runner.py          # replay/live orchestration
  diff_fetcher.py    # synthetic inline or external git clone
  collection/        # 선별 로직
eval/
  config/{repositories,commit-selection,thresholds}.yml
  fixtures/
    synthetic/<stack>/<case-id>.yml     # inline_patch 포함 (selvage 저작물)
    external/<stack>/<case-id>.yml      # repo_url+commit_sha+diff_range만 (코드 저장 X)
  manifests/replay/*.json
tests/eval/{test_models,test_matcher,test_metrics,test_replay,test_diff_fetcher}.py
docs/historical-evals/{index.md,archive/}   # 별도 리포 또는 submodule 권장
```

**fixture 정책 (라이센스 회피)**:
- **synthetic**: selvage 팀이 직접 작성한 작은 테스트 케이스. inline_patch 필드에 diff 텍스트 저장. selvage Apache 2.0 저작물. 라이센스 이슈 0.
- **external**: 외부 OSS repo의 diff를 평가. **코드 자체는 저장하지 않고** `repo_url + commit_sha + diff_range + license_attribution` 메타데이터만 저장. runtime에 `git clone → checkout → diff` 추출. 외부 코드를 한 줄도 복제/재배포하지 않으므로 라이센스 이슈 0.

### 4.2 Sprint 2 선행 인터페이스

```python
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

class VersionRef(BaseModel):
    name: str
    version: str
    digest: str | None = None

class DiffSnapshot(BaseModel):
    base_sha: str
    head_sha: str
    patch: str
    sha256: str
    files: list[str]

class ContextChunk(BaseModel):
    chunk_id: str
    file: str
    start_line: int | None = None
    end_line: int | None = None
    content_sha256: str
    text: str | None = None       # 공개 fixture만 inline
    strategy: str                 # smart|fallback|full|tool

class ToolCall(BaseModel):
    call_id: str
    name: str
    arguments: dict
    result_sha256: str | None = None
    status: str
    duration_ms: int

class Budget(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    max_context_tokens: int | None = None
    cost_usd: float = 0
    wall_time_ms: int = 0

class Finding(BaseModel):
    finding_id: str
    file: str
    start_line: int | None = None
    end_line: int | None = None
    category: str
    severity: str
    title: str
    description: str
    target_symbol: str | None = None
    evidence: list[str] = Field(default_factory=list)

class ReviewRun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "review-run/v1"
    run_id: str
    created_at: datetime
    source: dict                # repo, commit, trigger, selvage_version
    diff: DiffSnapshot
    model: VersionRef
    prompt: VersionRef
    skills: list[VersionRef] = Field(default_factory=list)
    context_chunks: list[ContextChunk] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    budgets: Budget
    findings: list[Finding] = Field(default_factory=list)
    status: str                 # success|failed|partial|cached
    error: str | None = None
```

`schema_version`은 payload 호환성, 각 digest는 재현성을 담당한다. timestamp/run_id는 비교 전에 제외하며 목록은 `finding_id`, `chunk_id`, `call_id`로 정렬한다. patch와 공개 context만 inline하고 민감한 live context는 digest+artifact reference 정책을 쓴다.

### 4.3 Golden fixture와 비교

**DiffSource** (라이센스 이슈 회피 핵심): synthetic은 inline 패치 저장, external은 메타데이터만 저장하고 runtime에 clone.

```python
class DiffSource(BaseModel):
    """두 가지 방식: synthetic inline 또는 external runtime-clone.
    외부 OSS 코드는 저장하지 않는다 (라이센스 이슈 0)."""
    model_config = ConfigDict(extra="forbid")
    kind: str  # "synthetic" | "external"
    # synthetic인 경우 (selvage 저작물, inline OK)
    inline_patch: str | None = None
    # external인 경우 (외부 OSS repo, 코드 저장 X)
    repo_url: str | None = None
    commit_sha: str | None = None
    diff_range: str | None = None  # "base..head" 형식
    license_attribution: str | None = None  # "© Author, MIT License"
    license_kind: str | None = None  # "MIT" | "Apache-2.0" | "BSD-3-Clause" | ... (permissive만 허용)
```

```python
class Location(BaseModel):
    file: str
    start_line: int | None = None
    end_line: int | None = None
    symbol: str | None = None

class ExpectedFinding(BaseModel):
    id: str
    locations: list[Location]
    categories: set[str]
    severity: str
    aliases: set[str] = Field(default_factory=set)
    required: bool = True
    tags: set[str] = Field(default_factory=set)  # caller, wrong-def 등

class NegativeExpectation(BaseModel):
    id: str
    location: Location | None = None
    forbidden_categories: set[str] = Field(default_factory=set)

class GoldenFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "golden/v1"
    case_id: str
    diff_source: DiffSource          # ★ 변경: diff_file 대신 DiffSource
    diff_sha256: str                 # synthetic은 inline_patch hash, external은 runtime 추출 diff hash
    stack: str
    expected: list[ExpectedFinding]
    negatives: list[NegativeExpectation] = Field(default_factory=list)
    thresholds: dict[str, float]
    provenance: dict                 # source SHA, labelers, reviewed_at
```

**DiffSource 검증 규칙** (런타임 + CI):
- `kind="synthetic"`: `inline_patch` 필수. `repo_url/commit_sha` 금지.
- `kind="external"`: `repo_url/commit_sha/diff_range/license_attribution/license_kind` 필수. `inline_patch` 금지.
- `license_kind` 화이트리스트: `MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC`, `MPL-2.0` (permissive만). **GPL/LGPL/AGPL/상용 금지** — 라이센스 전염/침해 리스크.
- 모든 external fixture는 CONTRIBUTING.md에 "이 리포는 외부 OSS 코드를 저장하지 않는다" 명시.

추출기는 기존 `ReviewResponse.issues`를 경로 POSIX화, severity enum화, line range화하고 텍스트 공백만 정규화한다. matcher는 `(정규화 경로 일치) AND (line range 교차 또는 symbol 일치) AND (category/alias 일치)` 후보만 만들고, 점수 `(location 0~2, category 0~1, severity 0~1)` 내림차순 뒤 `(expected.id, finding_id)`로 tie-break하는 one-to-one greedy matching을 사용한다. 임베딩·fuzzy 의미 비교는 금지한다. line 이동은 fixture에 허용 range로 명시한다.

| Metric | 정의 | PR 기본 gate |
|---|---|---|
| precision | `TP / (TP + FP)`; 예측 0이면 1.0 | 전체 ≥ 0.80 |
| recall | `TP / (TP + FN)`; 필수 expected 0이면 1.0 | 전체 ≥ 0.80, case별 하한 별도 |
| false positive rate | negative assertion 단위 `violated / total negatives` | ≤ 0.10; negatives 0이면 N/A |
| severity calibration | 매칭쌍의 `abs(rank(pred)-rank(gold))/2` 평균(error/warning/info) | error ≤ 0.25 |
| caller recall | `caller` tag가 붙은 필수 finding의 recall | Sprint 1 baseline 대비 하락 0, 절대 ≥ 0.85 |
| wrong-def rate | `wrong-def` negative 위반 수 / `wrong-def` 검사 수 | Sprint 1 baseline 이하, 목표 ≤ 0.05 |

보고서는 micro/macro 값을 함께 내며 0분모 정책과 N/A를 숨기지 않는다. fixture 변경은 코드 변경과 분리하고 labeler 2인 승인 또는 명시적 owner 승인을 요구한다.

### 4.4 선택적 LLM-as-judge

결정론적 matcher가 `unmatched`이면서 위치·category 후보는 있는 모호한 건만 judge queue에 보낸다. provider SDK를 직접 사용하되 `JudgeProtocol.evaluate(case, expected, actual) -> JudgeVerdict`로 격리하고 prompt/model/digest, 원문, 비용을 별도 manifest에 기록한다. temperature 0, 구조화 출력, 최대 1회 호출, 결과는 PR 차단 점수에 섞지 않는다. 사람이 승인한 verdict만 alias/range 개선 제안이 되며 golden을 자동 수정하지 않는다. nightly/manual workflow에서만 secret을 허용한다.

## 5. 단계별 구현 로드맵

| Phase | 작업 | 완료 조건 |
|---|---|---|
| A — 진단 정리 | 기존 `llm_eval` quarantine, 137개 archive inventory/hash/PII 검사, 이식 ADR | DeepEval import가 제품/CI 의존성에 0건 |
| B — 데이터 모델 | 위 Pydantic 모델, JSON Schema export, `ReviewLog` adapter, recorder protocol | round-trip·extra forbid·v1 fixture tests 통과 |
| C — 평가 로직 | normalize/extract/match/metric/report CLI 구현 | 순수 단위 테스트와 동일 입력 byte-identical report |
| D — golden 구축 | 언어/크기/clean-negative 층화, 기존 11 dataset·3 sample 수동 라벨링 | 최소 20 case, stack별·caller/wrong-def coverage 표 공개 |
| E — CI 통합 | replay gate, artifact, sticky PR comment; live/judge 별도 | fork PR secret 없이 동작, 실패 시 metric delta 표시 |

## 6. CI 통합 방안

PR 필수 job은 LLM을 호출하지 않고 versioned replay manifest 또는 test double 결과를 fixture와 비교한다. prompt/gateway 변경 PR은 replay fixture 호환성까지 검증하고, 실제 모델 품질 drift는 schedule/manual job이 관찰한다.

```yaml
name: eval-regression
on:
  pull_request:
    paths: ["selvage/**", "eval/**", "tests/eval/**", "pyproject.toml", "uv.lock"]
permissions:
  contents: read
  pull-requests: write
jobs:
  deterministic-eval:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv sync --locked --extra dev
      - run: uv run pytest tests/eval -q
      - run: uv run python -m selvage.src.eval.runner replay --fixtures eval/fixtures --runs eval/manifests/replay --report eval-report.md --json eval-report.json
      - uses: actions/upload-artifact@v4
        if: always()
        with: {name: eval-report, path: "eval-report.*"}
      - uses: actions/github-script@v7
        if: always() && github.event.pull_request.head.repo.fork == false
        with:
          script: |
            const fs = require('fs');
            const body = '<!-- selvage-eval -->\n' + fs.readFileSync('eval-report.md', 'utf8');
            const {owner, repo} = context.repo;
            const issue_number = context.issue.number;
            const comments = await github.paginate(github.rest.issues.listComments, {owner, repo, issue_number});
            const old = comments.find(c => c.body?.includes('<!-- selvage-eval -->'));
            old ? await github.rest.issues.updateComment({owner, repo, comment_id: old.id, body})
                : await github.rest.issues.createComment({owner, repo, issue_number, body});
```

fork PR에서는 write token이 없으므로 코멘트를 생략하고 job summary/artifact만 제공한다. `pull_request_target`에서 PR 코드를 실행하지 않는다. report 생성은 metric gate 실패 전에도 완료되도록 runner가 JSON/Markdown을 쓰고 비정상 exit code를 마지막에 반환한다.

## 7. 리스크와 제약

| 리스크 | 영향 | 대응 |
|---|---|---|
| LLM 비결정성과 replay의 차이 | PR gate가 실제 품질을 완전히 대변하지 않음 | PR은 코드 결정성, nightly는 drift로 역할 분리 |
| golden label 오류/과적합 | metric 신뢰도 저하 | provenance, 2인 검토, stack/size 층화, fixture 변경 분리 |
| line number 취약성 | 같은 finding이 FN 처리 | range/symbol을 fixture에 명시; fuzzy text는 금지 |
| caller/wrong-def 계약 미완성 | Sprint 1 metric 정의 충돌 | tag와 분모 인터페이스만 선행, Sprint 1 baseline을 version ref로 고정 |
| Sprint 2 manifest 변경 | adapter 중복 구현 | `review-run/v1` JSON Schema contract test와 migration function 제공 |
| 과거 archive의 절대 경로/개인정보 | 저장소 유출 | PII 검사·마스킹·hash inventory 후 이관 |
| PR comment 권한/중복 | fork 실패·spam | sticky marker, fork summary fallback, 최소 permissions |
| 비용과 secret | live eval 오용 | PR에서 secret/네트워크 0, judge는 manual/nightly budget cap |

## 8. 마스터 플랜 v1.1 — Sprint 0c 통합 체크리스트

### 설계/정리

- [ ] `llm_eval/`을 deprecated로 표시하고 DeepEval 의존·import·문서를 제거한다.
- [ ] 이 문서를 마스터 플랜 v1.1 Sprint 0c 기준 문서로 링크한다.
- [ ] eval-agent 137개 실파일과 “142개” 보고 차이를 migration record에 남긴다.
- [ ] 보존/포팅/폐기 목록을 ADR로 승인한다.

### ReviewRun 계약 (Sprint 2 선행)

- [ ] `review-run/v1` Pydantic 모델과 JSON Schema를 확정한다.
- [ ] diff/model/prompt/skill/context/tool/budget/findings 필드를 contract test로 고정한다.
- [ ] `ReviewLogManager` → `ReviewRun` adapter와 `RunRecorder` protocol을 만든다.
- [ ] normal, cache, proactive/fallback multiturn의 manifest coverage를 확인한다.

### Deterministic eval

- [ ] `golden/v1`과 fixture validator를 구현한다.
- [ ] finding normalize 및 stable one-to-one matcher를 구현한다.
- [ ] precision/recall/FPR/severity의 0분모·N/A 정책을 테스트한다.
- [ ] Sprint 1 caller recall/wrong-def tag 및 baseline 입력 계약을 연결한다.
- [ ] 같은 입력의 report가 byte-identical인지 검증한다.

### Corpus/역사 자산

- [ ] commit size/quota 설정과 경계 테스트를 포팅한다.
- [ ] 11개 기존 dataset과 3개 sample log를 사람이 재라벨링한다.
- [ ] 최소 20개 golden case와 clean negative를 stack/크기별로 구성한다.
- [ ] historical archive를 PII 마스킹·SHA-256 inventory 후 비평가용으로 보존한다.

### CI/운영

- [ ] PR replay workflow, artifact, job summary, sticky comment를 구축한다.
- [ ] fork PR 및 최소 permission 동작을 검증한다.
- [ ] fixture 변경 CODEOWNERS/2인 승인 규칙을 적용한다.
- [ ] live LLM 및 judge를 non-blocking scheduled/manual workflow로 격리한다.
- [ ] metric threshold, baseline 갱신 절차, rollback 기준을 운영 문서화한다.
