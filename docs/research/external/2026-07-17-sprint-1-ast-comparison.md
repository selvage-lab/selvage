# Selvage Sprint 1 AST V2 고도화를 위한 OSS 도구 심층 비교

> 조사일: 2026-07-17 · 관점: 1인 메인테이너, Python CLI, tree-sitter 기반 smart context
> 성격: 비교 지도(comparison atlas) — 선행 리서치 [`2026-07-17-ast-context-research.md`](./2026-07-17-ast-context-research.md)(처방형)와 직교하는 **횡단 비교** 관점

## 1. Executive Summary

현재 `ContextExtractor`는 단일 파일의 라인 범위를 AST 노드로 매핑하는 1차원 파이프라인이다. tree-sitter를 파서로만 쓰고 Query/tags.scm API는 쓰지 않으며, 노드 타입을 딕셔너리에 하드코딩한다. cross-file caller·name resolution·심볼 그래프·AST 캐시·토큰 랭킹이 모두 부재하다.

15종 OSS 비교 결론: heavyweight 런타임(CodeQL/Joern/Semgrep/scip-python/stack-graphs)의 직접 도입은 전면 배제한다. 대신 1인 메인테이너에게 최적인 세 축은 — Aider의 Personalized PageRank 랭킹(repomap.py로 검증된 엣지 가중치와 SQLite diskcache), SCIP 데이터 모델의 스키마만 차용(enclosing_range·SymbolRole bitset), tree-sitter 공식 tags.scm으로 하드코딩 대체 — 이다. code-review-graph(tirth8205)가 selvage와 동일 스택의 가장 가까운 벤치마크로 새롭게 식별되었다. 임베딩/벡터는 학술·산업 양쪽에서 AST 기반에 밀리므로 현 시점 도입하지 않는다. "Selena"라는 범용 AST OSS는 미확인이다.

## 2. 현재 SMART_CONTEXT 구현 분석 (코드 직접 인용)

> 참고: 요청 경로 `selvage/src/utils/prompts/context_extractor.py`, `resources/language_configs/`는 **존재하지 않는다**. 실제 위치는 `selvage/src/context_extractor/`이며 언어 설정은 별도 디렉토리가 아닌 클래스 변수에 하드코딩된다.

### 2.1 구현 구조와 알고리즘

`ContextExtractor.extract_contexts(file_content: str, changed_ranges)`(`context_extractor.py:215`)는 단일 파일 문자열만 받는다. 8단계 파이프라인: AST 파싱 → 각 변경 라인을 DFS로 가장 작게 감싸는 노드 탐색 → 부모 방향으로 `block_types` 매칭 → import 노드 별도 수집 → 포함 관계 중복 제거 → 텍스트 직렬화.

```python
# context_extractor.py:352-369 — DFS 라인-노드 탐색 (tree-sitter Query 미사용, 수동 순회)
def _find_node_by_line(self, root: Node, line_no: int) -> Node:
    for child in root.children:
        if child.start_point[0] + 1 <= line_no <= child.end_point[0] + 1:
            return self._find_node_by_line(child, line_no)
    return root
```

### 2.2 강점 (코드 기반 사실)

- 파일당 1회 파싱, `MeaninglessChangeFilter`가 1줄 주석/공백 변경을 사전 제거
- `_filter_nested_blocks()`로 부모-자식 포함 시 외부 블록만 유지(토큰 절약)
- Python 데코레이터 보존, JS/TS `require()` 동적 감지, 코틀린 import 주석 제거 등 디테일
- 폴백 정규식이 C/C++/Go/Rust/Swift/Dart/PHP/Ruby/Perl import 패턴 커버

### 2.3 약점과 정확한 한계 (코드 증거)

