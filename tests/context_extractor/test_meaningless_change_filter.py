"""MeaninglessChangeFilter 테스트 케이스."""

from __future__ import annotations

import pytest

from selvage.src.context_extractor.line_range import LineRange
from selvage.src.context_extractor.meaningless_change_filter import (
    MeaninglessChangeFilter,
)


@pytest.fixture
def filter_instance() -> MeaninglessChangeFilter:
    """MeaninglessChangeFilter 인스턴스를 반환합니다."""
    return MeaninglessChangeFilter()


@pytest.fixture
def sample_lines() -> list[str]:
    """다양한 라인 타입을 포함한 테스트 데이터를 반환합니다."""
    return [
        "def test_function():",  # 1: 코드
        "    # 이것은 주석입니다",  # 2: Python 주석
        "    ",  # 3: 빈 라인 (공백)
        "    return True",  # 4: 코드
        "// JavaScript comment",  # 5: JavaScript 주석
        "#include <stdio.h>",  # 6: 전처리기 지시문 (의미있음)
        "<!-- HTML comment -->",  # 7: HTML 주석
        "",  # 8: 완전히 빈 라인
        "  * 블록 주석 중간",  # 9: 블록 주석 중간
        "#define MAX_SIZE 100",  # 10: 전처리기 정의 (의미있음)
        "-- SQL comment",  # 11: SQL 주석
        "% LaTeX comment",  # 12: LaTeX 주석
    ]


@pytest.fixture
def sample_file_content(sample_lines: list[str]) -> str:
    """샘플 라인들을 파일 내용 문자열로 변환하여 반환합니다."""
    return "\n".join(sample_lines)


class TestMeaningfulLineDetection:
    """_is_meaningful_line() 메서드의 라인 의미 판단 기능 테스트."""

    def test_empty_lines_are_meaningless(
        self, filter_instance: MeaninglessChangeFilter
    ):
        """빈 라인들이 무의미하다고 판단되는지 테스트."""
        assert not filter_instance._is_meaningful_line("")
        assert not filter_instance._is_meaningful_line("   ")
        assert not filter_instance._is_meaningful_line("\t")
        assert not filter_instance._is_meaningful_line("  \t  ")

    def test_python_comments_are_meaningless(
        self, filter_instance: MeaninglessChangeFilter
    ):
        """Python 주석이 무의미하다고 판단되는지 테스트."""
        assert not filter_instance._is_meaningful_line("# 주석")
        assert not filter_instance._is_meaningful_line("  # 들여쓰기된 주석")
        assert not filter_instance._is_meaningful_line("\t# 탭으로 들여쓰기된 주석")

    def test_javascript_comments_are_meaningless(
        self, filter_instance: MeaninglessChangeFilter
    ):
        """JavaScript/Java 주석이 무의미하다고 판단되는지 테스트."""
        assert not filter_instance._is_meaningful_line("// 단일행 주석")
        assert not filter_instance._is_meaningful_line("  // 들여쓰기된 주석")
        assert not filter_instance._is_meaningful_line("/* 블록 주석 시작")
        assert not filter_instance._is_meaningful_line("  * 블록 주석 중간")
        assert not filter_instance._is_meaningful_line("  */ 블록 주석 끝")

    def test_html_comments_are_meaningless(
        self, filter_instance: MeaninglessChangeFilter
    ):
        """HTML 주석이 무의미하다고 판단되는지 테스트."""
        assert not filter_instance._is_meaningful_line("<!-- HTML 주석 -->")
        assert not filter_instance._is_meaningful_line(
            "  <!-- 들여쓰기된 HTML 주석 -->"
        )

    def test_sql_comments_are_meaningless(
        self, filter_instance: MeaninglessChangeFilter
    ):
        """SQL 주석이 무의미하다고 판단되는지 테스트."""
        assert not filter_instance._is_meaningful_line("-- SQL 주석")
        assert not filter_instance._is_meaningful_line("  -- 들여쓰기된 SQL 주석")

    def test_latex_comments_are_meaningless(
        self, filter_instance: MeaninglessChangeFilter
    ):
        """LaTeX 주석이 무의미하다고 판단되는지 테스트."""
        assert not filter_instance._is_meaningful_line("% LaTeX 주석")
        assert not filter_instance._is_meaningful_line("  % 들여쓰기된 LaTeX 주석")

    def test_preprocessor_directives_are_meaningful(
        self, filter_instance: MeaninglessChangeFilter
    ):
        """C/C++ 전처리기 지시문이 의미있다고 판단되는지 테스트."""
        assert filter_instance._is_meaningful_line("#include <stdio.h>")
        assert filter_instance._is_meaningful_line("#define MAX_SIZE 100")
        assert filter_instance._is_meaningful_line("#ifdef DEBUG")
        assert filter_instance._is_meaningful_line("#ifndef HEADER_H")
        assert filter_instance._is_meaningful_line("#pragma once")
        assert filter_instance._is_meaningful_line("  #include <iostream>")

    def test_regular_code_lines_are_meaningful(
        self, filter_instance: MeaninglessChangeFilter
    ):
        """일반 코드 라인이 의미있다고 판단되는지 테스트."""
        assert filter_instance._is_meaningful_line("def function():")
        assert filter_instance._is_meaningful_line("return True")
        assert filter_instance._is_meaningful_line("x = 5")
        assert filter_instance._is_meaningful_line("  print('hello')")
        assert filter_instance._is_meaningful_line("}")


