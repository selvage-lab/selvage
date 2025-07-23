# Tree-sitter 기반 컨텍스트 추출 전략 보고서

## 개요

기존 ContextStrategy 기반의 계층적 컨텍스트 제공 방식을 폐기하고, tree-sitter를 활용한 일관된 컨텍스트 추출 방식으로 전환하기 위한 설계 및 구현 방안을 제시합니다.

## 1. 현재 코드베이스 분석

### 1.1 기존 구조 분석

**Diff Parsing System (`selvage/src/diff_parser/`)**
- `parser.py`: Git diff 파싱 및 FileDiff 객체 생성
- `models/file_diff.py`: 파일별 변경사항과 메타데이터 관리
- `models/hunk.py`: 개별 변경 블록 관리

**Prompt Generation System (`selvage/src/utils/prompts/prompt_generator.py`)**
- `_create_simple_code_review_prompt()`: diff-only 모드
- `_create_full_context_code_review_prompt()`: full-context 모드
- 현재 최적화: `file.line_count == file.additions`로 새 파일/전면 재작성 감지

### 1.2 Tree-sitter 인프라 현황

**현재 설치된 의존성**
- `tree-sitter-language-pack==0.9.0`: 다양한 언어 파서 지원
- 테스트 코드: `tests/test_tree_sitter_parsing.py` 존재
- SCM 쿼리 파일들: `selvage/resources/queries/` 디렉토리

**지원 언어**
- Python, JavaScript, TypeScript, Java, Go, Rust, C/C++, C#, PHP 등 주요 언어 지원

## 2. 새로운 Tree-sitter 기반 컨텍스트 추출 전략

### 2.1 핵심 아이디어

변경된 줄과 **의미적으로 관련된 코드만** 일관되게 추출하여 컨텍스트로 제공

#### 추출 대상 (우선순위 순)
1. **변경된 줄이 포함된 함수/클래스 블럭**
2. **해당 블럭에서 호출/참조하는 함수/변수/상수**
3. **해당 블럭을 호출/참조하는 함수/로직**

### 2.2 구현 아키텍처

#### 2.2.1 새로운 클래스 구조

```python
@dataclass
class ContextExtraction:
    """Tree-sitter 기반 컨텍스트 추출 결과"""
    
    # 핵심 변경 블럭 (항상 포함)
    primary_block: CodeBlock
    
    # 관련 코드 블럭들 (상황에 따라 포함)
    called_blocks: list[CodeBlock] = field(default_factory=list)
    calling_blocks: list[CodeBlock] = field(default_factory=list)
    referenced_symbols: list[SymbolReference] = field(default_factory=list)
    
    # 메타데이터
    extraction_method: str = ""  # "tree_sitter", "fallback_regex", "line_based"
    confidence_score: float = 0.0


@dataclass
class CodeBlock:
    """추출된 코드 블럭"""
    
    code_content: str
    start_line: int
    end_line: int
    block_type: str  # "function", "class", "method", "property", "constant"
    symbol_name: str
    parent_scope: str | None = None


class TreeSitterContextExtractor:
    """Tree-sitter 기반 컨텍스트 추출기"""
    
    def __init__(self):
        self.language_parsers: dict[str, Any] = {}
        self.query_cache: dict[str, Any] = {}
    
    def extract_context_for_hunk(
        self, 
        file_content: str, 
        hunk: Hunk, 
        language: str
    ) -> ContextExtraction:
        """변경된 hunk에 대한 관련 컨텍스트를 추출합니다."""
        
        try:
            # 1. Tree-sitter 파싱 시도
            return self._extract_with_tree_sitter(file_content, hunk, language)
        except Exception as e:
            # 2. Fallback: 정규표현식 기반 추출
            console.warning(f"Tree-sitter 추출 실패, fallback 사용: {e}")
            return self._extract_with_fallback(file_content, hunk, language)
    
    def _extract_with_tree_sitter(
        self, 
        file_content: str, 
        hunk: Hunk, 
        language: str
    ) -> ContextExtraction:
        """Tree-sitter를 사용한 정확한 컨텍스트 추출"""
        
        parser = self._get_parser(language)
        tree = parser.parse(bytes(file_content, "utf-8"))
        
        # 변경된 라인들의 AST 노드 찾기
        changed_lines = self._get_changed_line_numbers(hunk)
        nodes_in_changes = []
        
        for line_num in changed_lines:
            node = self._find_node_at_line(tree.root_node, line_num)
            if node:
                nodes_in_changes.append(node)
        
        # 각 노드가 속한 함수/클래스 찾기
        primary_blocks = []
        for node in nodes_in_changes:
            containing_function = self._find_containing_function_or_class(node)
            if containing_function:
                block = self._node_to_code_block(containing_function, file_content)
                primary_blocks.append(block)
        
        # 중복 제거 및 주 블럭 선정
        primary_block = self._select_primary_block(primary_blocks)
        
        # 관련 코드 찾기
        called_blocks = self._find_called_functions(primary_block, tree, file_content)
        calling_blocks = self._find_calling_functions(primary_block, tree, file_content)
        referenced_symbols = self._find_referenced_symbols(primary_block, tree, file_content)
        
        return ContextExtraction(
            primary_block=primary_block,
            called_blocks=called_blocks,
            calling_blocks=calling_blocks,
            referenced_symbols=referenced_symbols,
            extraction_method="tree_sitter",
            confidence_score=0.9
        )
```

