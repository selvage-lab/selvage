"""ContextExtractor C# 테스트 케이스."""

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
        return Path(__file__).parent / "SampleCalculator.cs"

    @pytest.fixture
    def extractor(self) -> FallbackContextExtractor:
        """C#용 ContextExtractor 인스턴스를 반환합니다."""
        return FallbackContextExtractor()

    def test_extract_single_line_context(
        self,
        extractor: FallbackContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """단일 라인 추출 테스트."""
        changed_ranges = [LineRange(32, 32)]  # SampleCalculator 클래스 선언부
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # 정확한 expected_result 정의
        expected_result = [
            (
                "---- Dependencies/Imports ----\n"
                "using System;\n"
                "using System.Collections.Generic;\n"
                "using System.Linq;"
            ),
            (
                "---- Context Block 1 (Lines 27-37) ----\n"
                "// Fallback context extraction: limited to nearby lines\n"
                "    public string Formatted;\n"
                "    public int Count;\n"
                "    public int Precision;\n"
                "}\n"
                "\n"
                "public class SampleCalculator\n"
                "{\n"
                "    /**\n"
                "     * 간단한 계산기 클래스 - tree-sitter 테스트용\n"
                "     */\n"
                "    "
            )
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
            LineRange(47, 54),
            LineRange(50, 52),
        ]  # 생성자 부분 (병합됨: 42-59)
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # 정확한 expected_result 정의
        expected_result = [
            (
                "---- Dependencies/Imports ----\n"
                "using System;\n"
                "using System.Collections.Generic;\n"
                "using System.Linq;"
            ),
            (
                "---- Context Block 1 (Lines 42-59) ----\n"
                "// Fallback context extraction: limited to nearby lines\n"
                "    public SampleCalculator() : this(0)\n"
                "    {\n"
                "    }\n"
                "    \n"
                "    public SampleCalculator(int initialValue)\n"
                "    {\n"
                "        /**\n"
                "         * 계산기 초기화\n"
                "         */\n"
                "        this.value = initialValue;\n"
                "        this.history = new List<string>();\n"
                "        this.mode = Constants.CALCULATION_MODES[\"basic\"];\n"
                "    }\n"
                "    \n"
                "    public int AddNumbers(int a, int b)\n"
                "    {\n"
                "        /**\n"
                "         * 두 수를 더하는 메소드"
            )
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
            LineRange(84, 90),  # 79-95 범위로 확장
            LineRange(107, 129),  # 102-134 범위로 확장
        ]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # 정확한 expected_result 정의
        expected_result = [
            # Dependencies/Imports 블럭
            (
                "---- Dependencies/Imports ----\n"
                "using System;\n"
                "using System.Collections.Generic;\n"
                "using System.Linq;"
            ),
            # Context Block 1 (79-95)
            (
                "---- Context Block 1 (Lines 79-95) ----\n"
                "// Fallback context extraction: limited to nearby lines\n"
                "        if (!ValidateInputs(a, b))\n"
                "        {\n"
                "            throw new ArgumentException(\"입력값이 숫자가 아닙니다\");\n"
                "        }\n"
                "        \n"
                "        int result = a + b;\n"
                "        value = result;\n"
                "        LogOperation($\"add: {a} + {b}\", result);\n"
                "        Console.WriteLine($\"Addition result: {result}\");\n"
                "        \n"
                "        return result;\n"
                "    }\n"
                "    \n"
                "    public FormattedResult MultiplyAndFormat(List<int> numbers)\n"
                "    {\n"
                "        /**\n"
                "         * 숫자 리스트를 곱하고 결과를 포맷팅하는 메소드"
            ),
            # Context Block 2 (102-134)
            (
                "---- Context Block 2 (Lines 102-134) ----\n"
                "// Fallback context extraction: limited to nearby lines\n"
                "            {\n"
                "                return 0;\n"
                "            }\n"
                "            \n"
                "            // 재귀적 곱셈 함수 (중첩 내부 함수)\n"
                "            int MultiplyRecursive(List<int> items, int index = 0)\n"
                "            {\n"
                "                if (index >= items.Count)\n"
                "                {\n"
                "                    return 1;\n"
                "                }\n"
                "                return items[index] * MultiplyRecursive(items, index + 1);\n"
                "            }\n"
                "            \n"
                "            return MultiplyRecursive(nums);\n"
                "        }\n"
                "        \n"
                "        // 내부 함수: 결과 포맷팅\n"
                "        FormattedResult FormatResult(int value, int count)\n"
                "        {\n"
                "            return new FormattedResult\n"
                "            {\n"
                "                Result = value,\n"
                "                Formatted = $\"Product: {value:N0}\",\n"
                "                Count = count,\n"
                "                Precision = Constants.DEFAULT_PRECISION\n"
                "            };\n"
                "        }\n"
                "        \n"
                "        if (numbers.Count == 0)\n"
                "        {\n"
                "            return new FormattedResult\n"
                "            {"
            )
        ]
        
        # 엄격한 비교
        assert len(contexts) == 3, f"Expected 3 contexts, got {len(contexts)}"
        assert contexts == expected_result, (
            f"Expected exact match:\n{expected_result}\n\nGot:\n{contexts}"
        )

    def test_extract_empty_context(
        self,
        extractor: FallbackContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """빈 컨텍스트 추출 테스트."""
        changed_ranges = [
            LineRange(41, 41),  # 빈 라인
            LineRange(45, 45),  # 빈 라인
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
            LineRange(48, 48),  # 주석 라인
            LineRange(94, 94),  # 주석 라인
        ]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)
        assert len(contexts) == 0
