"""Hunk 라인 계산을 위한 유틸리티 클래스."""

from dataclasses import dataclass
from enum import Enum

from selvage.src.context_extractor.line_range import LineRange


class LineType(Enum):
    """Git diff 라인의 타입을 나타내는 enum."""

    ADDED = "+"
    DELETED = "-"
    CONTEXT = " "


@dataclass
class ChangeTracker:
    """라인 변경 추적을 위한 상태 클래스."""

    current_line: int
    first_change_line: int | None = None
    last_change_line: int | None = None


class HunkLineCalculator:
    """Hunk의 라인 계산과 관련된 유틸리티 메서드들을 제공하는 클래스."""

    @staticmethod
    def calculate_actual_change_lines(
        content: str, start_line_modified: int
    ) -> LineRange:
        """hunk content에서 실제 변경된 라인 범위를 정확히 계산합니다.

        unified context를 고려하여 실제 변경(+, -)이 발생한 라인만 식별합니다.

        Args:
            content: git diff 형식의 hunk 내용 문자열
            start_line_modified: modified 파일에서의 시작 라인 번호

        Returns:
            LineRange: 실제 변경이 발생한 라인 범위
        """
        lines = content.splitlines()
        tracker = ChangeTracker(current_line=start_line_modified)

        for line in lines:
            line_type = HunkLineCalculator._parse_diff_line(line)
            if line_type is None:
                continue

            if line_type == LineType.ADDED:
                HunkLineCalculator._process_added_line(tracker)
            elif line_type == LineType.DELETED:
                HunkLineCalculator._process_deleted_line(tracker)
            elif line_type == LineType.CONTEXT:
                HunkLineCalculator._process_context_line(tracker)

        return HunkLineCalculator._finalize_change_range(tracker, start_line_modified)

    @staticmethod
    def _parse_diff_line(line: str) -> LineType | None:
        """Diff 라인에서 라인 타입을 파싱합니다."""
        if not line:
            return None

        prefix = line[0]
        for line_type in LineType:
            if line_type.value == prefix:
                return line_type
        return None

    @staticmethod
    def _process_added_line(tracker: ChangeTracker) -> None:
        """추가된 라인을 처리합니다."""
        if tracker.first_change_line is None:
            tracker.first_change_line = tracker.current_line
        tracker.last_change_line = tracker.current_line
        tracker.current_line += 1

    @staticmethod
    def _process_deleted_line(tracker: ChangeTracker) -> None:
        """삭제된 라인을 처리합니다."""
        if tracker.first_change_line is None:
            tracker.first_change_line = tracker.current_line
        if (
            tracker.last_change_line is None
            or tracker.current_line > tracker.last_change_line
        ):
            tracker.last_change_line = tracker.current_line

    @staticmethod
    def _process_context_line(tracker: ChangeTracker) -> None:
        """컨텍스트 라인을 처리합니다."""
        tracker.current_line += 1

    @staticmethod
    def _finalize_change_range(
        tracker: ChangeTracker, start_line_modified: int
    ) -> LineRange:
        """최종 변경 범위를 계산합니다."""
        first_change = tracker.first_change_line or max(start_line_modified, 1)
        last_change = tracker.last_change_line or max(start_line_modified, 1)

        return LineRange(
            start_line=max(first_change, 1),
            end_line=max(last_change, first_change, 1),
        )
