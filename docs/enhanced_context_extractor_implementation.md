# Enhanced Context Extractor 구현 계획서

## 개요

현재 `OptimizedContextExtractor`는 변경된 라인이 속한 가장 작은 의미 단위의 블록만 추출합니다. 이를 확장하여 다음 기능을 추가합니다:

1. **의존성 분석**: 추출한 블록 내부에서 호출되는 외부 함수, 상수, 변수들을 추가로 추출
2. **참조 분석**: 추출한 블록의 요소들을 참조하는 코드 라인들을 찾아 출력

## 아키텍처 설계

### 새로 추가될 클래스들

```
selvage/src/context_extractor/
├── symbol_collector.py          # 심볼 사용/정의 수집
├── dependency_analyzer.py       # 의존성 분석
├── reference_analyzer.py        # 참조 분석
├── enhanced_context_extractor.py # 확장된 컨텍스트 추출기
└── models/
    ├── symbol_info.py          # 심볼 정보 모델
    ├── dependency_result.py    # 의존성 분석 결과
    └── reference_result.py     # 참조 분석 결과
```

## 상세 구현

### 1. 심볼 정보 모델 (`models/symbol_info.py`)

```python
"""심볼 정보를 표현하는 데이터 모델."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from tree_sitter import Node


class SymbolType(Enum):
    """심볼 타입 열거형."""

    FUNCTION = "function"
    CLASS = "class"
    VARIABLE = "variable"
    CONSTANT = "constant"
    METHOD = "method"
    PROPERTY = "property"
    IMPORT = "import"


@dataclass
class SymbolDefinition:
    """심볼 정의 정보."""

    name: str
    symbol_type: SymbolType
    node: Node
    line_number: int
    column: int
    scope_level: int

    @property
    def location(self) -> tuple[int, int]:
        """심볼 위치를 (line, column) 튜플로 반환."""
        return (self.line_number, self.column)


@dataclass
class SymbolUsage:
    """심볼 사용 정보."""

    name: str
    node: Node
    line_number: int
    column: int
    context: str  # 사용 컨텍스트 (함수 호출, 변수 참조 등)

    @property
    def location(self) -> tuple[int, int]:
        """심볼 위치를 (line, column) 튜플로 반환."""
        return (self.line_number, self.column)


@dataclass
class SymbolScope:
    """심볼 스코프 정보."""

    node: Node
    scope_type: str  # "module", "class", "function" 등
    start_line: int
    end_line: int
    parent_scope: Optional[SymbolScope] = None
    symbols: dict[str, SymbolDefinition] = None

    def __post_init__(self):
        if self.symbols is None:
            self.symbols = {}
```

### 2. 심볼 수집기 (`symbol_collector.py`)

