"""ContextExtractor TypeScript 테스트 케이스."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestBasicFunctionExtraction:
    """기본 함수/클래스 추출 기능 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.ts"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """TypeScript용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("typescript")

    def test_class_declaration(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스 선언부 추출 테스트."""
        changed_ranges = [LineRange(31, 31)]  # SampleCalculator 클래스 선언부
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        # import 문 검증
        assert "import * as fs from 'fs'" in all_context
        assert "import { join, resolve } from 'path'" in all_context
        assert "import { promisify } from 'util'" in all_context
        assert "class SampleCalculator" in all_context

    def test_constructor_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """생성자 메서드 추출 테스트."""
        changed_ranges = [
            LineRange(41, 46)
        ]  # constructor 메서드 (import 문 추가로 3줄 증가)
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        # import 문 검증
        assert "import * as fs from 'fs'" in all_context
        assert "import { join, resolve } from 'path'" in all_context
        assert "import { promisify } from 'util'" in all_context
        assert "class SampleCalculator" in all_context
        assert "constructor(" in all_context
        assert (
            "this.value = initialValue" in all_context
            or "this.value: number" in all_context
        )
        assert "this.history" in all_context

    def test_class_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스 메서드 추출 테스트."""
        changed_ranges = [LineRange(49, 72)]  # addNumbers 메서드
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "addNumbers" in all_context
        assert "number" in all_context  # TypeScript 타입 시스템

    def test_complex_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """복잡한 메서드 추출 테스트."""
        changed_ranges = [LineRange(79, 117)]  # multiplyAndFormat 메서드
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "multiplyAndFormat" in all_context

    def test_nested_inner_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """중첩 내부 함수 추출 테스트."""
        changed_ranges = [LineRange(90, 95)]  # multiplyRecursive 내부 함수
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "multiplyAndFormat" in all_context
        assert "multiplyRecursive" in all_context or "function" in all_context

    def test_external_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스 외부 함수 추출 테스트."""
        changed_ranges = [LineRange(142, 148)]  # helperFunction
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "function helperFunction" in all_context

    def test_factory_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """팩토리 함수 추출 테스트."""
        changed_ranges = [LineRange(160, 174)]  # advancedCalculatorFactory
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "advancedCalculatorFactory" in all_context

    def test_method_declaration_only(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """메서드 선언부만 추출 테스트."""
        changed_ranges = [
            LineRange(49, 49)
        ]  # addNumbers 선언부만 (import 문 추가로 3줄 증가)
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "addNumbers" in all_context

    def test_external_function_declaration_only(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """외부 함수 선언부만 추출 테스트."""
        changed_ranges = [LineRange(142, 142)]  # helperFunction 선언부만
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "helperFunction" in all_context


class TestModuleLevelElements:
    """모듈 레벨 요소 추출 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.ts"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """TypeScript용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("typescript")

    def test_basic_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """기본 상수들 추출 테스트."""
        changed_ranges = [LineRange(10, 11)]  # 상수 선언
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
        """객체 상수 추출 테스트."""
        changed_ranges = [LineRange(18, 21)]  # CALCULATION_MODES 객체
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
        changed_ranges = [
            LineRange(187, 187)
        ]  # MODULE_VERSION (import 문 추가로 3줄 증가)
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "MODULE_VERSION" in all_context


class TestMultiRangeExtraction:
    """여러 범위에 걸친 추출 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.ts"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """TypeScript용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("typescript")

    def test_three_cross_functions(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """3개 함수에 걸친 영역 추출 테스트."""
        changed_ranges = [
            LineRange(123, 174)
        ]  # calculateCircleArea ~ advancedCalculatorFactory
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "calculateCircleArea" in all_context
        assert "helperFunction" in all_context
        assert "advancedCalculatorFactory" in all_context

    def test_two_blocks_cross_methods(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """2개 블록에 걸친 메서드 추출 테스트."""
        changed_ranges = [LineRange(49, 53), LineRange(142, 157)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 2
        all_context = "\n".join(contexts)
        assert "addNumbers" in all_context
        assert "helperFunction" in all_context

    def test_non_contiguous_ranges(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """비연속적인 여러 범위 추출 테스트."""
        changed_ranges = [
            LineRange(10, 11),  # 파일 상수들
            LineRange(129, 131),  # validateRadius 내부 함수
            LineRange(187, 187),  # 모듈 레벨 상수들
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
        return Path(__file__).parent / "SampleCalculator.ts"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """TypeScript용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("typescript")

    def test_entire_class_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """전체 클래스 추출 테스트."""
        changed_ranges = [LineRange(31, 140)]  # SampleCalculator 전체 클래스
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "class SampleCalculator" in all_context
        assert "constructor" in all_context
        assert "addNumbers" in all_context

    def test_class_and_module_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스와 모듈 상수 동시 추출 테스트."""
        changed_ranges = [LineRange(10, 193)]  # 상수부터 모듈 끝까지
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "class SampleCalculator" in all_context
        assert "MODULE_VERSION" in all_context


class TestEdgeCases:
    """엣지 케이스 및 에러 처리 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.ts"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """TypeScript용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("typescript")

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
        changed_ranges = [LineRange(34, 35)]  # 빈 라인 또는 주석
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # 빈 라인 범위에서도 적절히 처리되어야 함
        assert len(contexts) >= 0
