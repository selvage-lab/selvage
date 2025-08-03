"""무의미한 변경사항을 필터링하는 유틸리티 모듈."""

from __future__ import annotations

import re
from collections.abc import Sequence

from .line_range import LineRange


class MeaninglessChangeFilter:
    """무의미한 변경사항을 필터링하는 유틸리티 클래스.

    1줄짜리 변경이면서 주석이나 빈 라인만 포함하는 경우를 무의미한 변경으로 간주하여
    제거한다.
    """

    def filter_meaningful_ranges_with_file_content(
        self, file_content: str, changed_ranges: Sequence[LineRange]
    ) -> list[LineRange]:
        """의미있는 변경 범위만 필터링하여 반환한다.

        Args:
            lines: 파일의 모든 라인들
            changed_ranges: 변경된 라인 범위들

        Returns:
            의미있는 변경 범위들의 리스트
        """
        lines = file_content.splitlines()
        return self.filter_meaningful_ranges_with_lines(lines, changed_ranges)

    def filter_meaningful_ranges_with_lines(
        self, lines: list[str], changed_ranges: Sequence[LineRange]
    ) -> list[LineRange]:
        """의미있는 변경 범위만 필터링하여 반환한다.

        Args:
            lines: 파일의 모든 라인들
            changed_ranges: 변경된 라인 범위들

        Returns:
            의미있는 변경 범위들의 리스트
        """
        meaningful_ranges = []
        for line_range in changed_ranges:
            if not self._is_single_meaningless_change(lines, line_range):
                meaningful_ranges.append(line_range)
        return meaningful_ranges

    def _is_meaningful_line(self, line: str) -> bool:
        """라인이 의미있는 내용을 포함하는지 확인한다.

        Args:
            line: 검사할 라인

        Returns:
            의미있는 라인 여부 (주석이나 빈 라인이 아닌 경우)
        """
        stripped = line.strip()

        # 빈 라인
        if not stripped:
            return False

        # 다양한 언어의 주석 패턴
        comment_patterns = [
            r"^\s*//",  # C/C++/Java/JavaScript 단일행 주석
            r"^\s*/\*",  # C/C++/Java/JavaScript 블록 주석 시작
            r"^\s*\*",  # C/C++/Java/JavaScript 블록 주석 중간
            r"^\s*\*/",  # C/C++/Java/JavaScript 블록 주석 끝
            r"^\s*#",  # Python/Shell/Ruby 주석 (#include, #define 등은 제외)
            r"^\s*<!--",  # HTML/XML 주석
            r"^\s*--",  # SQL/Lua 주석
            r"^\s*%",  # LaTeX/Matlab 주석
            r'^\s*"',  # VimScript 주석 (문자열과 구분 어려움)
        ]

        for pattern in comment_patterns:
            if re.match(pattern, stripped):
                # #으로 시작하는 경우 전처리기 지시문인지 확인
                if stripped.startswith("#"):
                    # #include, #define 같은 전처리기 지시문은 의미있는 라인
                    preprocessor_patterns = [
                        r"^\s*#(include|define|ifdef|ifndef|if|else|elif|endif)",
                        r"^\s*#(pragma|warning|error|undef|line)",
                    ]
                    for prep_pattern in preprocessor_patterns:
                        if re.match(prep_pattern, stripped):
                            return True
                    # 일반 주석으로 판단
                    return False
                return False

        return True

    def _is_single_meaningless_change(
        self, lines: list[str], line_range: LineRange
    ) -> bool:
        """1줄 변경이 무의미한지 확인한다 (빈 라인 또는 주석만인 경우).

        Args:
            lines: 파일의 모든 라인들
            line_range: 검사할 라인 범위

        Returns:
            1줄 무의미 변경 여부
        """
        # 1줄 변경이 아니면 의미있는 변경으로 간주
        if line_range.start_line != line_range.end_line:
            return False

        # 라인 범위 검증
        line_idx = line_range.start_line - 1  # 0-based 인덱스로 변환
        if line_idx < 0 or line_idx >= len(lines):
            return True  # 범위를 벗어나면 무의미한 변경으로 간주

        # 해당 라인이 의미있는 라인인지 확인
        line = lines[line_idx]
        return not self._is_meaningful_line(line)
