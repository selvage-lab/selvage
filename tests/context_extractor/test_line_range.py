import pytest

from selvage.src.context_extractor import LineRange


class TestLineRange:
    """LineRange 클래스의 기본 기능을 테스트한다."""

    def test_valid_line_range_creation(self):
        """유효한 LineRange 객체 생성을 테스트한다."""
        line_range = LineRange(1, 5)
        assert line_range.start_line == 1
        assert line_range.end_line == 5
        assert line_range.line_count() == 5

    def test_invalid_line_range_creation(self):
        """잘못된 LineRange 객체 생성 시 예외 발생을 테스트한다."""
        with pytest.raises(ValueError, match="Line number must be 1 or greater"):
            LineRange(0, 5)

        with pytest.raises(ValueError, match="Start line cannot be greater than end line"):
            LineRange(5, 3)

    def test_overlaps_detection(self):
        """두 LineRange 간의 겹침 감지를 테스트한다."""
        range1 = LineRange(1, 5)
        range2 = LineRange(3, 8)  # 겹침
        range3 = LineRange(6, 10)  # 겹치지 않음
        range4 = LineRange(5, 7)  # 경계에서 겹침

        assert range1.overlaps(range2) == True
        assert range1.overlaps(range3) == False
        assert range1.overlaps(range4) == True
        assert range2.overlaps(range1) == True  # 대칭성

    def test_contains_line(self):
        """특정 라인이 범위에 포함되는지 테스트한다."""
        line_range = LineRange(5, 10)

        assert line_range.contains(5) == True  # 시작 라인
        assert line_range.contains(10) == True  # 끝 라인
        assert line_range.contains(7) == True  # 중간 라인
        assert line_range.contains(4) == False  # 범위 밖 (이전)
        assert line_range.contains(11) == False  # 범위 밖 (이후)
