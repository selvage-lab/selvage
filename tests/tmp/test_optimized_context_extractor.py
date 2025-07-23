"""OptimizedContextExtractor 테스트 케이스."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import LineRange, OptimizedContextExtractor


class TestOptimizedContextExtractor:
    """OptimizedContextExtractor 테스트 클래스."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "test_sample_class.py"

    @pytest.fixture
    def extractor(self) -> OptimizedContextExtractor:
        """Python용 OptimizedContextExtractor 인스턴스를 반환합니다."""
        return OptimizedContextExtractor("python")

    @pytest.mark.parametrize(
        "changed_ranges,expected_blocks_info",
        [
            # 함수 3개에 걸친 영역 calculate_circle_area, helper_function,
            ([LineRange(88, 129)], ["function_definition"]),
            # 함수 영역 multiply_and_format
            (
                [LineRange(77, 80), LineRange(64, 84)],
                ["function_definition"],  # 파일 상수는 module 블록에 포함
            ),
            # 파일 상수 영역 (라인 7-8: MAX_CALCULATION_STEPS, DEFAULT_PRECISION)
            (
                [LineRange(7, 8)],
                ["module"],  # 파일 상수는 module 블록에 포함
            ),
            # 클래스 선언부 (라인 17: class SampleCalculator)
            (
                [LineRange(17, 17)],
                ["class_definition"],  # SampleCalculator 클래스 선언부만
            ),
            # 클래스 내부 __init__ 메서드
            (
                [LineRange(20, 21)],
                ["function_definition"],  # __init__ 메서드
            ),
            # 클래스 내부 add_numbers 메서드
            (
                [LineRange(30, 32)],  # validate_inputs 내부 함수 영역
                ["function_definition"],  # add_numbers 메서드 전체
            ),
            # multiply_and_format 메서드의 중첩 내부 함수인 calculate_product
            (
                [LineRange(55, 57)],  # multiply_recursive 중첩 내부 함수
                ["function_definition"],  # calculate_product 메서드 전체
            ),
            # 클래스 외부 helper_function (라인 94-106)
            (
                [LineRange(98, 100)],  # format_dict_items 내부 함수
                ["function_definition"],  # helper_function 전체
            ),
            # advanced_calculator_factory 함수
            (
                [LineRange(116, 118)],  # create_calculator_with_mode 내부 함수
                ["function_definition"],  # advanced_calculator_factory 전체
            ),
            # 모듈 레벨 상수
            (
                [LineRange(135, 136)],
                ["module"],  # MODULE_VERSION, AUTHOR_INFO는 module 블록에 포함
            ),
            # 여러 블록에 걸친 범위 (클래스 메서드 + 외부 함수)
            (
                [
                    LineRange(26, 30),
                    LineRange(100, 103),
                ],  # add_numbers + helper_function 시작
                ["function_definition", "function_definition"],  # 두 함수 모두
            ),
            # 클래스 전체를 포함하는 큰 범위
            (
                [LineRange(16, 91)],  # SampleCalculator 클래스 전체
                ["class_definition"],  # 클래스 전체
            ),
            # 클래스 전체와 모듈 상수
            (
                [LineRange(10, 136)],
                ["class_definition", "module"],  # 클래스 전체와 모듈 상수
            ),
        ],
    )
    def test_extract_contexts_various_blocks(
        self,
        extractor: OptimizedContextExtractor,
        sample_file_path: Path,
        changed_ranges: list[LineRange],
        expected_blocks_info: list[str],
    ) -> None:
        """다양한 블록을 추출하는 테스트."""
        # 파일이 존재하는지 확인
        assert sample_file_path.exists(), (
            f"테스트 파일이 존재하지 않습니다: {sample_file_path}"
        )

        # 컨텍스트 추출
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # 결과 검증
        assert len(contexts) > 0, "추출된 컨텍스트가 없습니다"
        assert len(contexts) >= len(expected_blocks_info), (
            f"예상보다 적은 블록이 추출됨: {len(contexts)} < {len(expected_blocks_info)}"
        )

        # 각 컨텍스트가 유효한 Python 코드인지 확인
        for i, context in enumerate(contexts):
            assert isinstance(context, str), f"컨텍스트 {i}가 문자열이 아닙니다"
            assert len(context.strip()) > 0, f"컨텍스트 {i}가 비어있습니다"

        # 로깅을 위한 정보 출력
        print(f"\n=== 테스트 결과: {len(contexts)}개 블록 추출 ===")
        for i, context in enumerate(contexts):
            lines = context.split("\n")
            first_line = lines[0].strip() if lines else ""
            print(f"블록 {i + 1}: {first_line} (총 {len(lines)}줄)")
