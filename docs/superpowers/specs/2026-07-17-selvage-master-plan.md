# Selvage Master Plan — Agent-Native Verified Review Engine

> 기준일: 2026-07-17 · 작성자: Claude Code (brainstorming session with @anomie7) · 상태: draft v1.3 (Plugin 우선 정책 + 2026-07 모델 업데이트)

## 0. Executive Summary

Selvage는 2026년 2월 `tasks/02-agent-native-review-mode.md`에서 **Agent-Delegated Review**(`get_review_context`, API 키 불필요 MCP 도구)라는 정확한 피벗을 잡았고, 이를 실제로 구현했습니다. 이 방향은 시장 흐름(gstack 4개월 122k stars, Claude Code 138k, Codex 98k)과 정확히 일치합니다. **방향이 틀린 게 아니라 5개월간 실행이 멈췄을 뿐입니다.**

이 마스터 플랜은 4개 Sprint(12–16주)로 방치 부채를 청산하면서 agent-native 방향을 가속합니다. 각 Sprint는 (a) 객관적 종료 metric, (b) 전용 브랜치/워크트리, (c) `claude -p` 독립 검증자 체크리스트를 갖습니다. 사용자는 각 마일스톤 PR을 리뷰하고 배포를 승인합니다.

---

## 1. 배경과 현재 상태 진단

### 1.1 자산 (유지)
- Python CLI, Apache-2.0, PyPI v0.4.1
- 테스트 823개 통과 / 18 스킵
- 멀티 LLM (15개 모델, 4개 provider) — `models.yml`이 2026년 중반 최신
- Tree-sitter AST 기반 Smart Context (Python/JS/TS/Java/Kotlin 등)
- MCP 서버 9개 도구, 특히 `get_review_context`(API 키 불필요, host agent LLM 재활용)
- 3계층 아키텍처 설계(`tasks/02-agent-native-review-mode.md`): Context Engine / Execution / Post-processing

### 1.2 방치 징후 (청산 대상)
- 최근 5개월 코드 커밋 0건
- 외부 PR #26을 85일 방치
- GitHub Actions/CI 인프라 부재
- CLAUDE.md(v3) vs 실제 prompt(v4) 불일치
- README 내 모델 표기 구형/신형 혼재
- `docs/context-optimization-analysis.md`(2025-07) AST 고도화 설계 미이행

### 1.3 경쟁 우위 (정제 필요)
CodeRabbit($24/월), Claude Code Review($15–25/PR), Codex(`codex review`), Cursor BugBot에 대비:
1. **AST-precise context** — tree-sitter로 변경 블록만. full-codebase 대비 토큰 5–10x 절약
2. **API 키 불필호** — `get_review_context`로 호스트 LLM 재활용. 추가 비용 $0
3. **Multi-LLM** — 15개 모델 스위칭. 단일 vendor lock-in 회피

**문제**: 이 3가지가 README 첫 화면에 불친절. 사용자가 모름.

### 1.4 시장 트렌드 (방향 일치 확인)
- Autonomous fixing, spec-driven review, repo graph, multi-agent verification
- Skill engineering, loop engineering, harness engineering, observability
- GitHub 모멘텀 = 범용 agent + skills (gstack, opencode, claude-code, codex)

---

## 2. 비전: "Agent-Native Verified Review Engine"

selvage는 "또 하나의 GitHub 코멘트 봇"이 아니라 **"로컬에서 코드를 구조적으로 압축하고, 원하는 LLM이나 코딩 에이전트에 검증 가능한 review context를 공급하는 오픈 품질 레이어"**입니다.

- **Agent-Native**: host agent(Claude Code, Cursor, Codex)의 LLM을 재활용
- **Verified**: finding마다 AST path, caller chain, test 결과를 증거로
- **Engine**: 재현 가능한 ReviewRun manifest + OTel trace로 eval/디버깅 기반

---

## 3. 마스터 플랜 — 4개 Sprint

### 3.0 실행 모델 (AI 병렬 디스패치 기반)

인간 기준 "1–2주"는 orca + codex/claude 병렬 디스패치 시대에 안 맞습니다. 대신 아래 모델을 사용합니다.

- **작업 단위 (task)**: 에이전트 1회 실행으로 끝낼 수 있는 분량
- **병렬 디스패치 그룹**: 서로 독립적인 task들을 묶어 여러 에이전트가 병렬 처리
- **검증 사이클**: 그룹 종료 시 `claude -p` 독립 검증자가 체크리스트 평가
- **승인 사이클**: 사용자가 PR을 리뷰하고 머지 승인 (실제 병목)

**wall-clock = (직렬 그룹 수 × 에이전트 실행 시간) + 사용자 승인 대기**

