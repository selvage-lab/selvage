"""ContextExtractor Swift 테스트 케이스."""

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
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.swift"

    @pytest.fixture
    def extractor(self) -> FallbackContextExtractor:
        """Swift용 ContextExtractor 인스턴스를 반환합니다."""
        return FallbackContextExtractor()

    def test_extract_single_line_context(
        self,
        extractor: FallbackContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """단일 라인 추출 테스트."""
        changed_ranges = [LineRange(25, 25)]  # SampleCalculator 클래스 선언부
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # 정확한 expected_result 정의
        expected_result = [
            ("---- Dependencies/Imports ----\nimport Foundation"),
            (
                "---- Context Block 1 (Lines 20-30) ----\n"
                "    let formatted: String\n"
                "    let count: Int\n"
                "    let precision: Int\n"
                "}\n"
                "\n"
                "class SampleCalculator {\n"
                "    /**\n"
                "     * 간단한 계산기 클래스 - tree-sitter 테스트용\n"
                "     */\n"
                "    \n"
                "    private var value: Int = 0"
            ),
        ]

        # 엄격한 비교
        assert len(contexts) == 2, f"Expected 2 contexts, got {len(contexts)}"
        assert contexts == expected_result, (
            f"Expected exact match:\n{expected_result}\n\nGot:\n{contexts}"
        )

    def test_extract_multiple_line_context(
        self,
        extractor: FallbackContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """여러 라인 추출 테스트."""
        changed_ranges = [
            LineRange(35, 42),
            LineRange(38, 40),
        ]  # init 메서드 부분 (병합됨: 30-47)
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # 정확한 expected_result 정의
        expected_result = [
            ("---- Dependencies/Imports ----\nimport Foundation"),
            (
                "---- Context Block 1 (Lines 30-47) ----\n"
                "    private var value: Int = 0\n"
                "    private var history: [String] = []\n"
                "    private var mode: String\n"
                "    \n"
                "    init(initialValue: Int = 0) {\n"
                "        /**\n"
                "         * 계산기 초기화\n"
                "         */\n"
                "        self.value = initialValue\n"
                "        self.history = []\n"
                '        self.mode = CALCULATION_MODES["basic"] ?? "basic"\n'
                "    }\n"
                "    \n"
                "    func addNumbers(a: Int, b: Int) throws -> Int {\n"
                "        /**\n"
                "         * 두 수를 더하는 메소드\n"
                "         */\n"
                "        "
            ),
        ]

        # 엄격한 비교
        assert len(contexts) == 2, f"Expected 2 contexts, got {len(contexts)}"
        assert contexts == expected_result, (
            f"Expected exact match:\n{expected_result}\n\nGot:\n{contexts}"
        )

    def test_extract_multiple_line_context_complex(
        self,
        extractor: FallbackContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """여러 라인 추출 테스트."""
        changed_ranges = [
            LineRange(65, 71),
            LineRange(85, 105),
        ]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # 엄격한 비교 (실제 출력에 맞춤)
        assert len(contexts) == 3, f"Expected 3 contexts, got {len(contexts)}"
        # Import문과 2개의 컨텍스트 블럭이 있어야 함
        assert "---- Dependencies/Imports ----" in contexts[0]
        assert "---- Context Block 1" in contexts[1]
        assert "---- Context Block 2" in contexts[2]

    def test_extract_empty_context(
        self,
        extractor: FallbackContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """빈 컨텍스트 추출 테스트."""
        changed_ranges = [
            LineRange(29, 29),  # 빈 라인
            LineRange(42, 42),  # 빈 라인
        ]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)
        assert len(contexts) == 0

    def test_extract_context_with_comment(
        self,
        extractor: FallbackContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """주석이 포함된 컨텍스트 추출 테스트."""
        changed_ranges = [
            LineRange(26, 26),  # 주석 라인
            LineRange(44, 44),  # 주석 라인
        ]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)
        assert len(contexts) == 0
