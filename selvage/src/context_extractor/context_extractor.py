"""ContextExtractor: 최적화된 tree-sitter 기반 컨텍스트 추출기."""

from __future__ import annotations

import logging
from collections.abc import Generator, Sequence
from pathlib import Path

from tree_sitter import Language, Node, Parser


class DeclarationOnlyNode:
    """클래스나 함수의 선언부만을 나타내는 래퍼 노드."""

    def __init__(self, original_node: Node):
        self._original_node = original_node
        self._is_declaration_only = True

    @property
    def start_point(self) -> tuple[int, int]:
        """시작 지점 반환."""
        return self._original_node.start_point

    @property
    def end_point(self) -> tuple[int, int]:
        """끝 지점을 선언부 라인의 끝으로 제한."""
        # 첫 번째 라인의 끝으로 제한
        start_line = self._original_node.start_point[0]
        original_text = self._original_node.text.decode("utf-8")
        first_line = original_text.split("\n")[0]
        return (start_line, len(first_line))

    @property
    def text(self) -> bytes:
        """선언부 텍스트만 반환."""
        original_text = self._original_node.text.decode("utf-8")
        first_line = original_text.split("\n")[0]
        return first_line.encode("utf-8")

    @property
    def type(self) -> str:
        """원본 노드의 타입 반환."""
        return self._original_node.type

    def __getattr__(self, name):
        """다른 속성들은 원본 노드에 위임."""
        return getattr(self._original_node, name)


# tree_sitter_language_pack 대신 tree_sitter_languages 사용
# (selvage 프로젝트에 맞게 조정)
try:
    from tree_sitter_language_pack import get_language, get_parser
except ImportError:
    try:
        import tree_sitter_languages as tsl

        def get_language(language: str) -> Language:
            return tsl.get_language(language)

        def get_parser(language: str) -> Parser:
            return tsl.get_parser(language)
    except ImportError:
        # 기본 fallback
        from tree_sitter import Language, Parser

        def get_language(language: str) -> Language:
            raise ImportError(f"Tree-sitter language '{language}'를 로드할 수 없습니다")

        def get_parser(language: str) -> Parser:
            raise ImportError(f"Tree-sitter parser '{language}'를 로드할 수 없습니다")


from .line_range import LineRange

logger = logging.getLogger(__name__)