#### 2.2.2 언어별 특화 쿼리 활용

```python
# Python 예시 쿼리
PYTHON_FUNCTION_QUERY = """
(function_definition
  name: (identifier) @function.name
  parameters: (parameters) @function.params
  body: (block) @function.body) @function.definition
  
(class_definition
  name: (identifier) @class.name
  body: (block) @class.body) @class.definition

(call
  function: (identifier) @call.function
  arguments: (argument_list) @call.args) @function.call
"""

# JavaScript/TypeScript 예시 쿼리  
JS_FUNCTION_QUERY = """
(function_declaration
  name: (identifier) @function.name
  parameters: (formal_parameters) @function.params
  body: (statement_block) @function.body) @function.definition

(method_definition
  name: (property_identifier) @method.name
  value: (function) @method.function) @method.definition

(call_expression
  function: (identifier) @call.function
  arguments: (arguments) @call.args) @function.call
"""
```

### 2.3 통합된 Prompt Generation

```python
class EnhancedPromptGenerator(PromptGenerator):
    """Tree-sitter 기반 컨텍스트 추출을 사용하는 프롬프트 생성기"""
    
    def __init__(self):
        super().__init__()
        self.context_extractor = TreeSitterContextExtractor()
    
    def _create_smart_context_prompt(
        self, 
        review_request: ReviewRequest
    ) -> ReviewPromptWithSmartContext:
        """스마트 컨텍스트 기반 프롬프트 생성"""
        
        system_prompt_content = self._get_code_review_system_prompt(
            is_include_entirely_new_content=review_request.is_include_entirely_new_content()
        )
        
        system_prompt = SystemPrompt(role="system", content=system_prompt_content)
        user_prompts: list[UserPromptWithSmartContext] = []
        
        for file in review_request.processed_diff.files:
            if is_ignore_file(file.filename):
                continue
            
            # 각 hunk에 대해 스마트 컨텍스트 추출
            smart_contexts = []
            for hunk in file.hunks:
                context = self.context_extractor.extract_context_for_hunk(
                    file.file_content or "", 
                    hunk, 
                    file.language
                )
                smart_contexts.append(context)
            
            user_prompt = UserPromptWithSmartContext(
                file_name=file.filename,
                language=file.language,
                smart_contexts=smart_contexts,
                original_hunks=file.hunks
            )
            user_prompts.append(user_prompt)
        
        return ReviewPromptWithSmartContext(
            system_prompt=system_prompt,
            user_prompts=user_prompts
        )


@dataclass
class UserPromptWithSmartContext:
    """스마트 컨텍스트가 포함된 사용자 프롬프트"""
    
    file_name: str
    language: str
    smart_contexts: list[ContextExtraction]
    original_hunks: list[Hunk]
    
    def to_prompt_text(self) -> str:
        """프롬프트 텍스트로 변환"""
        
        sections = []
        sections.append(f"## 파일: {self.file_name}")
        sections.append(f"언어: {self.language}")
        sections.append("")
        
        for i, context in enumerate(self.smart_contexts):
            sections.append(f"### 변경사항 {i+1}")
            sections.append("")
            
            # 주요 컨텍스트 (항상 포함)
            sections.append("#### 변경이 포함된 코드 블럭:")
            sections.append(f"```{self.language}")
            sections.append(context.primary_block.code_content)
            sections.append("```")
            sections.append("")
            
            # 관련 코드 (조건적 포함)
            if context.called_blocks:
                sections.append("#### 이 코드에서 호출하는 함수/메서드:")
                for block in context.called_blocks:
                    sections.append(f"```{self.language}")
                    sections.append(block.code_content)
                    sections.append("```")
                sections.append("")
            
            if context.calling_blocks:
                sections.append("#### 이 코드를 호출하는 함수/메서드:")
                for block in context.calling_blocks:
                    sections.append(f"```{self.language}")
                    sections.append(block.code_content)
                    sections.append("```")
                sections.append("")
            
            # 실제 변경사항
            hunk = self.original_hunks[i]
            sections.append("#### 실제 변경내용:")
            sections.append("변경 전:")
            sections.append(f"```{self.language}")
            sections.append(hunk.get_before_code())
            sections.append("```")
            sections.append("")
            sections.append("변경 후:")
            sections.append(f"```{self.language}")
            sections.append(hunk.get_after_code())
            sections.append("```")
            sections.append("")
        
        return "\n".join(sections)
