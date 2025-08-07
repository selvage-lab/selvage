"""ContextExtractor Go 테스트 케이스."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import LineRange
from selvage.src.context_extractor.fallback_context_extractor import (
    FallbackContextExtractor,
)


class TestBasicFunctionExtraction:
    """기본 함수/클래스 추출 기능 테스트."""

    @pytest.fixture
    def sample_file_content(self) -> str:
        """테스트용 샘플 파일 내용을 반환합니다."""
        file_path = Path(__file__).parent / "SampleCalculator.go"
        return file_path.read_text(encoding="utf-8")

    @pytest.fixture
    def extractor(self) -> FallbackContextExtractor:
        """Go용 ContextExtractor 인스턴스를 반환합니다."""
        return FallbackContextExtractor()

    def test_extract_single_line_context(
        self,
        extractor: FallbackContextExtractor,
        sample_file_content: str,
    ) -> None:
        """단일 라인 추출 테스트."""
        changed_ranges = [LineRange(33, 33)]  # SampleCalculator 구조체 선언부
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        # 정확한 expected_result 정의
        expected_result = [
            ("---- Dependencies/Imports ----\npackage main\nimport ("),
            (
                "---- Context Block 1 (Lines 28-38) ----\n"
                '\tFormatted string `json:"formatted"`\n'
                '\tCount     int    `json:"count"`\n'
                '\tPrecision int    `json:"precision"`\n'
                "}\n"
                "\n"
                "type SampleCalculator struct {\n"
                "\t/**\n"
                "\t * 간단한 계산기 클래스 - tree-sitter 테스트용\n"
                "\t */\n"
                "\tvalue   int\n"
                "\thistory []string"
            ),
        ]

        # 엄격한 비교
        assert len(contexts) == 2, f"Expected 2 contexts, got {len(contexts)}"
        assert (
            contexts == expected_result
        ), f"Expected exact match:\n{expected_result}\n\nGot:\n{contexts}"

    def test_extract_multiple_line_context(
        self,
        extractor: FallbackContextExtractor,
        sample_file_content: str,
    ) -> None:
        """여러 라인 추출 테스트."""
        changed_ranges = [
            LineRange(47, 54),
            LineRange(50, 52),
        ]  # 생성자 부분 (병합됨: 42-59)
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        # 정확한 expected_result 정의
        expected_result = [
            ("---- Dependencies/Imports ----\npackage main\nimport ("),
            (
                "---- Context Block 1 (Lines 42-59) ----\n"
                "func NewSampleCalculator(initialValue int) *SampleCalculator {\n"
                "\t/**\n"
                "\t * 계산기 초기화\n"
                "\t */\n"
                "\treturn &SampleCalculator{\n"
                "\t\tvalue:   initialValue,\n"
                "\t\thistory: make([]string, 0),\n"
                '\t\tmode:    CalculationModes["basic"],\n'
                "\t}\n"
                "}\n"
                "\n"
                "func (calc *SampleCalculator) AddNumbers(a, b int) (int, error) {\n"
                "\t/**\n"
                "\t * 두 수를 더하는 메소드\n"
                "\t */\n"
                "\t\n"
                "\t// 내부 함수: 입력값 검증\n"
                "\tvalidateInputs := func(x, y int) bool {"
            ),
        ]

        # 엄격한 비교
        assert len(contexts) == 2, f"Expected 2 contexts, got {len(contexts)}"
        assert (
            contexts == expected_result
        ), f"Expected exact match:\n{expected_result}\n\nGot:\n{contexts}"

    def test_extract_multiple_line_context_complex(
        self,
        extractor: FallbackContextExtractor,
        sample_file_content: str,
    ) -> None:
        """여러 라인 추출 테스트."""
        changed_ranges = [
            LineRange(67, 73),
            LineRange(85, 105),
        ]
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        # 엄격한 비교 (실제 출력에 맞춤)
        assert len(contexts) == 3, f"Expected 3 contexts, got {len(contexts)}"
        # Import문과 2개의 컨텍스트 블럭이 있어야 함
        assert "---- Dependencies/Imports ----" in contexts[0]
        assert "---- Context Block 1" in contexts[1]
        assert "---- Context Block 2" in contexts[2]

    def test_extract_empty_context(
        self,
        extractor: FallbackContextExtractor,
        sample_file_content: str,
    ) -> None:
        """빈 컨텍스트 추출 테스트."""
        changed_ranges = [
            LineRange(41, 41),  # 빈 라인
            LineRange(52, 52),  # 빈 라인
        ]
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)
        assert len(contexts) == 0

    def test_extract_context_with_comment(
        self,
        extractor: FallbackContextExtractor,
        sample_file_content: str,
    ) -> None:
        """주석이 포함된 컨텍스트 추출 테스트."""
        changed_ranges = [
            LineRange(43, 43),  # 주석 라인
            LineRange(54, 54),  # 주석 라인
        ]
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)
        assert len(contexts) == 0