- codex 1회 실행: 보통 1–3시간 (웹 검색 + 코드 작성 + 테스트)
- claude -p 1회 실행: 수분–30분 (체크리스트 검증)
- 사용자 승인: 가변 (몇 시간~하루)

Sprint는 인간 기간이 아니라 **디스패치 사이클 수**로 표현합니다.

### 3.0.1 Sprint 요약

| Sprint | 디스패치 모델 | 병렬 그룹 수 | 직렬 깊이 | wall-clock 추정 (사용자 대기 제외) |
|---|---|---|---|---|
| **0a. CI/CD 인프라** | codex 1대 + claude -p 검증 | 1 | 1 | 3–6시간 |
| **0b. 문서/마켓플레이스** | codex 1대 + claude -p 검증 | 1 (0a와 병렬) | 1 | 2–4시간 |
| **1. AST V2** | codex 2대 병렬 (model + extractor) + claude -p 검증 | 2 | 2 | 1–2일 |
| **2. Verified Review** | codex 2–3대 병렬 + claude -p 검증 | 3 | 3 | 2–4일 |
| **3. Distribution** | codex 2대 병렬 (ast-grep + SARIF) + claude -p 검증 | 2 | 2 | 1–2일 |

### 3.0.2 마스터 플랜 표

| Sprint | 목표 | 종료 metric | 릴리스 |
|---|---|---|---|
| **0a. CI/CD 인프라** | GitHub Actions + develop 브랜치 + TestPyPI 자동 배포 | CI green (push/PR), TestPyPI 자동 업로드, e2e Docker 통과 | — (내부 인프라) |
| **0b. 문서/마켓플레이스** | README/CLAUDE.md 동기화, Claude Plugin Marketplace 등록 | README 차별점 명시, Claude Plugin `/plugin install` 작동 | **v0.4.2** |
| **0c. Eval 인프라** | 자체 경량 eval (ReviewRun + golden fixture) | review-run/v1 스키마 확정, deterministic matcher, ≥20 golden case, CI eval-regression 동작 | **v0.4.2** (0b와 동반) 또는 **v0.5.0** |
| **1. AST V2** | cross-file caller chain + ranking | caller recall ≥50%↑, wrong-def <5%, 토큰 15%↓ (Sprint 0c metric로 측정) | **v0.5.0** |
| **2. Verified Review Engine** | reviewer → verifier 전환 | 80% finding에 evidence, FP 30%↓ (Sprint 0c metric로 측정) | **v0.6.0** |
| **3. Distribution & Polish** | CI 통합 + 한국어 rule pack | GitHub Action 작동, SARIF 표시 | **v0.7.0** |

**의존성 그래프**:
```
0a (CI/CD)   ─┬─→ 1 (AST V2) ─→ 2 (Verified Review) ─→ 3 (Distribution)
              │        ↑
0b (문서/마켓) ┘        │
                        │
0c (Eval 인프라) ───────┘  (Sprint 1의 metric 측정을 위해 선행)
```

- Sprint 0a/0b/0c는 서로 **독립적 병렬 진행 가능**
- Sprint 0c는 Sprint 1의 **metric 측정 기반**이므로 Sprint 1 착수 전 완료 권장 (Phase A–B는 최소한 끝낼 것)
- Sprint 1→2→3은 직렬 (각각 이전 산출물에 의존)
- Sprint 2의 `ReviewRun` manifest는 Sprint 0c의 `review-run/v1` 스키마와 동일 — Sprint 0c에서 먼저 정의하고 Sprint 2에서 활용

### 3.1 Sprint 0 — Reactivation (0a + 0b 병렬)

Sprint 0는 두 sub-track으로 분리합니다. 0a는 Sprint 1의 필수 선행, 0b는 0a 및 Sprint 1과 병렬 진행.

#### 3.1.1 Sprint 0a — CI/CD 인프라

**목표**: 영속적인 CI/CD 파이프라인 구축. 이후 모든 Sprint의 기반.

**작업**:
- `develop` 브랜치 생성 — main의 stable mirror, Sprint 통합 지점
- GitHub Actions 워크플로우 2종:
  - `.github/workflows/ci.yml` — pytest + ruff + build (feature 브랜치 PR 게이트)
  - `.github/workflows/release.yml` — TestPyPI(develop push) / PyPI(main push) 자동 배포
- TestPyPI 자동 배포 파이프라인 — `scripts/build_testpypi_image.sh`를 Actions에서 호출, `selvage-testpypi:latest` Docker 이미지 빌드 + `e2e/` 통합 테스트 실행
- `feature/*` 브랜치 정책 — Sprint 작업은 feature 브랜치에서, develop로 PR
- CHANGELOG 자동화 — commitizen 도입 또는 `scripts/update_changelog.py`
- `pytest tests/` 전체 통과 확인, flaky 테스트 안정화

