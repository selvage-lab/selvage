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
            raise ValueError("Line number must be 1 or greater")
        if self.start_line > self.end_line:
            raise ValueError("Start line cannot be greater than end line")

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