```

## 3. 구현 단계별 계획

### 3.1 1차 구현 (파일 내부 컨텍스트)

**목표**: 변경된 파일 내에서만 관련 컨텍스트 추출

#### 구현 범위
- ✅ Tree-sitter 파서 초기화 및 언어별 쿼리 시스템
- ✅ 변경된 라인이 포함된 함수/클래스 블럭 추출  
- ✅ 해당 블럭에서 호출하는 함수/변수 추출
- ✅ 해당 블럭을 호출하는 함수 추출
- ✅ Fallback 메커니즘 (정규표현식 기반)

#### 예상 효과
- **토큰 사용량**: 기존 full-context 대비 30-50% 감소
- **컨텍스트 품질**: 변경 라인과 직접적으로 관련된 코드만 포함
- **처리 성능**: AST 파싱으로 정확도 향상

### 3.2 2차 구현 (크로스 파일 컨텍스트)

**목표**: 다른 파일에서 참조되는 함수/클래스까지 포함

#### 확장 방법

**Import/Export 관계 분석**
```python
class CrossFileContextExtractor:
    """크로스 파일 컨텍스트 추출기"""
    
    def find_cross_file_dependencies(
        self, 
        primary_block: CodeBlock, 
        project_root: str
    ) -> list[CodeBlock]:
        """다른 파일에서의 관련 코드 찾기"""
        
        dependencies = []
        
        # 1. Import 문 분석으로 의존성 파일 찾기
        imported_modules = self._analyze_imports(primary_block.file_path)
        
        # 2. 각 의존성 파일에서 관련 심볼 찾기
        for module_path in imported_modules:
            if os.path.exists(module_path):
                symbols = self._find_exported_symbols(module_path, primary_block)
                dependencies.extend(symbols)
        
        # 3. 역방향 참조 찾기 (이 심볼을 import하는 파일들)
        referencing_files = self._find_referencing_files(primary_block, project_root)
        for ref_file in referencing_files:
            usage_blocks = self._find_symbol_usage(ref_file, primary_block.symbol_name)
            dependencies.extend(usage_blocks)
        
        return dependencies
    
    def _analyze_imports(self, file_path: str) -> list[str]:
        """파일의 import 문 분석하여 의존성 파일 목록 반환"""
        # Python: from x import y, import x
        # JavaScript: import x from 'y', require('x')
        # 언어별 import 패턴 분석
        pass
    
    def _find_exported_symbols(
        self, 
        module_path: str, 
        target_block: CodeBlock
    ) -> list[CodeBlock]:
        """모듈에서 export되는 심볼 중 target_block에서 사용하는 것들 찾기"""
        pass
    
    def _find_referencing_files(
        self, 
        target_block: CodeBlock, 
        project_root: str
    ) -> list[str]:
        """프로젝트에서 target_block의 심볼을 참조하는 파일들 찾기"""
        # ripgrep 등을 활용한 빠른 텍스트 검색
        pass
