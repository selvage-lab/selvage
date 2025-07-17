# Selvage에서 Tree-sitter 활용 케이스 분석

## 🎯 핵심 목표

Selvage의 diff-only 모드 개선을 위한 **적응형 컨텍스트 추출**에서 tree-sitter의 효과적 활용 방안

## 📋 기본 활용 케이스 (기존)

### 1. 변경 라인 기반 블록 추출

```python
def extract_changed_function_blocks(file_content: str, changed_lines: list[int]) -> list[str]:
    """변경된 라인을 포함하는 함수 블록들 추출"""
    # tree-sitter로 함수 정의 노드 찾기
    # 각 changed_line이 포함된 함수 블록 식별
    # 중복 제거하여 반환
```

### 2. 변경 라인 기반 클래스 블록 추출

```python
def extract_changed_class_blocks(file_content: str, changed_lines: list[int]) -> list[str]:
    """변경된 라인을 포함하는 클래스 블록들 추출"""
    # 클래스 정의 노드에서 변경사항을 포함하는 부분만 추출
```

### 3. 참조 관계 분석

```python
def find_function_references(function_name: str, codebase_files: list[str]) -> list[ReferenceInfo]:
    """변경된 함수를 참조하는 모든 위치 찾기"""
    # 함수 호출, 메서드 체이닝 등 참조 관계 추적
```

## 🚀 확장된 활용 케이스

### 4. 스마트 컨텍스트 경계 결정

```python
class SmartContextExtractor:
    """변경사항의 의미적 범위에 따른 최적 컨텍스트 추출"""

    def determine_semantic_boundary(self, file_content: str, hunks: list[Hunk]) -> ContextRange:
        """의미적 경계를 고려한 컨텍스트 범위 결정"""
        # 변경사항이 함수 시그니처인지, 함수 본문인지 판단
        # 중첩된 함수/클래스 구조에서 적절한 범위 설정
        # 관련성 높은 코드만 포함하도록 경계 최적화

    def extract_minimal_meaningful_context(self, change_type: ChangeType) -> str:
        """변경 유형별 최소 의미있는 컨텍스트 추출"""
        if change_type == ChangeType.FUNCTION_SIGNATURE:
            return self._extract_function_with_docstring()
        elif change_type == ChangeType.IMPORT_STATEMENT:
            return self._extract_import_section()
        elif change_type == ChangeType.CLASS_METHOD:
            return self._extract_method_with_class_context()
```

### 5. 언어별 특화 추출 전략

```python
class LanguageSpecificExtractor:
    """프로그래밍 언어별 특화된 컨텍스트 추출 전략"""

    def extract_python_context(self, hunks: list[Hunk]) -> str:
        """Python 특화: 데코레이터, docstring, type hint 포함"""
        # @decorator가 있는 함수는 데코레이터부터 포함
        # docstring이 있으면 함수와 함께 추출
        # type hint 변경 시 관련 import 문도 포함

    def extract_javascript_context(self, hunks: list[Hunk]) -> str:
        """JavaScript 특화: 화살표 함수, 클로저, 모듈 export 고려"""
        # const func = () => {} 패턴 인식
        # React 컴포넌트의 경우 export와 함께 추출
        # 클로저 내부 함수 변경 시 외부 함수도 포함

    def extract_java_context(self, hunks: list[Hunk]) -> str:
        """Java 특화: 접근 제한자, 어노테이션, 제네릭 고려"""
        # @Override, @Deprecated 등 어노테이션 포함
        # 제네릭 타입 변경 시 관련 타입 정보 포함
        # 내부 클래스 변경 시 외부 클래스 컨텍스트 고려
```

### 6. 의존성 영향 범위 분석

