"""HunkLineCalculator 클래스 테스트 모듈"""

from selvage.src.diff_parser.utils.hunk_line_calculator import HunkLineCalculator


class TestHunkLineCalculator:
    """HunkLineCalculator.calculate_actual_change_lines 메서드의 동작을 검증하는 테스트 클래스"""

    def test_addition_only_with_context(self):
        """추가만 있는 경우 (unified context 포함)"""
        content = """ context line 1
 context line 2
 context line 3
+new line 1
+new line 2
 context line 4
 context line 5"""
        start_line_modified = 10

        result = HunkLineCalculator.calculate_actual_change_lines(
            content, start_line_modified
        )

        # 컨텍스트 3줄 후 추가된 라인들: 13, 14
        assert result.start_line == 13
        assert result.end_line == 14

    def test_deletion_only_with_context(self):
        """삭제만 있는 경우 (unified context 포함)"""
        content = """ context line 1
 context line 2
-deleted line 1
-deleted line 2
 context line 3
 context line 4"""
        start_line_modified = 5

        result = HunkLineCalculator.calculate_actual_change_lines(
            content, start_line_modified
        )

        # 컨텍스트 2줄 후 삭제된 라인들: 7
        assert result.start_line == 7
        assert result.end_line == 7

    def test_modification_with_context(self):
        """수정 (삭제 + 추가)이 있는 경우"""
        content = """ context line 1
 context line 2
-old line
+new line 1
+new line 2
 context line 3
 context line 4"""
        start_line_modified = 1

        result = HunkLineCalculator.calculate_actual_change_lines(
            content, start_line_modified
        )

        # 컨텍스트 2줄 후: 3번째 라인에서 삭제, 3-4번째 라인에 추가
        assert result.start_line == 3
        assert result.end_line == 4

    def test_multiple_changes_with_context(self):
        """여러 라인 변경이 있는 경우"""
        content = """ context line 1
 context line 2
-deleted line 1
-deleted line 2
+new line 1
+new line 2
+new line 3
 context line 3
 context line 4"""
        start_line_modified = 20

        result = HunkLineCalculator.calculate_actual_change_lines(
            content, start_line_modified
        )

        # 컨텍스트 2줄 후: 22번째 라인에서 삭제 시작, 22-24번째 라인에 추가
        assert result.start_line == 22
        assert result.end_line == 24

    def test_file_start_change(self):
        """파일 시작 부분 변경 (위쪽 컨텍스트 < 5줄)"""
        content = """+new line 1
+new line 2
 context line 1
 context line 2
 context line 3"""
        start_line_modified = 1

        result = HunkLineCalculator.calculate_actual_change_lines(
            content, start_line_modified
        )

        # 파일 시작부터 새 라인 추가: 1, 2
        assert result.start_line == 1
        assert result.end_line == 2

    def test_file_end_change(self):
        """파일 끝 부분 변경 (아래쪽 컨텍스트 < 5줄)"""
        content = """ context line 1
 context line 2
+new line 1
+new line 2"""
        start_line_modified = 10

        result = HunkLineCalculator.calculate_actual_change_lines(
            content, start_line_modified
        )

        # 컨텍스트 2줄 후 추가: 12, 13
        assert result.start_line == 12
        assert result.end_line == 13

    def test_small_file_change(self):
        """작은 파일에서의 변경"""
        content = """-old line
+new line"""
        start_line_modified = 1

        result = HunkLineCalculator.calculate_actual_change_lines(
            content, start_line_modified
        )

        # 1번째 라인 삭제하고 추가: 1
        assert result.start_line == 1
        assert result.end_line == 1
