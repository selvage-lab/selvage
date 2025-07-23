# tree-sitter 기반 동적 컨텍스트 추출 전략 (실행 가능한 코드 버전)

> **목표**: 변경 라인과 _의미론적으로_ 연관된 코드만 선별하여 LLM 컨텍스트로 제공하면서도, 실제 프로젝트에서 바로 활용할 수 있는 구현 예시를 포함한다.

---

## 1. 핵심 개념

1. **Scope 1 – 직접 컨텍스트**: 변경 라인을 포함하는 _가장 가까운_ 함수/메서드/클래스/상수 블록.
2. **Scope 2 – 내부 의존성**: Scope 1 내부에서 호출·참조되는 동일 파일 내 다른 정의.
3. **Scope 3 – 외부 참조** _(확장 과제)_ : Scope 1 을 호출·참조하는 다른 블록 **및** 타 파일 정의.

> 1차 구현 범위는 **동일 파일(Scope 1+2)** 로 한정한다.

---

## 2. 의존 라이브러리 준비

```bash
pip install tree-sitter-language-pack==0.1.0   # 예시 버전
```

`tree_sitter_language_pack` 은 여러 언어용 prebuilt grammar 와 헬퍼 API(`get_language`, `get_parser`)를 제공한다. 이미 `tests/test_tree_sitter_parsing.py` 에서 사용 중이다.

---

## 3. 구현 코드 (Python 예시)

아래 코드는 _실제로 실행 가능한_ 최소 구현이다. **변경 라인 리스트**와 **파일 경로**를 입력하면 Scope 1+2 컨텍스트를 문자열로 반환한다.

```python
# selvage/src/context/context_extractor.py
"""tree-sitter를 이용한 동적 컨텍스트 추출기 (1차 구현)"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, list

from tree_sitter_language_pack import get_language, get_parser
from tree_sitter import Node

# ──────────────────────────────────────────────────────────────
# 유틸 – diff 변경 라인 파싱 (Git diff → line numbers)
# ----------------------------------------------------------------
LINE_RE = re.compile(r"^(\+|\-)?(?P<num>\d+)")

def parse_changed_lines(diff_hunk_text: str) -> list[int]:
    """@@ 블록 내부에서 `+` 표식이 붙은 라인 번호를 추출한다."""
    lines: list[int] = []
    for raw in diff_hunk_text.splitlines():
        if raw.startswith("+") and not raw.startswith("+++"):  # 제외: 파일 헤더
            m = LINE_RE.match(raw[1:])
            if m:
                lines.append(int(m.group("num")))
    return lines

# ----------------------------------------------------------------
# 핵심 – ContextExtractor
# ----------------------------------------------------------------
class ContextExtractor:  # pylint: disable=too-few-public-methods
    """변경 라인을 기반으로 Scope 1,2 컨텍스트를 생성한다."""

    def __init__(self, language_name: str = "python") -> None:
        self.language = get_language(language_name)
        self.parser = get_parser(language_name)

    # ── public ────────────────────────────────────────────────
    def extract(self, file_path: str | Path, changed_lines: Iterable[int]) -> str:
        code_bytes = Path(file_path).read_bytes()
        tree = self.parser.parse(code_bytes)
        root = tree.root_node

        # 1. Scope 1: 각 변경 라인을 포함하는 상위 블록 수집
        scope1_nodes: set[Node] = set()
        for ln in changed_lines:
            node = self._find_node_by_line(root, ln)
            block = self._find_enclosing_block(node)
            if block:
                scope1_nodes.add(block)

        # 2. Scope 2: Scope 1 내부에서 참조되는 정의 수집
        scope2_nodes: set[Node] = set()
        for blk in scope1_nodes:
            scope2_nodes.update(self._find_internal_dependencies(blk, root))

        # 3. 코드 추출 & 정렬
        all_nodes = sorted(
            scope1_nodes.union(scope2_nodes), key=lambda n: n.start_point
        )
        snippets = [self._slice_code(code_bytes, n) for n in all_nodes]
        return "\n\n".join(snippets)

    # ── private helpers ───────────────────────────────────────
    def _find_node_by_line(self, root: Node, line_no: int) -> Node:
        """DFS로 해당 라인을 가장 작게 감싸는 노드를 찾는다 (0-based)."""
        for child in root.children:
            if (child.start_point[0] <= line_no - 1 <= child.end_point[0]):
                return self._find_node_by_line(child, line_no)
        return root

    def _find_enclosing_block(self, node: Node) -> Node | None:
        """함수/클래스/모듈 수준 상수 등의 블록 노드 탐색."""
        block_types = {
            "function_definition",
            "class_definition",
            "module",  # 파일 레벨 상수용
        }
        cur = node
        while cur:
            if cur.type in block_types:
                return cur
            cur = cur.parent  # type: ignore[attr-defined]
        return None

    def _find_internal_dependencies(self, block: Node, root: Node) -> set[Node]:
        """block 내부의 식별자 사용 → 동일 파일 정의 노드 매핑."""
        deps: set[Node] = set()

        # 1) 호출·식별자 캡처 쿼리 준비
        query_src = "(" "identifier" "@id)"
        query = self.language.query(query_src)
        captures = query.captures(block)
        identifiers = {cap[0].text.decode("utf8") for cap in captures}

        # 2) 파일 전체에서 정의 노드 찾기
        def_query_src = (
            "(function_definition name: (identifier) @def) "
            "| (class_definition name: (identifier) @def) "
            "| (assignment left: (identifier) @def)"
        )
        def_query = self.language.query(def_query_src)
        for def_node, _ in def_query.captures(root):
            name = def_node.text.decode("utf8")
            if name in identifiers and not self._is_node_inside(def_node, block):
                deps.add(def_node.parent or def_node)
        return deps

    @staticmethod
    def _is_node_inside(inner: Node, outer: Node) -> bool:  # noqa: ANN001
        return (
            outer.start_byte <= inner.start_byte <= outer.end_byte
            and outer.start_byte <= inner.end_byte <= outer.end_byte
        )

    @staticmethod
    def _slice_code(code: bytes, node: Node) -> str:  # noqa: ANN001
        return code[node.start_byte : node.end_byte].decode("utf8")
```

