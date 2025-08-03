"""ContextExtractor: 최적화된 tree-sitter 기반 컨텍스트 추출기."""

from __future__ import annotations

import logging
import re
from collections.abc import Generator, Sequence

from tree_sitter import Language, Node, Parser
from tree_sitter_language_pack import get_language, get_parser

from selvage.src.exceptions import UnsupportedLanguageError

from .line_range import LineRange
from .meaningless_change_filter import MeaninglessChangeFilter

logger = logging.getLogger(__name__)


class ContextExtractor:
    """최적화된 tree-sitter 기반 컨텍스트 추출기.

    주요 특징:
    - 파일을 한 번만 읽어서 처리
    - node.text로 직접 코드 추출
    - 강화된 타입 안전성과 에러 핸들링
    """

    # 지원 프로그래밍 언어 목록
    SUPPORTED_LANGUAGES = ["python", "javascript", "typescript", "java", "kotlin"]

    # 언어별 블록 타입 매핑
    LANGUAGE_BLOCK_TYPES = {
        "python": frozenset(
            {
                "function_definition",
                "async_function_definition",
                "class_definition",
                "module",
                "decorated_definition",
                "import_from_statement",
                "import_statement",
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
                "import_statement",
                "import_declaration",
                "call_expression",  # require() 호출
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
                "import_statement",
                "import_declaration",
                "import_require_clause",
                "call_expression",  # require() 호출
            }
        ),
        "java": frozenset(
            {
                "class_declaration",
                "method_declaration",
                "interface_declaration",
                "enum_declaration",
                "constructor_declaration",
                "record_declaration",
                "annotation_type_declaration",
                "import_declaration",
                "package_declaration",
                "static_import_declaration",
            }
        ),
        "kotlin": frozenset(
            {
                "class_declaration",
                "function_declaration",
                "object_declaration",
                "interface_declaration",
                "type_alias",
                "companion_object",
                "secondary_constructor",
                "enum_entry",
                "annotation_declaration",
                "init_block",
                "lambda_expression",
                "property_declaration",
                "import_header",
                "package_header",
            }
        ),
    }

    # 언어별 의존성 관련 노드 타입들 (import, require 등)
    LANGUAGE_DEPENDENCY_TYPES = {
        "python": frozenset(
            {
                "import_statement",
                "import_from_statement",
                "future_import_statement",
            }
        ),
        "javascript": frozenset(
            {
                "import_statement",
                "import_declaration",
                "call_expression",  # require() 호출
                "lexical_declaration",  # const, let, var 선언 (require 포함 여부를 동적으로 체크)
                "variable_declaration",  # var 선언
            }
        ),
        "typescript": frozenset(
            {
                "import_statement",
                "import_declaration",
                "import_require_clause",
                "call_expression",  # require() 호출
                "lexical_declaration",  # const, let, var 선언 (require 포함 여부를 동적으로 체크)
                "variable_declaration",  # var 선언
            }
        ),
        "java": frozenset(
            {
                "import_declaration",
                "package_declaration",
                "static_import_declaration",
            }
        ),
        "kotlin": frozenset(
            {
                "import_header",
                "package_header",
                "import_list",
            }
        ),
    }

    # 언어별 루트 노드 타입 매핑
    LANGUAGE_ROOT_TYPES = {
        "python": "module",
        "java": "program",
        "javascript": "program",
        "typescript": "program",
        "kotlin": "source_file",
    }

    def __init__(self, language: str) -> None:
        """추출기 초기화.

        Args:
            language: 지원 언어 (기본값: python)

        Raises:
            UnsupportedLanguageError: 지원하지 않는 언어인 경우
        """
        if language not in self.SUPPORTED_LANGUAGES:
            raise UnsupportedLanguageError(language)

        try:
            self._language: Language = get_language(language)
            self._parser: Parser = get_parser(language)
            self._language_name = language
            self._block_types = self.LANGUAGE_BLOCK_TYPES[language]
            self._dependency_types = self.LANGUAGE_DEPENDENCY_TYPES.get(
                language, frozenset()
            )
            # 무의미한 변경 필터링 객체
            self._filter = MeaninglessChangeFilter()
        except Exception as e:
            raise ValueError(f"언어 '{language}' 초기화 실패: {e}") from e

    @classmethod
    def get_supported_languages(cls) -> list[str]:
        """지원하는 언어 목록을 반환한다."""
        return cls.SUPPORTED_LANGUAGES

    @classmethod
    def get_block_types_for_language(cls, language: str) -> frozenset[str]:
        """특정 언어의 블록 타입들을 반환한다."""
        return cls.LANGUAGE_BLOCK_TYPES.get(language, frozenset())

    def _is_root_node(self, node: Node) -> bool:
        """노드가 루트(전체 파일) 노드인지 확인한다.

        Args:
            node: 확인할 노드

        Returns:
            루트 노드 여부
        """
        root_type = self.LANGUAGE_ROOT_TYPES.get(self._language_name)
        return root_type and node.type == root_type

    def extract_contexts(
        self, file_content: str, changed_ranges: Sequence[LineRange]
    ) -> list[str]:
        """변경된 라인 범위들을 기반으로 컨텍스트 블록들을 추출한다.

        Args:
            file_content: 분석할 파일의 내용
            changed_ranges: 변경된 라인 범위들 (LineRange 객체들)

        Returns:
            추출된 컨텍스트 코드 블록들의 리스트

        Raises:
            ValueError: 파일 내용이 없거나 파싱 오류
        """
        if not changed_ranges:
            return []

        # 1. file_content 인코딩 처리
        try:
            code_bytes = file_content.encode("utf-8")
        except UnicodeEncodeError as e:
            raise ValueError(f"파일 인코딩 오류: {e}") from e

        # 2. 1줄 무의미 변경 필터링
        meaningful_ranges = self._filter.filter_meaningful_ranges_with_file_content(
            file_content, changed_ranges
        )

        # 의미있는 변경이 없으면 빈 결과 반환
        if not meaningful_ranges:
            return []

        # 3. AST 파싱
        try:
            tree = self._parser.parse(code_bytes)
            if tree.root_node.has_error:
                logger.warning("파싱 경고: 구문 오류 감지됨")
        except Exception as e:
            raise ValueError(f"파싱 실패: {e}") from e

        # 4. 변경 범위의 각 라인에 대해 최소 블록들 찾기
        context_blocks: set[Node] = set()
        for changed_range in meaningful_ranges:
            # 각 LineRange에 대해 최소 노드들 찾기
            minimal_nodes = self._find_minimal_nodes_for_range(
                tree.root_node, changed_range
            )
            for node in minimal_nodes:
                block = self._get_appropriate_context_for_node(node)
                if block is not None:
                    context_blocks.add(block)

        # 4. 의존성 노드들 수집
        dependency_nodes = self._collect_dependency_nodes(tree.root_node)

        # 5. 포함 관계 중복 블록 제거
        filtered_blocks = self._filter_nested_blocks(context_blocks)

        # 6. dependency 노드와 겹치는 context 블록 제거
        filtered_blocks = self._remove_context_dependency_overlap(
            filtered_blocks, dependency_nodes
        )

        # 7. 모든 노드들을 합치고 위치 순으로 정렬
        all_nodes = list(filtered_blocks) + dependency_nodes
        sorted_nodes = sorted(all_nodes, key=lambda n: n.start_point)

        # 8. 텍스트 추출 및 포맷팅
        # 의존성 노드들과 컨텍스트 노드들 분리
        contexts = []
        dependency_blocks = []
        context_blocks = []
        for node in sorted_nodes:
            try:
                node_text = node.text.decode("utf-8")

                # 코틀린 import_header 노드인 경우 주석 제거
                node_text = self._clean_kotlin_import(
                    node, node_text, set(dependency_nodes)
                )

                # Python decorated_definition의 원본 파일 직접 추출
                if (
                    self._language_name == "python"
                    and node.type == "decorated_definition"
                ):
                    node_text = self._extract_lines_from_original(node, file_content)

                # 의존성 노드인지 컨텍스트 노드인지 구분
                if self._is_dependency_node(node):
                    dependency_blocks.append(node_text)
                else:
                    context_blocks.append((node_text, node))
            except UnicodeDecodeError:
                logger.error(f"노드 텍스트 디코딩 실패: {node.start_point}")
                continue

        # 의존성 블록 포맷팅
        if dependency_blocks:
            formatted_dependency = self._format_dependency_block(dependency_blocks)
            contexts.append(formatted_dependency)

        # 연속 블록 병합 및 포맷팅
        merged_blocks = self._merge_adjacent_context_blocks(context_blocks)
        for i, (merged_context, start_line, end_line) in enumerate(merged_blocks, 1):
            formatted_context = self._format_context_block(
                merged_context, start_line, end_line, i
            )
            contexts.append(formatted_context)

        return contexts

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
            # 루트 노드(빈 라인이나 의미 없는 라인)는 제외
            if not self._is_root_node(smallest_node):
                minimal_nodes.add(smallest_node)
        return minimal_nodes

    def _find_minimal_enclosing_block(self, node: Node) -> Node | None:
        """현재 노드에서 부모 방향으로 올라가며 가장 가까운 블록을 찾는다.
        데코레이터가 있는 경우 데코레이터를 포함한 전체 정의를 반환한다.
        module은 제외."""
        current = node
        found_block = None

        while current is not None:
            if current.type in self._block_types and not self._is_root_node(current):
                found_block = current

                # 데코레이터가 있는지 확인하기 위해 부모 노드 체크
                if (
                    current.parent
                    and current.parent.type == "decorated_definition"
                    and current.parent.children
                    and current.parent.children[-1] == current
                ):
                    # 현재 블록이 decorated_definition의 마지막 자식인 경우
                    # (즉, 실제 정의 부분인 경우) decorated_definition 반환
                    return current.parent

                return found_block
            current = current.parent

        # 모든 상위가 루트 노드인 경우 원래 노드 반환 (파일 레벨 상수 등)
        return node if not self._is_root_node(node) else None

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

        # 파일 레벨에서 식별자인 경우 assignment 전체 반환
        if node.type == "identifier" and self._is_file_level_node(node):
            return self._handle_assignment_node(node)

        # 일반적인 블록 처리
        return self._find_minimal_enclosing_block(node)

    def _is_file_level_assignment(self, node: Node) -> bool:
        """파일 레벨 assignment인지 확인한다."""
        # 노드에서 상위로 올라가면서 assignment 찾기
        current = node
        while current:
            # assignment이고 그 부모가 루트 노드인 경우
            if current.type == "assignment":
                return current.parent and self._is_root_node(current.parent)
            # expression_statement 안의 assignment인 경우
            if current.type == "expression_statement":
                return current.parent and self._is_root_node(current.parent)
            # JavaScript/TypeScript의 lexical_declaration (const, let, var)인 경우
            if current.type == "lexical_declaration":
                return current.parent and self._is_root_node(current.parent)
            current = current.parent
        return False

    def _is_file_level_node(self, node: Node) -> bool:
        """노드가 파일 레벨에 있는지 확인한다."""
        # 최대 2-3단계까지만 올라가서 module 찾기
        current = node
        depth = 0
        while current and depth < 3:
            if current.parent and self._is_root_node(current.parent):
                return True
            current = current.parent
            depth += 1
        return False

    def _handle_assignment_node(self, node: Node) -> Node | None:
        """파일 레벨 assignment의 적절한 컨텍스트를 찾는다."""
        # assignment나 expression_statement를 찾아서 반환
        current = node
        while current:
            if current.type in [
                "assignment",
                "expression_statement",
                "lexical_declaration",
                "const_declaration",
                "var_declaration",
                "preproc_def",
                "preproc_include",
            ]:
                return current
            current = current.parent

        # 식별자인 경우, 부모에서 assignment 찾기
        if node.type == "identifier":
            parent = node.parent
            while parent:
                if parent.type in [
                    "assignment",
                    "expression_statement",
                    "lexical_declaration",
                    "const_declaration",
                    "var_declaration",
                    "preproc_def",
                    "preproc_include",
                ]:
                    return parent
                parent = parent.parent

        return node

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

    def _collect_dependency_nodes(self, root: Node) -> list[Node]:
        """전체 AST에서 의존성 관련 노드들을 수집한다.

        Args:
            root: AST 루트 노드

        Returns:
            의존성 노드들의 리스트 (위치 순으로 정렬됨)
        """
        if not self._dependency_types:
            return []

        dependency_nodes = []

        for node in self._iter_nodes(root):
            if self._is_dependency_node(node):
                dependency_nodes.append(node)

        # 위치 순으로 정렬
        return sorted(dependency_nodes, key=lambda n: n.start_point)

    def _is_dependency_node(self, node: Node) -> bool:
        """노드가 의존성 관련 노드인지 확인한다.

        Args:
            node: 확인할 노드

        Returns:
            의존성 노드 여부
        """
        if node.type in self._dependency_types:
            # JS/TS의 경우 추가 확인
            if node.type == "call_expression":
                # call_expression은 단독으로는 dependency로 취급하지 않음
                return False
            elif node.type in ("lexical_declaration", "variable_declaration"):
                # lexical_declaration은 require() 호출이 포함된 경우만 dependency
                return self._contains_require_call(node)
            return True
        return False

    def _contains_require_call(self, node: Node) -> bool:
        """lexical_declaration이나 variable_declaration에 require() 호출 포함 여부 확인.

        Args:
            node: lexical_declaration 또는 variable_declaration 노드

        Returns:
            require 호출 포함 여부
        """
        # 정규표현식을 사용한 간단하고 정확한 require() 검출
        try:
            node_text = node.text.decode("utf-8")
            return bool(re.search(r"=\s*require\s*\(", node_text))
        except UnicodeDecodeError:
            return False

    def _remove_context_dependency_overlap(
        self, context_blocks: set[Node], dependency_nodes: list[Node]
    ) -> set[Node]:
        """dependency 노드와 겹치는 context 블록을 제거한다.

        Args:
            context_blocks: 컨텍스트 블록들의 집합
            dependency_nodes: 의존성 노드들의 리스트

        Returns:
            겹치지 않는 컨텍스트 블록들의 집합
        """
        if not dependency_nodes:
            return context_blocks

        filtered_blocks = set()
        dependency_positions = {
            (node.start_point, node.end_point) for node in dependency_nodes
        }

        for context_block in context_blocks:
            context_position = (context_block.start_point, context_block.end_point)
            if context_position not in dependency_positions:
                filtered_blocks.add(context_block)

        return filtered_blocks

    def _clean_kotlin_import(
        self, node: Node, node_text: str, dependency_nodes: set
    ) -> str:
        """코틀린 import_header 노드인 경우 주석 제거 처리.

        Args:
            node: 처리할 노드
            node_text: 노드의 텍스트
            dependency_nodes: 의존성 노드 집합

        Returns:
            처리된 텍스트 (코틀린 import_header인 경우 주석 제거됨)
        """
        if (
            self._language_name == "kotlin"
            and node.type in self._dependency_types
            and node in dependency_nodes
        ):
            return self._clean_import_header(node_text)
        return node_text

    def _clean_import_header(self, text: str) -> str:
        """코틀린 import_header에서 주석 부분 제거.

        \n\n 패턴 이후의 모든 내용을 제거하여 import 문만 남긴다.

        Args:
            text: 정리할 텍스트

        Returns:
            정리된 텍스트 (import 문만 포함)
        """
        double_newline_index = text.find("\n\n")
        if double_newline_index != -1:
            # 첫 번째 빈 줄까지만 포함하고 나머지는 제거
            return text[: double_newline_index + 1].rstrip()
        return text

    def _extract_lines_from_original(self, node: Node, original_code: str) -> str:
        """decorated_definition 노드의 라인을 원본 파일에서 직접 추출한다.

        Args:
            node: decorated_definition 노드
            original_code: 원본 파일의 전체 코드

        Returns:
            원본 파일에서 직접 추출한 텍스트 (들여쓰기 보존)
        """
        # 노드의 라인 범위 추출 (0-based)
        start_line = node.start_point[0]
        end_line = node.end_point[0]

        # 원본 파일에서 해당 라인들 직접 추출
        original_lines = original_code.splitlines()

        # 라인 범위 검증
        if start_line >= len(original_lines) or end_line >= len(original_lines):
            # 범위를 벗어나는 경우 기존 방식 사용
            return node.text.decode("utf-8")

        # 해당 라인 범위 추출 (end_line 포함)
        extracted_lines = original_lines[start_line : end_line + 1]

        return "\n".join(extracted_lines)

    def _format_dependency_block(self, dependency_blocks: list[str]) -> str:
        """의존성 블록들을 하나의 포맷팅된 블록으로 만든다.

        Args:
            dependency_blocks: 의존성 코드 블록들의 리스트

        Returns:
            포맷팅된 의존성 블록
        """
        if not dependency_blocks:
            return ""

        # 모든 dependency 블록을 합치고 줄 단위로 분리
        all_lines = []
        for block in dependency_blocks:
            all_lines.extend(block.split("\n"))

        # 빈 줄과 중복 제거하면서 순서 유지
        unique_lines = []
        seen = set()
        for line in all_lines:
            stripped_line = line.strip()
            if stripped_line and stripped_line not in seen:
                unique_lines.append(line)
                seen.add(stripped_line)

        dependency_content = "\n".join(unique_lines)
        return f"---- Dependencies/Imports ----\n{dependency_content}"

    def _format_context_block(
        self, context: str, start_line: int, end_line: int, block_number: int
    ) -> str:
        """컨텍스트 블록을 구분선과 함께 포맷팅한다.

        Args:
            context: 추출된 컨텍스트 내용
            start_line: 시작 라인 (1-based)
            end_line: 끝 라인 (1-based)
            block_number: 블록 번호

        Returns:
            포맷팅된 컨텍스트 블록
        """
        header = (
            f"---- Context Block {block_number} (Lines {start_line}-{end_line}) ----"
        )
        return f"{header}\n{context}"

    def _merge_adjacent_context_blocks(
        self, context_blocks: list[tuple[str, Node]]
    ) -> list[tuple[str, int, int]]:
        """연속된 1줄짜리 블록들을 병합한다.

        Args:
            context_blocks: (context_text, node) 튜플들의 리스트

        Returns:
            (merged_context, start_line, end_line) 튜플들의 리스트
        """
        if not context_blocks:
            return []

        # 라인 번호 기준으로 정렬
        sorted_blocks = sorted(context_blocks, key=lambda x: x[1].start_point[0])
        merged_blocks = []
        current_group = [sorted_blocks[0]]

        for context_text, node in sorted_blocks[1:]:
            last_node = current_group[-1][1]

            # 현재 노드와 이전 노드의 라인 번호 (1-based)
            current_line = node.start_point[0] + 1
            last_line = last_node.end_point[0] + 1

            # 연속된 1줄짜리 노드인지 확인
            if (
                current_line == last_line + 1  # 연속된 라인
                and (
                    self._is_single_line_node(last_node)
                    or self._is_single_line_node(node)
                )
            ):
                current_group.append((context_text, node))
            else:
                # 현재 그룹을 병합하여 결과에 추가
                merged_blocks.append(self._merge_block_group(current_group))
                current_group = [(context_text, node)]

        # 마지막 그룹 처리
        if current_group:
            merged_blocks.append(self._merge_block_group(current_group))

        return merged_blocks

    def _is_single_line_node(self, node: Node) -> bool:
        """노드가 1줄짜리인지 확인한다.

        Args:
            node: 확인할 노드

        Returns:
            1줄 노드 여부
        """
        return node.start_point[0] == node.end_point[0]

    def _merge_block_group(
        self, block_group: list[tuple[str, Node]]
    ) -> tuple[str, int, int]:
        """블록 그룹을 하나로 병합한다.

        Args:
            block_group: 병합할 블록들의 그룹

        Returns:
            (merged_context, start_line, end_line) 튜플
        """
        if len(block_group) == 1:
            context_text, node = block_group[0]
            start_line = node.start_point[0] + 1  # 1-based
            end_line = node.end_point[0] + 1  # 1-based
            return (context_text, start_line, end_line)

        # 여러 블록을 병합
        merged_contexts = []
        start_line = block_group[0][1].start_point[0] + 1  # 1-based
        end_line = block_group[-1][1].end_point[0] + 1  # 1-based

        for context_text, _ in block_group:
            merged_contexts.append(context_text)

        merged_context = "\n".join(merged_contexts)
        return (merged_context, start_line, end_line)
