"""ContextExtractor C 테스트 케이스."""

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
        file_path = Path(__file__).parent / "SampleCalculator.c"
        return file_path.read_text(encoding="utf-8")

    @pytest.fixture
    def extractor(self) -> FallbackContextExtractor:
        """C용 ContextExtractor 인스턴스를 반환합니다."""
        return FallbackContextExtractor()

    def test_extract_single_line_context(
        self,
        extractor: FallbackContextExtractor,
        sample_file_content: str,
    ) -> None:
        """단일 라인 추출 테스트."""
        changed_ranges = [LineRange(35, 35)]  # SampleCalculator 구조체 선언부
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        # 정확한 expected_result 정의
        expected_result = [
            (
                "---- Dependencies/Imports ----\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n"
                "#include <string.h>\n"
                "#include <stdbool.h>\n"
                "#include <math.h>\n"
                "#define MAX_CALCULATION_STEPS 100\n"
                "#define DEFAULT_PRECISION 2\n"
                "#define PI_CONSTANT 3.14159"
            ),
            (
                "---- Context Block 1 (Lines 30-40) ----\n"
                "    char formatted[100];\n"
                "    int count;\n"
                "    int precision;\n"
                "} FormattedResult;\n"
                "\n"
                "typedef struct {\n"
                "    int value;\n"
                "    char history[MAX_CALCULATION_STEPS][100];\n"
                "    int history_count;\n"
                "    char mode[50];\n"
                "} SampleCalculator;"
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
        ]  # SampleCalculator 구조체 선언부 (병합됨: 42-59)
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        # 정확한 expected_result 정의
        expected_result = [
            (
                "---- Dependencies/Imports ----\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n"
                "#include <string.h>\n"
                "#include <stdbool.h>\n"
                "#include <math.h>\n"
                "#define MAX_CALCULATION_STEPS 100\n"
                "#define DEFAULT_PRECISION 2\n"
                "#define PI_CONSTANT 3.14159"
            ),
            (
                "---- Context Block 1 (Lines 42-59) ----\n"
                "// 생성자 함수\n"
                "SampleCalculator* create_sample_calculator(int initial_value) {\n"
                "    /**\n"
                "     * 계산기 초기화\n"
                "     */\n"
                "    SampleCalculator* calc = (SampleCalculator*)malloc("
                "sizeof(SampleCalculator));\n"
                "    calc->value = initial_value;\n"
                "    calc->history_count = 0;\n"
                "    strcpy(calc->mode, CALCULATION_MODES.basic);\n"
                "    return calc;\n"
                "}\n"
                "\n"
                "int add_numbers(SampleCalculator* calc, int a, int b) {\n"
                "    /**\n"
                "     * 두 수를 더하는 메소드\n"
                "     */\n"
                "    \n"
                "    // 내부 함수: 입력값 검증"
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
            LineRange(78, 84),  # 73-89 범위로 확장
            LineRange(100, 122),  # 95-127 범위로 확장
        ]
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        # 정확한 expected_result 정의
        expected_result = [
            # Dependencies/Imports 블럭
            (
                "---- Dependencies/Imports ----\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n"
                "#include <string.h>\n"
                "#include <stdbool.h>\n"
                "#include <math.h>\n"
                "#define MAX_CALCULATION_STEPS 100\n"
                "#define DEFAULT_PRECISION 2\n"
                "#define PI_CONSTANT 3.14159"
            ),
            # Context Block 1 (73-89)
            (
                "---- Context Block 1 (Lines 73-89) ----\n"
                "    if (!validate_inputs(a, b)) {\n"
                '        printf("Error: 입력값이 숫자가 아닙니다\\n");\n'
                "        return -1;\n"
                "    }\n"
                "    \n"
                "    int result = a + b;\n"
                "    calc->value = result;\n"
                "    \n"
                "    char operation[50];\n"
                '    sprintf(operation, "add: %d + %d", a, b);\n'
                "    log_operation(calc, operation, result);\n"
                '    printf("Addition result: %d\\n", result);\n'
                "    \n"
                "    return result;\n"
                "}\n"
                "\n"
                "FormattedResult multiply_and_format(SampleCalculator* calc, "
                "int* numbers, int size) {"
            ),
            # Context Block 2 (95-127)
            (
                "---- Context Block 2 (Lines 95-127) ----\n"
                "    int calculate_product(int* nums, int size) {\n"
                "        if (size == 0) {\n"
                "            return 0;\n"
                "        }\n"
                "        \n"
                "        // 재귀적 곱셈 함수 (중첩 내부 함수)\n"
                "        int multiply_recursive(int* items, int size, int index) {\n"
                "            if (index >= size) {\n"
                "                return 1;\n"
                "            }\n"
                "            return items[index] * multiply_recursive("
                "items, size, index + 1);\n"
                "        }\n"
                "        \n"
                "        return multiply_recursive(nums, size, 0);\n"
                "    }\n"
                "    \n"
                "    // 내부 함수: 결과 포맷팅\n"
                "    FormattedResult format_result(int value, int count) {\n"
                "        FormattedResult result;\n"
                "        result.result = value;\n"
                '        sprintf(result.formatted, "Product: %d", value);\n'
                "        result.count = count;\n"
                "        result.precision = DEFAULT_PRECISION;\n"
                "        return result;\n"
                "    }\n"
                "    \n"
                '    FormattedResult empty_result = {0, "Empty list", '
                "0, DEFAULT_PRECISION};\n"
                "    \n"
                "    if (size == 0) {\n"
                "        return empty_result;\n"
                "    }\n"
                "    \n"
                "    int result = calculate_product(numbers, size);"
            ),
        ]

        # 엄격한 비교
        assert len(contexts) == 3, f"Expected 3 contexts, got {len(contexts)}"
        assert (
            contexts == expected_result
        ), f"Expected exact match:\n{expected_result}\n\nGot:\n{contexts}"

    def test_extract_empty_context(
        self,
        extractor: FallbackContextExtractor,
        sample_file_content: str,
    ) -> None:
        """빈 컨텍스트 추출 테스트."""
        changed_ranges = [
            LineRange(88, 88),
            LineRange(110, 110),
        ]  # SampleCalculator 구조체 선언부
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)
        assert len(contexts) == 0

    def test_extract_context_with_comment(
        self,
        extractor: FallbackContextExtractor,
        sample_file_content: str,
    ) -> None:
        """주석이 포함된 컨텍스트 추출 테스트."""
        changed_ranges = [
            LineRange(94, 94),
            LineRange(100, 100),
        ]  # SampleCalculator 구조체 선언부
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)
        assert len(contexts) == 0