```python
class DependencyImpactAnalyzer:
    """변경사항이 미치는 의존성 영향 범위 분석"""

    def analyze_method_signature_change(self, method_node: Node) -> ImpactScope:
        """메서드 시그니처 변경의 영향 범위 분석"""
        # 매개변수 추가/제거/변경 감지
        # 반환 타입 변경 감지
        # 영향받는 호출자 예상 범위 계산

    def find_breaking_changes(self, before_ast: Node, after_ast: Node) -> list[BreakingChange]:
        """API 호환성을 깨는 변경사항 식별"""
        # public 메서드/클래스 제거
        # 메서드 시그니처 변경
        # 상수 값 변경 등

    def suggest_related_files(self, changed_symbols: list[str]) -> list[str]:
        """변경된 심볼과 관련된 파일들 제안"""
        # import 관계 추적
        # 상속 관계 분석
        # 인터페이스 구현 관계 확인
```

### 7. 테스트 코드 연관성 분석

```python
class TestRelationshipAnalyzer:
    """변경사항과 테스트 코드의 연관성 분석"""

    def find_related_test_files(self, changed_functions: list[str]) -> list[str]:
        """변경된 함수와 관련된 테스트 파일 찾기"""
        # test_*.py 패턴의 파일들에서 함수명 검색
        # 테스트 케이스에서 import하는 모듈 추적
        # mock 객체로 사용되는 함수들 식별

    def analyze_test_coverage_impact(self, changed_code: str) -> TestCoverageReport:
        """변경사항이 테스트 커버리지에 미치는 영향"""
        # 새로 추가된 코드 경로 식별
        # 기존 테스트로 커버되지 않는 부분 표시
        # 추가 테스트가 필요한 영역 제안
```

### 8. 코드 품질 패턴 분석

```python
class CodeQualityPatternAnalyzer:
    """코드 품질과 관련된 패턴 분석"""

    def detect_code_smell_patterns(self, ast_nodes: list[Node]) -> list[CodeSmell]:
        """코드 스멜 패턴 감지"""
        # 긴 매개변수 목록 (>5개)
        # 깊은 중첩 구조 (>4단계)
        # 복잡한 조건문 (cyclomatic complexity)
        # 중복 코드 블록

    def analyze_complexity_changes(self, before_ast: Node, after_ast: Node) -> ComplexityDelta:
        """변경사항으로 인한 복잡도 변화 분석"""
        # Cyclomatic complexity 변화
        # 중첩 깊이 변화
        # 매개변수 개수 변화

    def suggest_refactoring_opportunities(self, context: str) -> list[RefactoringOpportunity]:
        """리팩토링 기회 제안"""
        # Extract Method 후보
        # Extract Class 후보
        # Replace Conditional with Polymorphism 후보
```

### 9. 성능 최적화된 부분 추출

```python
class PerformanceOptimizedExtractor:
    """대용량 파일에서 성능 최적화된 부분 추출"""

    def extract_with_lazy_parsing(self, file_path: str, target_lines: list[int]) -> str:
        """지연 파싱을 통한 효율적 추출"""
        # 전체 파일을 파싱하지 않고 필요한 부분만
        # 점진적 파싱으로 메모리 사용량 최적화
        # 캐싱을 통한 재파싱 방지

    def batch_extract_multiple_files(self, file_changes: dict[str, list[int]]) -> dict[str, str]:
        """여러 파일의 변경사항을 일괄 처리"""
        # 동일한 언어 파일들을 묶어서 처리
        # 파서 재사용으로 초기화 비용 절약
        # 병렬 처리 지원
```

### 10. 오류 복구 및 Fallback 전략

```python
class RobustExtractor:
    """파싱 오류 시 견고한 복구 전략"""

    def extract_with_fallback(self, file_content: str, hunks: list[Hunk]) -> str:
        """tree-sitter 실패 시 대안 전략"""
        try:
            return self._tree_sitter_extract(file_content, hunks)
        except ParsingError:
            return self._regex_based_extract(file_content, hunks)  # 정규식 기반 fallback
        except UnsupportedLanguageError:
            return self._heuristic_extract(file_content, hunks)    # 휴리스틱 기반 fallback

    def handle_syntax_errors(self, file_content: str) -> ParseResult:
        """구문 오류가 있는 파일의 부분 파싱"""
        # 오류 지점 이전까지만 파싱
        # 주석 처리된 코드 블록 무시
        # 불완전한 구문 구조 허용
```

## 🔧 구현 우선순위 및 복잡도 분석