### 사용 예시

```python
from selvage.src.context.context_extractor import ContextExtractor

# 가정: diff로부터 변경 라인 번호 [10, 11, 12] 확보
extractor = ContextExtractor("python")
context = extractor.extract("path/to/changed_file.py", [10, 11, 12])
print(context)
```

---

## 4. 테스트 (Pytest)

`tests/test_tree_sitter_parsing.py` 의 방식을 재활용해, 실제 컨텍스트 추출 동작을 검증하는 테스트를 추가할 수 있다.

```python
# tests/test_context_extractor.py
from selvage.src.context.context_extractor import ContextExtractor


def test_scope1_extraction(tmp_path):
    sample = tmp_path / "sample.py"
    sample.write_text(
        """
class Foo:
    CONST = 1

    def bar(self):
        return self.CONST

    def baz(self):
        return self.bar()
"""
    )
    # 변경 라인은 bar() 본문의 5번째 줄이라고 가정 (1-based)
    extractor = ContextExtractor()
    ctx = extractor.extract(sample, [5])
    assert "def bar" in ctx  # Scope 1
    assert "CONST = 1" in ctx  # Scope 2 내부 의존성
```

---

## 5. 외부 파일 컨텍스트 (확장 설계 요약)

1. **프로젝트 전역 심볼 인덱스** 구축 → `SymbolIndexer` (SQLite 또는 in-memory).
2. **import 분석**으로 외부 모듈 경로 매핑.
3. 인덱스 조회 후 해당 파일을 `ContextExtractor`에 재귀적으로 적용.

---

## 6. 단계별 구현 일정 (업데이트)

| Phase | 범위                          | 예상 기간 |
| ----- | ----------------------------- | --------- |
| 1     | 동일 파일 Scope 1+2 (위 코드) | 2~3일     |
| 2     | 전역 인덱스 + 외부 파일       | 4~7일     |
| 3     | 성능 최적화 & 다언어 지원     | 지속적    |

---

**문서 작성일**: 2025-07-19  
**작성자**: Claude Code  
**버전**: 2.0