**종료 조건**:
- [ ] `develop` 브랜치 존재, main과 동기화된 상태
- [ ] `.github/workflows/ci.yml`이 feature PR에서 동작 (pytest/ruff/build)
- [ ] `.github/workflows/release.yml`이 develop push에서 TestPyPI 업로드
- [ ] TestPyPI 업로드 후 Docker `selvage-testpypi:latest` 빌드 + `e2e/` 통과
- [ ] main merge 시 PyPI + tag + GitHub Release 자동화
- [ ] `pytest tests/` 0 failure

**배포**: 내부 인프라 (별도 릴리스 없음)

#### 3.1.2 Sprint 0b — 문서/마켓플레이스

**목표**: 외부 소통 부채 청산, "API 키 불필요 / AST-precise / multi-LLM" 3대 차별점 명확화.

**작업**:
- README.md / README_KR.md rewrite — 첫 100줄에 3대 차별점 명시, 비교 표 추가
- CLAUDE.md 동기화 — prompt v3 → v4, models.yml과 일치, README 모델 표기 통일
- **Claude Code Plugin Marketplace 등록** — `plugin/.claude-plugin/plugin.json` 검증, `/plugin install selvage` 동작 확인, 마켓플레이스 PR(필요시)
- glama.json / smithery.yaml 재검증 (이미 등록됨, 버전 동기화만)
- REVIEWING.md 추가 — 외부 기여자 PR 리뷰 프로세스 (반응 시간 SLA 등)
- Issue/PR 템플릿 — `.github/ISSUE_TEMPLATE/bug.yml`, `feature.yml`, `.github/PULL_REQUEST_TEMPLATE.md`
- CHANGELOG.md v0.4.2 항목 추가

**종료 조건**:
- [ ] README 첫 100줄에 3대 차별점 명시 (grep으로 검증 가능한 키워드)
- [ ] README_KR.md 동일 구조
- [ ] CLAUDE.md prompt 버전 v4 표시
- [ ] README 내 모델 표기가 models.yml과 일치
- [ ] Claude Code Plugin Marketplace에서 `/plugin install` 동작 (실제 설치 테스트)
- [ ] glama.ai / smithery.ai에서 현재 버전 표시
- [ ] REVIEWING.md 존재
- [ ] Issue/PR 템플릿 존재
- [ ] CHANGELOG v0.4.2 갱신

**배포**: v0.4.2 — PyPI + GitHub Release + Claude Plugin Marketplace. "다시 살아났다" 시그널.

### 3.2 Sprint 1 — AST V2 (2–3주)

**목표**: codex AST 리서치 TOP 5의 1, 2, 3번 통합으로 cross-file caller chain + ranking 구축.

**작업**:
- `Symbol`, `Reference`, `Edge`, `Provenance` Pydantic 데이터 모델 — `selvage/src/diff_parser/symbol_index/`
- tree-sitter `tags.scm` 기반 Symbol/Reference extractor (Python/JS/TS 우선)
- SQLite incremental cache (content-hash 기반 invalidate)
- import-aware resolver, 1-hop reverse caller chain
- Aider식 changed-symbol personalization + token-budget ranking
- `SMART_CONTEXT_V2` feature flag (env `SELVAGE_CONTEXT_VERSION=v2`)
- 평가 fixture 10–20개 (Python/JS/TS 각 언어별) — `tests/fixtures/symbol_index/`
- 평가 metric 측정 스크립트 — `scripts/eval_context_v2.py`

**종료 조건**:
- [ ] Symbol/Reference/Edge/Provenance 모델 정의
- [ ] tags.scm extractor가 Python/JS/TS에서 동작
- [ ] SQLite cache가 content-hash로 invalidate
- [ ] 1-hop caller chain이 fixture에서 정확 추출
- [ ] SMART_CONTEXT_V2 feature flag로 on/off
- [ ] metric: 기존 SMART_CONTEXT 대비 caller recall ≥50%↑, wrong-def <5%, 토큰 15%↓
- [ ] flag off 시 기존 동작 100% 보존 (회귀 테스트 통과)

**배포**: v0.5.0 PyPI + MCP 마켓 갱신

### 3.3 Sprint 2 — Verified Review Engine (4–6주)

**목표**: reviewer → verifier 전환. finding마다 AST path, caller chain, test 결과를 증거로.