| 한계 | 상태 | 코드 증거 |
|---|---|---|
| **tree-sitter Query / tags.scm 미사용** | 수동 DFS·상향 탐색만 | `Query`/`captures` grep 결과 0건, `context_extractor.py:352-397` |
| **노드 타입 하드코딩** | 언어별 딕셔너리 3종 | `LANGUAGE_BLOCK_TYPES`(`:33-111`), `LANGUAGE_DEPENDENCY_TYPES`(`:114-157`) |
| **AST 지원 언어** | 5개만 | `SUPPORTED_LANGUAGES = ["python","javascript","typescript","java","kotlin"]`(`:30`) |
| **감지-지원 갭** | 17개 감지 중 12개 강제 폴백 | `language_detector.py:3-29` (go/ruby/php/csharp/cpp/c 미지원) |
| **cross-file caller** | 구조적 불가(단일 `file_content` 입력) | `context_extractor.py:215-216` |
| **name resolution / import 해석** | 없음 | `resolve`/`scope`/`symbol_table` grep 0건 |
| **AST 파싱 캐시** | 없음(매번 재파싱) | 기존 `cache/`는 LLM 결과 캐시 전용 |
| **incremental parsing** | 미사용(`old_tree` 인자 없음) | `self._parser.parse(code_bytes)`(`:250`) |
| **토큰 예산/랭킹** | 없음(줄 수 휴리스틱만) | `smart_context_utils.py:14-26` |
| **심볼 그래프 모델** | 존재 안 함 | `Symbol`/`Reference`/`Edge` 클래스 0건 |

`use_smart_context()`는 단순 휴리스틱이다:

```python
# smart_context_utils.py:14-26 — 랭킹 없이 줄 수만으로 smart/full 결정
if total_changes <= 5: return True
if total_lines < 30: return False
change_ratio = total_changes / total_lines
return change_ratio <= 0.2
```

## 3. OSS 도구 비교표

| 도구 | 핵심 접근법 | 언어 지원 | 라이선스 | 활성도(2026-07) | selvage 적용 가능성 |
|---|---|---|---|---|---|
| **tree-sitter tags.scm** (표준) | `@definition.*`/`@reference.*` 캡처 선언적 symbol 추출 | tree-sitter grammar 전체(~40+) | MIT/Apache(언어별) | GitHub code nav·Helix·Neovim·Aider 사용 | **높음** — 하드코딩을 표준 쿼리로 대체 |
| **Aider repo map** | tags.scm + **Personalized PageRank** + 엣지 가중치 + binary search 토큰 fitting | 30+ | Apache-2.0 | 47.4k stars, 2026-05 최신, 활발 | **높음** — 알고리즘 직접 차용 가능 |
| **SCIP(프로토콜)** | Protobuf Symbol/Role/Occurrence/Relationship 모델 | 언어 독립 | Apache-2.0 | 2026-03 커뮤니티 이관(Meta/Uber) | **중간** — 스키마 참고 강력 권장, 전체 스택 반대 |
| **code-review-graph**(tirth8205) | tree-sitter + SQLite + **blast-radius minimal set** + FTS5 | 20+ | (repo 확인) | ~20k stars, 코드 리뷰 특화 | **매우 높음** — selvage와 가장 유사한 벤치마크 |
| **ast-grep** | tree-sitter + YAML structural rule | 20+ | **MIT** | 15.1k stars, 전일 커밋, 매우 활발 | **중간~높음** — CodeRabbit이 리뷰에 사용(검증됨) |
| **Semgrep CE** | 패턴 매칭 + intra-function dataflow | 40+ | LGPL-2.1 | 15.9k stars, 활발 | **낮음** — wheel 43-75MB, 철학만 차용 |
| **Joern (CPG)** | AST+CFG+DDG+CDG 단일 그래프 | 12 | Apache-2.0 | 3.2k stars, 거의 매일 릴리스 | **낮음(직접)** — JVM/Scala/8GB+, 모델링 아이디어만 |
| **CodeQL** | 관계형 DB + QL dataflow/taint | 12 | repo MIT / engine 상용 | 9.8k stars, 활발 | **낮음(직접)** — JVM+200-400MB+DB 빌드 |
| **Tabby** | tree-sitter tags + RAG 임베딩 | tree-sitter 전체 | Apache-2.0 | ~25k stars, 활발 | **낮음** — GPU/벡터 인덱스 과중, 단 "임베딩 도구도 tree-sitter 쓴다"는 역발견 |
| **Greptile** | AST graph + docstring LLM 생성 → 임베딩 + agent swarm | 다양 | 상용 SaaS | YC W24, 활발 | **낮음(직접)** — "AST가 주, 임베딩은 보조" 설계 참고 |
| **Comby** | parser combinator 런타임 + `:[hole]` lexical 매칭 | ~전체 | Apache-2.0 | 2.7k stars, 활동 둔화 | **낮음** — AST 아님, Python 바인딩 약함 |
| **LSIF** | JSON Lines vertex/edge 포맷(SCIP 전신) | 언어 독립 | MIT(스펙) | **사실상 deprecated**(lsif.dev 2025-06 archived) | **배제** |
| **tree-sitter-stack-graphs** | `.tsg` DSL push/pop name resolution | 4개 공식 | MIT/Apache | **2025-09-09 archived** | **배제**(죽은 기술, Python 규칙 미성숙) |
| **Bloop** | Rust+Tantivy+Qdrant 임베딩 하이브리드 | 언어 무관 | AGPL-3.0 | **2025-01-02 archived** | **배제**(중단) |
| **"Selena"** | (이름 변형 Selene/Sema/Caelena 포함 폭검색) | — | — | 확인 불가 | 범용 AST code intelligence OSS로 **미확인**(selene은 Lua linter로 이름만 유사) |

