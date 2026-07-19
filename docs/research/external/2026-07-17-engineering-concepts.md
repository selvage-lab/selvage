# 2026 AI Engineering Concepts: 코드 리뷰 도구 관점의 기술 지도

> 조사 기준일: 2026-07-17 (KST)  
> 범위: 공개 웹의 공식 문서, 원 논문, 원 GitHub 저장소를 우선 확인했다. “최신” 기능은 기준일 현재의 문서 상태이며 빠르게 바뀔 수 있다.

## 한눈에 보는 결론

2026년 AI 엔지니어링의 초점은 “더 좋은 한 번의 프롬프트”에서 **재사용 가능한 능력(Skill), 검증 가능한 반복(Loop), 통제된 실행 환경(Harness), 추적 가능한 품질(Eval & Observability), 명시적 계약(Spec)**으로 이동했다. 다섯 개념은 경쟁 관계가 아니라 층이다. Spec이 성공 조건을 정하고, Skill이 도메인 절차를 공급하며, Harness가 모델·도구·상태를 실행한다. Loop는 관찰과 평가 결과를 다음 행동에 반영하고, observability는 전체 궤적을 증거로 남긴다.

Selvage는 이미 Python CLI, 멀티 LLM, Tree-sitter AST 기반 Smart Context, 대규모 변경의 멀티턴 처리, 자체 MCP 서버와 `get_review_context`를 갖고 있다. 따라서 새 “에이전트 제품”을 별도로 만드는 것보다 이 다섯 층을 리뷰 파이프라인에 명시적으로 분리하는 편이 제품 차별화에 유리하다.

---

## 1. Skill Engineering

### 정의

Skill Engineering은 반복되는 프롬프트, 도메인 지식, 작업 순서, 예제, 템플릿, 결정적 스크립트를 **발견·호출·버전 관리 가능한 능력 단위**로 패키징하는 실무다. Anthropic의 [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)는 `SKILL.md`의 이름·설명 메타데이터를 상시 노출하고, 실제 지침과 참조 파일·스크립트는 필요할 때만 읽는 progressive disclosure를 사용한다. 이는 매 요청에 긴 시스템 프롬프트를 넣는 방식과 다르다.

