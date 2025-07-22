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
            # 파일 상수 영역 (라인 7-8: MAX_CALCULATION_STEPS, DEFAULT_PRECISION)
            (
                [LineRange(7, 8)],
                ["module"],  # 파일 상수는 module 블록에 포함
            ),
            # 클래스 선언부 (라인 16: class SampleCalculator)
            (
                [LineRange(16, 16)],
                ["class_definition"],  # SampleCalculator 클래스 전체
            ),
            # 클래스 내부 __init__ 메서드 (라인 18-22)
            (
                [LineRange(20, 21)],
                ["function_definition"],  # __init__ 메서드
            ),
            # 클래스 내부 add_numbers 메서드 (라인 25-42)
            (
                [LineRange(30, 32)],  # validate_inputs 내부 함수 영역
                ["function_definition"],  # add_numbers 메서드 전체
            ),
            # multiply_and_format 메서드의 중첩 내부 함수 (라인 53-58)
            (
                [LineRange(55, 57)],  # multiply_recursive 중첩 내부 함수
                ["function_definition"],  # multiply_and_format 메서드 전체
            ),
            # 클래스 외부 helper_function (라인 94-106)
            (
                [LineRange(98, 100)],  # format_dict_items 내부 함수
                ["function_definition"],  # helper_function 전체
            ),
            # 팩토리 함수의 내부 함수 (라인 115-119)
            (
                [LineRange(116, 118)],  # create_calculator_with_mode 내부 함수
                ["function_definition"],  # advanced_calculator_factory 전체
            ),
            # 모듈 레벨 상수 (라인 130-134)
            (
                [LineRange(131, 132)],
                ["module"],  # MODULE_VERSION, AUTHOR_INFO는 module 블록에 포함
            ),
            # 여러 블록에 걸친 범위 (클래스 메서드 + 외부 함수)
            (
                [
                    LineRange(25, 30),
                    LineRange(95, 98),
                ],  # add_numbers + helper_function 시작
                ["function_definition", "function_definition"],  # 두 함수 모두
            ),
            # 클래스 전체를 포함하는 큰 범위
            (
                [LineRange(16, 91)],  # SampleCalculator 클래스 전체
                ["class_definition"],  # 클래스 전체
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

    def test_extract_contexts_file_constants_specific(
        self, extractor: OptimizedContextExtractor, sample_file_path: Path
    ) -> None:
        """파일 상수 영역을 구체적으로 테스트."""
        # PI_CONSTANT 라인을 타겟팅
        changed_ranges = [LineRange(9, 9)]  # PI_CONSTANT = 3.14159

        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) > 0
        # 모든 파일 레벨 내용이 module 블록으로 추출되어야 함
        assert any("PI_CONSTANT" in context for context in contexts)

    def test_extract_contexts_nested_function_specific(
        self, extractor: OptimizedContextExtractor, sample_file_path: Path
    ) -> None:
        """중첩 내부 함수를 구체적으로 테스트."""
        # multiply_recursive 함수 내부를 타겟팅
        changed_ranges = [LineRange(55, 58)]  # multiply_recursive 함수

        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) > 0
        # multiply_and_format 메서드 전체가 추출되어야 함
        assert any(
            "multiply_and_format" in context and "multiply_recursive" in context
            for context in contexts
        )

    def test_extract_contexts_empty_ranges(
        self, extractor: OptimizedContextExtractor, sample_file_path: Path
    ) -> None:
        """빈 범위 리스트에 대한 테스트."""
        contexts = extractor.extract_contexts(sample_file_path, [])
        assert contexts == []

    def test_extract_contexts_nonexistent_file(
        self, extractor: OptimizedContextExtractor
    ) -> None:
        """존재하지 않는 파일에 대한 테스트."""
        nonexistent_file = Path("nonexistent_file.py")
        changed_ranges = [LineRange(1, 5)]

        with pytest.raises(FileNotFoundError):
            extractor.extract_contexts(nonexistent_file, changed_ranges)

    def test_line_range_functionality(self) -> None:
        """LineRange 클래스의 기능을 테스트."""
        # 기본 생성
        range1 = LineRange(10, 20)
        assert range1.start_line == 10
        assert range1.end_line == 20

        # 겹침 확인
        range2 = LineRange(15, 25)
        assert range1.overlaps(range2)

        range3 = LineRange(25, 30)
        assert not range1.overlaps(range3)

        # 포함 확인
        assert range1.contains(15)
        assert not range1.contains(25)

        # 라인 수
        assert range1.line_count() == 11

    def test_extractor_supported_languages(self) -> None:
        """지원 언어 확인 테스트."""
        languages = OptimizedContextExtractor.get_supported_languages()
        assert "python" in languages
        assert "javascript" in languages
        assert "typescript" in languages

        # Python 블록 타입 확인
        python_blocks = OptimizedContextExtractor.get_block_types_for_language("python")
        assert "function_definition" in python_blocks
        assert "class_definition" in python_blocks

    def test_extractor_unsupported_language(self) -> None:
        """지원하지 않는 언어에 대한 테스트."""
        with pytest.raises(ValueError):
            OptimizedContextExtractor("unsupported_language")