### 1단계: 기본 구현 (낮은 복잡도)

- [x] 기본 함수/클래스 블록 추출 (케이스 1, 2)
- [ ] 언어별 특화 전략 기본 버전 (케이스 5)
- [ ] 오류 복구 Fallback 전략 (케이스 10)

### 2단계: 스마트 기능 (중간 복잡도)

- [ ] 스마트 컨텍스트 경계 결정 (케이스 4)
- [ ] 코드 품질 패턴 분석 (케이스 8)
- [ ] 성능 최적화 (케이스 9)

### 3단계: 고급 분석 (높은 복잡도)

- [ ] 의존성 영향 범위 분석 (케이스 6)
- [ ] 테스트 연관성 분석 (케이스 7)
- [ ] 참조 관계 분석 (케이스 3)

## ⚖️ 비용-효과 분석

### 높은 효과, 낮은 비용

- **케이스 4**: 스마트 컨텍스트 경계 → 토큰 사용량 대폭 절약
- **케이스 5**: 언어별 특화 → 리뷰 품질 향상
- **케이스 10**: Fallback 전략 → 시스템 안정성 확보

### 중간 효과, 중간 비용

- **케이스 8**: 코드 품질 분석 → 부가가치 제공
- **케이스 9**: 성능 최적화 → 대용량 프로젝트 지원

### 낮은 효과, 높은 비용

- **케이스 6**: 의존성 분석 → 구현 복잡도 대비 효과 미미
- **케이스 7**: 테스트 연관성 → 특정 상황에서만 유용

## 🚨 주의사항 및 한계점

1. **언어별 지원 차이**: 모든 프로그래밍 언어가 동일한 품질의 tree-sitter 파서를 가지지 않음
2. **메모리 사용량**: 대용량 파일에서 AST 구축 시 상당한 메모리 필요
3. **파싱 시간**: 복잡한 파일의 경우 파싱 시간이 길어질 수 있음
4. **의존성 관리**: tree-sitter-language-pack의 업데이트 및 호환성 관리 필요
5. **오류 처리**: 구문 오류나 지원되지 않는 언어에 대한 견고한 처리 필요

## 📊 결론 및 권장사항

**우선 구현 권장**: 케이스 4, 5, 10 (기본 기능 + 안정성)
**차순 구현 검토**: 케이스 8, 9 (부가가치 기능)  
**장기 검토**: 케이스 3, 6, 7 (고급 분석 기능)

tree-sitter 도입 시 **단계적 접근**을 통해 기본 기능부터 안정화한 후 고급 기능을 점진적으로 추가하는 것이 바람직합니다.

## 💻 핵심 케이스 구현 예시

### 케이스 4: 스마트 컨텍스트 경계 결정 구현