**작업**:
- `ReviewRun` manifest — diff snapshot, base/head SHA, model/prompt/skill versions, context chunks, tool calls, budgets, findings를 불변 JSON으로 저장 — `selvage/src/review/run_manifest.py`
- Finding verification loop — 1차 reviewer가 finding 후보 → verifier가 AST V2 caller chain + 선택적 테스트 실행으로 반증/확인 → `supported`/`uncertain`/`rejected` + evidence line
- Finding provenance API — model + AST path + verifier 결과 + 근거 라인을 finding에 첨부
- OTel-native review trace — root `review.run` span 아래 `git.diff`, `ast.context`, `llm.call`, `tool.verify`, `finding.merge` span. OTLP endpoint 있을 때만 export (opt-in)
- `verify_finding` MCP 도구 추가 (옵션, 기존 `get_review_context`와 병행)
- CLI 출력 개선 — finding마다 evidence drill-down 지원 (rich tree)
- JSON 출력 스키마 확장 — `evidence` 필드 추가

**종료 조건**:
- [ ] ReviewRun manifest에 모든 실행 증거 기록
- [ ] verifier가 AST V2 caller chain을 활용해 반증/확인
- [ ] finding provenance에 AST path/evidence 포함
- [ ] OTel trace가 review.run root + spans로 구성 (opt-in)
- [ ] `verify_finding` MCP 도구 동작
- [ ] CLI에서 finding evidence drill-down 가능
- [ ] false positive 30%↓ (평가 fixture 기반)

**배포**: v0.6.0 PyPI + MCP 마켓 갱신

### 3.4 Sprint 3 — Distribution & Polish (2–3주)

**목표**: AST V2 + Verified Review를 세상에 내놓기. CI 통합, 한국어/보안 rule pack.

**작업**:
- ast-grep optional deterministic rule adapter — `selvage[security]` extra, `ast-grep scan --json` subprocess + JSON 경계, Apache-2.0 호환 rule 5–10개 (보안/SQL/shell injection)
- SARIF 출력 — `selvage review --format sarif > review.sarif`
- `.selvage.yml` 프로젝트 설정 — model, language, ignore, focus, rules
- `selvage-lab/selvage-action` GitHub Actions 워크플로우 — PR 트리거 자동 리뷰
- 한국어 rule pack 시드 — OWASP, 전자금융감독규정, 개인정보처리 (bilingual)

**종료 조건**:
- [ ] ast-grep adapter가 보안 패턴 deterministic 탐지
- [ ] SARIF가 GitHub Security 탭에 표시
- [ ] `.selvage.yml` 파싱/적용 동작
- [ ] selvage-action이 PR에서 자동 리뷰
- [ ] 한국어 rule pack 5개 이상
- [ ] v0.7.0 PyPI 업로드 성공

**배포**: v0.7.0 PyPI + GitHub Marketplace (Actions)

### 3.5 장기 (v0.8+, 마스터 플랜 이후)

- ast-grep 한국어/한국 규정 rule pack 확장
- SCIP index adapter (optional, precise resolution)
- auto-fix (`selvage review --apply`)
- 증분 리뷰 (`selvage review --since-last-review`)
- VS Code 확장

---

## 4. 마일스톤 / 릴리스 체계

| 버전 | Sprint | 핵심 가치 | 배포 채널 | 추정 wall-clock (사용자 대기 제외) |
|---|---|---|---|---|
| (내부) | 0a | CI/CD 인프라 — TestPyPI + develop 브랜치 | — | 3–6시간 |
| **v0.4.2** | 0b | "다시 살아났다" — 문서/마켓/Claude Plugin | PyPI, GitHub Release, Claude Plugin Marketplace | 2–4시간 (0a와 병렬) |
| **v0.5.0** | 1 | AST V2 — cross-file caller chain | PyPI, glama, smithery, Claude Plugin Marketplace | 1–2일 |
| **v0.6.0** | 2 | Verified Review — finding에 증거 | PyPI, MCP 마켓 | 2–4일 |
| **v0.7.0** | 3 | CI 통합 — GitHub Action + SARIF | PyPI, GitHub Marketplace (Actions) | 1–2일 |

**총 wall-clock 추정**: 5–9일 (순수 작업) + 사용자 승인 대기. 기존 "12–16주" 인간 기준 → AI 병렬 기준으로 **약 10–20%로 압축**.

각 릴리스마다:
1. CHANGELOG.md 갱신
2. `__version__.py` 버전업
3. git tag `vX.Y.Z`
4. GitHub Actions 자동 빌드 → PyPI 업로드
5. GitHub Release 노트 자동 생성
6. MCP 마켓플레이스 server.json 버전 갱신

---

## 5. 브랜치 / 워크트리 전략

### 5.1 orca 워크트리 계층