```python
"""AST에서 심볼 사용과 정의를 수집하는 클래스."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Set

from tree_sitter import Language, Node, Parser

from .models.symbol_info import SymbolDefinition, SymbolScope, SymbolType, SymbolUsage

logger = logging.getLogger(__name__)


class SymbolCollector:
    """AST에서 심볼 정보를 수집하는 클래스."""

    def __init__(self, language: str):
        """SymbolCollector 초기화.

        Args:
            language: 프로그래밍 언어 (예: "python", "java")
        """
        self.language = language
        self._parser = Parser()
        self._language = Language(
            f"/opt/homebrew/lib/python3.11/site-packages/tree_sitter_languages/languages.so",
            language
        )
        self._parser.set_language(self._language)

        # 언어별 쿼리 패턴 설정
        self._setup_queries()

    def _setup_queries(self) -> None:
        """언어별 쿼리 패턴 설정."""
        if self.language == "python":
            self._definition_query = self._language.query("""
                ; 함수 정의
                (function_definition
                  name: (identifier) @function.name) @function.def

                ; 클래스 정의
                (class_definition
                  name: (identifier) @class.name) @class.def

                ; 변수 할당
                (assignment
                  left: (identifier) @variable.name) @variable.def

                ; 상수 (대문자 변수)
                (assignment
                  left: (identifier) @constant.name
                  (#match? @constant.name "^[A-Z_][A-Z0-9_]*$")) @constant.def

                ; 메서드 정의
                (function_definition
                  name: (identifier) @method.name
                  parameters: (parameters
                    (identifier) @method.self
                    (#eq? @method.self "self"))) @method.def
            """)

            self._usage_query = self._language.query("""
                ; 함수 호출
                (call
                  function: (identifier) @function.call)

                ; 속성 접근을 통한 메서드 호출
                (call
                  function: (attribute
                    attribute: (identifier) @method.call))

                ; 변수/상수 참조
                (identifier) @variable.ref

                ; import 문
                (import_statement
                  name: (dotted_name
                    (identifier) @import.name))

                (import_from_statement
                  name: (dotted_name
                    (identifier) @import.from))
            """)

    def collect_symbols_in_node(self, root_node: Node, file_content: str) -> tuple[
        Dict[str, List[SymbolDefinition]],
        Dict[str, List[SymbolUsage]]
    ]:
        """노드 내에서 모든 심볼 정의와 사용을 수집.

        Args:
            root_node: 분석할 루트 노드
            file_content: 파일 전체 내용

        Returns:
            (심볼_정의들, 심볼_사용들) 튜플
        """
        definitions: Dict[str, List[SymbolDefinition]] = {}
        usages: Dict[str, List[SymbolUsage]] = {}

        # 스코프 분석
        scopes = self._analyze_scopes(root_node)

        # 정의 수집
        definition_captures = self._definition_query.captures(root_node)
        for node, capture_name in definition_captures:
            symbol_def = self._create_symbol_definition(
                node, capture_name, file_content, scopes
            )
            if symbol_def:
                if symbol_def.name not in definitions:
                    definitions[symbol_def.name] = []
                definitions[symbol_def.name].append(symbol_def)

        # 사용 수집
        usage_captures = self._usage_query.captures(root_node)
        for node, capture_name in usage_captures:
            symbol_usage = self._create_symbol_usage(
                node, capture_name, file_content
            )
            if symbol_usage:
                if symbol_usage.name not in usages:
                    usages[symbol_usage.name] = []
                usages[symbol_usage.name].append(symbol_usage)

        return definitions, usages

    def _analyze_scopes(self, root_node: Node) -> List[SymbolScope]:
        """노드 내 스코프들을 분석."""
        scopes = []

        def visit_node(node: Node, parent_scope: SymbolScope = None) -> None:
            scope = None

            if node.type in ("module", "class_definition", "function_definition"):
                scope = SymbolScope(
                    node=node,
                    scope_type=node.type,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    parent_scope=parent_scope
                )
                scopes.append(scope)

            for child in node.children:
                visit_node(child, scope or parent_scope)

        visit_node(root_node)
        return scopes

    def _create_symbol_definition(
        self,
        node: Node,
        capture_name: str,
        file_content: str,
        scopes: List[SymbolScope]
    ) -> SymbolDefinition | None:
        """심볼 정의 객체 생성."""
        try:
            name = node.text.decode('utf-8')
            line_num = node.start_point[0] + 1
            column = node.start_point[1]

            # 심볼 타입 결정
            if "function" in capture_name:
                symbol_type = SymbolType.FUNCTION
            elif "class" in capture_name:
                symbol_type = SymbolType.CLASS
            elif "method" in capture_name:
                symbol_type = SymbolType.METHOD
            elif "constant" in capture_name:
                symbol_type = SymbolType.CONSTANT
            else:
                symbol_type = SymbolType.VARIABLE

            # 스코프 레벨 계산
            scope_level = self._calculate_scope_level(node, scopes)

            return SymbolDefinition(
                name=name,
                symbol_type=symbol_type,
                node=node,
                line_number=line_num,
                column=column,
                scope_level=scope_level
            )
        except Exception as e:
            logger.warning(f"심볼 정의 생성 실패: {e}")
            return None

    def _create_symbol_usage(
        self,
        node: Node,
        capture_name: str,
        file_content: str
    ) -> SymbolUsage | None:
        """심볼 사용 객체 생성."""
        try:
            name = node.text.decode('utf-8')
            line_num = node.start_point[0] + 1
            column = node.start_point[1]

            # 사용 컨텍스트 결정
            if "call" in capture_name:
                context = "function_call"
            elif "ref" in capture_name:
                context = "variable_reference"
            elif "import" in capture_name:
                context = "import"
            else:
                context = "unknown"

            return SymbolUsage(
                name=name,
                node=node,
                line_number=line_num,
                column=column,
                context=context
            )
        except Exception as e:
            logger.warning(f"심볼 사용 생성 실패: {e}")
            return None

    def _calculate_scope_level(self, node: Node, scopes: List[SymbolScope]) -> int:
        """노드의 스코프 레벨 계산."""
        level = 0
        for scope in scopes:
            if (scope.start_line <= node.start_point[0] + 1 <= scope.end_line):
                level += 1
        return level
```

