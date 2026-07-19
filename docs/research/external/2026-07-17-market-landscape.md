# AI 코드 리뷰 도구 시장 지형 — 2026년 중반

> 조사 기준일: 2026-07-17 (가격은 USD, 세금 제외). 공식 문서·가격표·변경 로그와 GitHub 원문을 우선했다. 제품명·가격은 변동이 빠르므로 이 문서는 시점 스냅샷이다.

## Executive summary

**핵심 요약.** 시장은 단순 diff 요약에서 저장소 전체를 탐색하고, 사양·조직 규칙을 검증하며, 발견한 문제를 직접 고치는 agentic review로 이동했다. 동시에 전용 SaaS는 $24~30/개발자/월 또는 리뷰별 과금으로 수렴하고, 범용 CLI는 무료 오픈소스/BYOK와 구독형 고성능 에이전트로 양극화된다.

- 가격 경쟁의 기준도 바뀌었다. CodeRabbit Pro는 연간 결제 시 $24/사용자/월, Greptile Pro는 $30/활성 개발자/월+초과 리뷰 $1, Qodo는 좌석이 아니라 월 $30부터의 credit pool, Ellipsis는 예시상 중간 PR 리뷰당 약 $0.74다. 반대로 Claude Code Review는 깊은 멀티 에이전트 검증을 내세우며 평균 $15~25/PR이다. [CodeRabbit 가격](https://www.coderabbit.ai/pricing), [Greptile 가격](https://www.greptile.com/pricing), [Qodo 가격](https://www.qodo.ai/pricing/), [Ellipsis 가격](https://www.ellipsis.dev/pricing), [Claude Code Review](https://support.claude.com/en/articles/14233555-set-up-code-review-for-claude-code)
- `Greptaper`는 공식 제품·저장소를 확인하지 못했다. `CodeRabbit-GPT5` 역시 별도 제품이 아니라 CodeRabbit이 GPT-5 계열을 멀티모델 파이프라인에서 평가·라우팅한 맥락이다. Qodo의 과거 명칭도 “MergeMate”가 아니라 **Qodo Merge(구 PR-Agent)**이며, 회사명은 CodiumAI에서 Qodo로 바뀌었다. [CodeRabbit 모델 운영 설명](https://www.coderabbit.ai/blog/behind-the-curtain-what-it-really-takes-to-bring-a-new-model-online-at-coderabbit), [Qodo 명칭 안내](https://www.qodo.ai/formerly-qodo-merge/), [Qodo 리브랜딩](https://www.qodo.ai/blog/introducing-qodo-a-new-name-the-same-commitment-to-quality/)

## 1. 상용 경쟁사 최신 상태

**핵심 요약.** 전용 리뷰 업체는 정밀도와 조직별 규칙을, 플랫폼 업체는 GitHub/IDE/에이전트 안에서의 즉시 수정과 배포 연결을 차별점으로 삼는다. 지난 12개월의 공통 업데이트는 멀티 에이전트, 티켓·문서 문맥, 로컬 사전 리뷰, 사용량 과금이다.

| 제품 | 핵심 기능·차별점 | 2026-07 가격 | 최근 12개월 주요 변화 |
|---|---|---|---|
| **CodeRabbit** | GitHub/GitLab/Azure DevOps PR 리뷰, linters·SAST 결합, 대화형 수정, multi-repo 분석과 Plan→review→unit test/merge-conflict 해결까지 연결한다. [제품/가격](https://www.coderabbit.ai/pricing) | Pro $24/사용자/월(연간), Pro+ $48, Enterprise 협의·self-host 옵션. [가격](https://www.coderabbit.ai/pricing) | 2026년 Plan, 논리 순서로 PR을 보여주는 Change Stack, 전역 override·감사 로그, Pro+를 추가했다. [changelog](https://docs.coderabbit.ai/changelog) |
| **Greptile** | 저장소 그래프를 이용한 full-codebase review, 사용자 규칙·feedback 학습, GitHub/GitLab, self-host를 제공한다. 외부 SDK의 파트너 제공 문서까지 출처와 함께 적용하는 점이 독특하다. [문서/변경 로그](https://www.greptile.com/changelog) | Starter 무료(1명, 월 50 standard reviews), Pro $30/활성 개발자/월에 50 credits, 초과 $1/review; Enterprise 협의. [가격](https://www.greptile.com/pricing) | v4에서 업체 측 측정상 addressed comments/PR이 0.92→1.60으로 늘었고, 2026-06 Repo Clusters(최대 7개 관련 repo), partner context, 무료 개인 tier를 출시했다. [v4](https://www.greptile.com/blog/greptile-v4), [changelog](https://www.greptile.com/changelog) |
| **Qodo** (구 Qodo Merge/PR-Agent) | multi-agent review, PR-history 기반 Context Engine, 중앙 Rule System, IDE·Git·CLI, multi-repo 및 on-prem/air-gap이 강점이다. [Qodo 2 review](https://docs.qodo.ai/code-review), [배포/기능](https://www.qodo.ai/formerly-qodo-merge/) | 영구 무료 tier 없이 14일 trial. Pro Team은 $30/월 2,500 credits(약 18 reviews)부터, $0.012/credit; Enterprise 협의/BYOK/on-prem. [가격](https://www.qodo.ai/pricing/) | 2026-02 Qodo 2.0 GA로 멀티 에이전트 리뷰, 2.1로 규칙 자동 발견·충돌 관리와 Azure DevOps, 2.2로 PR Knowledge와 finding recommendation agent를 도입했다. [changelog](https://docs.qodo.ai/changelog), [2.2](https://www.qodo.ai/blog/qodo-2-2-code-review-that-learns-from-your-pr-history-context/) |
| **Cursor BugBot** | PR 자동/수동 리뷰, directory-scoped `.cursor/BUGBOT.md`, IDE에서 발견 항목을 즉시 고치는 흐름과 push 전 `/review`를 결합한다. [문서](https://docs.cursor.com/bugbot) | 2026-06부터 좌석 $40 정액을 없애고 사용량 과금; 평균 run $1.00~1.50, effort level로 비용·깊이 조절. [가격 변경](https://cursor.com/blog/may-2026-bugbot-changes) | 2026-06 Composer 2.5 기반으로 평균 약 90초, 업체 측 기준 22% 저렴하고 10% 더 많은 버그를 찾도록 갱신; incremental review와 로컬 `/review` 추가. [changelog](https://cursor.com/changelog/bugbot-updates-june-2026) |
| **GitHub Copilot code review** | GitHub PR·VS Code에서 inline finding과 적용 가능한 수정안을 만들며, custom instructions뿐 아니라 2026년에는 agent skills와 MCP context도 public preview로 읽는다. 리뷰 모델은 자동 선택이라 사용자가 바꿀 수 없다. [기능](https://docs.github.com/en/copilot/concepts/agents/code-review) | 유료 Copilot에 포함: Pro $10, Pro+ $39, Max $100, Business $19, Enterprise $39/사용자/월. 1 AI credit=$0.01이며 2026-06-01부터 agentic review는 Actions minutes도 소비한다. [플랜](https://docs.github.com/en/copilot/get-started/plans), [과금](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing) | 2026년 usage-based AI credits, 무면허 PR 작성자에 대한 조직 직접 과금, MCP/skills 기반 context와 review effort를 도입했다. [기능/사용량](https://docs.github.com/en/copilot/concepts/agents/code-review), [과금 전환](https://docs.github.com/en/copilot/reference/copilot-billing/request-based-billing-legacy/what-changed-with-billing) |
| **Sourcegraph** | 전용 리뷰 봇보다는 reviewer/agent 아래의 **retrieval layer**다. cross-repo Code Search, precise navigation, Deep Search, MCP로 callers·tests·관련 변경을 공급한다. Amp는 2025-12 별도 회사가 됐다. [시장 포지션](https://sourcegraph.com/blog/ai-code-review), [분리](https://sourcegraph.com/blog?page=2) | 공개 self-serve 단가는 없고 volume/Enterprise 협의. [가격](https://sourcegraph.com/pricing?product=codeIntelligence) | 2026-02 Sourcegraph 7.0이 “AI agent용 intelligence layer”로 재정의됐고, MCP 및 experimental Agentic Migrations를 확대했다. [7.0](https://sourcegraph.com/blog/a-new-era-for-sourcegraph-the-intelligence-layer-for-ai-coding-agents-and-developers), [agentic coding](https://sourcegraph.com/blog/agentic-coding) |
| **Bito** | codebase-aware PR/IDE/CLI 리뷰, static analysis·OSS vulnerability 결과 결합, feedback 학습, Jira/Confluence requirement validation, GitHub/GitLab/Bitbucket 및 self-managed를 지원한다. [개요](https://docs.bito.ai/ai-code-reviews-in-git/overview) | Free는 PR summary, Team $12(연간)/$15(월간), Professional $20/$25 per seat; self-host는 Professional에 $5/seat/월 추가, Enterprise 협의. [가격/플랜](https://docs.bito.ai/help/billing-and-plans/overview) | 2025-09 Jira ticket 검증, 11월 `AGENTS.md` 등 agent rule 자동 적용과 `.bito.yaml`, 2026-01 CLI review, 02월 Confluence context를 추가했다. [changelog](https://docs.bito.ai/changelog) |
| **Ellipsis** | repo 안에 정의한 managed coding agents가 PR 리뷰뿐 아니라 call-site 수정, 테스트 실행, Sentry alert fix와 PR 생성까지 수행한다. 과거 review feedback을 팀 규칙으로 활용하고 BYOK Bedrock/private cloud를 제공한다. [가격·기능](https://www.ellipsis.dev/pricing) | 좌석비 없이 token+CPU+memory+platform fee. 계산기 예시의 중간 PR review는 약 $0.74; 신규 조직 $100 credit, spending cap 지원. [가격](https://www.ellipsis.dev/pricing) | 공개된 정형 changelog는 찾기 어렵지만, 현재 제품은 “리뷰 코멘트”보다 git-push로 배포하는 범용 agent와 action/fix 자동화에 초점을 둔다. [제품/가격](https://www.ellipsis.dev/pricing) |
| **Greptaper** | 2026-07-17 현재 공식 사이트·문서·활성 GitHub 저장소로 식별되지 않았다. 유사 명칭인 Greptile과 혼동했을 가능성이 높다. | 검증 불가 | 검증 불가. 비교·구매 목록에서는 정확한 vendor URL 확인 전 제외하는 것이 안전하다. |
| **CodeRabbit-GPT5** | 별도 제품/SKU가 아니다. CodeRabbit은 GPT-5를 “bug-hunting detailed developer”, GPT-5-Codex를 patch generator 성향으로 평가해 서로 다른 pipeline 역할에 배치한다. [모델 분석](https://www.coderabbit.ai/blog/the-end-of-one-sized-fits-all-prompts-why-llm-models-are-no-longer-interchangeable) | CodeRabbit 요금에 포함; 모델별 별도 공개 가격 없음. [가격](https://www.coderabbit.ai/pricing) | 최근 12개월에는 GPT-5·5.1·Codex 등 모델별 eval을 거쳐 prompt와 context packing을 따로 조정하는 multi-model 운영 방식이 공개됐다. [운영 설명](https://www.coderabbit.ai/blog/behind-the-curtain-what-it-really-takes-to-bring-a-new-model-online-at-coderabbit) |

## 2. OSS·CLI 경쟁 지형

**핵심 요약.** 이 그룹은 대개 “전용 PR 리뷰어”가 아니라 로컬 diff를 읽고 테스트·수정까지 할 수 있는 범용 코딩 에이전트다. 따라서 Selvage와의 직접 경쟁은 리뷰 UX보다 무료/BYOK, 모델 선택, MCP, local-first context 조립에서 발생한다.

| 도구 | 리뷰 관점의 상태·차별점 | 가격 및 최근 상태 |
|---|---|---|
| **Aider** | git-native 터미널 pair programmer로 repo map, diff/edit format, 자동 commit을 제공해 “변경 검토→수정”을 한 세션에서 수행한다. 여러 provider/OpenRouter를 고를 수 있다. [repo](https://github.com/Aider-AI/aider), [모델 설정](https://aider.chat/docs/troubleshooting/models-and-keys.html) | Apache-2.0 무료+LLM API 비용. 2026-05까지 활동했으며, 모델별 edit format과 비용 metadata를 계속 갱신했다. [releases](https://github.com/Aider-AI/aider/releases), [metadata](https://aider.chat/docs/config/adv-model-settings.html) |
| **Cline** | VS Code·CLI의 autonomous agent로 Plan/Act, MCP, rules/skills/plugins, command permission, local model을 지원한다. 전용 PR bot보다는 로컬 검토와 실제 수정에 강하다. [repo](https://github.com/cline/cline), [CLI](https://docs.cline.bot/cli/cli-reference) | Apache-2.0 앱 무료; Cline credits/BYOK/provider 사용량 또는 local compute. 2026년 CLI·ACP·scheduler·kanban까지 표면이 넓어졌다. [비용](https://docs.cline.bot/core-workflows/task-management), [CLI](https://docs.cline.bot/cli/cli-reference) |
| **Continue** | CLI/VS Code/JetBrains, configurable models·rules·MCP와 GitHub Actions PR review recipe를 제공하며 offline/local model도 가능하다. [가이드](https://docs.continue.dev/guides/overview) | Apache-2.0 무료+provider 비용. 다만 2026년 final 2.0.0 뒤 기존 repo를 read-only/비활성 유지로 전환했다고 공지해 신규 채택 리스크가 있다. [공식 상태](https://docs.continue.dev/) |
| **OpenHands** | model-agnostic autonomous developer로 GUI/TUI/CLI, sandbox, Git/Jira/Slack, Agent SDK·MCP를 제공한다. 이슈 해결·테스트·PR 생성 루프가 중심이다. [repo](https://github.com/OpenHands/OpenHands), [가격](https://www.openhands.dev/pricing/) | 로컬 OSS 무료(MIT), Individual cloud 무료+BYOK/at-cost model, Enterprise 협의. 2026-03 Planning Agent와 skills slash menu를 추가했다. [업데이트](https://www.openhands.dev/blog/openhands-product-update---march-2026) |
| **Claude Code** | 터미널 agent이며 `/security-review`와 GitHub Action 외에, 2026년 Team/Enterprise용 Code Review research preview가 specialized agent fleet+verification으로 full-codebase PR을 분석한다. `CLAUDE.md`·`REVIEW.md` 규칙을 읽는다. [security review](https://support.claude.com/en/articles/11932705-automated-security-reviews-in-claude-code), [Code Review](https://support.claude.com/en/articles/14233555-set-up-code-review-for-claude-code) | CLI는 Pro $20, Max $100/$200 또는 Team/Enterprise/API; 전용 Code Review는 별도 평균 $15~25/PR. 소스 공개 repo지만 명시적 OSS license가 없어 “CLI”로 보는 편이 정확하다. [플랜](https://support.claude.com/en/articles/11049762-choose-a-claude-plan), [repo](https://github.com/anthropics/claude-code) |
| **Codex CLI** | 로컬 sandbox/approval, `AGENTS.md`, MCP·web search와 `codex review`를 제공하며, GitHub에서는 PR intent와 전체 codebase를 탐색하고 tests를 실행한 뒤 같은 thread에서 수정까지 위임할 수 있다. [repo](https://github.com/openai/codex), [리뷰](https://openai.com/index/introducing-upgrades-to-codex/) | Apache-2.0 CLI; ChatGPT Plus/Pro/Business/Edu/Enterprise에 포함 또는 API 비용. 2026년 app의 multi-agent 병렬 실행, Hooks·remote SSH와 조직 통제가 추가됐다. [app](https://openai.com/index/introducing-the-codex-app/), [2026 updates](https://openai.com/index/work-with-codex-from-anywhere/) |
| **Bloop** | Rust semantic code search/repo 이해 도구로 리뷰 context에 인접했지만 전용 reviewer는 아니다. [repo](https://github.com/BloopAI/bloop) | Apache-2.0 무료. repo가 2024-12 이후 업데이트 없이 archived되어 현재 경쟁력은 낮다. [repo 상태](https://github.com/BloopAI/bloop) |
| **Ruler** | 한 벌의 Markdown rules를 Claude Code, Codex, Cursor, Cline 등 여러 agent 형식으로 배포해 review standard의 vendor lock-in을 줄인다. [repo](https://github.com/intellectronica/ruler) | MIT 무료. 2026-07까지 활발하며, 그 자체가 reviewer라기보다 cross-agent rule distribution layer다. [commits](https://github.com/intellectronica/ruler/commits/main/) |
| **Refact** | IDE local engine, BYOK/local models, RAG, shell/browser/Git/MCP를 갖춘 agent다. [제품](https://refact.ai/blog/2026/refact-cloud-is-shutting-down/) | 2026-04 Cloud 종료를 발표하고 local-first·BYOK·community-maintained OSS로 전환했다. hosted subscription은 사라지며 provider/local compute만 부담한다. [종료 공지](https://refact.ai/blog/2026/refact-cloud-is-shutting-down/), [repo](https://github.com/smallcloudai/refact) |
| **Tabby** | self-hosted AI coding assistant/server로 IDE completion·chat와 private deployment가 중심이며 전용 PR review workflow는 약하다. [repo](https://github.com/TabbyML/tabby) | Community/self-host 무료, Enterprise는 별도 계약. 2026-06까지 유지되지만 핵심 차별점은 review precision보다 데이터 통제와 local serving이다. [repo/releases](https://github.com/TabbyML/tabby/releases) |

## 3. 시장 트렌드 5개

**핵심 요약.** 리뷰의 산출물이 “코멘트”에서 “검증된 변경”으로 바뀌고, 품질은 모델 이름보다 어떤 코드·사양·조직 지식을 회수하고 어떤 도구로 검증하느냐에 더 좌우된다.

1. **Autonomous fixing과 closed loop.** BugBot은 push 전 리뷰를, Codex는 review thread에서 수정 위임을, Ellipsis는 테스트가 통과할 때까지 고쳐 PR을 여는 흐름을 제공한다. 리뷰와 구현의 제품 경계가 사라지고 있다. [BugBot](https://cursor.com/changelog/bugbot-updates-june-2026), [Codex](https://openai.com/index/introducing-upgrades-to-codex/), [Ellipsis](https://www.ellipsis.dev/pricing)
2. **Spec-driven review.** Bito의 Jira·Confluence 검증, CodeRabbit Plan, Qodo ticket/rule compliance처럼 “코드가 문법적으로 맞는가”보다 “요구사항과 acceptance criteria를 구현했는가”가 새 평가 축이다. [Bito changelog](https://docs.bito.ai/changelog), [CodeRabbit changelog](https://docs.coderabbit.ai/changelog), [Qodo](https://www.qodo.ai/formerly-qodo-merge/)
3. **Repo graph와 institutional memory.** Greptile Repo Clusters, Qodo PR Knowledge, Sourcegraph cross-repo retrieval은 diff 밖의 callers·과거 결정·관련 서비스를 찾는다. 즉 장기 moat는 LLM 자체보다 context graph와 feedback history에 형성된다. [Greptile](https://www.greptile.com/changelog), [Qodo 2.2](https://www.qodo.ai/blog/qodo-2-2-code-review-that-learns-from-your-pr-history-context/), [Sourcegraph](https://sourcegraph.com/blog/ai-code-review)
4. **멀티 에이전트 검증과 reviewer independence.** Qodo와 Claude는 서로 다른 issue class를 병렬 탐색하고 verification/dedup 단계를 둔다. 하나의 생성 모델이 자기 코드를 단순 재독하는 방식보다 독립 역할·모델·adversarial pass가 신뢰 설계의 핵심이 된다. [Qodo 2.0](https://docs.qodo.ai/code-review), [Claude Code Review](https://support.claude.com/en/articles/14233555-set-up-code-review-for-claude-code)
5. **Review-action 통합과 usage economics.** GitHub는 review에 AI credits+Actions minutes를, Cursor는 effort별 run 비용을, Greptile은 included review+overage를 부과한다. 정밀한 incremental context, cache, AST selection은 품질 기능인 동시에 gross-margin 기능이 됐다. [GitHub 과금](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing), [Cursor 가격](https://cursor.com/blog/may-2026-bugbot-changes), [Greptile billing](https://www.greptile.com/docs/code-review-bot/billing-seats)

## 4. GitHub momentum — 최근 6개월 TOP 10

**핵심 요약.** 별 증가는 OpenCode·Claude Code·Codex 같은 범용 agent와, 2026년 3월 등장해 review/ship workflow를 skills로 패키징한 gstack에 집중됐다. 이는 전용 reviewer뿐 아니라 “기존 agent에 꽂는 품질 레이어”가 직접 대체재임을 뜻한다.

방법론: GitHub에는 공식 “6개월 trending” 누적표가 없으므로, 2026-03-23 OSS Insight의 동일 카테고리 스냅샷과 2026-07-17 GitHub API 관측값을 비교했다. `gstack`은 2026-03-11 신규 repo라 생성 이후 전량을 증가분으로 보았다. 따라서 아래 `관측 증가`는 엄밀한 2026-01-17 기준이 아니라 **최근 4개월의 검증 가능한 하한치**이며, 현재 stars는 반올림하지 않은 조사 시점 값이다. 별은 관심도 지표이지 실제 사용량·품질 지표가 아니다. [OSS Insight 기준표](https://ossinsight.io/blog/coding-agent-wars-2026), [GitHub Trending](https://github.com/trending)

| 순위 | 저장소 | 2026-07-17 stars | 2026-03 이후 관측 증가 | 한 줄 설명 |
|---:|---|---:|---:|---|
| 1 | [garrytan/gstack](https://github.com/garrytan/gstack) | 122,244 | +122,244 | Claude/Codex 등에서 plan→review→QA→ship을 실행하는 opinionated skills 묶음; 2026-03 신규. |
| 2 | [anomalyco/opencode](https://github.com/anomalyco/opencode) | 186,468 | +58,191 | 멀티 provider·TUI 중심의 오픈소스 코딩 에이전트. |
| 3 | [anthropics/claude-code](https://github.com/anthropics/claude-code) | 138,081 | +56,644 | repo-aware terminal agent와 hooks/subagents; 전용 PR Code Review의 호스트. |
| 4 | [openai/codex](https://github.com/openai/codex) | 98,780 | +31,811 | Rust 기반 local agent, sandbox·MCP·내장 review와 cloud handoff. |
| 5 | [aaif-goose/goose](https://github.com/aaif-goose/goose) | 51,288 | +17,835 | model-agnostic·MCP 확장형 로컬 autonomous agent. |
| 6 | [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) | 80,998 | +11,422 | sandboxed software agent platform·SDK와 Git workflow. |
| 7 | [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) | 106,021 | +7,286 | Gemini 기반 오픈소스 터미널 agent와 MCP/automation. |
| 8 | [cline/cline](https://github.com/cline/cline) | 64,722 | +5,470 | VS Code·CLI에서 모델을 골라 파일·명령·브라우저를 조작하는 agent. |
| 9 | [Aider-AI/aider](https://github.com/Aider-AI/aider) | 47,432 | +5,168 | git-native multi-LLM pair programmer와 repo map. |
| 10 | [continuedev/continue](https://github.com/continuedev/continue) | 34,914 | +2,917 | configurable IDE/CLI agent; 현재 final 2.0 이후 maintenance 종료 상태. |

## 5. 시장 빈틈과 Selvage의 포지션

**핵심 요약.** 상위 SaaS는 깊은 문맥과 자동 수정을 제공하지만 비용·클라우드 종속·불투명한 모델 선택이 커지고, 범용 agent는 리뷰 전용의 결정적 context packing과 일관된 출력이 약하다. Selvage가 차지할 수 있는 자리는 “어떤 agent/LLM에도 붙는 로컬 review context compiler”다.

### 아직 충분히 채워지지 않은 니치

| 빈틈 | 현재 한계 | 기회 |
|---|---|---|
| **진짜 local-first·privacy** | 주요 전용 reviewer의 self-host/on-prem은 Enterprise 협의이며, Claude Code Review는 zero-data-retention 조직에서 사용할 수 없다. [Greptile](https://www.greptile.com/pricing), [Qodo](https://www.qodo.ai/pricing/), [Claude](https://support.claude.com/en/articles/14233555-set-up-code-review-for-claude-code) | 로컬 diff/AST 처리, BYOK/local OpenAI-compatible endpoint, 전송 전 context preview·redaction을 무료 기본값으로 제공. |
| **사용자가 통제하는 multi-LLM** | Copilot review는 모델 switching을 지원하지 않고, CodeRabbit은 내부 라우팅을 공개 가격 단위로 노출하지 않는다. [Copilot](https://docs.github.com/en/copilot/concepts/agents/code-review), [CodeRabbit](https://www.coderabbit.ai/blog/behind-the-curtain-what-it-really-takes-to-bring-a-new-model-online-at-coderabbit) | 같은 context에 2개 모델을 병렬 실행하고 합의/불일치·비용·latency를 비교하는 reviewer council. |
| **MCP-native review primitive** | GitHub·Sourcegraph가 MCP를 받아들이지만 대부분은 기존 제품에 추가된 context channel이다. [GitHub](https://docs.github.com/en/copilot/concepts/agents/code-review), [Sourcegraph](https://sourcegraph.com/blog/agentic-coding) | `get_review_context`, `review_diff`, `validate_finding`, `apply_fix`를 작고 조합 가능한 MCP tools로 설계해 모든 host agent에서 재사용. |
| **무료 self-hosted review gate** | Continue는 maintenance 종료, Bloop은 archived, Refact는 community-only로 전환했다. [Continue](https://docs.continue.dev/), [Bloop](https://github.com/BloopAI/bloop), [Refact](https://refact.ai/blog/2026/refact-cloud-is-shutting-down/) | GitHub Actions/GitLab CI용 headless JSON/SARIF, deterministic exit code, budget ceiling을 제공하는 가벼운 OSS gate. |
| **비영어권·한국어 품질** | Bito는 20+ 출력 언어를 지원하지만, 시장 리더의 규칙 예시·온보딩·평가셋은 영어 중심이다. [Bito plans](https://docs.bito.ai/help/billing-and-plans/overview) | 한국어 finding·commit/PR 요약뿐 아니라 한국어 요구사항→코드 compliance benchmark와 bilingual rule pack을 제공. |
| **커스텀 rule plugin 생태계** | `.coderabbit.yaml`, `.greptile/`, Qodo Rule System 등 vendor별 규칙 형식이 파편화됐다. [CodeRabbit](https://docs.coderabbit.ai/changelog), [Greptile](https://www.greptile.com/changelog), [Qodo](https://docs.qodo.ai/changelog) | `AGENTS.md`/`REVIEW.md`/Ruler 규칙을 읽는 adapter와 언어·프레임워크별 review plugin registry를 만든다. |

### Selvage: 현재 위치와 차별화 우선순위

Selvage는 Apache-2.0 Python CLI로 staged/unstaged/branch/commit diff를 리뷰하고, OpenAI·Anthropic·Google·OpenRouter를 선택할 수 있다. Tree-sitter AST로 변경 라인을 감싸는 최소 code block과 dependency statements를 추출하고, 큰 입력은 multi-turn으로 나누며, 자체 MCP server와 host agent가 자체 LLM으로 리뷰하게 하는 `get_review_context`를 이미 제공한다. [Selvage README](https://github.com/selvage-lab/selvage), [PyPI](https://pypi.org/project/selvage/)

현재 포지션은 CodeRabbit/Greptile 같은 SaaS PR lifecycle 제품보다 **Aider·Cline과 전용 SaaS 사이의 로컬 review engine/context layer**에 가깝다. Sourcegraph가 enterprise cross-repo retrieval layer라면 Selvage는 개인·소팀용 AST-precise diff context layer가 될 수 있다. 특히 host agent의 기존 구독/모델을 그대로 쓰게 하는 MCP delegated review는 별도 per-seat/per-review 과금과 모델 lock-in을 동시에 피한다. [Selvage MCP 설명](https://github.com/selvage-lab/selvage#agent-delegated-review-no-api-key-required), [Sourcegraph 포지션](https://sourcegraph.com/blog/ai-code-review)

우선순위는 다음과 같다.

1. **“AST context가 더 싸고 정확하다”를 수치화한다.** 동일 PR에서 raw diff/full-repo/RAG 대비 input tokens, file recall, accepted finding rate, false-positive rate를 공개 benchmark로 만든다. 시장이 model claim보다 retrieval evidence를 요구하기 시작했다. [Sourcegraph의 retrieval 논점](https://sourcegraph.com/blog/ai-code-review)
2. **reviewer에서 verifier로 확장한다.** finding마다 AST path·관련 call site·실행한 test를 evidence로 붙이고, 선택적으로 patch 생성→test→재리뷰까지 닫힌 루프를 제공한다. 이는 Codex·Claude의 verification 방향과 경쟁하되 로컬·멀티 LLM으로 차별화한다. [Codex review](https://openai.com/index/introducing-upgrades-to-codex/), [Claude review](https://support.claude.com/en/articles/14233555-set-up-code-review-for-claude-code)
3. **MCP를 배포 채널로 만든다.** Claude Code 플러그인에 더해 Cursor/Codex/Cline/OpenHands용 설치 recipe, stable JSON schema, SARIF와 CI exit policy를 제공한다. MCP가 보편화될수록 host UI보다 잘 조립된 review context와 검증 도구가 Selvage의 moat가 된다. [Selvage README](https://github.com/selvage-lab/selvage), [OpenHands MCP](https://www.openhands.dev/pricing/)
4. **한국어와 open rule packs를 선점한다.** Django/FastAPI, Spring, React, 보안·개인정보, 한국 전자금융/공공 규칙의 bilingual packs와 한국어 ticket compliance를 커뮤니티 plugin으로 배포한다. 범용 글로벌 SaaS가 경제적으로 깊게 현지화하기 어려운 면이다.

결론적으로 Selvage가 피해야 할 경쟁은 “또 하나의 GitHub 코멘트 봇”이다. 가장 방어력 있는 메시지는 **로컬에서 코드를 구조적으로 압축하고, 원하는 LLM이나 코딩 에이전트에 검증 가능한 review context를 공급하는 오픈 품질 레이어**다. 이 포지션은 프라이버시·비용 통제·멀티 LLM·MCP·한국어라는 아직 분산된 수요를 하나의 일관된 CLI에 묶는다.