```
selvage/main (사용자 검수/배포, 브랜치: main)
└── master-plan-2026-07-17/ (작업 허브, 브랜치: anomie7/master-plan-2026-07-17)
    ├── docs/superpowers/specs/2026-07-17-selvage-master-plan.md (이 문서)
    ├── docs/superpowers/plans/ (각 Sprint 구현 계획)
    ├── docs/research/external/ (codex 리서치 결과)
    ├── sprint-0-reactivation/ (Sprint 0 실행)
    │   브랜치: release/v0.4.2
    ├── sprint-1-ast-v2/ (Sprint 1 실행)
    │   브랜치: release/v0.5.0
    ├── sprint-2-verified-review/ (Sprint 2 실행)
    │   브랜치: release/v0.6.0
    └── sprint-3-distribution/ (Sprint 3 실행)
        브랜치: release/v0.7.0
```

### 5.2 브랜치 정책 (main + develop + feature/*)

```
main      ──── 사용자가 직접 관리, 배포 브랜치 ──── tag vX.Y.Z → PyPI + GitHub Release
            │
develop   ──── Sprint 통합 지점, stable mirror of main + 진행 중 Sprint 병합
            │  push → TestPyPI 자동 배포 + Docker 통합 테스트
            │
feature/* ──── 개별 task 작업 브랜치 (예: feature/sprint-0a-ci-yaml)
               PR → develop (CI 게이트: pytest + ruff + build)
```

- `main`: 사용자만 머지. 릴리스 브랜치.
- `develop`: Sprint의 feature들이 모이는 통합 브랜치. Sprint 종료 시 main으로 PR.
- `feature/*`: 에이전트가 디스패치되는 실제 작업 브랜치. 1 task = 1 feature 원칙.
- `anomie7/master-plan-2026-07-17`: 디자인/계획 문서만 보관. 코드 변경 없음.

**Sprint 브랜치 네이밍**:
- Sprint 0a: `feature/sprint-0a-ci-cd-*` (여러 feature로 쪼갬)
- Sprint 0b: `feature/sprint-0b-docs-*`, `feature/sprint-0b-claude-plugin`
- Sprint 1: `feature/sprint-1-symbol-model`, `feature/sprint-1-tags-extractor`, ...
- 각 Sprint의 feature들이 develop로 PR → Sprint 전체 완료 시 main으로 cherry-pick 또는 squash merge

### 5.2.1 TestPyCI/CD 파이프라인 상세

```
┌─────────────────────────────────────────────────────────────────┐
│ feature/sprint-N-* 브랜치에서 PR 생성                            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────┐
        │ .github/workflows/ci.yml             │
        │  - pytest tests/                     │
        │  - ruff check .                      │
        │  - python -m build (검증 only)       │
        │  - coverage 보고                     │
        └──────────────────────────────────────┘
                            │ PR 승인 (사용자)
                            ▼
        ┌──────────────────────────────────────┐
        │ develop 브랜치로 merge               │
        │  → .github/workflows/release.yml     │
        │    1) python -m build                │
        │    2) twine upload --repository testpypi │
        │    3) scripts/build_testpypi_image.sh │
        │    4) docker run selvage-testpypi:latest pytest e2e/ │
        └──────────────────────────────────────┘
                            │ Sprint 종료 시 (사용자 승인)
                            ▼
        ┌──────────────────────────────────────┐
        │ main 브랜치로 merge (PR)             │
        │  → .github/workflows/release.yml     │
        │    1) twine upload (PyPI 정식)       │
        │    2) git tag vX.Y.Z                 │
        │    3) GitHub Release 자동 생성       │
        │    4) MCP 마켓 server.json 갱신 PR   │
        └──────────────────────────────────────┘
```

기존 자산 활용: `scripts/build_testpypi_image.sh`, `e2e/dockerfiles/testpypi/Dockerfile`, `e2e/` 테스트 스위트.

### 5.3 Sprint 실행 워크플로우

각 Sprint:
1. master-plan 워크트리에서 `writing-plans` 스킬로 구현 계획 작성 → `docs/superpowers/plans/sprint-N-<topic>.md`
2. 전용 child 워크트리 생성: `orca worktree create --name sprint-N-<topic> --parent-worktree name:master-plan-2026-07-17 --agent <codex|claude>`
3. 워크트리에서 `release/vX.Y.Z` 브랜치로 작업
4. 독립 검증자(`claude -p`) 체크리스트 실행 (§6)
5. 사용자 PR 리뷰
6. Merge to main → tag → PyPI 배포
7. Sprint 워크트리 정리

---

## 6. 독립 검증자 (claude -p) 체크리스트

각 Sprint 종료 시, **main 작업 세션과 다른 독립 컨텍스트**를 가진 Claude가 체크리스트 기반 검증을 수행.