```python
from typing import NamedTuple
from tree_sitter_language_pack import get_language, get_parser

class ContextRange(NamedTuple):
    start_line: int
    end_line: int
    context_type: str
    confidence: float

class SmartContextExtractor:
    def __init__(self, language: str):
        self.language = get_language(language)
        self.parser = get_parser(language)

    def extract_optimal_context(self, file_content: str, hunks: list[Hunk]) -> str:
        """변경사항에 대한 최적 컨텍스트 추출"""
        tree = self.parser.parse(bytes(file_content, 'utf-8'))

        context_ranges = []
        for hunk in hunks:
            change_type = self._analyze_change_type(tree, hunk)
            context_range = self._determine_context_boundary(tree, hunk, change_type)
            context_ranges.append(context_range)

        # 중복 제거 및 병합
        merged_ranges = self._merge_overlapping_ranges(context_ranges)
        return self._extract_content_by_ranges(file_content, merged_ranges)

    def _analyze_change_type(self, tree: Tree, hunk: Hunk) -> str:
        """변경사항의 의미적 타입 분석"""
        query_patterns = {
            'function_signature': '(function_definition name: (_) @func_name)',
            'import_statement': '(import_statement)',
            'class_definition': '(class_definition name: (_) @class_name)',
            'variable_assignment': '(assignment left: (_) @var_name)',
        }

        for change_type, pattern in query_patterns.items():
            query = self.language.query(pattern)
            captures = query.captures(tree.root_node)

            for node, _ in captures:
                if self._line_intersects_hunk(node, hunk):
                    return change_type

        return 'generic_change'

    def _determine_context_boundary(self, tree: Tree, hunk: Hunk, change_type: str) -> ContextRange:
        """변경 타입에 따른 컨텍스트 경계 결정"""
        if change_type == 'function_signature':
            return self._get_function_with_docstring_boundary(tree, hunk)
        elif change_type == 'import_statement':
            return self._get_import_section_boundary(tree, hunk)
        elif change_type == 'class_definition':
            return self._get_class_boundary(tree, hunk)
        else:
            return self._get_surrounding_lines_boundary(hunk, lines_before=3, lines_after=3)

    def _get_function_with_docstring_boundary(self, tree: Tree, hunk: Hunk) -> ContextRange:
        """함수와 docstring을 포함한 경계 설정"""
        # 함수 정의 노드 찾기
        function_query = self.language.query("""
            (function_definition
                name: (identifier) @func_name
                body: (block) @func_body
            ) @function
        """)

        captures = function_query.captures(tree.root_node)
        for node, tag in captures:
            if tag == 'function' and self._line_intersects_hunk(node, hunk):
                start_line = node.start_point[0]
                end_line = node.end_point[0]

                # docstring 체크 (함수 시작 직후의 string literal)
                first_stmt = node.child_by_field_name('body').children[1]  # block -> ['{', stmt, '}']
                if first_stmt and first_stmt.type == 'expression_statement':
                    expr = first_stmt.children[0]
                    if expr.type == 'string':
                        # docstring이 있으면 포함
                        pass

                return ContextRange(start_line + 1, end_line + 1, 'function_with_docstring', 0.9)

        # 함수를 찾지 못한 경우 기본 범위
        return self._get_surrounding_lines_boundary(hunk, 5, 5)
```

### 케이스 5: 언어별 특화 추출 예시

```python
class PythonSpecificExtractor:
    """Python 언어 특화 컨텍스트 추출"""

    def extract_python_function_context(self, tree: Tree, hunk: Hunk) -> str:
        """Python 함수의 완전한 컨텍스트 추출"""
        # 데코레이터 포함 함수 정의 쿼리
        decorator_function_query = self.language.query("""
            (decorated_definition
                (decorator)* @decorators
                definition: (function_definition) @function
            ) @decorated_func
        """)

        captures = decorator_function_query.captures(tree.root_node)
        for node, tag in captures:
            if tag == 'decorated_func' and self._line_intersects_hunk(node, hunk):
                return self._extract_node_text(node)  # 데코레이터부터 함수 끝까지

        # 일반 함수 정의 (데코레이터 없음)
        function_query = self.language.query("""
            (function_definition
                name: (identifier) @name
                parameters: (parameters) @params
                return_type: (type)? @return_type
                body: (block) @body
            ) @function
        """)

        captures = function_query.captures(tree.root_node)
        for node, tag in captures:
            if tag == 'function' and self._line_intersects_hunk(node, hunk):
                return self._extract_node_text(node)

    def extract_python_class_context(self, tree: Tree, hunk: Hunk) -> str:
        """Python 클래스의 완전한 컨텍스트 추출"""
        # 클래스 정의 + 상속 + docstring
        class_query = self.language.query("""
            (class_definition
                name: (identifier) @class_name
                superclasses: (argument_list)? @inheritance
                body: (block) @class_body
            ) @class
        """)

        captures = class_query.captures(tree.root_node)
        for node, tag in captures:
            if tag == 'class' and self._line_intersects_hunk(node, hunk):
                # 클래스 내부에서 변경된 메서드만 포함할지 전체 클래스를 포함할지 결정
                if self._is_method_level_change(node, hunk):
                    return self._extract_changed_methods_with_class_signature(node, hunk)
                else:
                    return self._extract_node_text(node)  # 전체 클래스
```

### 케이스 10: Fallback 전략 구현

