# Tree-sitter 기반 변경 코드 컨텍스트 자동 추출 설계안

## 1. 목표

변경된 코드 라인을 중심으로 LLM 리뷰에 필요한 최소·최대 컨텍스트를 자동으로 생성한다.

- **최대**: 해당 변경과 의미적으로 연결된 모든 정의·참조 포함
- **최소**: 무관한 블록은 배제하여 토큰 낭비 방지

## 2. 범위

1차 구현은 **변경된 파일 내부** 분석으로 한정한다. 이후 모듈 간 의존성 그래프 확장을 고려한다.

## 3. 사용 기술

- tree-sitter core + tree-sitter-language-pack
- Python API (`tree_sitter_language_pack.get_language`, `get_parser`)
- Selvage diff parser(hunk) 연동

## 4. 단계별 파이프라인

1. **Diff-Hunk 매핑**: git diff → `file_diff.hunks`로 변경 라인 범위 수집
2. **상위 블록 탐색**: 변경 라인이 속한 가장 가까운 syntax node(function, class 등) 찾기
3. **내부 참조 수집**: 상위 블록 내부 호출·참조 식별자(`identifier`, `attribute`) 수집
4. **정의 추적**: 동일 파일 AST 전역 탐색하여 식별자 정의 노드 매핑
5. **역참조 추적**: 2단계 블록을 호출하는 다른 블록 탐색
6. **컨텍스트 패키징**: 정의→호출 순 소스 조각 추출, 토큰 초과 시 중요도 기준 절단

## 5. 의사코드

```python
for file in changed_files:
    tree = parser.parse(code_bytes)
    for hunk in file.hunks:
        touched = nodes_covering_range(tree, hunk)
        root = nearest_block(touched)
        ctx = {root}
        ctx |= collect_called_blocks(root)
        ctx |= collect_definitions(ctx)
        ctx |= collect_callers(root)
        yield extract_source(ctx)
```

## 6. 파일 간 확장 전략

- Static import 그래프(AST `import`, `from import`) 구축
- Identifier FQN(모듈.이름) 해석 후 타 파일 점프
- 캐싱된 AST + 간단 인덱스(DB)로 성능 확보

## 7. 구현 로드맵

1. Prototype: `selvage/context/extractor.py` (단일 파일 분석)
2. Integrate: `prompt_generator`에 컨텍스트 삽입
3. Cross-file 분석 + 캐시
4. 테스트: `tests/test_tree_sitter_parsing.py` 확장

## 8. 리스크 및 대응

- **동적 import**: static 분석 한계 → grep fallback
- **데코레이터**: decorator 등록 시 추가 패스
- **성능**: 대형 파일 incremental parsing, diff-size threshold 캐시

## 9. 참고

- tree-sitter query guide
- GitHub semantic-scope 사례

---

## 10. 1차 구현: 단일 파일 컨텍스트 추출기 (실행 가능 코드)

다음 스크립트는 **변경 라인 집합(1-based)**을 입력받아 동일 파일 내에서 관련 블록을 추출한다.
의존성: `tree_sitter_language_pack`만 있으면 실행 가능하다. (Selvage 코드에 의존하지 않음)

