"""LineRange: 코드 파일의 라인 범위를 나타내는 클래스."""

from __future__ import annotations

from dataclasses import dataclass


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
    def from_tuple(cls, range_tuple: tuple[int, int]) -> LineRange:
        """tuple에서 LineRange를 생성합니다."""
        return cls(range_tuple[0], range_tuple[1])

    @classmethod
    def from_hunk(cls, new_start: int, new_count: int) -> LineRange:
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

    def overlaps(self, other: LineRange) -> bool:
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