class ContextExtractor:
    """최적화된 tree-sitter 기반 컨텍스트 추출기.

    주요 특징:
    - 파일을 한 번만 읽어서 처리
    - node.text로 직접 코드 추출
    - 강화된 타입 안전성과 에러 핸들링
    """

    # 언어별 블록 타입 매핑
    LANGUAGE_BLOCK_TYPES = {
        "python": frozenset(
            {
                "function_definition",
                "async_function_definition",
                "class_definition",
                "module",
                "decorated_definition",
            }
        ),
        "javascript": frozenset(
            {
                "class",
                "class_declaration",
                "function_expression",
                "function_declaration",
                "generator_function",
                "generator_function_declaration",
                "method_definition",
                "arrow_function",
                "program",
            }
        ),
        "typescript": frozenset(
            {
                "class_declaration",
                "function_declaration",
                "function_expression",
                "method_definition",
                "interface_declaration",
                "type_alias_declaration",
                "namespace_declaration",
                "enum_declaration",
                "arrow_function",
                "program",
            }
        ),
        "go": frozenset(
            {
                "function_declaration",
                "method_declaration",
                "type_declaration",
                "source_file",
                "package_clause",
            }
        ),
        "java": frozenset(
            {
                "class_declaration",
                "method_declaration",
                "interface_declaration",
                "enum_declaration",
                "program",
            }
        ),
        "c": frozenset(
            {
                "function_definition",
                "struct_specifier",
                "enum_specifier",
                "translation_unit",
            }
        ),
        "cpp": frozenset(
            {
                "function_definition",
                "class_specifier",
                "struct_specifier",
                "namespace_definition",
                "enum_specifier",
                "translation_unit",
            }
        ),
        "csharp": frozenset(
            {
                "class_declaration",
                "method_declaration",
                "interface_declaration",
                "struct_declaration",
                "enum_declaration",
                "namespace_declaration",
                "compilation_unit",
            }
        ),
        "kotlin": frozenset(
            {
                "class_declaration",
                "function_declaration",
                "object_declaration",
            }
        ),
        "swift": frozenset(
            {
                "class_declaration",
                "protocol_declaration",
                "function_declaration",
                "property_declaration",
                "init_declaration",
                "deinit_declaration",
                "subscript_declaration",
            }
        ),
    }

    def __init__(self, language: str = "python") -> None:
        """추출기 초기화.

        Args:
            language: 지원 언어 (기본값: python)

        Raises:
            ValueError: 지원하지 않는 언어인 경우
        """
        if language not in self.LANGUAGE_BLOCK_TYPES:
            raise ValueError(
                f"지원하지 않는 언어: '{language}'. "
                f"지원 언어: {list(self.LANGUAGE_BLOCK_TYPES.keys())}"
            )

        try:
            self._language: Language = get_language(language)
            self._parser: Parser = get_parser(language)
            self._language_name = language
            self._block_types = self.LANGUAGE_BLOCK_TYPES[language]
        except Exception as e:
            raise ValueError(f"언어 '{language}' 초기화 실패: {e}") from e

    @classmethod
    def get_supported_languages(cls) -> list[str]:
        """지원하는 언어 목록을 반환한다."""
        return list(cls.LANGUAGE_BLOCK_TYPES.keys())

    @classmethod
    def get_block_types_for_language(cls, language: str) -> frozenset[str]:
        """특정 언어의 블록 타입들을 반환한다."""
        return cls.LANGUAGE_BLOCK_TYPES.get(language, frozenset())

    def extract_contexts(
        self, file_path: str | Path, changed_ranges: Sequence[LineRange]
    ) -> list[str]:
        """변경된 라인 범위들을 기반으로 컨텍스트 블록들을 추출한다.

        Args:
            file_path: 분석할 파일 경로
            changed_ranges: 변경된 라인 범위들 (LineRange 객체들)

        Returns:
            추출된 컨텍스트 코드 블록들의 리스트

        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
            ValueError: 파일 인코딩 오류 또는 파싱 오류
        """
        if not changed_ranges:
            return []

        # 1. 파일 읽기 (한 번만)
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        try:
            code_text = file_path.read_text(encoding="utf-8")
            code_bytes = code_text.encode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"파일 인코딩 오류 ({file_path}): {e}") from e

        # 2. AST 파싱
        try:
            tree = self._parser.parse(code_bytes)
            if tree.root_node.has_error:
                logger.warning(f"파싱 경고: {file_path}에서 구문 오류 감지됨")
        except Exception as e:
            raise ValueError(f"파싱 실패 ({file_path}): {e}") from e

        # 3. 변경 범위의 각 라인에 대해 최소 블록들 찾기
        context_blocks: set[Node] = set()
        for changed_range in changed_ranges:
            # 각 LineRange에 대해 최소 노드들 찾기
            minimal_nodes = self._find_minimal_nodes_for_range(
                tree.root_node, changed_range
            )
            for node in minimal_nodes:
                block = self._get_appropriate_context_for_node(node)
                if block is not None:
                    context_blocks.add(block)

        # 4. 포함 관계 중복 블록 제거
        filtered_blocks = self._filter_nested_blocks(context_blocks)

        # 5. 블록들을 위치 순으로 정렬하고 텍스트 추출
        sorted_blocks = sorted(filtered_blocks, key=lambda n: n.start_point)

        contexts = []
        for block in sorted_blocks:
            try:
                block_text = block.text.decode("utf-8")
                contexts.append(block_text)
            except UnicodeDecodeError:
                logger.error(f"블록 텍스트 디코딩 실패: {block.start_point}")
                continue

        return contexts

    # ── Private Helper Methods ──────────────────────────────────────

    def _iter_nodes(self, node: Node) -> Generator[Node, None, None]:
        """DFS 방식으로 모든 노드를 순회한다."""
        yield node
        for child in node.children:
            yield from self._iter_nodes(child)

    def _node_overlaps_line_ranges(
        self, node: Node, ranges: Sequence[LineRange]
    ) -> bool:
        """노드가 지정된 LineRange들 중 하나라도 겹치는지 확인한다.

        LineRange 객체를 사용하여 더 명확하고 안전한 범위 체크를 수행합니다.
        """
        node_start = node.start_point[0] + 1  # 1-based
        node_end = node.end_point[0] + 1  # 1-based

        for line_range in ranges:
            # LineRange의 overlaps 메서드를 활용하여 직관적인 체크
            node_range = LineRange(node_start, node_end)
            if node_range.overlaps(line_range):
                return True

        return False

    def _find_node_by_line(self, root: Node, line_no: int) -> Node:
        """DFS로 해당 라인을 가장 작게 감싸는 노드를 찾는다 (1-based)."""
        for child in root.children:
            if child.start_point[0] + 1 <= line_no <= child.end_point[0] + 1:
                return self._find_node_by_line(child, line_no)
        return root

    def _find_minimal_nodes_for_range(
        self, root: Node, line_range: LineRange
    ) -> set[Node]:
        """LineRange의 각 라인에 대해 가장 작은 노드를 찾아 집합으로 반환"""
        minimal_nodes: set[Node] = set()
        for line_no in range(line_range.start_line, line_range.end_line + 1):
            smallest_node = self._find_node_by_line(root, line_no)
            # module 노드(빈 라인이나 의미 없는 라인)는 제외
            if smallest_node.type != "module":
                minimal_nodes.add(smallest_node)
        return minimal_nodes

    def _find_minimal_enclosing_block(self, node: Node) -> Node | None:
        """현재 노드에서 부모 방향으로 올라가며 가장 가까운 블록을 찾는다.
        module은 제외."""
        current = node
        while current is not None:
            if current.type in self._block_types and current.type != "module":
                return current
            current = current.parent
        # 모든 상위가 module인 경우 원래 노드 반환 (파일 레벨 상수 등)
        return node if node.type != "module" else None

    def _filter_nested_blocks(self, blocks: set[Node]) -> set[Node]:
        """포함 관계에 있는 중복 블록들을 제거하여 가장 큰 블록만 유지한다."""
        if len(blocks) <= 1:
            return blocks

        blocks_list = list(blocks)
        filtered_blocks = set()

        for i, block in enumerate(blocks_list):
            is_contained = False

            # 다른 블록들과 비교하여 포함 관계 확인
            for j, other_block in enumerate(blocks_list):
                if i != j and self._is_node_contained_in(block, other_block):
                    is_contained = True
                    break

            # 다른 블록에 포함되지 않은 블록만 유지
            if not is_contained:
                filtered_blocks.add(block)

        return filtered_blocks

    def _get_appropriate_context_for_node(self, node: Node) -> Node | None:
        """노드 타입에 따라 적절한 컨텍스트 블록을 결정한다."""
        # 파일 레벨 assignment (상수) 처리
        if self._is_file_level_assignment(node):
            return self._handle_assignment_node(node)

        # 모듈 레벨에서 식별자인 경우 assignment 전체 반환
        if node.type == "identifier" and self._is_module_level_node(node):
            return self._handle_assignment_node(node)

        # 클래스 선언부 처리
        if node.type == "class" or self._is_class_declaration_line(node):
            return self._handle_class_declaration(node)

        # 함수 선언부 처리
        if node.type == "function_definition" or self._is_function_declaration_line(
            node
        ):
            return self._handle_function_declaration(node)

        # 일반적인 블록 처리
        return self._find_minimal_enclosing_block(node)

    def _is_file_level_assignment(self, node: Node) -> bool:
        """파일 레벨 assignment인지 확인한다."""
        # 노드에서 상위로 올라가면서 assignment 찾기
        current = node
        while current:
            # assignment이고 그 부모가 module인 경우
            if current.type == "assignment":
                return current.parent and current.parent.type == "module"
            # expression_statement 안의 assignment인 경우
            if current.type == "expression_statement":
                return current.parent and current.parent.type == "module"
            current = current.parent
        return False

    def _is_module_level_node(self, node: Node) -> bool:
        """노드가 모듈 레벨에 있는지 확인한다."""
        # 최대 2-3단계까지만 올라가서 module 찾기
        current = node
        depth = 0
        while current and depth < 3:
            if current.parent and current.parent.type == "module":
                return True
            current = current.parent
            depth += 1
        return False

    def _handle_assignment_node(self, node: Node) -> Node | None:
        """파일 레벨 assignment의 적절한 컨텍스트를 찾는다."""
        # assignment나 expression_statement를 찾아서 반환
        current = node
        while current:
            if current.type in ["assignment", "expression_statement"]:
                return current
            current = current.parent

        # 식별자인 경우, 부모에서 assignment 찾기
        if node.type == "identifier":
            parent = node.parent
            while parent:
                if parent.type in ["assignment", "expression_statement"]:
                    return parent
                parent = parent.parent

        return node

    def _is_class_declaration_line(self, node: Node) -> bool:
        """클래스 선언부 라인인지 확인한다."""
        current = node
        while current:
            if current.type == "class_definition":
                # 클래스 정의의 첫 번째 라인(선언부)인지 확인
                class_start_line = current.start_point[0]
                node_line = node.start_point[0]
                return node_line == class_start_line
            current = current.parent
        return False

    def _is_function_declaration_line(self, node: Node) -> bool:
        """함수 선언부 라인인지 확인한다."""
        current = node
        while current:
            if current.type == "function_definition":
                # 함수 정의의 첫 번째 라인(선언부)인지 확인
                func_start_line = current.start_point[0]
                node_line = node.start_point[0]
                return node_line == func_start_line
            current = current.parent
        return False

    def _handle_class_declaration(self, node: Node) -> Node | None:
        """클래스 선언부의 적절한 컨텍스트를 결정한다."""
        # 클래스 정의를 찾기
        current = node
        class_def_node = None
        while current:
            if current.type == "class_definition":
                class_def_node = current
                break
            current = current.parent

        if class_def_node is None:
            return self._find_minimal_enclosing_block(node)

        # 클래스 선언부 라인인지 확인
        class_start_line = class_def_node.start_point[0]
        node_line = node.start_point[0]

        if node_line == class_start_line:
            # 클래스 선언부만 변경된 경우: 선언부만 추출
            return self._extract_class_declaration_only(class_def_node)
        else:
            # 클래스 내부가 변경된 경우: 전체 클래스 추출
            return class_def_node

    def _extract_class_declaration_only(self, class_def_node: Node) -> Node | None:
        """클래스 선언부만 추출한다 (첫 번째 라인만)."""
        # 클래스 선언부만 포함하는 특별한 래퍼 노드 생성
        return DeclarationOnlyNode(class_def_node)

    def _handle_function_declaration(self, node: Node) -> Node | None:
        """함수 선언부의 적절한 컨텍스트를 결정한다."""
        # 함수 정의를 찾기
        current = node
        func_def_node = None
        while current:
            if current.type == "function_definition":
                func_def_node = current
                break
            current = current.parent

        if func_def_node is None:
            return self._find_minimal_enclosing_block(node)

        # 함수 선언부 라인인지 확인
        func_start_line = func_def_node.start_point[0]
        node_line = node.start_point[0]

        if node_line == func_start_line:
            # 함수 선언부만 변경된 경우: 선언부만 추출
            return DeclarationOnlyNode(func_def_node)
        else:
            # 함수 내부가 변경된 경우: 전체 함수 추출
            return func_def_node

    def _is_node_contained_in(self, inner: Node, outer: Node) -> bool:
        """inner 노드가 outer 노드에 완전히 포함되는지 확인한다."""
        return (
            outer.start_point[0] <= inner.start_point[0]
            and outer.end_point[0] >= inner.end_point[0]
            and
            # 동일한 노드가 아닌 경우만
            (
                outer.start_point != inner.start_point
                or outer.end_point != inner.end_point
            )
        )

    def _find_nearest_block(self, node: Node) -> Node | None:
        """현재 노드에서 부모 방향으로 올라가며 가장 가까운 블록을 찾는다."""
        current = node
        while current is not None:
            if current.type in self._block_types:
                return current
            current = current.parent
        return None