[Cursor Rules](https://docs.cursor.com/context/rules)는 같은 문제의 더 가벼운 형태다. `.cursor/rules/*.mdc`에 Always, glob 기반 Auto Attached, Agent Requested, Manual 규칙을 두어 저장소 맥락과 코딩 정책을 재사용한다. Rule은 주로 “어떻게 행동할지”를 지속적으로 주입하고, Skill은 지침 외에도 실행 코드와 산출물 템플릿까지 포함하는 경향이 있다. `AGENTS.md`, Claude Code의 `.claude/skills/`, 다양한 agent-skill 호환 시스템은 이 패턴을 IDE 밖 CLI 에이전트로 확장한다.

### 왜 중요한가 / 커뮤니티 내 위치

Skill은 prompt engineering과 fine-tuning 사이의 운영 계층이다. 모델 가중치를 바꾸지 않고 조직의 리뷰 기준과 도구 사용법을 배포하며, 필요한 지식만 로드해 토큰을 절약한다. 동시에 Skill은 실행 권한을 가진 “소프트웨어 공급망”이므로 출처, 권한, 네트워크 접근, 스크립트 감사가 필수다. Anthropic도 Skill을 소프트웨어처럼 감사하라고 경고한다. 공식 예제와 명세는 [anthropics/skills](https://github.com/anthropics/skills), 상호운용 예는 [huggingface/skills](https://github.com/huggingface/skills)에서 볼 수 있다.

작성은 하나의 좁은 책임, 정확한 trigger 설명(무엇을/언제), 단계별 절차, 좋은/나쁜 예, 실패·중단 조건, 최소 권한 스크립트로 구성한다. 배포는 프로젝트 디렉터리와 Git, 개인 디렉터리, 플러그인/마켓플레이스, API 업로드 중 표면에 맞게 선택한다. 평가는 단순히 “실행됐는가”가 아니라 ① trigger precision/recall, ② 비활성 기준 대비 task success, ③ 토큰·지연 비용, ④ 잘못된 도구 호출과 보안 위반, ⑤ 모델·저장소별 회귀를 고정 데이터셋에서 반복 측정한다. 2026년 [SWE-Skills-Bench](https://arxiv.org/abs/2603.15401)는 실제 저장소 태스크에서 skill의 효과를 분리 측정하려는 흐름을 보여준다.

### 대표 도구/프로젝트

- [Anthropic Agent Skills 문서](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview), [anthropics/skills](https://github.com/anthropics/skills): `SKILL.md` 명세, 템플릿, 예제, 플러그인 배포.
- [Cursor Rules](https://docs.cursor.com/context/rules): 경로·관련성·수동 호출에 따라 적용하는 저장소 규칙.
- [AGENTS.md](https://agents.md/): 여러 코딩 에이전트가 읽는 저장소 수준 운영 지침.
- [skills.sh](https://skills.sh/): 커뮤니티 skill 탐색·설치 생태계. 설치 전 내용과 provenance 감사가 전제다.

### Selvage 적용 아이디어

1. **Review Skill SDK**: `security-review`, `python-api-compat`, `migration-review`처럼 `SKILL.md + rubric.yaml + examples/ + optional scripts/`를 정의하고 CLI·MCP·Claude 플러그인이 같은 패키지를 읽게 한다.
2. **AST-aware trigger**: 파일 glob만 보지 말고 Tree-sitter 노드, import 변화, public API 변경, SQL/crypto 호출을 trigger feature로 사용해 필요한 skill만 로드한다.
3. **서명된 배포와 sandbox**: Skill manifest에 버전·해시·권한(파일/명령/네트워크)을 선언하고, 제3자 스크립트는 기본 비활성 및 격리 실행한다.
4. **Skill eval CLI**: `selvage skill eval`로 golden diff에 대한 발견율, 오탐, 리뷰 중복, 토큰 비용을 no-skill baseline과 모델별로 비교해 PR 품질 게이트로 만든다.

---

## 2. Loop Engineering

### 정의

Loop Engineering은 에이전트가 **상태를 관찰하고, 다음 행동을 선택하고, 외부 피드백으로 평가한 뒤, 종료하거나 수정해 재시도**하도록 제어 루프를 설계하는 일이다. 핵심은 무한히 “다시 생각”시키는 것이 아니라 상태, 검증기, 예산, 종료 조건을 명시하는 것이다.

[ReAct](https://arxiv.org/abs/2210.03629)는 reasoning과 action/observation을 교차시켜 외부 환경에서 계획을 갱신한다. [Reflexion](https://arxiv.org/abs/2303.11366)은 실패의 scalar 또는 언어 피드백을 짧은 reflection memory로 바꾸어 다음 trial을 개선한다. [Self-Refine](https://arxiv.org/abs/2303.17651)은 초안→자기 피드백→수정의 inference-time 반복이다. 한편 RALM(Retrieval-Augmented Language Model)은 그 자체가 개선 루프라기보다 생성 중 검색 결과를 관찰로 공급하는 계열이다. 그러므로 ReAct/Reflexion의 evidence acquisition 구성요소로 보는 편이 정확하다.

### 왜 중요한가 / 커뮤니티 내 위치

코드 리뷰는 한 번의 생성보다 루프에 잘 맞는다. “의심 지점 찾기→정의·호출부 검색→테스트/정적 분석 확인→finding 작성→반증 검색”이 인간 리뷰 과정과 가깝기 때문이다. 하지만 같은 모델이 만든 결론을 같은 모델이 근거 없이 승인하면 self-confirmation이 강화된다. 2026년 [recursive self-improvement survey](https://arxiv.org/abs/2607.07663)가 강조하듯, 자유 형식 자기평가보다 테스트·타입체커·AST invariant 같은 외부 검증기가 강하다. 비용 폭증, 컨텍스트 오염, 반복적 오탐을 막기 위해 max turns, token/cost budget, progress invariant, 동일 상태 감지, human escalation이 필요하다.

### 대표 도구/프로젝트

- [ReAct](https://react-lm.github.io/), [Reflexion](https://arxiv.org/abs/2303.11366), [Self-Refine](https://selfrefine.info/): 행동, 기억, 출력 개선의 세 가지 대표 패턴.
- [LangGraph](https://github.com/langchain-ai/langgraph): 상태 그래프, checkpoint, human-in-the-loop 기반 장기 실행.
- [AutoGen](https://github.com/microsoft/autogen), [CrewAI](https://github.com/crewAIInc/crewAI): 복수 역할·에이전트 대화와 반복 실행.
- [Inspect AI의 ReAct agent](https://inspect.aisi.org.uk/): sandbox, 도구, scorer를 포함한 평가 가능한 loop 구현.

### Selvage 적용 아이디어

1. **Finding verification loop**: 1차 reviewer가 finding 후보를 만들면 verifier가 Smart Context에서 반증 근거와 테스트를 찾고, `supported / uncertain / rejected` 및 증거 라인을 반환한다.
2. **다모델 debate를 선택적으로 사용**: 고위험 security/API finding만 다른 provider가 비판하게 하고, 합의가 아니라 독립 증거·AST 경로·테스트 결과로 채택한다.
3. **Active context expansion**: 처음에는 최소 AST 블록을 주고, reviewer가 unresolved symbol이나 call site를 요청할 때만 컨텍스트를 확장해 RALM형 검색 루프의 비용을 통제한다.
4. **명시적 종료 정책**: 새 증거 없음, 동일 finding hash 반복, budget 초과, 모든 rubric 통과를 종료 조건으로 기록하고 MCP 응답에 종료 이유를 노출한다.
5. **학습 가능한 reflection memory**: 확인된 오탐/누락만 익명화해 저장소별 review memory 후보로 만들되, 자동 영구 반영 대신 인간 승인과 만료일을 둔다.

---

## 3. Harness Engineering

### 정의

Harness Engineering은 foundation model이 실제 에이전트로 작동하도록 입력, 도구, 메모리, 권한, sandbox, retry, checkpoint, 동시성, 예산, 결과 형식을 중개하는 **실행 기질(runtime substrate)**을 설계하는 일이다. [AI Harness Engineering](https://arxiv.org/abs/2605.13357)은 성능 단위를 모델 단독이 아니라 model–harness–environment 시스템으로 본다.

세 용어를 구분해야 한다. **Agent harness/scaffold**는 모델의 관찰→도구 호출→상태 갱신을 실행한다. **Runtime harness**는 프로세스·컨테이너·비밀·파일시스템·승인·복구 같은 운영 경계를 제공한다. **Evaluation harness**는 고정 task를 여러 trial로 실행하고 transcript와 outcome을 수집해 grader로 채점·집계한다. Anthropic의 [agent eval 안내](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)도 Claude Code 같은 agent harness와 평가 인프라를 명확히 나눈다.

### 왜 중요한가 / 커뮤니티 내 위치

같은 모델도 harness의 컨텍스트 선택, 도구 schema, 오류 반환, timeout, 작업 디렉터리에 따라 결과가 크게 달라진다. 특히 코드 에이전트는 명령 실행과 파일 변경이라는 실제 side effect를 가지므로 재현 가능한 commit, 깨끗한 sandbox, network policy와 artifact 보존이 모델 선택만큼 중요하다. Harness는 loop를 안전하게 돌리고 eval을 공정하게 만드는 공통 기반이다.

### 대표 도구/프로젝트

- [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness): 광범위한 LM task/model adapter와 YAML/CLI 평가.
- [Inspect AI](https://inspect.aisi.org.uk/): dataset–solver/agent–scorer 조합, MCP 도구, Docker/Kubernetes 등 sandbox, 외부 coding-agent 평가.
- [DeepEval](https://github.com/confident-ai/deepeval): pytest 유사 LLM/agent eval, tracing과 CI CLI.
- [Patronus AI](https://docs.patronus.ai/docs): evaluator, experiment, agent failure 분석, production monitoring 및 MCP.
- [SWE-bench](https://github.com/SWE-bench/SWE-bench), [Terminal-Bench](https://github.com/laude-institute/terminal-bench): 실제 코드/터미널 outcome 기반 harness 벤치마크.

### Selvage 적용 아이디어

1. **ReviewRun 계약**: diff snapshot, base/head SHA, model·prompt·skill versions, context chunks, tool calls, budgets, findings를 하나의 불변 run manifest로 저장해 CLI와 MCP 결과를 재현한다.
2. **Provider-neutral adapter**: 모델별 retry/structured-output 차이는 adapter에 가두고 동일한 review task와 JSON schema로 비교한다. 멀티턴 chunk 순서도 seed와 함께 기록한다.
3. **격리된 검증 runtime**: 리뷰 자체는 read-only를 기본으로 하고, 테스트 실행은 임시 worktree/container에서 allowlist 명령·시간·CPU·network 제한 하에 수행한다.
4. **Selvage eval harness**: 실제 버그 diff, clean diff, adversarial diff를 fixture로 묶고 finding-level precision/recall, severity calibration, localization, cost, p95 latency를 모델×skill×context 전략별로 산출한다.
5. **checkpoint/resume**: 큰 PR의 파일/청크별 결과를 durable checkpoint로 남겨 provider 장애 후 중복 과금 없이 재개하고 최종 dedup 단계만 다시 실행한다.

---

## 4. Agent Eval & Observability

### 정의

Agent eval은 “좋다”를 task·dataset·grader·metric으로 조작화해 변경 전후를 비교하는 활동이고, observability는 실제 실행의 trace, span, tool call, prompt/model version, token·비용·지연, 오류, 사용자 feedback을 수집해 **왜 그런 결과가 나왔는지** 조사 가능하게 만드는 활동이다. Eval은 주로 사전·반복적 검증, observability는 운영 분포의 가시성이지만, production trace를 regression dataset으로 승격하는 순간 하나의 feedback loop가 된다.

### 왜 중요한가 / 2026 커뮤니티 내 위치

에이전트는 최종 텍스트만 보면 도구를 잘못 골랐는지, 우연히 맞았는지, 실제 환경 상태를 바꿨는지 알 수 없다. 따라서 final outcome과 trajectory를 함께 평가하고 여러 trial에서 성공률과 일관성을 본다. Anthropic은 deterministic grader를 우선하고 필요한 곳에 LLM judge와 인간 교정을 겹치는 “Swiss cheese” 방식을 권한다. 2026년에는 vendor SDK만의 trace에서 [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/)와 OTLP export로 수렴해 기존 관측 스택과 연결하려는 움직임이 뚜렷하다.

프로토콜도 계층을 혼동하지 않아야 한다. [Agent Protocol](https://github.com/langchain-ai/agent-protocol)은 framework-neutral runs, threads, store API를 정의한다. “llama-protocol/agent-protocol”이라는 공인 단일 프로젝트는 확인되지 않았으며, 조사상 지칭 가능한 활성 원본은 LangChain의 저장소다. 이는 MCP(도구·컨텍스트 연결), A2A(에이전트 간 통신), OTel(telemetry)과 목적이 다르다.

### 대표 도구/프로젝트

- [Langfuse](https://github.com/langfuse/langfuse): 오픈소스·self-host 가능한 tracing, prompt/dataset/eval 플랫폼이며 OTel을 지원한다.
- [Helicone](https://github.com/Helicone/helicone): gateway 중심의 provider routing/fallback, 비용·지연, session/agent trace.
- [Braintrust](https://www.braintrust.dev/docs): trace→annotation→dataset→experiment→CI/online scoring의 폐루프.
- [AgentOps](https://docs.agentops.ai/v1/introduction): agent session replay, 비용·오류·도구 활동 관측.
- [LangSmith](https://docs.langchain.com/langsmith/evaluation-concepts): LangChain/LangGraph 친화적 tracing, dataset, offline/online eval.
- [OpenTelemetry](https://opentelemetry.io/)와 [Agent Protocol](https://github.com/langchain-ai/agent-protocol): vendor-neutral telemetry 및 실행 API 경계.

### Selvage 적용 아이디어

1. **OTel-native review trace**: root `review.run` 아래 `git.diff`, `ast.context`, `llm.call`, `tool.verify`, `finding.merge` span을 만들고 OTLP endpoint가 있을 때만 export한다. 코드·prompt 본문은 opt-in/redaction한다.
2. **Finding provenance UI/API**: 각 finding에 model/prompt/skill/context hash, 근거 AST node, verifier 결과를 연결해 MCP client가 “왜 이 지적이 나왔나”를 drill-down하게 한다.
3. **Offline/online dataset flywheel**: 사용자의 accept/dismiss/수정, CI 결과, 실제 회귀를 수집하되 PII·소스 제거 후 hard-negative/golden dataset 후보로 보내고 인간 승인 후 eval에 편입한다.
4. **품질 SLO**: 단순 호출 성공률 외에 validated finding rate, false-positive proxy, duplicate rate, severity drift, cost/KLoC, p95 time-to-first-finding을 모델·언어·PR 크기별로 모니터링한다.
5. **exporter plugin**: 로컬 JSONL 기본값을 유지하면서 Langfuse/Helicone/Braintrust/LangSmith는 선택 adapter로 제공해 오픈소스 CLI의 vendor lock-in을 피한다.

---

## 5. Spec-driven Development & Review

### 정의

Spec-driven development(SDD)는 자연어 요청을 바로 코드로 변환하지 않고 **검토 가능한 요구사항과 acceptance criteria→설계→작업→테스트→코드→리뷰**의 추적 가능한 계약으로 바꾸는 방식이다. TDD가 실행 가능한 테스트에서 설계를 밀어 올린다면 SDD는 사용자 의도, 제약, 비기능 요구, 설계 결정을 먼저 안정화하고 테스트와 리뷰가 그 계약을 검증하게 한다.

[GitHub Spec Kit](https://github.github.com/spec-kit/)의 기본 흐름은 Spec→Plan→Tasks→Implement이며 agent별 command와 저장소 구조를 설치한다. [Kiro Specs](https://kiro.dev/docs/cli/v3/specs/)는 `.kiro/specs/<name>/requirements.md`, `design.md`, `tasks.md`를 만들고 단계별 인간 검토와 실행 중 검증을 제공한다. “Amazon Kiro”와 “Kiro”는 별도 도구가 아니라 같은 제품 계열이다. 요청에 적힌 중국어 **专项整治**는 일반적으로 “특별 정비/집중 단속”을 뜻하며, 확인 가능한 SDD 도구·방법론 이름은 아니므로 대표 프로젝트 목록에서는 제외한다.

### 왜 중요한가 / 커뮤니티 내 위치

에이전트가 코드를 더 빨리 생성할수록 잘못된 요구를 빠르게 구현하는 비용도 커진다. Spec은 인간과 에이전트가 성공 조건을 공유하고, 리뷰가 스타일 의견 대신 “어떤 requirement와 test를 만족/위반했는가”를 말하게 한다. 단, 문서가 많다고 정확성이 생기지는 않는다. spec–test–code drift, 오래된 acceptance criteria, agent가 자신이 만든 spec을 느슨하게 해석하는 문제가 있다. 따라서 각 requirement에 안정적 ID를 주고 테스트·변경 코드·finding의 양방향 traceability와 review gate를 자동화해야 한다.

### 대표 도구/프로젝트

- [GitHub Spec Kit](https://github.com/github/spec-kit): agent-agnostic CLI 템플릿과 specify/plan/tasks/implement workflow.
- [Kiro](https://github.com/kirodotdev/Kiro): requirements-first/design-first/bugfix spec, steering, hooks, MCP.
- [OpenSpec](https://github.com/Fission-AI/OpenSpec): brownfield 변화에 맞춘 경량 SDD artifact와 change workflow.
- [Cucumber](https://github.com/cucumber/cucumber), [pytest-bdd](https://github.com/pytest-dev/pytest-bdd): acceptance criteria를 실행 가능한 BDD 테스트로 연결.

### Selvage 적용 아이디어

1. **Spec ingestion**: CLI/MCP가 `.kiro/specs`, Spec Kit artifact, issue/PR body를 자동 탐색하고 requirement ID와 acceptance criteria만 Smart Context에 구조화해 넣는다.
2. **Traceability review**: `REQ-12 → tests/test_auth.py::test_expiry → changed AST nodes → findings` 그래프를 만들고 미구현 요구, 테스트 없는 요구, 요구 없는 scope creep을 별도 finding 유형으로 낸다.
3. **Spec-aware rubric**: correctness/security/style 외에 `spec_conformance`, `acceptance_coverage`, `design_deviation`을 추가하되, 모호한 spec은 코드 결함으로 단정하지 않고 clarification으로 분류한다.
4. **Spec → Test → Code → Review gate**: 구현 전에 테스트 후보의 완전성과 모순을 리뷰하고, 구현 후 fail-to-pass/pass-to-pass 및 AST API 변화를 검증한 뒤 사람이 승인하도록 CI exit code와 SARIF/JSON을 제공한다.
5. **Drift diff**: spec·test·public API의 세 diff를 함께 비교해 코드만 바뀐 경우뿐 아니라 spec만 완화되거나 테스트가 삭제되어 “통과”한 경우도 경고한다.

---

## 최근 6개월 GitHub Trending Dev Tools — 편집 TOP 15

GitHub Trending은 일/주/월 현재 순위만 제공하고 6개월 공식 archive/API를 제공하지 않는다. 따라서 아래는 **2026-01-17~07-17에 GitHub Trending/주간 순위에 등장했거나 높은 star velocity·release 활동이 관찰된 개발자용 AI 도구**를, 이 보고서와의 관련성·지속 활동으로 재정렬한 편집 순위다. 누적 star 순위나 GitHub 공식 반기 순위로 해석하면 안 된다. 기준일 당일 Trending 페이지에는 skill 저장소와 agent 안전 도구가 상위에 나타났고, 주간 집계도 agent/dev tooling 집중을 보고했다([GitHub Trending](https://github.com/trending), [2026-07-13 주간 스냅샷](https://www.techtarget.com/searchapparchitecture/tip/What-repos-are-trending-on-GitHub)).

1. [anomalyco/opencode](https://github.com/anomalyco/opencode) — provider-agnostic 오픈소스 terminal coding agent.
2. [openai/codex](https://github.com/openai/codex) — 로컬에서 실행되는 경량 coding-agent CLI.
3. [anthropics/skills](https://github.com/anthropics/skills) — Agent Skills 명세·템플릿·공식 예제.
4. [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) — Gemini 기반 오픈소스 terminal agent와 MCP client/server.
5. [mattpocock/skills](https://github.com/mattpocock/skills) — 실무 개발 workflow를 패키징한 대형 skill 모음.
6. [github/spec-kit](https://github.com/github/spec-kit) — agent-agnostic spec-driven development toolkit.
7. [browser-use/browser-use](https://github.com/browser-use/browser-use) — 웹을 agent action environment로 만드는 브라우저 자동화.
8. [All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands) — sandbox형 software-development agent 플랫폼.
9. [langfuse/langfuse](https://github.com/langfuse/langfuse) — self-host 가능한 LLM/agent observability와 eval.
10. [mendableai/firecrawl](https://github.com/mendableai/firecrawl) — agent/RAG를 위한 웹 수집·구조화 API.
11. [cline/cline](https://github.com/cline/cline) — IDE 안에서 계획·도구·승인을 결합한 coding agent.
12. [confident-ai/deepeval](https://github.com/confident-ai/deepeval) — LLM/agent 테스트와 tracing을 결합한 Python eval framework.
13. [UKGovernmentBEIS/inspect_ai](https://github.com/UKGovernmentBEIS/inspect_ai) — sandbox와 외부 agent를 지원하는 AI evaluation framework.
14. [Dicklesworthstone/destructive_command_guard](https://github.com/Dicklesworthstone/destructive_command_guard) — agent의 위험한 shell/git 명령을 차단하는 runtime guard.
15. [Nutlope/hallmark](https://github.com/Nutlope/hallmark) — Claude Code, Cursor, Codex용 디자인 품질 skill.

## Selvage 권장 도입 순서

단기에는 `ReviewRun` manifest와 OTel span으로 실행 증거를 고정하고, 실제 diff 기반 golden/clean eval suite를 만든다. 그 위에 spec ingestion과 finding verification loop를 올린다. 마지막으로 검증된 rubric을 Review Skill SDK로 외부화한다. 이 순서는 **관측할 수 없는 loop**와 **평가할 수 없는 skill**을 먼저 확산시키는 위험을 줄인다. 제품 메시지도 “LLM이 리뷰한다”보다 “AST로 필요한 근거를 선택하고, 복수 모델과 검증 루프로 finding을 확인하며, spec부터 결과까지 재현 가능한 증거를 남긴다”로 이동할 수 있다.

핵심 원칙은 간단하다. 생성은 확률적이어도 **입력 snapshot, 실행 권한, 검증기, 종료 조건, provenance와 품질 기준은 결정적으로 관리**해야 한다.
