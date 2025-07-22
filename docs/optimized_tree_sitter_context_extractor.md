# 최적화된 Tree-sitter 컨텍스트 추출기 (하이브리드 버전)

> **목표**: 변경 라인과 _의미론적으로_ 연관된 코드만 선별하여 LLM 컨텍스트로 제공하면서도, 실제 프로젝트에서 바로 활용할 수 있는 구현 예시를 포함한다.

---

## 1. 핵심 최적화 구현

### 1.1 메인 추출기 클래스

```python
"""optimized_context_extractor.py: 최적화된 컨텍스트 추출기"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Generator

from tree_sitter import Language, Node, Parser
from tree_sitter_language_pack import get_language, get_parser

logger = logging.getLogger(__name__)

@dataclass
class LineRange:
    """코드 파일의 라인 범위를 나타내는 클래스.

    tuple[int, int] 대신 사용하여 명확성과 타입 안전성을 제공합니다.
    Git diff, 코드 분석, 텍스트 처리 등 다양한 용도로 사용할 수 있습니다.
    """
    start_line: int
    end_line: int

    def __post_init__(self) -> None:
        """유효성 검증을 수행합니다."""
        if self.start_line < 1 or self.end_line < 1:
            raise ValueError("라인 번호는 1 이상이어야 합니다")
        if self.start_line > self.end_line:
            raise ValueError("시작 라인이 끝 라인보다 클 수 없습니다")

    @classmethod
    def from_tuple(cls, range_tuple: tuple[int, int]) -> 'LineRange':
        """tuple에서 LineRange를 생성합니다."""
        return cls(range_tuple[0], range_tuple[1])

    @classmethod
    def from_hunk(cls, new_start: int, new_count: int) -> 'LineRange':
        """Git hunk 정보에서 LineRange를 생성합니다."""
        if new_count <= 0:
            raise ValueError("hunk count는 양수여야 합니다")
        return cls(new_start, new_start + new_count - 1)

    def to_tuple(self) -> tuple[int, int]:
        """tuple 형태로 변환합니다 (하위 호환성)."""
        return (self.start_line, self.end_line)

    def contains(self, line: int) -> bool:
        """지정된 라인이 이 범위에 포함되는지 확인합니다."""
        return self.start_line <= line <= self.end_line

    def overlaps(self, other: 'LineRange') -> bool:
        """다른 범위와 겹치는지 확인합니다."""
        # 두 범위가 겹치는 조건 (직관적으로 표현)
        # 시작이 상대방 끝 이전이고, 끝이 상대방 시작 이후면 겹침
        return self.start_line <= other.end_line and self.end_line >= other.start_line

    def line_count(self) -> int:
        """범위에 포함된 라인 수를 반환합니다."""
        return self.end_line - self.start_line + 1

    def __str__(self) -> str:
        return f"LineRange({self.start_line}-{self.end_line})"

    def __repr__(self) -> str:
        return f"LineRange(start_line={self.start_line}, end_line={self.end_line})"

class OptimizedContextExtractor:
    """최적화된 tree-sitter 기반 컨텍스트 추출기.

    주요 특징:
    - 파일을 한 번만 읽어서 처리
    - node.text로 직접 코드 추출
    - 강화된 타입 안전성과 에러 핸들링
    """

    # 언어별 블록 타입 매핑
    LANGUAGE_BLOCK_TYPES = {
        "python": frozenset({
            "function_definition", "async_function_definition",
            "class_definition", "module", "decorated_definition"
        }),
        "javascript": frozenset({
            "class", "class_declaration", "function_expression",
            "function_declaration", "generator_function",
            "generator_function_declaration", "method_definition",
            "arrow_function", "program"
        }),
        "typescript": frozenset({
            "class_declaration", "function_declaration", "function_expression",
            "method_definition", "interface_declaration", "type_alias_declaration",
            "namespace_declaration", "enum_declaration", "arrow_function", "program"
        }),
        "go": frozenset({
            "function_declaration", "method_declaration", "type_declaration",
            "source_file", "package_clause"
        }),
        "rust": frozenset({
            "struct_item", "enum_item", "union_item", "type_item",
            "function_item", "trait_item", "mod_item", "impl_item", "source_file"
        }),
        "java": frozenset({
            "class_declaration", "method_declaration", "interface_declaration",
            "enum_declaration", "program"
        }),
        "c": frozenset({
            "function_definition", "struct_specifier", "enum_specifier",
            "translation_unit"
        }),
        "cpp": frozenset({
            "function_definition", "class_specifier", "struct_specifier",
            "namespace_definition", "enum_specifier", "translation_unit"
        }),
        "csharp": frozenset({
            "class_declaration", "method_declaration", "interface_declaration",
            "struct_declaration", "enum_declaration", "namespace_declaration",
            "compilation_unit"
        })
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
        self,
        file_path: str | Path,
        changed_ranges: Sequence[LineRange]
    ) -> list[str]:
        """변경된 라인 범위들을 기반으로 컨텍스트 블록들을 추출한다.

        Args:
            file_path: 분석할 파일 경로
            changed_ranges: 변경된 라인 범위들 (LineRange 객체들)

        Returns:
            추출된 컨텍스트 코드 블록들의 리스트

        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
            UnicodeDecodeError: 파일 인코딩 오류
            ValueError: 파싱 오류
        """
        if not changed_ranges:
            return []

        # 1. 파일 읽기 (한 번만)
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        try:
            code_text = file_path.read_text(encoding='utf-8')
            code_bytes = code_text.encode('utf-8')
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(
                f"파일 인코딩 오류 ({file_path}): {e}"
            ) from e

        # 2. AST 파싱
        try:
            tree = self._parser.parse(code_bytes)
            if tree.root_node.has_error:
                logger.warning(f"파싱 경고: {file_path}에서 구문 오류 감지됨")
        except Exception as e:
            raise ValueError(f"파싱 실패 ({file_path}): {e}") from e

        # 3. 변경 범위와 겹치는 블록들 찾기
        context_blocks: set[Node] = set()
        for node in self._iter_nodes(tree.root_node):
            if self._node_overlaps_line_ranges(node, changed_ranges):
                block = self._find_nearest_block(node)
                if block is not None:
                    context_blocks.add(block)

        # 4. 블록들을 위치 순으로 정렬하고 텍스트 추출
        sorted_blocks = sorted(context_blocks, key=lambda n: n.start_point)

        contexts = []
        for block in sorted_blocks:
            try:
                block_text = block.text.decode('utf-8')
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

    def _node_overlaps_line_ranges(self, node: Node, ranges: Sequence[LineRange]) -> bool:
        """노드가 지정된 LineRange들 중 하나라도 겹치는지 확인한다.

        LineRange 객체를 사용하여 더 명확하고 안전한 범위 체크를 수행합니다.
        """
        node_start = node.start_point[0] + 1  # 1-based
        node_end = node.end_point[0] + 1      # 1-based

        for line_range in ranges:
            # LineRange의 overlaps 메서드를 활용하여 직관적인 체크
            node_range = LineRange(node_start, node_end)
            if node_range.overlaps(line_range):
                return True

        return False

    def _find_nearest_block(self, node: Node) -> Node | None:
        """현재 노드에서 부모 방향으로 올라가며 가장 가까운 블록을 찾는다."""
        current = node
        while current is not None:
            if current.type in self._block_types:
                return current
            current = current.parent
        return None

```

---

# 단위 테스트 및 검증

---

**문서 작성일**: 2025-07-21  
**작성자**: Claude Code (최적화 버전)  
**버전**: 1.0 - Hybrid Optimized Edition