## 4. 기능 매트릭스 — selvage와 각 도구 비교

이 표가 본 문서의 핵심 차별화(선행 리서치에 없는 횡단 비교)다.

| 기능 | selvage 현구조 | Aider | SCIP | code-review-graph | ast-grep | Joern(CPG) | CodeQL | 임베딩계(Bloop/Tabby/Greptile) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Cross-file caller** | ✗(단일 파일) | 파일 PageRank(심볼 정확도 낮음) | 정확(Pyright) | call edge+blast radius | ✗ | 정확(call graph) | 정확 | 의미적 유사도만 |
| **Name resolution** | ✗ | 문자열 매칭 | 타입 추론(높음) | tree-sitter+옵션 Jedi | ✗ | scope+DDG | compiler-grade | ✗ |
| **Deterministic rules** | ✗ | ✗ | ✗ | ✗ | **강함**(YAML rule) | 강함(CPGQL) | 강함(QL) | ✗(비결정적) |
| **Repo graph 모델** | ✗(Symbol/Edge 0건) | 파일 노드 PageRank | Symbol/Occurrence/Relationship | Symbol/Edge | — | **AST+CFG+DDG+CDG** | relational DB | 임베딩 벡터 |
| **Token efficiency** | 중간(포함관계 제거만) | **매우 높음**(ranked map) | N/A | **매우 높음**(38-528x 절감) | — | 높음(slicing) | — | 중간(노이즈 혼재) |
| **Incremental cache** | ✗(매번 재파싱) | SQLite diskcache+mtime | Document 단위 | SQLite+SHA-256(<2s/2900파일) | ✗(상태 없음) | flatgraph DB | relational DB | sharded 인덱싱(무거움) |

**아키텍처 패턴 분류**(선행 리서치에 없는 관점): selvage는 **Query-only 패턴**(매번 AST 순회, 상태 없음)에 속한다. Aider/code-review-graph는 **File-local index 패턴**, stack-graphs는 **Name-binding DSL 패턴**, SCIP/CodeQL은 **Compiler index 패턴**, Greptile은 **Service-side graph 패턴**이다. Sprint 1은 Query-only → File-local index로의 이동이 핵심이다.

## 5. Top 5 도입 우선순위 (1인 메인테이너 관점)