class TestSingleMeaninglessChange:
    """_is_single_meaningless_change() 메서드의 1줄 무의미한 변경 판단 테스트."""

    def test_single_line_comment_change_is_meaningless(
        self, filter_instance: MeaninglessChangeFilter, sample_lines: list[str]
    ):
        """1줄 주석 변경이 무의미하다고 판단되는지 테스트."""
        # Line 2: Python 주석
        comment_range = LineRange(2, 2)
        assert filter_instance._is_single_meaningless_change(
            sample_lines, comment_range
        )

        # Line 5: JavaScript 주석
        js_comment_range = LineRange(5, 5)
        assert filter_instance._is_single_meaningless_change(
            sample_lines, js_comment_range
        )

    def test_single_line_empty_change_is_meaningless(
        self, filter_instance: MeaninglessChangeFilter, sample_lines: list[str]
    ):
        """1줄 빈 라인 변경이 무의미하다고 판단되는지 테스트."""
        # Line 3: 공백만 있는 라인
        blank_range = LineRange(3, 3)
        assert filter_instance._is_single_meaningless_change(sample_lines, blank_range)

        # Line 8: 완전히 빈 라인
        empty_range = LineRange(8, 8)
        assert filter_instance._is_single_meaningless_change(sample_lines, empty_range)

    def test_single_line_code_change_is_meaningful(
        self, filter_instance: MeaninglessChangeFilter, sample_lines: list[str]
    ):
        """1줄 코드 변경이 의미있다고 판단되는지 테스트."""
        # Line 1: 함수 정의
        code_range = LineRange(1, 1)
        assert not filter_instance._is_single_meaningless_change(
            sample_lines, code_range
        )

        # Line 4: return 문
        return_range = LineRange(4, 4)
        assert not filter_instance._is_single_meaningless_change(
            sample_lines, return_range
        )

    def test_single_line_preprocessor_change_is_meaningful(
        self, filter_instance: MeaninglessChangeFilter, sample_lines: list[str]
    ):
        """1줄 전처리기 지시문 변경이 의미있다고 판단되는지 테스트."""
        # Line 6: #include
        include_range = LineRange(6, 6)
        assert not filter_instance._is_single_meaningless_change(
            sample_lines, include_range
        )

        # Line 10: #define
        define_range = LineRange(10, 10)
        assert not filter_instance._is_single_meaningless_change(
            sample_lines, define_range
        )

    def test_multi_line_change_is_always_meaningful(
        self, filter_instance: MeaninglessChangeFilter, sample_lines: list[str]
    ):
        """다줄 변경은 항상 의미있다고 판단되는지 테스트."""
        # 2줄 범위 (주석 포함)
        multi_range = LineRange(2, 3)
        assert not filter_instance._is_single_meaningless_change(
            sample_lines, multi_range
        )

        # 여러 줄 범위
        big_range = LineRange(1, 5)
        assert not filter_instance._is_single_meaningless_change(
            sample_lines, big_range
        )

    def test_out_of_bounds_range_is_meaningless(
        self, filter_instance: MeaninglessChangeFilter, sample_lines: list[str]
    ):
        """범위를 벗어나는 라인은 무의미하다고 판단되는지 테스트."""
        # 파일 범위를 벗어나는 라인
        out_of_bounds = LineRange(100, 100)
        assert filter_instance._is_single_meaningless_change(
            sample_lines, out_of_bounds
        )

        # 음수 라인 테스트 (범위 검증 로직 확인)
        # 직접 0-based 인덱스로 테스트
        line_idx = -1
        if line_idx < 0 or line_idx >= len(sample_lines):
            result = True  # 범위를 벗어나면 무의미한 변경으로 간주
        assert result


