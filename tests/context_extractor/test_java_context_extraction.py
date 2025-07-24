"""ContextExtractor Java 테스트 케이스."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestBasicFunctionExtraction:
    """기본 함수/클래스 추출 기능 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return (
            Path(__file__).parent
            / "language_samples"
            / "java"
            / "SampleCalculator.java"
        )

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Java용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("java")

    def test_class_declaration(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스 선언부 추출 테스트."""
        changed_ranges = [LineRange(20, 20)]  # SampleCalculator 클래스 선언부
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        # 클래스 검증 (Java는 전체 클래스가 추출됨)
        assert "public class SampleCalculator" in all_context
        # Java에서는 클래스 전체가 추출되므로 내부 요소들도 포함됨
        assert "private int value" in all_context

    def test_constructor_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """생성자 메서드 추출 테스트."""
        changed_ranges = [LineRange(33, 40)]  # 파라미터 있는 생성자
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        # 선언부 검증
        assert "public SampleCalculator(int initialValue)" in all_context
        # 내부 코드 블록 검증 (전체 메서드 추출 확인)
        assert "this.value = initialValue" in all_context
        assert "this.history = new ArrayList<>()" in all_context
        assert 'this.mode = Constants.CALCULATION_MODES.get("basic")' in all_context

    def test_class_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스 메서드 추출 테스트."""
        changed_ranges = [LineRange(42, 44)]  # addNumbers 메서드
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        # 선언부 검증
        assert "public int addNumbers(int a, int b)" in all_context
        # 내부 코드 블록 검증 (전체 메서드 추출 확인)
        assert "class InputValidator" in all_context
        assert "class OperationLogger" in all_context
        assert "int result = a + b" in all_context

    def test_complex_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """복잡한 메서드 추출 테스트."""
        changed_ranges = [
            LineRange(75, 78),
            LineRange(120, 125),
        ]  # multiplyAndFormat 메서드
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        # 선언부 검증
        assert (
            "public Map<String, Object> multiplyAndFormat(List<Integer> numbers)"
            in all_context
        )
        # 내부 코드 블록 검증 (전체 메서드 추출 확인)
        assert "class ProductCalculator" in all_context
        assert "class ResultFormatter" in all_context
        assert "class RecursiveMultiplier" in all_context

    def test_nested_inner_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """중첩 내부 함수 추출 테스트."""
        changed_ranges = [LineRange(87, 95)]  # RecursiveMultiplier 내부 클래스
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        # 선언부 검증
        assert (
            "class ProductCalculator" in all_context
            or "class RecursiveMultiplier" in all_context
        )
        # 내부 코드 블록 검증 (전체 함수 추출 확인)
        assert "public int multiplyRecursive" in all_context
        assert "if (index >= items.size())" in all_context

    def test_external_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스 외부 함수 추출 테스트."""
        changed_ranges = [LineRange(155, 160)]  # helperFunction 내부 코드 범위
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        # 선언부 검증
        assert "public static String helperFunction" in all_context
        # 내부 코드 블록 검증 (전체 함수 추출 확인)
        assert "class DictFormatter" in all_context
        assert "List<String> formattedItems" in all_context

    def test_factory_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """팩토리 함수 추출 테스트."""
        changed_ranges = [LineRange(182, 190)]  # advancedCalculatorFactory 메서드
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        # 선언부 검증
        assert (
            "public static SampleCalculator advancedCalculatorFactory(String mode)"
            in all_context
        )
        # 내부 코드 블록 검증 (전체 함수 추출 확인)
        assert "class CalculatorCreator" in all_context
        assert "class ModeValidator" in all_context

    def test_method_declaration_only(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """메서드 선언부만 추출 테스트."""
        changed_ranges = [LineRange(42, 42)]  # addNumbers 선언부만
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "public int addNumbers(int a, int b)" in all_context
        # Java에서는 메서드 전체가 추출되므로 내부 클래스도 포함됨
        assert "class InputValidator" in all_context

    def test_external_function_declaration_only(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """외부 함수 선언부만 추출 테스트."""
        changed_ranges = [LineRange(155, 155)]  # helperFunction 선언부만
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "public static String helperFunction" in all_context
        # Java에서는 메서드 전체가 추출되므로 내부 클래스도 포함됨
        assert "class DictFormatter" in all_context


class TestModuleLevelElements:
    """모듈 레벨 요소 추출 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return (
            Path(__file__).parent
            / "language_samples"
            / "java"
            / "SampleCalculator.java"
        )

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Java용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("java")

    def test_basic_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """기본 상수들 추출 테스트."""
        changed_ranges = [LineRange(9, 10)]  # Constants 클래스 내 상수들
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "MAX_CALCULATION_STEPS = 100" in all_context
        assert "DEFAULT_PRECISION = 2" in all_context

    def test_map_constant(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """맵 상수 추출 테스트."""
        changed_ranges = [LineRange(12, 16)]  # CALCULATION_MODES 맵
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "CALCULATION_MODES = Map.of(" in all_context

    def test_module_bottom_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """모듈 하단 상수들 추출 테스트."""
        changed_ranges = [LineRange(212, 213)]  # MODULE_VERSION
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert 'MODULE_VERSION = "1.0.0"' in all_context


class TestMultiRangeExtraction:
    """여러 범위에 걸친 추출 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return (
            Path(__file__).parent
            / "language_samples"
            / "java"
            / "SampleCalculator.java"
        )

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Java용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("java")

    def test_three_cross_classes(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """3개 클래스에 걸친 영역 추출 테스트."""
        changed_ranges = [
            LineRange(129, 210)
        ]  # calculateCircleArea ~ CalculatorFactory
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "public double calculateCircleArea" in all_context
        assert "public static String helperFunction" in all_context
        assert "public static SampleCalculator advancedCalculatorFactory" in all_context

    def test_two_blocks_cross_methods(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """2개 블록에 걸친 메서드 추출 테스트."""
        changed_ranges = [LineRange(42, 47), LineRange(155, 160)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 2
        all_context = "\n".join(contexts)
        assert "public int addNumbers(int a, int b)" in all_context
        assert "public static String helperFunction" in all_context

    def test_non_contiguous_ranges(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """비연속적인 여러 범위 추출 테스트."""
        changed_ranges = [
            LineRange(9, 10),  # Constants 클래스 상수들
            LineRange(135, 137),  # RadiusValidator 내부 클래스
            LineRange(212, 213),  # 모듈 레벨 상수들
        ]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 2
        all_context = "\n".join(contexts)
        assert "MAX_CALCULATION_STEPS = 100" in all_context
        assert "class RadiusValidator" in all_context or "validateRadius" in all_context
        assert 'MODULE_VERSION = "1.0.0"' in all_context


class TestComplexScenarios:
    """복잡한 시나리오 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return (
            Path(__file__).parent
            / "language_samples"
            / "java"
            / "SampleCalculator.java"
        )

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Java용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("java")

    def test_entire_class_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """전체 클래스 추출 테스트."""
        changed_ranges = [LineRange(20, 148)]  # SampleCalculator 전체 클래스
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "public class SampleCalculator" in all_context
        assert "public SampleCalculator(int initialValue)" in all_context
        assert "public int addNumbers(int a, int b)" in all_context

    def test_class_and_module_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스와 모듈 상수 동시 추출 테스트."""
        changed_ranges = [LineRange(8, 217)]  # Constants 클래스부터 모듈 상수까지
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "public class SampleCalculator" in all_context
        assert 'MODULE_VERSION = "1.0.0"' in all_context


class TestEdgeCases:
    """엣지 케이스 및 에러 처리 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return (
            Path(__file__).parent
            / "language_samples"
            / "java"
            / "SampleCalculator.java"
        )

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Java용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("java")

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