### 3. 의존성 분석기 (`dependency_analyzer.py`)

```python
"""코드 블록의 의존성을 분석하는 클래스."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Set

from tree_sitter import Node

from .models.symbol_info import SymbolDefinition, SymbolUsage
from .symbol_collector import SymbolCollector

logger = logging.getLogger(__name__)


@dataclass
class DependencyResult:
    """의존성 분석 결과."""

    missing_dependencies: Dict[str, List[SymbolUsage]]  # 블록 내에서 정의되지 않은 심볼들
    resolved_dependencies: Dict[str, SymbolDefinition]  # 해결된 의존성들
    unresolved_dependencies: Set[str]  # 파일 내에서도 찾을 수 없는 의존성들


class DependencyAnalyzer:
    """코드 블록의 의존성을 분석하는 클래스."""

    def __init__(self, language: str):
        """DependencyAnalyzer 초기화.

        Args:
            language: 프로그래밍 언어
        """
        self.language = language
        self.symbol_collector = SymbolCollector(language)

    def analyze_dependencies(
        self,
        context_blocks: List[Node],
        file_root: Node,
        file_content: str
    ) -> DependencyResult:
        """컨텍스트 블록들의 의존성을 분석.

        Args:
            context_blocks: 분석할 컨텍스트 블록들
            file_root: 파일 전체 AST 루트
            file_content: 파일 전체 내용

        Returns:
            의존성 분석 결과
        """
        # 1. 전체 파일에서 심볼 정의 수집
        file_definitions, _ = self.symbol_collector.collect_symbols_in_node(
            file_root, file_content
        )

        # 2. 각 컨텍스트 블록 내 심볼 분석
        all_block_definitions: Dict[str, SymbolDefinition] = {}
        all_block_usages: Dict[str, List[SymbolUsage]] = {}

        for block in context_blocks:
            block_defs, block_usages = self.symbol_collector.collect_symbols_in_node(
                block, file_content
            )

            # 블록 내 정의들 병합
            for name, definitions in block_defs.items():
                if name not in all_block_definitions:
                    all_block_definitions[name] = definitions[0]  # 첫 번째 정의 사용

            # 블록 내 사용들 병합
            for name, usages in block_usages.items():
                if name not in all_block_usages:
                    all_block_usages[name] = []
                all_block_usages[name].extend(usages)

        # 3. 의존성 분석
        missing_dependencies: Dict[str, List[SymbolUsage]] = {}
        resolved_dependencies: Dict[str, SymbolDefinition] = {}
        unresolved_dependencies: Set[str] = set()

        for symbol_name, usages in all_block_usages.items():
            # 블록 내에서 정의되지 않은 심볼인지 확인
            if symbol_name not in all_block_definitions:
                missing_dependencies[symbol_name] = usages

                # 전체 파일에서 정의를 찾기
                if symbol_name in file_definitions:
                    resolved_dependencies[symbol_name] = file_definitions[symbol_name][0]
                else:
                    unresolved_dependencies.add(symbol_name)

        return DependencyResult(
            missing_dependencies=missing_dependencies,
            resolved_dependencies=resolved_dependencies,
            unresolved_dependencies=unresolved_dependencies
        )

    def get_dependency_blocks(
        self,
        dependency_result: DependencyResult,
        file_root: Node
    ) -> List[Node]:
        """의존성 정의들을 포함하는 블록들을 반환.

        Args:
            dependency_result: 의존성 분석 결과
            file_root: 파일 루트 노드

        Returns:
            의존성 정의들을 포함하는 블록들
        """
        dependency_blocks = []

        for symbol_name, symbol_def in dependency_result.resolved_dependencies.items():
            # 심볼 정의를 포함하는 적절한 블록 찾기
            block = self._find_containing_block(symbol_def.node, file_root)
            if block and block not in dependency_blocks:
                dependency_blocks.append(block)

        return dependency_blocks

    def _find_containing_block(self, symbol_node: Node, file_root: Node) -> Node | None:
        """심볼을 포함하는 적절한 블록을 찾기."""
        current = symbol_node.parent

        while current and current != file_root:
            # 함수, 클래스, 또는 모듈 레벨 할당인지 확인
            if current.type in (
                "function_definition",
                "class_definition",
                "assignment",  # 모듈 레벨 상수/변수
                "expression_statement"  # 모듈 레벨 표현식
            ):
                return current
            current = current.parent

        return symbol_node  # 최후의 수단으로 심볼 노드 자체 반환
```