```python
class RobustExtractor:
    """견고한 컨텍스트 추출 with fallback"""

    def extract_with_multiple_fallbacks(self, file_content: str, hunks: list[Hunk]) -> str:
        """다단계 fallback 전략을 통한 견고한 추출"""

        # 1차: tree-sitter 시도
        try:
            return self._tree_sitter_extract(file_content, hunks)
        except Exception as e:
            logger.warning(f"Tree-sitter 추출 실패: {e}")

        # 2차: 언어별 AST 파서 시도 (Python의 경우 ast 모듈)
        try:
            return self._language_specific_ast_extract(file_content, hunks)
        except Exception as e:
            logger.warning(f"언어별 AST 추출 실패: {e}")

        # 3차: 정규식 기반 추출
        try:
            return self._regex_based_extract(file_content, hunks)
        except Exception as e:
            logger.warning(f"정규식 추출 실패: {e}")

        # 4차: 휴리스틱 기반 (들여쓰기 분석)
        try:
            return self._heuristic_extract(file_content, hunks)
        except Exception as e:
            logger.warning(f"휴리스틱 추출 실패: {e}")

        # 최후: 주변 라인 추출
        return self._extract_surrounding_lines(file_content, hunks, context_lines=5)

    def _regex_based_extract(self, file_content: str, hunks: list[Hunk]) -> str:
        """정규식을 사용한 함수/클래스 블록 추출"""
        lines = file_content.split('\n')
        context_blocks = []

        for hunk in hunks:
            for line_num in range(hunk.start_line, hunk.end_line + 1):
                # Python 함수 정의 패턴
                func_pattern = r'^\s*def\s+\w+\s*\('
                # Python 클래스 정의 패턴
                class_pattern = r'^\s*class\s+\w+\s*[:\(]'

                block = self._find_block_by_regex(lines, line_num, func_pattern, class_pattern)
                if block:
                    context_blocks.append(block)

        return '\n'.join(context_blocks)

    def _heuristic_extract(self, file_content: str, hunks: list[Hunk]) -> str:
        """들여쓰기 기반 휴리스틱 추출"""
        lines = file_content.split('\n')
        context_blocks = []

        for hunk in hunks:
            for line_num in range(hunk.start_line, hunk.end_line + 1):
                block = self._extract_indentation_block(lines, line_num)
                context_blocks.append(block)

        return '\n'.join(context_blocks)

    def _extract_indentation_block(self, lines: list[str], target_line: int) -> str:
        """들여쓰기 레벨을 기준으로 블록 추출"""
        if target_line >= len(lines):
            return ""

        target_indent = len(lines[target_line]) - len(lines[target_line].lstrip())

        # 블록 시작점 찾기 (같거나 낮은 들여쓰기 레벨)
        start_line = target_line
        while start_line > 0:
            line_indent = len(lines[start_line]) - len(lines[start_line].lstrip())
            if line_indent <= target_indent and lines[start_line].strip():
                if self._is_block_start(lines[start_line]):
                    break
            start_line -= 1

        # 블록 끝점 찾기
        end_line = target_line
        while end_line < len(lines) - 1:
            end_line += 1
            line_indent = len(lines[end_line]) - len(lines[end_line].lstrip())
            if line_indent <= target_indent and lines[end_line].strip():
                end_line -= 1
                break

        return '\n'.join(lines[start_line:end_line + 1])

    def _is_block_start(self, line: str) -> bool:
        """라인이 블록 시작인지 판단"""
        stripped = line.strip()
        return (stripped.startswith('def ') or
                stripped.startswith('class ') or
                stripped.startswith('if ') or
                stripped.startswith('for ') or
                stripped.startswith('while ') or
                stripped.startswith('with ') or
                stripped.startswith('try:'))
```

이제 Selvage의 tree-sitter 활용 케이스가 **기본 4개에서 구체적인 10개 케이스**로 확장되었으며, **구현 우선순위와 실용적인 코드 예시**까지 포함되어 있습니다. 특히 **케이스 4 (스마트 컨텍스트 경계)**, **케이스 5 (언어별 특화)**, **케이스 10 (Fallback 전략)**은 Selvage의 diff-only 모드 개선에 직접적으로 도움이 될 것입니다.
