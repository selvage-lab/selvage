# Selvage AST 기반 Smart Context 고도화 딥리서치

> 조사일: 2026-07-17 · 대상: Python CLI, Apache-2.0, 1인 메인테이너 관점

## 1. 결론 요약

Selvage가 다음에 만들어야 할 것은 “더 큰 AST 블록”이 아니라 **변경 심볼을 기점으로 한 작은 repository context graph**다. 현재 `ContextExtractor`는 변경 라인을 포함하는 같은 파일의 최소 함수·클래스와 모든 import를 반환한다. 실제 AST 지원은 Python, JavaScript, TypeScript, Java, Kotlin이며 Go/Rust 등은 `FALLBACK_CONTEXT`의 정규식 import와 변경부 ±5줄에 머문다. 따라서 동일 이름의 다른 정의를 구별하지 못하고, 다른 파일의 caller/definition/contract를 찾지 못하며, 보안·정책 위반도 LLM이 매번 재판단한다.

가장 현실적인 진화 순서는 다음과 같다.

1. 기존 Python tree-sitter 위에 공식 `tags.scm` 계열 query를 얹어 symbol definition/reference/call을 정규화한다.
2. 파일별 결과를 SQLite에 캐시하고 import/call edge를 구성한다.
3. diff의 변경 심볼에서 caller/callee를 1~2 hop 탐색해 토큰 예산으로 자른다.
4. Aider식 중요도 랭킹으로 “무엇을 넣을지” 결정한다.
5. ast-grep 규칙은 결정적 pre-review로 실행해 확정 finding은 LLM 추론에서 제외하거나 증거로 전달한다.

SCIP·CodeQL은 정확도의 상한을 보여주는 **선택적 외부 index adapter**, stack-graphs와 Greptile은 설계 참고가 적절하다. 벡터 RAG는 자연어 의도·유사 구현 검색에는 좋지만 caller chain의 진실 공급원으로 쓰면 안 된다.

## 2. 현재 SMART_CONTEXT의 한계

| 한계 | 실패 시나리오 | 필요한 보완 |
|---|---|---|
| 파일 내부·라인 중심 | `service.py:update_user()` 반환형 변경을 `api.py`와 테스트의 caller가 계속 옛 계약으로 사용 | symbol index + cross-file reverse call edge |
| 문법 블록만 인지 | 서로 다른 모듈에 `parse()`가 여럿이면 단순 이름 참조가 어느 정의인지 불명확 | import alias, scope, qualified name을 고려한 name resolution |
| 모든 import를 무조건 첨부 | 큰 파일에서 실제 변경과 무관한 import가 토큰을 소비 | 변경 심볼이 참조하는 dependency만 선택 |
| 언어별 node type 하드코딩 | grammar 업데이트·새 언어마다 Python 코드를 수정 | 버전 고정된 query pack(`tags.scm`)과 fixture test |
| 규칙 탐지 없음 | `subprocess.run(..., shell=True)`, 문자열 SQL, 검증 누락을 LLM이 비결정적으로 판단 | ast-grep/Semgrep의 deterministic rule gate |
| freshness/ranking 없음 | 매 리뷰 전체 repo를 훑거나, 발견한 관련 심볼을 모두 넣어 prompt 팽창 | mtime/content-hash incremental cache + graph rank/token budget |

## 3. OSS·프레임워크 비교

통합 복잡도는 Selvage에 실제 기능을 넣는 비용(낮음/중간/높음/매우 높음)이다.