### 6.1 실행 방식

옵션 A (orca 기반):
```bash
orca worktree create --name verify-sprint-N --parent-worktree name:sprint-N-<topic> --agent claude \
  --prompt "$(cat docs/superpowers/specs/sprint-N-verification-checklist.md)"
```

옵션 B (직접):
```bash
cd /Users/demin_coder/orca/workspaces/selvage/sprint-N-<topic>
claude -p "$(cat ../master-plan-2026-07-17/docs/superpowers/specs/sprint-N-verification-checklist.md)"
```

검증자는 체크리스트의 각 항목을 객관적으로 평가하고, FAIL 항목이 있으면 수정 권고안과 함께 보고.

### 6.2 Sprint별 체크리스트

#### Sprint 0a 체크리스트 (CI/CD 인프라)

```markdown
# Sprint 0a CI/CD 인프라 검증

아래 항목을 하나씩 객관적으로 검증하라. 각 항목에 PASS/FAIL과 증거(파일 경로, 명령어 출력 등)를 붙일 것.

## 브랜치 구조
1. develop 브랜치가 존재하고 main과 동기화돼 있는가? (git branch -a 출력)
2. feature/* 브랜치 정책이 문서화됐는가? (CONTRIBUTING.md 또는 REVIEWING.md)

## CI 워크플로우
3. .github/workflows/ci.yml이 존재하는가?
4. ci.yml이 feature 브랜치 PR에서 pytest를 실행하는가? (workflow run 증거)
5. ci.yml이 ruff check를 실행하는가?
6. ci.yml이 python -m build를 실행하는가?
7. coverage 보고가 있는가?

## Release 워크플로우
8. .github/workflows/release.yml이 존재하는가?
9. develop 브랜치 push 시 TestPyPI로 자동 업로드되는가? (Actions 로그 증거)
10. scripts/build_testpypi_image.sh가 Actions에서 호출되는가?
11. selvage-testpypi:latest Docker 이미지가 빌드되는가?
12. e2e/ 통합 테스트가 Docker 안에서 실행되는가?
13. main 브랜치 merge 시 PyPI 정식 업로드 + tag + GitHub Release가 자동화됐는가?

## 품질 게이트
14. pytest tests/ 가 0 failure로 통과하는가? (stdout 마지막 20줄)

최종 판정: 14/14 PASS면 Sprint 0a 종료 승인. FAIL 항목은 수정 권고안 작성.
```

#### Sprint 0b 체크리스트 (문서/마켓플레이스)

```markdown
# Sprint 0b 문서/마켓플레이스 검증

## README/CLAUDE.md 동기화
1. README.md 첫 100줄에 "API 키 불필요" 키워드가 명시됐는가? (head -100 README.md | grep)
2. README.md 첫 100줄에 "AST" 또는 "tree-sitter"가 명시됐는가?
3. README.md 첫 100줄에 "multi-LLM" 또는 "OpenRouter"가 명시됐는가?
4. README_KR.md도 동일한 차별점 구조인가?
5. CLAUDE.md의 prompt 버전이 v4로 표시되는가? (grep 결과)
6. README 내 모델 표기가 models.yml과 일치하는가?

## Claude Code Plugin Marketplace
7. plugin/.claude-plugin/plugin.json이 Claude plugin marketplace 스키마를 만족하는가?
8. plugin/agents/selvage-reviewer.md와 plugin/skills/review/SKILL.md가 유효한가?
9. Claude Code에서 `/plugin install selvage`가 동작하는가? (실제 설치 로그)
10. 마켓플레이스 등록 PR이 제출됐거나 승인됐는가? (URL)

## 기존 마켓 갱신
11. glama.json이 valid하고 현재 버전을 반영하는가?
12. smithery.yaml이 valid하고 현재 버전을 반영하는가?

## 프로세스 문서
13. REVIEWING.md가 존재하고 외부 기여자 PR 리뷰 프로세스(반응 시간 SLA 등)를 설명하는가?
14. .github/ISSUE_TEMPLATE/bug.yml, feature.yml이 존재하는가?
15. .github/PULL_REQUEST_TEMPLATE.md가 존재하는가?
16. CHANGELOG.md가 v0.4.2 항목으로 갱신됐는가?

최종 판정: 16/16 PASS면 Sprint 0b 종료 승인. v0.4.2 릴리스 가능.
```

#### Sprint 1 체크리스트 (요약)

