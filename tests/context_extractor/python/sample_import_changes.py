"""Import 변경 테스트용 샘플 파일 - multiline import 구문 포함."""

import re
from dataclasses import dataclass

from selvage.src.context_extractor.line_range import LineRange
from selvage.src.diff_parser.utils.hunk_line_calculator import HunkLineCalculator


@dataclass
class ImportTestClass:
    """Import 변경 테스트를 위한 클래스."""

    name: str
    value: int = 0

    def process_data(self, data: str) -> str:
        """데이터 처리 메서드."""
        pattern = r"\d+"
        numbers = re.findall(pattern, data)

        line_range = LineRange(1, 10)
        calculator = HunkLineCalculator()

        return f"Processed: {numbers}, Range: {line_range}"


def helper_function() -> str:
    """도우미 함수."""
    return "Helper result"


# 모듈 상수
MODULE_CONSTANT = "test_value"