| 접근법 | 정의와 작동 방식 | Selvage 적용·가져올 가치 | 라이선스·의존성 | 복잡도 |
|---|---|---|---|---|
| **Aider repo map** | tree-sitter query로 파일별 definition/reference tag를 만들고, reference→definition 파일 graph에 가중 PageRank를 수행한다. 채팅 파일·언급 식별자에 personalization을 주고, 상위 정의의 signature/핵심 line을 토큰 예산 안에서 렌더링·캐시한다. [공식 설명](https://aider.chat/2023/10/22/repomap.html), [구현](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py) | `changed symbol`을 personalization seed로 삼아 repo outline과 관련 심볼을 압축한다. 단, 같은 이름을 연결하는 heuristic이므로 정확한 caller graph가 아니라 **ranking layer**로 사용한다. | Apache-2.0. Python, tree-sitter/`grep-ast`, NetworkX, disk cache 계열. 코드를 통째로 가져오기보다 알고리즘 재구현 권장. | **중간** |
| **SCIP** | LSIF 후속인 언어 중립 Protobuf index. 문서별 occurrence(range, symbol, role)와 symbol information을 저장하여 go-to-definition, references, implementations를 compiler-accurate하게 제공한다. [schema/도구](https://github.com/sourcegraph/scip), [index 구조](https://sourcegraph.com/docs/code-navigation/writing-an-indexer) | `index.scip` consumer를 선택 기능으로 두면 TS/JS, Java/Kotlin, Python, Go, Rust 등의 정확한 definition/reference를 공통 모델로 흡수할 수 있다. caller는 reference occurrence를 AST의 call site·enclosing symbol과 결합해 역조회한다. 빌드·의존성 해석이 필요한 언어별 indexer 설치/실행은 사용자 책임으로 둔다. | Protocol/주요 indexer Apache-2.0, Protobuf와 외부 언어별 indexer 필요. Python 공식 rich binding은 없으므로 generated protobuf 또는 `scip` JSON/snapshot adapter 필요. | **높음** |
| **tree-sitter-stack-graphs** | 언어별 name-binding 규칙을 DSL로 기술하고 reference/definition, scope push/pop graph의 유효 경로를 찾는다. 파일별 partial path를 미리 만들고 query 때 stitch해 shadowing·import를 증분 해석한다. [원리](https://github.blog/open-source/introducing-stack-graphs/), [저장소](https://github.com/github/stack-graphs) | build 없이 Python import/alias/shadowing을 푸는 아이디어는 훌륭하다. 그러나 call graph가 아니라 name resolution 기반이며 각 언어 규칙을 유지해야 한다. **Python 한정 실험 외에는 패스**하고, “파일별 fact + query-time stitch” 설계만 차용한다. | MIT OR Apache-2.0. Rust crate/CLI, tree-sitter, SQLite 기능. 저장소가 GitHub의 지원·업데이트 종료 상태임을 명시한다. | **매우 높음** |
| **ast-grep** | tree-sitter AST에 실제 코드처럼 쓴 pattern과 `$META` wildcard를 구조적으로 매칭한다. YAML rule, relational/composite 조건, test, JSON 결과를 지원한다. [프로젝트](https://github.com/ast-grep/ast-grep), [JSON/단일 rule 실행](https://ast-grep.github.io/guide/tooling-overview.html) | 보안·정책 pattern을 diff 파일/변경 range에 결정적으로 적용한다. 예: shell 실행, raw SQL, 위험 API를 JSON finding으로 받아 `RULE_CONTEXT`로 직접 보고하고 LLM에는 “확정 사실+주변 함수”만 준다. LLM 토큰·재현성·false narrative를 줄인다. name resolution/caller chain 도구는 아니다. | MIT. Rust 구현이지만 `ast-grep-cli` pip wheel/standalone CLI가 있어 Python에서는 `subprocess`+JSON로 격리 가능; source build 불필요. | **낮음~중간** |
| **Semgrep CE** | 코드 유사 YAML pattern, metavariable, constant propagation, intraprocedural dataflow/taint로 다언어 정적 분석을 수행한다. 동일 입력에 deterministic·offline인 것이 원칙이다. [CE 원칙](https://semgrep.dev/docs/contributing/semgrep-philosophy), [규칙 예시](https://semgrep.dev/docs/writing-rules/rule-ideas) | 검증된 보안 규칙과 taint가 ast-grep보다 강하다. 선택적 `selvage review --semgrep`에서 SARIF/JSON finding을 context에 합치는 방식이 현실적이다. 다만 CE는 파일 경계를 넘지 않으므로 caller chain 해법은 아니며, 기본 설치 크기·실행시간도 더 크다. | Engine LGPL-2.1. Python 배포물+OCaml/native engine. Community rule은 별도 **Semgrep Rules License**로 재배포/서비스 제한이 있으므로 registry를 제품에 vendor하지 말고 사용자 rule 또는 허용된 config만 받는다. | **중간** |
| **Greptile repo graph** | 공개 문서상 repo 전체를 스캔해 directory/file/function/class/variable 노드와 call/import/dependency/usage edge를 저장하고, diff마다 caller·dependency·유사 pattern을 실시간 조회한다. [공식 graph 문서](https://www.greptile.com/docs/how-greptile-works/graph-based-codebase-context) | 목표 아키텍처의 좋은 제품 사례다. 변경 함수→caller/contract→유사 구현을 함께 제시해 ripple effect를 본다. 그러나 parsing, resolver, graph DB, embedding/ranking의 구체 구현은 공개되지 않았다. 공개 설명을 넘어 AST나 저장소 기술을 단정하지 말고 **추론 가능한 정보 모델만** 차용한다. | 상용 proprietary 서비스/API; OSS 라이선스나 내장 가능한 의존성 없음. | **직접 통합 제외** |
| **CodeQL** | extractor가 소스를 언어별 relational database로 만들고 QL query가 AST, type, control/data flow, call 관계를 질의해 SARIF를 낸다. [CLI 개요](https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-cli) | cross-file security/dataflow와 call graph의 정확도 상한. 이미 CodeQL SARIF가 존재하면 import하는 adapter는 가치가 있지만, 매 로컬 review마다 DB를 생성하는 것은 느리고 무겁다. | query/library 저장소는 MIT지만 engine/CLI는 별도 CodeQL Terms. 비공개 코드의 일반 분석은 GitHub Code Security 상용 라이선스가 필요하다. [라이선스 구분](https://github.com/github/codeql) | **매우 높음/기본 제외** |
| **tree-sitter `tags.scm`** | grammar 저장소의 `queries/tags.scm`가 `@definition.function`, `@definition.class`, `@reference.call` 등 표준 capture로 named entity를 뽑는다. Python binding의 `QueryCursor`로 직접 실행할 수 있다. [공식 tag 규약](https://tree-sitter.github.io/tree-sitter/4-code-navigation.html), [Python query API](https://github.com/tree-sitter/py-tree-sitter) | 현재 node-type 표를 `Symbol{name, kind, role, range, container}`로 일반화하는 최단 경로. 정의·호출 후보와 repo outline을 한 번에 얻고 Aider ranking의 입력이 된다. 단독으로는 동일 이름 reference를 정확한 정의에 resolve하지 못한다. | Tree-sitter/runtime MIT; 각 grammar/query 라이선스 확인·NOTICE 반영 필요(주요 공식 grammar는 MIT). 이미 있는 Python/tree-sitter stack을 재사용. | **낮음** |

### 3.1 Pure AST, graph, RAG의 트레이드오프

| 방식 | 강점 | 약점 | Selvage 역할 |
|---|---|---|---|
| Pure AST/query | 빠름, offline, 재현 가능, line precision, 추가 모델 비용 없음 | 파일 간 binding·동적 dispatch·자연어 의미가 약함 | 변경 심볼, outline, deterministic rule의 **사실 계층** |
| Symbol/repo graph | caller chain, blast radius, multi-hop 구조 질의, edge provenance | 언어별 resolver와 freshness 관리; heuristic edge의 오탐 | context 후보 확장과 ranking의 **관계 계층** |
| Vector RAG | “비슷한 validation 구현”, 문서·주석·도메인 용어 등 lexical mismatch 검색 | embedding 비용/모델 의존, chunking·staleness, 근사 검색, caller 증명 불가 | graph 결과가 부족할 때 opt-in **유사도 계층** |
| Hybrid | AST 경계로 chunk하고 graph neighbor를 우선한 뒤 BM25/vector로 보충 | 평가·튜닝·운영 면적 증가 | 장기 목표; 초기 MVP에는 vector DB 불필요 |

[Pinecone](https://docs.pinecone.io/guides/get-started/overview) 같은 관리형 서비스는 별도 계정·네트워크·코드 유출 정책을 요구한다. 로컬 실험이라면 Apache-2.0이며 Python API, local path, vector/FTS/hybrid search를 제공하는 [LanceDB](https://github.com/lancedb/lancedb)가 맞지만, embedding provider까지 Selvage의 기본 의존성으로 넣지는 않는다. AST 경계 chunking이 고정 line chunk보다 낫다는 최근 cAST 연구도 이 방향을 지지한다([EMNLP 2025 논문](https://aclanthology.org/anthology-files/anthology-files/pdf/findings/2025.findings-emnlp.430.pdf)).

## 4. 핵심 기능을 가져오는 구체 설계

### Cross-file caller chain 추적

`tags.scm`로 각 파일의 definition과 `reference.call`을 뽑고 call node를 가장 가까운 enclosing definition에 귀속한다. import 문을 `module/alias/imported-name`으로 정규화해 우선 resolve하고, 같은 모듈·qualified name·scope를 점수화해 `CALLS(caller, callee, confidence, evidence_range)`를 SQLite에 저장한다. 변경 파일만 content hash로 재색인하고 reverse adjacency로 caller를 찾는다.

리뷰 시에는 `changed line → enclosing symbol → direct callers → callers의 caller(최대 2 hop)`로 확장하되, public API·test·변경 심볼을 직접 import한 edge를 우선하고 hop별 cap과 토큰 budget을 둔다. 동적 dispatch, reflection, monkey patching은 `heuristic`으로 표시하고 “가능한 caller”로 LLM에 전달한다. SCIP index가 있으면 동일 edge를 `precise` provenance로 덮어쓴다. 예를 들어 `normalize_email()`이 `str`에서 `Optional[str]`로 바뀌면 API handler, batch job, test caller의 null handling 부분만 함께 제공한다.

### Deterministic rule matching

기본은 별도 optional extra 또는 자동 탐지된 `sg` binary다. `ast-grep scan --json`을 **변경 파일에만** 실행하고 finding range가 diff와 겹치거나 변경 심볼 내부일 때 채택한다. rule id, severity, matched text, line, message를 구조화하고, 확정 rule은 LLM에게 재탐지시키지 말고 “영향·수정 적합성만 검토”시킨다. 예를 들어 Python의 `subprocess.$F(..., shell=True)` 또는 JS의 string-built SQL rule이 맞으면 주변 함수와 1-hop caller만 첨부한다. rule fixture를 저장해 같은 commit에서 결과가 항상 같음을 CI로 보장한다. Semgrep은 taint가 꼭 필요한 opt-in profile로 뒤에 붙인다.

### Symbol-level name resolution

MVP는 stack-graphs를 이식하지 않는다. `(language, module_path, container, kind, name/signature)`의 stable symbol key를 만들고 다음 순서로 resolve한다: ① 같은 lexical scope, ② explicit import/alias, ③ 같은 module, ④ wildcard/package export, ⑤ repo-wide name 후보. 1~3만 `resolved`, 이후는 `candidate`로 표시한다. Python/TS의 import alias fixture부터 시작하고 Java/Kotlin은 package+type 정보를 추가한다. 장기적으로 사용자가 생성한 SCIP occurrence를 읽으면 compiler-derived symbol ID로 교체할 수 있다. 이 “정확도 provenance”가 단순 이름 일치보다 중요한 안전장치다.

## 5. Selvage AST 고도화 우선순위 추천 TOP 5

점수는 Impact/ Effort 각각 5점 척도이며 Effort가 높을수록 어렵다.

| 순위 | 과제 | Impact | Effort | 위치 | 판단 |
|---:|---|---:|---:|---|---|
| **1** | `tags.scm` 기반 공통 Symbol/Reference extractor | 5 | 2 | Quick win | 기존 parser·Python binding 재사용. 모든 후속 graph/rank의 토대 |
| **2** | SQLite incremental symbol/import/call graph + 1~2 hop caller context | 5 | 3 | Strategic | SMART_CONTEXT의 가장 큰 맹점인 cross-file blast radius 해결 |
| **3** | Aider식 changed-symbol personalization + token-budget ranking | 4 | 2 | Quick win | graph가 만든 과잉 후보를 prompt 가치로 전환; NetworkX 없이 작은 PageRank도 가능 |
| **4** | ast-grep optional deterministic rule adapter | 4 | 2 | Quick win | 보안/정책 finding의 재현성 확보와 LLM 비용 절감; CLI JSON 경계로 Rust 격리 |
| **5** | SCIP optional index consumer/provenance override | 5 | 4 | Bet | 설치된 indexer가 있는 사용자에게 precise resolution 제공; 기본 경로는 아님 |

stack-graphs 직접 도입, CodeQL DB 생성, vector DB 기본 탑재는 high-effort/운영부담 대비 현재 단계의 핵심 문제와 맞지 않아 TOP 5에서 제외한다. Semgrep은 ast-grep MVP가 안정된 뒤 `security` extra로 제공한다.

## 6. 1인 메인테이너용 단계적 범위

| 단계 | 현실적 산출물 | 명시적 비범위 |
|---|---|---|
| 1 (1~2주) | `Symbol`, `Reference`, `Edge`, `Provenance` 모델; Python/JS/TS tags query; SQLite content-hash cache; golden fixture | 완전한 type inference, graph DB 서버 |
| 2 (2~3주) | import-aware resolver, reverse caller 1 hop, token budget/rank, `SMART_CONTEXT_V2` feature flag와 품질 metric | reflection/dynamic dispatch 정확 해석 |
| 3 (1~2주) | `ast-grep-cli` 자동 탐지/optional extra, JSON adapter, 5~10개 자체 Apache-2.0-compatible rule 및 tests | Semgrep registry 재배포 |
| 4 (후속) | caller 2 hop, Java/Kotlin package resolution, SCIP 파일 adapter, opt-in local hybrid retrieval 실험 | Rust binding 직접 유지, CodeQL 엔진 내장 |

출력에는 각 block마다 `reason`(`changed`, `caller`, `callee`, `rule`, `ranked-symbol`), `confidence`, `source_range`, `estimated_tokens`를 붙인다. 평가는 언어별 10~20개 fixture에서 **caller recall@K, wrong-definition rate, context tokens, extraction latency, fallback rate**를 측정하고 기존 SMART_CONTEXT와 A/B 비교한다. 이 정도면 Python CLI의 배포 단순성을 지키면서도 Greptile식 repository awareness의 핵심을 작고 검증 가능한 형태로 가져올 수 있다.

## 참고 원칙

- SCIP의 precise navigation은 compiler 정보를 사용하고 search/tree-sitter 기반 탐색은 heuristic이라는 구분을 유지한다([Sourcegraph code navigation](https://sourcegraph.com/docs/code-navigation)).
- Greptile 세부 아키텍처는 비공개다. 이 문서의 graph storage/retrieval 평가는 공식 문서에 명시된 entity와 관계만 바탕으로 한 설계 추론이다.
- 라이선스는 2026-07-17 공개 저장소 기준이며, 실제 배포 전 의존 버전의 SPDX와 NOTICE를 다시 확인한다.
