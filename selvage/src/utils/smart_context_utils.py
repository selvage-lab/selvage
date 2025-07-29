"""Smart Context 관련 유틸리티 클래스"""

from selvage.src.diff_parser.models.file_diff import FileDiff


class SmartContextUtils:
    """Smart Context 적용 여부를 판단하는 유틸리티 클래스"""

    @staticmethod
    def use_smart_context(file_diff: FileDiff) -> bool:
        """smart context 적용 기준을 판단합니다.

        Args:
            file_diff: 파일 차이 정보

        Returns:
            bool: smart context 적용 여부
        """
        total_lines = file_diff.line_count
        total_changes = file_diff.additions + file_diff.deletions

        # 매우 작은 변경(5줄 이하)은 무조건 허용
        if total_changes <= 5:
            return True

        # 30줄 미만 파일은 smart context 미적용
        if total_lines < 30:
            return False

        # 30줄 이상 파일에서 변경 비율이 20% 이하인 경우만 적용
        change_ratio = total_changes / total_lines
        return change_ratio <= 0.2