- AST V2 데이터 모델 정의 (Symbol/Reference/Edge/Provenance)
- Python/JS/TS tags.scm extractor 동작
- SQLite cache content-hash invalidate
- 1-hop caller chain 추출 정확도 (fixture 기반)
- SMART_CONTEXT_V2 feature flag on/off
- metric 달성: caller recall ≥50%↑, wrong-def <5%, 토큰 15%↓
- flag off 시 기존 동작 보존 (회귀 테스트 통과)
- AST V2 평가 보고서 docs/research/internal/sprint-1-ast-v2-eval.md 작성

#### Sprint 2 체크리스트 (요약)

- ReviewRun manifest 스키마 정의 + 실행 증거 전부 기록
- verifier가 AST V2 caller chain 활용
- finding provenance에 AST path/evidence 포함
- OTel trace (review.run root + spans) opt-in 동작
- `verify_finding` MCP 도구 동작
- CLI evidence drill-down 동작
- false positive 30%↓ (평가 fixture)

#### Sprint 3 체크리스트 (요약)

- ast-grep adapter 보안 패턴 deterministic 탐지
- SARIF 출력 valid + GitHub Security 탭 표시
- `.selvage.yml` 파싱/적용 동작
- selvage-action PR 자동 리뷰 동작
- 한국어 rule pack 5개 이상
- v0.7.0 PyPI 업로드 성공

### 6.3 검증자 산출물 형식

```markdown
# Sprint N 검증 보고 (YYYY-MM-DD)

검증자: claude -p (독립 컨텍스트)
검증 대상: release/vX.Y.Z-<topic> 브랜치 HEAD <sha>

## 결과 요약
- PASS: X/Y
- FAIL: Z (항목 번호)

## 항목별 평가
1. [PASS] ... 증거: ...
2. [FAIL] ... 이유: ... 수정 권고: ...

## 종합 판정
- [ ] Sprint 종료 승인 (모든 항목 PASS)
- [ ] 수정 후 재검증 필요 (FAIL 항목 존재)

## 권고사항
...
```

---

## 7. 배포 파이프라인

각 v0.X.Y 릴리스:

1. Sprint 워크트리에서 코드 완성 + 테스트 통과
2. 독립 검증자 체크리스트 PASS
3. PR to main (Sprint 브랜치 → main)
4. 사용자 리뷰 + 승인
5. Merge to main (squash or merge commit)
6. `git tag vX.Y.Z` + `git push --tags`
7. GitHub Actions 자동 빌드 (`python -m build`)
8. PyPI 업로드 (twine, `SELVAGE_PYPI_TOKEN` secret)
9. GitHub Release 노트 자동 생성 (CHANGELOG 기반)
10. MCP 마켓플레이스 server.json 버전 갱신 (별도 PR 또는 자동)

---

## 8. 리스크와 완화

| 리스크 | 확률 | 영향 | 완화 |
|---|---|---|---|
| 1인 메인테이너 번아웃 | 높음 | 높음 | Sprint 4–6주 제한, 명확한 종료 metric, 부채 청산 우선 |
| AST V2 언어별 파편화 | 중간 | 중간 | Python/JS/TS 우선, Java/Kotlin은 Sprint 4+(v0.8+)로 |
| OTel 의존성 무거움 | 낮음 | 중간 | opt-in, OTLP endpoint 있을 때만 export |
| ast-grep Rust 바인딩 복잡도 | 중간 | 중간 | subprocess + JSON 경계로 격리, `ast-grep-cli` pip wheel 사용 |
| 독립 검증자 품질 편차 | 중간 | 중간 | 체크리스트 고정, deterministic exit, 증거 요구 |
| 시장 변화 (Claude/Codex 리뷰 고도화) | 높음 | 높음 | Agent-Delegated Review로 호스트 agent에 종속 (역이용) |
| MCP 프로토콜 변경 | 낮음 | 높음 | FastMCP 업데이트 추적, 스키마 버전 고정 |

---

## 9. 성공 지표

### 3개월 후 (Sprint 1 완료 시)
- PyPI 월간 다운로드: baseline 대비 2x (목표 ~500)
- GitHub stars: +50
- MCP 마켓플레이스(glama + smithery) 설치: 100+

### 6개월 후 (Sprint 3 완료 시)
- PyPI 월간 다운로드: 5x (목표 2,500+)
- GitHub stars: 500+ (현재 baseline에서 +400)
- selvage-action GitHub Marketplace 설치: 50+
- 한국 개발자 커뮤니티(블로그/X/Slack) 언급: 10+

### 12개월 후 (장기 비전)
- 한국 코드 리뷰 도구 1위 OSS
- "AST-precise context + Agent-Delegated Review"가 selvage의 정체성으로 정착
- v1.0.0 (Spec-driven review, auto-fix 포함)

---

## 10. 의사결정 기록 (ADR-style)

