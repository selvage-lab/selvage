"""ContextExtractor C 테스트 케이스."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestBasicFunctionExtraction:
    """기본 함수/클래스 추출 기능 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "language_samples" / "c" / "SampleCalculator.c"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """C용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("c")

    def test_class_declaration(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """구조체 선언부 추출 테스트."""
        changed_ranges = [LineRange(35, 35)]  # SampleCalculator 구조체 선언부
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        # #include 문 검증
        assert "#include <stdio.h>" in all_context
        assert "#include <stdlib.h>" in all_context
        assert "#include <string.h>" in all_context
        assert "#include <stdbool.h>" in all_context
        assert "#include <math.h>" in all_context
        assert "SampleCalculator" in all_context

    def test_constructor_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """초기화 함수 추출 테스트."""
        changed_ranges = [LineRange(43, 52)]  # create_sample_calculator 함수
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        # #include 문 검증
        assert "#include <stdio.h>" in all_context
        assert "#include <stdlib.h>" in all_context
        assert "#include <string.h>" in all_context
        assert "#include <stdbool.h>" in all_context
        assert "#include <math.h>" in all_context
        assert "create_sample_calculator" in all_context
        assert "value" in all_context
        assert "history" in all_context

    def test_class_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """함수 추출 테스트."""
        changed_ranges = [LineRange(54, 87)]  # add_numbers 함수
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "add_numbers" in all_context

    def test_complex_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """복잡한 함수 추출 테스트."""
        changed_ranges = [LineRange(89, 135)]  # multiply_and_format 함수
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "multiply_and_format" in all_context

    def test_nested_inner_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """중첩 내부 함수 추출 테스트."""
        changed_ranges = [LineRange(101, 106)]  # multiply_recursive 내부 함수
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "multiply_recursive" in all_context

    def test_external_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """외부 함수 추출 테스트."""
        changed_ranges = [LineRange(156, 179)]  # helper_function
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "helper_function" in all_context

    def test_factory_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """팩토리 함수 추출 테스트."""
        changed_ranges = [LineRange(181, 209)]  # advanced_calculator_factory
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "advanced_calculator_factory" in all_context

    def test_method_declaration_only(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """함수 선언부만 추출 테스트."""
        changed_ranges = [LineRange(54, 54)]  # add_numbers 선언부만
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "add_numbers" in all_context

    def test_external_function_declaration_only(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """외부 함수 선언부만 추출 테스트."""
        changed_ranges = [LineRange(156, 156)]  # helper_function 선언부만
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "helper_function" in all_context


class TestModuleLevelElements:
    """모듈 레벨 요소 추출 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "language_samples" / "c" / "SampleCalculator.c"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """C용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("c")

    def test_basic_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """기본 상수들 추출 테스트."""
        changed_ranges = [LineRange(12, 14)]  # 상수 선언
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "MAX_CALCULATION_STEPS" in all_context
        assert "DEFAULT_PRECISION" in all_context

    def test_object_constant(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """구조체 상수 추출 테스트."""
        changed_ranges = [LineRange(22, 26)]  # CALCULATION_MODES 구조체
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "CALCULATION_MODES" in all_context

    def test_module_bottom_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """모듈 하단 상수들 추출 테스트."""
        changed_ranges = [LineRange(219, 221)]  # MODULE_VERSION
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "MODULE_VERSION" in all_context


class TestMultiRangeExtraction:
    """여러 범위에 걸친 추출 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "language_samples" / "c" / "SampleCalculator.c"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """C용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("c")

    def test_three_cross_functions(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """3개 함수에 걸친 영역 추출 테스트."""
        changed_ranges = [
            LineRange(137, 209)
        ]  # calculate_circle_area ~ advanced_calculator_factory
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "calculate_circle_area" in all_context
        assert "helper_function" in all_context
        assert "advanced_calculator_factory" in all_context

    def test_two_blocks_cross_methods(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """2개 블록에 걸친 함수 추출 테스트."""
        changed_ranges = [LineRange(54, 62), LineRange(156, 165)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 2
        all_context = "\n".join(contexts)
        assert "add_numbers" in all_context
        assert "helper_function" in all_context

    def test_non_contiguous_ranges(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """비연속적인 여러 범위 추출 테스트."""
        changed_ranges = [
            LineRange(12, 14),  # 파일 상수들
            LineRange(143, 145),  # validate_radius 내부 함수
            LineRange(219, 221),  # 모듈 레벨 상수들
        ]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "MAX_CALCULATION_STEPS" in all_context
        assert "MODULE_VERSION" in all_context


class TestComplexScenarios:
    """복잡한 시나리오 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "language_samples" / "c" / "SampleCalculator.c"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """C용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("c")

    def test_entire_class_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """전체 구조체와 관련 함수 추출 테스트."""
        changed_ranges = [LineRange(35, 135)]  # SampleCalculator 전체 구조체와 함수들
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert (
            "struct SampleCalculator" in all_context
            or "SampleCalculator" in all_context
        )
        assert "create_sample_calculator" in all_context
        assert "add_numbers" in all_context

    def test_class_and_module_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """구조체와 모듈 상수 동시 추출 테스트."""
        changed_ranges = [LineRange(12, 221)]  # 상수부터 모듈 끝까지
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "SampleCalculator" in all_context
        assert "MODULE_VERSION" in all_context


class TestEdgeCases:
    """엣지 케이스 및 에러 처리 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "language_samples" / "c" / "SampleCalculator.c"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """C용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("c")

    def test_invalid_line_ranges(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """파일 범위를 벗어나는 라인 범위 테스트."""
        changed_ranges = [LineRange(200, 300)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # 범위를 벗어나더라도 에러가 발생하지 않아야 함
        assert len(contexts) >= 0

    def test_reverse_line_ranges(self) -> None:
        """잘못된 범위 생성 시 예외 발생 테스트."""
        with pytest.raises(ValueError, match="시작 라인이 끝 라인보다 클 수 없습니다"):
            LineRange(50, 30)

    def test_empty_line_ranges(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """빈 라인 범위 처리 테스트."""
        changed_ranges = [LineRange(15, 16)]  # 빈 라인 또는 주석
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # 빈 라인 범위에서도 적절히 처리되어야 함
        assert len(contexts) >= 0