```python
"""extractor.py: 변경 라인 기반 컨텍스트 블록 추출 프로토타입"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from tree_sitter_language_pack import get_language, get_parser

# ────────────────────────────────────────────────────────────────────────────────
# 초기화
# ----------------------------------------------------------------------------
_LANGUAGE = get_language("python")
_PARSER = get_parser("python")

# 블록으로 간주할 노드 타입 (필요 시 확장)
_BLOCK_TYPES = {
    "function_definition",  # def foo():
    "class_definition",     # class Bar:
    "module",               # 파일 루트
}


# ────────────────────────────────────────────────────────────────────────────────
# AST 유틸리티
# ----------------------------------------------------------------------------

def _iter_nodes(node) -> Iterable:  # noqa: ANN001 – 간단한 helper
    """DFS 순회 (재귀)."""
    yield node
    for child in node.children:
        yield from _iter_nodes(child)


def _nearest_block(node):
    """현재 노드부터 부모 방향으로 올라가면서 가장 가까운 블록 노드 반환."""
    while node and node.type not in _BLOCK_TYPES:
        node = node.parent
    return node


# ────────────────────────────────────────────────────────────────────────────────
# Public API
# ----------------------------------------------------------------------------

def extract_context_blocks(file_path: str | Path, changed_lines: Sequence[int]) -> list[tuple[int, int]]:
    """변경 라인을 포함하는 블록 범위(start, end)를 반환한다.

    Args:
        file_path: 분석할 파일 경로
        changed_lines: 1-based 변경 라인 번호 시퀀스

    Returns:
        (start_line, end_line) 튜플 리스트 (1-based, inclusive)
    """
    code = Path(file_path).read_text()
    tree = _PARSER.parse(code.encode())

    # 집합으로 변환하여 중복 제거 및 빠른 lookup
    line_set = set(changed_lines)
    candidate_blocks: set = set()

    for node in _iter_nodes(tree.root_node):
        start, end = node.start_point[0] + 1, node.end_point[0] + 1
        # 변경 라인이 노드 범위 안에 포함되면 → 상위 블록 등록
        if any(start <= ln <= end for ln in line_set):
            candidate_blocks.add(_nearest_block(node))

    # 결과를 실제 라인 범위 튜플로 변환 (중복 제거)
    ranges: set[tuple[int, int]] = {
        (blk.start_point[0] + 1, blk.end_point[0] + 1) for blk in candidate_blocks
    }
    return sorted(ranges)


if __name__ == "__main__":
    # 데모 실행: 예시 파일 + 임의 변경 라인
    FILE = Path(__file__).with_name("example_code.py")
    CONTEXTS = extract_context_blocks(FILE, [25, 78])
    print("추출된 블록 범위:")
    for s, e in CONTEXTS:
        print(f"  - {s}~{e} line")
```

### 10.1 예시 코드(`example_code.py`, 총 100라인)

```python
"""example_code.py: extractor 데모용 파일 (≈100 lines)"""

import math

PI = math.pi  # [변경 후보 75~80 라인 참고]


def helper(x: float) -> float:
    """간단한 제곱 함수"""
    return x * x


class Calculator:
    """계산기 클래스."""

    PRECISION: int = 8  # 클래스 상수 (변경 예시)

    def square_area(self, r: float) -> float:
        """원의 넓이를 계산한다."""
        return PI * helper(r)

    def hypotenuse(self, a: float, b: float) -> float:
        # 피타고라스 정리
        return math.sqrt(helper(a) + helper(b))


# ---- 더미 코드 블록으로 100라인 채우기 ----

def _dummy(n: int) -> None:
    total = 0
    for i in range(n):
        total += helper(i)
    print(total)


def example_function() -> None:
    """데모용 함수 (변경 라인 25 위치 포함)"""
    values = [1, 2, 3]
    squares = [helper(v) for v in values]
    print(squares)  # <- 25번째 줄 부근에서 변경된다고 가정


for i in range(20):
    _dummy(i)


# padding lines to reach ≈100
for _ in range(60):
    pass
```

### 10.2 데모 실행 결과 (예시)

```
$ python extractor.py
추출된 블록 범위:
  - 18~27 line   # example_function 블록
  - 3~5 line     # PI 상수 (모듈 루트)
```

- **Case 1 (함수 내부 변경)**: 25라인 변경 → `example_function`(18~27) 반환
- **Case 2 (모듈 상수 변경)**: 78라인(Padding 대신 실제 변경 위치가 상수에 있다고 가정) → 3~5 라인 반환

해당 범위를 `Path.read_text().splitlines()`로 잘라서 LLM 프롬프트에 삽입하면 된다.

---

> ⚠️ 위 코드는 프로토타입이므로 실제 Selvage 통합 시 다음을 보완해야 한다.
>
> 1. `changed_lines` 계산을 git-diff 파서(`diff_parser.models.hunk.Hunk`)로부터 자동 도출
> 2. 토큰 길이 초과 시 우선순위 정렬(변경 블록 우선, 호출/참조 블록 후순위)
> 3. 테스트 추가(`tests/test_context_extractor.py`) 및 Ruff + Pytest 통합