| 순위 | 도입 항목 | Impact | Effort | 근거 |
|---|---|:---:|:---:|---|
| **1** | **tree-sitter `tags.scm` 도입** | 높음 | 낮음 | 하드코딩 3종 딕셔너리를 표준 쿼리로 대체. `@reference.call` 캡처로 역방향 의존성을 "무상" 획득. 언어 확장 비용 사실상 제로. Aider가 ctags→tags.scm으로 간 이유와 동일 |
| **2** | **Aider식 Personalized PageRank 랭킹** | 높음 | 낮음~중간 | `repomap.py` 소스 검증. "변경 파일이 참조하는 심볼 ×50" 가중치를 diff에 즉시 적용. `networkx.pagerank`+`diskcache` pip 설치로 해결, 완전 결정적 |
| **3** | **SQLite cache + SHA-256 incremental** | 높음 | 낮음 | code-review-graph/Aider/CodeGraph 모두 입증. 표준 `sqlite3`로 외부 의존 0. FTS5로 FALLBACK_CONTEXT 정규식 대체. 2,900 파일 <2초 |
| **4** | **code-review-graph 직접 벤치마크** | 높음 | 낮음(조사만) | selvage와 **동일 스택**(Python+tree-sitter+SQLite+코드 리뷰 특화). blast-radius minimal set, confidence 라벨(EXTRACTED/INFERRED/AMBIGUOUS) 등 최소 스키마를 그대로 참조 |
| **5** | **SCIP 영감 Symbol/Reference/Edge 스키마** | 중간 | 중간 | `Occurrence.enclosing_range`(이미 SMART_CONTEXT가 하는 일을 표준화), `SymbolRole` bitset, `Relationship` 플래그만 발췌. **전체 스택(scip-python)은 Kind=0 버그(#212)+Node.js 의존으로 반대** |

**배제**: CodeQL/Joern/Semgrep 런타임 직접 도입(전부 비현실적), LSIF(deprecated), stack-graphs(archived), Bloop(archived), 임베딩/벡터 DB(비결정성+인프라 과중).

## 6. Sprint 1 AST V2 구체적 권고사항

### 6.1 tags.scm 도입 경로

`tree_sitter_language_pack`이 이미 설치되어 있으므로, Aider 방식대로 각 언어의 `queries/tags.scm`을 번들한다(Python은 350 bytes, 4개 패턴). 핵심은 definition/reference 이원 구분이다:

```scheme
;; tree-sitter-python queries/tags.scm (표준)
(function_definition name: (identifier) @name) @definition.function
(class_definition  name: (identifier) @name) @definition.class
(call function: [(identifier) @name
                 (attribute attribute: (identifier) @name)]) @reference.call
```

이것만으로 `LANGUAGE_BLOCK_TYPES` 하드코딩(`context_extractor.py:33-111`, 5언어×수십 타입)을 대체하고, 현재 없는 역방향 호출 추적(`@reference.call`)의 기반을 확보한다. 모든 공식 grammar의 tags.scm은 MIT/Apache라 라이선스 리스크가 없다. tree-sitter의 `test/tags/` 주석 기반 테스트(`; ^ definition.function`)를 그대로 활용해 AST 추출 로직을 표준 프레임워크로 검증할 수 있다.

### 6.2 SQLite cache 전략 (code-review-graph 검증 패턴)

```sql
CREATE TABLE files (
    file_path TEXT PRIMARY KEY,
    content_hash TEXT,    -- SHA-256, 변경 감지 핵심
    mtime REAL,
    language TEXT
);
CREATE TABLE symbols (
    id INTEGER PRIMARY KEY,
    name TEXT, kind TEXT,                -- function|class|method|variable|module
    file_path TEXT REFERENCES files(file_path),
    start_line INTEGER, end_line INTEGER,
    signature TEXT, docstring TEXT       -- signature~10-50 토큰
);
CREATE TABLE edges (
    source_id INTEGER REFERENCES symbols(id),
    target_id INTEGER REFERENCES symbols(id),
    edge_kind TEXT,                       -- calls|imports|inherits|implements
    role INTEGER,                         -- SCIP SymbolRole 영감: Def=1,Ref=2,Write=4,Read=8
    confidence TEXT                       -- EXTRACTED|INFERRED|AMBIGUOUS
);
CREATE VIRTUAL TABLE symbols_fts USING fts5(name, signature, docstring);
```

증분 흐름: 파일 SHA-256 → `files.content_hash` 비교 → 변경 파일만 재파싱 → dependent(역방향 edge) 노드만 갱신. `diskcache.Cache`에 `{mtime, data:[Tag]}` 저장 + `CACHE_VERSION`으로 구 캐시 자동 무효화(Aider 패턴). 이것은 현재 매 리뷰마다 `ContextExtractor(file.language)`를 새로 생성하고 `parser.parse()`를 반복하는 낭비(`prompt_generator.py:110`)를 제거한다.

### 6.3 Aider식 ranking 적용 (repomap.py 소스 인용)

Aider의 엣지 가중치 공식을 diff에 맵핑한다(`aider/repomap.py` 직접 인용):

```python
# 변경 파일을 Aider의 chat_rel_fnames(×50 부스트 대상)로 취급
personalization = {fname: 50.0 for fname in diff_changed_files}
mul = 1.0
if ident in mentioned_idents:   mul *= 10    # LLM 언급 식별자
if is_meaningful(ident, len>=8): mul *= 10    # snake/camel 의미 식별자
if ident.startswith("_"):       mul *= 0.1   # private 억제
if len(defines[ident]) > 5:     mul *= 0.1   # 과다 정의 억제
if referencer in chat_rel:      use_mul *= 50  # ★변경 파일의 참조 = 최우선
num_refs = math.sqrt(num_refs)               # 참조 빈도 √n 감쇠
G.add_edge(referencer, definer, weight=use_mul*num_refs, ident=ident)
ranked = nx.pagerank(G, weight="weight", personalization=personalization, dangling=personalization)
```

핵심 차용: 수식 전체가 아닌 (a) personalization 개념, (b) "변경 파일 참조 ×50", (c) √(참조빈도) 감쇠, (d) binary search 토큰 fitting(`--map-tokens` 예산 내 상위 N개). `nx.pagerank`의 power iteration(tol=1e-06 고정, 난수 없음)은 **완전히 결정적**이라 동일 diff → 동일 컨텍스트를 보장한다. 이것이 임베딩 접근 대비 결정적 리뷰 도구에서 가지는 결정적 장점이다.

### 6.4 Symbol/Reference/Edge 모델 스키마 (SCIP 영감)

SCIP `scip.proto`에서 Python에 필요한 것만 축소 발췌:

| SCIP 엔티티 | selvage 제안 | 설계 영감 |
|---|---|---|
| `Symbol`(정규화 ID `<scheme> <module> <descriptor>`) | `Symbol(id,name,kind,file_path,start_line,end_line)` | ID 포맷 패턴 차용 |
| `Occurrence.symbol_roles`(7-bit bitset) | `Reference.role`(Definition/Read/Write/Import 4-5개) | diff 변경 유형 분류 |
| `Occurrence.enclosing_range`(v0.9 신규) | `Reference.enclosing_symbol_id`(FK) | **이미 SMART_CONTEXT가 하는 일** — 부모 함수/클래스 추적을 표준화 |
| `Relationship.is_implementation/is_type_definition` | `Edge.kind`(calls/imports/inherits/implements) | 다중 관계 표준화 |
| `SymbolInformation.kind`(86개) | `Symbol.kind`(5-7개) | Python 필요분만 |

주의: `overflow_symbol_roles`는 proposal 단계(Issue #154)로 v0.9 미구현. 현재 `int32` 비트마스크(32비트 중 7비트 사용)로 충분하다.

### 6.5 정밀도 계층과 provenance 원칙

선행 리서치의 핵심 철학을 계승: tree-sitter 기반은 heuristic(신뢰도 `EXTRACTED`/`INFERRED`), SCIP/CodeQL은 compiler-precise(`precise`)로 **provenance를 라벨로 분리**한다. Sprint 1은 heuristic 계층만 다루고, 향후 SCIP consumer를 **선택적 외부 adapter**로 둘 수 있도록 스키마를 열어둔다.

### 6.6 핵심 논증: 왜 deterministic AST인가

세 가지 독립 검증이 임베딩 단독 대비 AST graph를 지지한다. (1) **LLMxCPG**(USENIX Security 2025): CPG slicing으로 코드 67-84% 축소 시 LLM F1 15-40% 개선, slicing 생략 시 정확도 급락(0.7250→0.4875). (2) **GitLab**: "AST-based graphs outperform RAG in code reviews by 21%". (3) **arXiv 2601.08773**: AST 파생 그래프가 LLM 추출 지식그래프/일반 RAG 대비 우수. 결정적으로 **임베딩 도구 Tabby조차** 공식 문서에 "parses relevant code into Tree Sitter tags to provide effective prompts"라고 명시하며, 가장 정교한 임베딩 상용 도구 Greptile조차 AST graph를 주축으로 삼는다. 임베딩의 비결정성(같은 diff, 다른 컨텍스트)은 리뷰 도구에서 치명적이며, deterministic AST는 변동 원인을 LLM 호출 한 곳으로 격리한다.

## 7. 참고 링크

**selvage 현 구현 (직접 인용 원본)**
- `selvage/src/context_extractor/context_extractor.py` — `LANGUAGE_BLOCK_TYPES`(L33-111), `_find_node_by_line`(L352), `_find_minimal_enclosing_block`(L371), `_collect_dependency_nodes`(L521)
- `selvage/src/utils/prompts/prompt_generator.py:106-144` — smart/fallback/full 분기
- `selvage/src/context_extractor/smart_context_utils.py:14-26` — `use_smart_context()` 휴리스틱

**tree-sitter / tags.scm**
- tree-sitter Code Navigation: https://tree-sitter.github.io/tree-sitter/4-code-navigation.html
- tree-sitter-python tags.scm: https://github.com/tree-sitter/tree-sitter-python/blob/master/queries/tags.scm
- tree-sitter-javascript tags.scm: https://github.com/tree-sitter/tree-sitter-javascript/blob/master/queries/tags.scm

**Aider (랭킹 알고리즘)**
- repomap.py 소스: https://github.com/Aider-AI/aider/blob/main/aider/repomap.py
- Repo map 블로그: https://aider.chat/2023/10/22/repomap.html
- 알고리즘 분석(NousResearch): https://github.com/NousResearch/hermes-agent/issues/535

**SCIP / LSIF / stack-graphs**
- scip-code/scip: https://github.com/scip-code/scip · scip.proto: https://github.com/scip-code/scip/blob/main/scip.proto
- SCIP 거버넌스 전환: https://sourcegraph.com/blog/the-future-of-scip
- scip-python Issue #212 (Kind=0 버그): https://github.com/sourcegraph/scip-python/issues/212
- Eric Fritz LLM Antihallucinogen: https://www.eric-fritz.com/articles/llm-antihallucinogen
- LSIF (archived): https://lsif.dev/ · stack-graphs (archived 2025-09-09): https://github.com/github/stack-graphs

**LLM 코드 리뷰 벤치마크**
- code-review-graph (tirth8205): https://github.com/tirth8205/code-review-graph
- CodeGraph (colbymchenry): https://github.com/colbymchenry/codegraph

**Structural analysis / CPG**
- ast-grep: https://github.com/ast-grep/ast-grep (15.1k stars, MIT) · How it works(CodeRabbit 사례): https://ast-grep.github.io/advanced/how-ast-grep-works.html
- Joern: https://docs.joern.io/code-property-graph/
- Yamaguchi et al., CPG 원논문(IEEE S&P 2014): https://www.ieee-security.org/TC/SP2014/papers/ModelingandDiscoveringVulnerabilitieswithCodePropertyGraphs.pdf
- LLMxCPG(USENIX Security 2025): https://arxiv.org/html/2507.16585v1
- CodeQL dataflow: https://codeql.github.com/docs/writing-codeql-queries/about-data-flow-analysis/
- Semgrep: https://github.com/semgrep/semgrep · Comby: https://comby.dev/

**임베딩 vs AST (논증)**
- Tabby(tree-sitter tags 명시): https://tabby.tabbyml.com/docs/welcome/
- Greptile graph context: https://www.greptile.com/docs/how-greptile-works/graph-based-codebase-context · 임베딩 한계 자체 측정: https://www.greptile.com/blog/semantic-codebase-search
- Reliable Graph-RAG(arXiv 2601.08773): https://arxiv.org/abs/2601.08773
- Bloop(archived): https://github.com/BloopAI/bloop

**선행 리서치 (본 문서와 직교)**
- `2026-07-17-ast-context-research.md`(처방형 4단계 로드맵)
- `2026-07-17-market-landscape.md`, `2026-07-17-engineering-concepts.md`