### 4. 참조 분석기 (`reference_analyzer.py`)

```python
"""추출된 블록의 요소들을 참조하는 위치를 찾는 클래스."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Set

from tree_sitter import Node

from .models.symbol_info import SymbolDefinition, SymbolUsage
from .symbol_collector import SymbolCollector

logger = logging.getLogger(__name__)


@dataclass
class ReferenceResult:
    """참조 분석 결과."""

    defined_symbols: Dict[str, SymbolDefinition]  # 블록에서 정의된 심볼들
    references: Dict[str, List[SymbolUsage]]  # 각 심볼을 참조하는 위치들
    reference_lines: Dict[str, List[int]]  # 심볼별 참조 라인 번호들


class ReferenceAnalyzer:
    """추출된 블록의 참조를 분석하는 클래스."""

    def __init__(self, language: str):
        """ReferenceAnalyzer 초기화.

        Args:
            language: 프로그래밍 언어
        """
        self.language = language
        self.symbol_collector = SymbolCollector(language)

    def analyze_references(
        self,
        context_blocks: List[Node],
        file_root: Node,
        file_content: str
    ) -> ReferenceResult:
        """컨텍스트 블록들의 참조를 분석.

        Args:
            context_blocks: 분석할 컨텍스트 블록들
            file_root: 파일 전체 AST 루트
            file_content: 파일 전체 내용

        Returns:
            참조 분석 결과
        """
        # 1. 컨텍스트 블록에서 정의된 심볼들 수집
        defined_symbols: Dict[str, SymbolDefinition] = {}

        for block in context_blocks:
            block_defs, _ = self.symbol_collector.collect_symbols_in_node(
                block, file_content
            )

            for name, definitions in block_defs.items():
                if name not in defined_symbols:
                    defined_symbols[name] = definitions[0]

        # 2. 전체 파일에서 심볼 사용 수집
        _, file_usages = self.symbol_collector.collect_symbols_in_node(
            file_root, file_content
        )

        # 3. 정의된 심볼들의 참조 찾기
        references: Dict[str, List[SymbolUsage]] = {}
        reference_lines: Dict[str, List[int]] = {}

        for symbol_name in defined_symbols.keys():
            if symbol_name in file_usages:
                # 컨텍스트 블록 외부에서의 사용만 필터링
                external_usages = self._filter_external_usages(
                    file_usages[symbol_name], context_blocks
                )

                if external_usages:
                    references[symbol_name] = external_usages
                    reference_lines[symbol_name] = [
                        usage.line_number for usage in external_usages
                    ]

        return ReferenceResult(
            defined_symbols=defined_symbols,
            references=references,
            reference_lines=reference_lines
        )

    def _filter_external_usages(
        self,
        usages: List[SymbolUsage],
        context_blocks: List[Node]
    ) -> List[SymbolUsage]:
        """컨텍스트 블록 외부의 사용만 필터링."""
        external_usages = []

        for usage in usages:
            is_external = True

            for block in context_blocks:
                if self._is_node_inside_block(usage.node, block):
                    is_external = False
                    break

            if is_external:
                external_usages.append(usage)

        return external_usages

    def _is_node_inside_block(self, node: Node, block: Node) -> bool:
        """노드가 특정 블록 내부에 있는지 확인."""
        return (
            block.start_point <= node.start_point and
            node.end_point <= block.end_point
        )
```

### 5. 확장된 컨텍스트 추출기 (`enhanced_context_extractor.py`)