- **ADR-001**: Sprint 간은 직렬이 원칙이되, 독립적인 sub-track은 병렬 디스패치한다. 특히 Sprint 0b(문서/마켓)는 Sprint 0a(CI/CD) 및 Sprint 1과 병렬 진행. 단, 코드 의존성이 있는 Sprint(1→2→3)은 직렬.
- **ADR-002**: AST V2는 feature flag로 도입 (`SELVAGE_CONTEXT_VERSION=v2`). 이유: 기존 사용자 회귀 방지, A/B 평가 가능.
- **ADR-003**: 독립 검증자는 `claude -p` 또는 orca 워크트리 claude로 실행. 이유: main 세션과 컨텍스트 격리로 객관성 확보.
- **ADR-004**: ast-grep은 Rust 바인딩 직접 구현 대신 subprocess + JSON. 이유: Python CLI 단순성 유지, Rust 격리.
- **ADR-005**: OTel은 opt-in. 이유: zero-data-retention 조직 사용자 보호, 기본 의존성 최소.
- **ADR-006**: `.selvage.yml`은 Sprint 3에서 도입 (Sprint 0이 아님). 이유: AST V2/Verified Review와 결합해야 가치 있음.
- **ADR-007 (eval 위치/라이센스)**: eval 인프라 로직(`selvage/src/eval/`)은 selvage 리포 안에 구축. fixture는 두 종류 — (a) **synthetic**: selvage 팀이 직접 작성한 inline 패치 (Apache 2.0 저작물), (b) **external**: 외부 OSS repo의 diff를 runtime에 clone하여 추출, **코드 자체는 저장하지 않음** (메타데이터 `repo_url + commit_sha + diff_range + license_attribution`만 보관). 이유: 공개 repo에 타 OSS 코드를 포함하는 것은 라이센스/저작권 리스크 (GPL 전염, attribution 부담). 코드를 복제하지 않으면 리스크 0. external fixture는 permissive 라이센스(MIT/Apache/BSD/ISC/MPL)만 허용, GPL/상용 금지.
- **ADR-008 (CLI vs Plugin 정책 — Plugin 우선, CLI 현행 유지)**: 새 기능(AST V2, Verified Review, rule pack 등)은 **Plugin/MCP에 먼저** 구현하고 CLI는 그 다음. 단, **CLI는 경량화하지 않고 현행 구조 유지** (사용자 결정, 2026-07-19). 이유: (a) 시장 트렌트가 agent+plugin로 이동 중 (codex market-landscape: gstack 122k, opencode 186k, claude-code 138k)이므로 Plugin 우선이 합리적. (b) 단, CI/자동화(Sprint 3 GitHub Action, SARIF)는 agent 없이 돌아가야 하므로 CLI가 여전히 필요 — 경량화하면 CI 통합이 복잡해짐. (c) 1인 메인테이너 부담을 고려할 때, CLI 구조 변경(모듈 분리 등)은 가치 대비 비용이 큼. 그래서 CLI는 현행 유지하되 새 기능의 70%는 Plugin/MCP 우선으로.

---

## 11. 참고 자료

### 리서치 결과 (codex)
- `docs/research/external/2026-07-17-market-landscape.md` — 시장/경쟁사 분석
- `docs/research/external/2026-07-17-engineering-concepts.md` — Skill/Loop/Harness/Eval/Spec
- `docs/research/external/2026-07-17-ast-context-research.md` — AST 고도화 OSS 리서치 (TOP 5 우선순위)

### 기존 설계 (selvage 내부)
- `docs/product_analysis_and_roadmap.md` — 2026-01 원본 로드맵
- `tasks/02-agent-native-review-mode.md` — Agent-Delegated Review 설계
- `docs/agent-delegated-review-spec.md` — 위 스펙 상세 (45KB)
- `docs/context-optimization-analysis.md` — 2025-07 AST 고도화 원본 설계

### 외부 링크
- [Anthropic Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Aider repo map](https://aider.chat/2023/10/22/repomap.html)
- [ast-grep](https://ast-grep.github.io/)
- [SCIP](https://github.com/sourcegraph/scip)
- [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/)

---

## 12. 다음 단계

1. 사용자가 이 마스터 플랜을 리뷰하고 승인
2. `writing-plans` 스킬로 Sprint 0 세부 구현 계획 작성 → `docs/superpowers/plans/sprint-0-reactivation.md`
3. Sprint 0 전용 워크트리 생성 (`orca worktree create --name sprint-0-reactivation --parent-worktree name:master-plan-2026-07-17`)
4. Sprint 0 실행 → 검증 → PR → v0.4.2 배포
5. Sprint 1–3 반복

---

*문서 버전: 1.0 · 최종 갱신: 2026-07-17 · 작성자: Claude Code (brainstorming session)*