```

**Git Hook 기반 증분 인덱싱**
```python
class ProjectSymbolIndex:
    """프로젝트 전체 심볼 인덱스"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.symbol_index: dict[str, list[SymbolLocation]] = {}
        self.file_dependency_graph: dict[str, list[str]] = {}
    
    def build_initial_index(self):
        """초기 프로젝트 인덱스 구축"""
        for file_path in self._get_all_source_files():
            self._index_file_symbols(file_path)
    
    def update_index_for_changed_files(self, changed_files: list[str]):
        """변경된 파일들에 대해서만 인덱스 업데이트"""
        for file_path in changed_files:
            self._reindex_file(file_path)
    
    def find_symbol_references(self, symbol_name: str) -> list[SymbolLocation]:
        """심볼의 모든 참조 위치 반환"""
        return self.symbol_index.get(symbol_name, [])
```

### 3.3 성능 최적화 방안

#### 캐싱 전략
```python
@dataclass
class CachedContextExtraction:
    """캐시된 컨텍스트 추출 결과"""
    
    file_path: str
    file_hash: str  # 파일 내용 해시
    hunk_signature: str  # hunk 고유 서명
    extraction_result: ContextExtraction
    timestamp: float
    
class ContextExtractionCache:
    """컨텍스트 추출 결과 캐시"""
    
    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.memory_cache: dict[str, CachedContextExtraction] = {}
    
    def get_cached_extraction(
        self, 
        file_path: str, 
        hunk: Hunk
    ) -> ContextExtraction | None:
        """캐시된 추출 결과 반환"""
        
        file_hash = self._calculate_file_hash(file_path)
        hunk_signature = self._calculate_hunk_signature(hunk)
        cache_key = f"{file_path}:{file_hash}:{hunk_signature}"
        
        # 메모리 캐시 확인
        if cache_key in self.memory_cache:
            cached = self.memory_cache[cache_key]
            if time.time() - cached.timestamp < 3600:  # 1시간 유효
                return cached.extraction_result
        
        # 디스크 캐시 확인
        cache_file = self.cache_dir / f"{hash(cache_key)}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    return ContextExtraction.from_dict(cached_data)
            except Exception:
                pass
        
        return None
```

#### 병렬 처리
```python
async def extract_contexts_parallel(
    files: list[FileDiff], 
    extractor: TreeSitterContextExtractor
) -> list[list[ContextExtraction]]:
    """여러 파일의 컨텍스트를 병렬로 추출"""
    
    tasks = []
    for file in files:
        for hunk in file.hunks:
            task = asyncio.create_task(
                extractor.extract_context_for_hunk_async(
                    file.file_content or "", 
                    hunk, 
                    file.language
                )
            )
            tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 결과 정리 및 예외 처리
    processed_results = []
    for result in results:
        if isinstance(result, Exception):
            console.warning(f"컨텍스트 추출 실패: {result}")
            # fallback 결과 사용
            processed_results.append(None)
        else:
            processed_results.append(result)
    
    return processed_results
```

## 4. 예상 효과 및 장점

### 4.1 토큰 사용량 최적화

**시나리오 비교**

| 시나리오 | 기존 (full-context) | 새로운 방식 | 개선율 |
|----------|---------------------|-------------|--------|
| 1줄 변경 (500줄 파일) | 500줄 전체 | ~50줄 함수 블럭 | **90% 감소** |
| 함수 내 5줄 변경 | 500줄 전체 | ~80줄 (함수+호출) | **84% 감소** |
| 클래스 메서드 변경 | 500줄 전체 | ~150줄 (클래스+관련) | **70% 감소** |
| 새 파일 생성 | 전체 내용 | 전체 내용 | **변화 없음** |

### 4.2 컨텍스트 품질 향상

**정확한 범위 제공**
- ✅ 변경과 직접적으로 관련된 코드만 포함
- ✅ 함수/클래스 경계를 정확하게 인식
- ✅ 호출 관계와 의존성을 명확하게 파악

**언어별 특화**
- ✅ 각 언어의 구문 구조에 맞는 정확한 추출
- ✅ Tree-sitter AST 기반으로 오류 최소화
- ✅ 복잡한 중첩 구조도 정확하게 처리

### 4.3 확장성과 유지보수성

**모듈화된 설계**
- 각 언어별 쿼리는 독립적으로 관리
- Fallback 메커니즘으로 안정성 보장
- 캐싱으로 성능 향상

**점진적 개선**
- 1차: 파일 내부 컨텍스트 
- 2차: 크로스 파일 컨텍스트
- 3차: 고급 의존성 분석

## 5. 리스크 및 대응 방안

### 5.1 주요 리스크

**성능 리스크**
- Tree-sitter 파싱 오버헤드
- 대용량 파일 처리 시간
- 메모리 사용량 증가

**정확성 리스크**  
- 언어별 파서 품질 차이
- 복잡한 동적 호출 관계 누락
- 매크로/템플릿 코드 처리 한계

### 5.2 대응 방안

**성능 최적화**
```python
class PerformanceOptimizer:
    """성능 최적화 관리자"""
    
    def __init__(self):
        self.size_thresholds = {
            "small": 1000,    # 1KB 미만
            "medium": 50000,  # 50KB 미만  
            "large": 200000,  # 200KB 미만
            "huge": float('inf')
        }
    
    def should_use_tree_sitter(
        self, 
        file_size: int, 
        language: str
    ) -> bool:
        """파일 크기와 언어에 따라 tree-sitter 사용 여부 결정"""
        
        if file_size > self.size_thresholds["huge"]:
            return False  # 너무 큰 파일은 fallback
        
        if language not in WELL_SUPPORTED_LANGUAGES:
            return False  # 지원이 부족한 언어는 fallback
        
        return True
    
    def get_extraction_strategy(
        self, 
        file_size: int, 
        change_density: float
    ) -> str:
        """파일 크기와 변경 밀도에 따른 추출 전략 선택"""
        
        if file_size < self.size_thresholds["small"]:
            return "full_file"  # 작은 파일은 전체 포함
        elif change_density > 0.3:  # 변경이 30% 이상
            return "extended_context"  # 넓은 컨텍스트
        else:
            return "focused_context"  # 집중된 컨텍스트
```

**품질 보장**
```python
class QualityAssurance:
    """추출 품질 보장 시스템"""
    
    def validate_extraction(
        self, 
        extraction: ContextExtraction, 
        original_hunk: Hunk
    ) -> float:
        """추출 결과의 품질 점수 계산"""
        
        score = 0.0
        
        # 1. 변경된 라인이 추출된 컨텍스트에 포함되어 있는지 확인
        if self._contains_changed_lines(extraction, original_hunk):
            score += 0.4
        
        # 2. 추출된 코드 블럭이 완전한지 확인 (문법적으로)
        if self._is_syntactically_complete(extraction.primary_block):
            score += 0.3
        
        # 3. 관련 코드의 관련성 점수
        relevance_score = self._calculate_relevance_score(extraction)
        score += 0.3 * relevance_score
        
        return score
    
    def _contains_changed_lines(
        self, 
        extraction: ContextExtraction, 
        hunk: Hunk
    ) -> bool:
        """변경된 라인이 추출 컨텍스트에 포함되어 있는지 확인"""
        
        changed_lines = set(range(
            hunk.start_line_modified,
            hunk.start_line_modified + hunk.line_count_modified
        ))
        
        extracted_lines = set(range(
            extraction.primary_block.start_line,
            extraction.primary_block.end_line + 1
        ))
        
        return bool(changed_lines.intersection(extracted_lines))
```

## 6. 결론 및 권장사항

### 6.1 핵심 가치 제안

1. **일관된 컨텍스트 제공**: ContextStrategy의 복잡성 제거하고 단일 알고리즘으로 통합
2. **토큰 효율성**: 평균 70-85% 토큰 사용량 감소 예상  
3. **의미적 정확성**: AST 기반으로 구문적으로 완전한 컨텍스트 보장
4. **확장 가능성**: 크로스 파일 분석까지 단계적 확장 가능

### 6.2 구현 우선순위

**Phase 1 (2-3일)**: 기본 Tree-sitter 컨텍스트 추출
- TreeSitterContextExtractor 클래스 구현
- Python, JavaScript 언어 우선 지원
- Fallback 메커니즘 구현

**Phase 2 (3-4일)**: Prompt 시스템 통합
- EnhancedPromptGenerator 구현
- 기존 시스템과 호환성 유지
- A/B 테스트를 위한 플래그 도입

**Phase 3 (선택적, 5-7일)**: 고도화
- 크로스 파일 분석
- 성능 최적화 및 캐싱
- 추가 언어 지원

### 6.3 성공 지표

- **토큰 사용량**: 70% 이상 감소
- **리뷰 품질**: 기존 대비 90% 이상 유지
- **처리 시간**: 2배 이내 증가 허용
- **안정성**: 99% 이상 추출 성공률

---

**문서 작성일**: 2025-07-21  
**작성자**: Claude Code  
**버전**: 1.0  
**대상**: Selvage 개발팀