```python
"""의존성과 참조 분석을 포함한 확장된 컨텍스트 추출기."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

from tree_sitter import Node

from .dependency_analyzer import DependencyAnalyzer, DependencyResult
from .line_range import LineRange
from .optimized_context_extractor import OptimizedContextExtractor
from .reference_analyzer import ReferenceAnalyzer, ReferenceResult

logger = logging.getLogger(__name__)


@dataclass
class EnhancedExtractionResult:
    """확장된 컨텍스트 추출 결과."""

    primary_contexts: List[str]  # 기본 컨텍스트 블록들
    dependency_contexts: List[str]  # 의존성 블록들
    dependency_result: DependencyResult  # 의존성 분석 결과
    reference_result: ReferenceResult  # 참조 분석 결과


class EnhancedContextExtractor:
    """의존성과 참조 분석을 포함한 확장된 컨텍스트 추출기."""

    def __init__(self, language: str):
        """EnhancedContextExtractor 초기화.

        Args:
            language: 프로그래밍 언어
        """
        self.language = language
        self.base_extractor = OptimizedContextExtractor(language)
        self.dependency_analyzer = DependencyAnalyzer(language)
        self.reference_analyzer = ReferenceAnalyzer(language)

    def extract_enhanced_contexts(
        self,
        file_path: str | Path,
        changed_ranges: Sequence[LineRange],
        include_dependencies: bool = True,
        include_references: bool = True
    ) -> EnhancedExtractionResult:
        """확장된 컨텍스트 추출.

        Args:
            file_path: 분석할 파일 경로
            changed_ranges: 변경된 라인 범위들
            include_dependencies: 의존성 분석 포함 여부
            include_references: 참조 분석 포함 여부

        Returns:
            확장된 컨텍스트 추출 결과
        """
        if not changed_ranges:
            return EnhancedExtractionResult(
                primary_contexts=[],
                dependency_contexts=[],
                dependency_result=DependencyResult({}, {}, set()),
                reference_result=ReferenceResult({}, {}, {})
            )

        # 1. 기본 컨텍스트 추출
        primary_contexts = self.base_extractor.extract_contexts(file_path, changed_ranges)

        # 2. AST 정보 재사용을 위해 파일 다시 파싱
        file_path = Path(file_path)
        code_text = file_path.read_text(encoding="utf-8")
        code_bytes = code_text.encode("utf-8")

        tree = self.base_extractor._parser.parse(code_bytes)
        file_root = tree.root_node

        # 3. 기본 컨텍스트에 해당하는 노드들 찾기
        context_nodes = self._find_context_nodes(file_root, primary_contexts, code_text)

        # 4. 의존성 분석
        dependency_result = DependencyResult({}, {}, set())
        dependency_contexts = []

        if include_dependencies and context_nodes:
            dependency_result = self.dependency_analyzer.analyze_dependencies(
                context_nodes, file_root, code_text
            )

            # 의존성 블록들 추출
            dependency_blocks = self.dependency_analyzer.get_dependency_blocks(
                dependency_result, file_root
            )

            dependency_contexts = [
                block.text.decode('utf-8') for block in dependency_blocks
            ]

        # 5. 참조 분석
        reference_result = ReferenceResult({}, {}, {})

        if include_references and context_nodes:
            reference_result = self.reference_analyzer.analyze_references(
                context_nodes, file_root, code_text
            )

        return EnhancedExtractionResult(
            primary_contexts=primary_contexts,
            dependency_contexts=dependency_contexts,
            dependency_result=dependency_result,
            reference_result=reference_result
        )

    def _find_context_nodes(
        self,
        file_root: Node,
        context_texts: List[str],
        file_content: str
    ) -> List[Node]:
        """컨텍스트 텍스트에 해당하는 노드들을 찾기."""
        context_nodes = []

        def find_matching_nodes(node: Node) -> None:
            try:
                node_text = node.text.decode('utf-8')
                if node_text in context_texts:
                    context_nodes.append(node)
                    return  # 매칭된 노드의 자식은 검사하지 않음
            except UnicodeDecodeError:
                pass

            for child in node.children:
                find_matching_nodes(child)

        find_matching_nodes(file_root)
        return context_nodes

    def format_result(self, result: EnhancedExtractionResult) -> str:
        """추출 결과를 포맷팅하여 반환."""
        output = []

        # 1. 기본 컨텍스트
        output.append("=== Primary Contexts ===")
        for i, context in enumerate(result.primary_contexts, 1):
            output.append(f"\n--- Context Block {i} ---")
            output.append(context)

        # 2. 의존성 컨텍스트
        if result.dependency_contexts:
            output.append("\n\n=== Dependencies ===")
            for i, dep_context in enumerate(result.dependency_contexts, 1):
                output.append(f"\n--- Dependency {i} ---")
                output.append(dep_context)

        # 3. 참조 정보
        if result.reference_result.reference_lines:
            output.append("\n\n=== References ===")
            for symbol, lines in result.reference_result.reference_lines.items():
                output.append(f"\n'{symbol}' 사용 라인: {', '.join(map(str, lines))}")

        # 4. 미해결 의존성
        if result.dependency_result.unresolved_dependencies:
            output.append("\n\n=== Unresolved Dependencies ===")
            for dep in result.dependency_result.unresolved_dependencies:
                output.append(f"- {dep}")

        return "\n".join(output)
```