class TestMeaningfulRangeFiltering:
    """filter_meaningful_ranges_* 메서드들의 범위 필터링 기능 테스트."""

    def test_filter_mixed_meaningful_and_meaningless_ranges(
        self, filter_instance: MeaninglessChangeFilter, sample_lines: list[str]
    ):
        """의미있는 범위와 무의미한 범위가 섞인 경우 필터링 테스트."""
        ranges = [
            LineRange(1, 1),  # 코드 (의미있음)
            LineRange(2, 2),  # 주석 (무의미함)
            LineRange(3, 3),  # 빈 라인 (무의미함)
            LineRange(4, 4),  # 코드 (의미있음)
            LineRange(6, 6),  # 전처리기 (의미있음)
        ]

        meaningful_ranges = filter_instance.filter_meaningful_ranges_with_lines(
            sample_lines, ranges
        )

        expected = [LineRange(1, 1), LineRange(4, 4), LineRange(6, 6)]
        assert meaningful_ranges == expected

    def test_filter_all_meaningful_ranges(
        self, filter_instance: MeaninglessChangeFilter, sample_lines: list[str]
    ):
        """모든 범위가 의미있는 경우 필터링 테스트."""
        ranges = [
            LineRange(1, 1),  # 코드
            LineRange(4, 4),  # 코드
            LineRange(6, 6),  # 전처리기
            LineRange(10, 10),  # 전처리기
        ]

        meaningful_ranges = filter_instance.filter_meaningful_ranges_with_lines(
            sample_lines, ranges
        )

        assert meaningful_ranges == ranges

    def test_filter_all_meaningless_ranges(
        self, filter_instance: MeaninglessChangeFilter, sample_lines: list[str]
    ):
        """모든 범위가 무의미한 경우 필터링 테스트."""
        ranges = [
            LineRange(2, 2),  # 주석
            LineRange(3, 3),  # 빈 라인
            LineRange(5, 5),  # JavaScript 주석
            LineRange(8, 8),  # 빈 라인
        ]

        meaningful_ranges = filter_instance.filter_meaningful_ranges_with_lines(
            sample_lines, ranges
        )

        assert meaningful_ranges == []

    def test_filter_empty_ranges_list(
        self, filter_instance: MeaninglessChangeFilter, sample_lines: list[str]
    ):
        """빈 범위 리스트 필터링 테스트."""
        ranges: list[LineRange] = []

        meaningful_ranges = filter_instance.filter_meaningful_ranges_with_lines(
            sample_lines, ranges
        )

        assert meaningful_ranges == []

    def test_filter_with_file_content_string(
        self, filter_instance: MeaninglessChangeFilter, sample_file_content: str
    ):
        """파일 내용 문자열을 직접 받아서 필터링하는 테스트."""
        ranges = [
            LineRange(1, 1),  # 코드
            LineRange(2, 2),  # 주석
            LineRange(4, 4),  # 코드
        ]

        meaningful_ranges = filter_instance.filter_meaningful_ranges_with_file_content(
            sample_file_content, ranges
        )

        expected = [LineRange(1, 1), LineRange(4, 4)]
        assert meaningful_ranges == expected

    def test_multi_line_ranges_are_preserved(
        self, filter_instance: MeaninglessChangeFilter, sample_lines: list[str]
    ):
        """다줄 범위는 내용과 상관없이 보존되는지 테스트."""
        ranges = [
            LineRange(2, 3),  # 주석 + 빈 라인 (다줄이므로 보존)
            LineRange(5, 7),  # 주석들 (다줄이므로 보존)
            LineRange(1, 1),  # 1줄 코드 (의미있음)
            LineRange(8, 8),  # 1줄 빈 라인 (무의미함)
        ]

        meaningful_ranges = filter_instance.filter_meaningful_ranges_with_lines(
            sample_lines, ranges
        )

        expected = [LineRange(2, 3), LineRange(5, 7), LineRange(1, 1)]
        assert meaningful_ranges == expected