## 사용 예시

### 기본 사용법

```python
from selvage.src.context_extractor import LineRange, EnhancedContextExtractor

# 확장된 컨텍스트 추출기 생성
extractor = EnhancedContextExtractor("python")

# 변경된 라인 범위 정의
changed_ranges = [LineRange(20, 25), LineRange(50, 55)]

# 확장된 컨텍스트 추출
result = extractor.extract_enhanced_contexts(
    "sample.py",
    changed_ranges,
    include_dependencies=True,
    include_references=True
)

# 결과 출력
print(extractor.format_result(result))

# 개별 정보 접근
print("의존성 블록 수:", len(result.dependency_contexts))
print("참조 정보:", result.reference_result.reference_lines)
```

### 기존 OptimizedContextExtractor와의 호환성

```python
# 기존 방식 (변경 없음)
from selvage.src.context_extractor import OptimizedContextExtractor

extractor = OptimizedContextExtractor("python")
contexts = extractor.extract_contexts("sample.py", changed_ranges)

# 새로운 방식 (기본 컨텍스트만 필요한 경우)
enhanced_extractor = EnhancedContextExtractor("python")
result = enhanced_extractor.extract_enhanced_contexts(
    "sample.py",
    changed_ranges,
    include_dependencies=False,
    include_references=False
)
contexts = result.primary_contexts  # 기존과 동일한 결과
```

## 테스트 계획

### 단위 테스트

1. `SymbolCollector` 테스트

   - 함수/클래스/변수 정의 수집
   - 함수 호출/변수 참조 수집
   - 스코프 분석

2. `DependencyAnalyzer` 테스트

   - 내부/외부 의존성 구분
   - 의존성 해결
   - 순환 의존성 처리

3. `ReferenceAnalyzer` 테스트
   - 참조 위치 정확성
   - 블록 내외부 구분
   - 다양한 참조 타입

### 통합 테스트

```python
def test_comprehensive_extraction():
    """종합적인 추출 테스트."""
    extractor = EnhancedContextExtractor("python")

    # 복잡한 Python 파일로 테스트
    result = extractor.extract_enhanced_contexts(
        "complex_sample.py",
        [LineRange(30, 35)],  # 특정 메서드 수정
        include_dependencies=True,
        include_references=True
    )

    # 검증
    assert len(result.primary_contexts) > 0
    assert len(result.dependency_contexts) > 0
    assert len(result.reference_result.reference_lines) > 0
```

## 성능 고려사항

1. **AST 파싱 최적화**: 파일당 한 번만 파싱하고 재사용
2. **쿼리 캐싱**: tree-sitter 쿼리 결과 캐싱
3. **점진적 분석**: 필요에 따라 의존성/참조 분석 선택적 실행
4. **메모리 관리**: 대용량 파일 처리 시 메모리 사용량 제한

## 확장 가능성

1. **언어 지원 확장**: Java, JavaScript, TypeScript 등
2. **프로젝트 간 의존성**: 다른 파일의 import/export 분석
3. **의미적 분석**: 타입 정보를 활용한 더 정확한 의존성 분석
4. **성능 분석**: 의존성 그래프 기반 성능 영향도 분석
