"""ContextExtractor 테스트 케이스."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestBasicFunctionExtraction:
    """기본 함수/클래스 추출 기능 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "language_samples" / "python" / "sample_class.py"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Python용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("python")

    def test_class_declaration(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스 선언부 추출 테스트."""
        changed_ranges = [LineRange(17, 17)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        # 선언부만 검증
        assert "class SampleCalculator:" in all_context
        # 클래스 내부 코드는 포함되지 않아야 함 (선언부만 추출 확인)
        assert "def __init__" not in all_context
        assert "def add_numbers" not in all_context

    def test_init_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """__init__ 메서드 추출 테스트."""
        changed_ranges = [LineRange(20, 21)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        # 선언부 검증
        assert "def __init__(self, initial_value: int = 0):" in all_context
        # 내부 코드 블록 검증 (전체 메서드 추출 확인)
        assert "self.value = initial_value" in all_context
        assert "self.history = []" in all_context
        assert 'self.mode = CALCULATION_MODES["basic"]' in all_context

    def test_class_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스 메서드 추출 테스트."""
        changed_ranges = [LineRange(30, 32)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        # 선언부 검증
        assert "def add_numbers(self, a: int, b: int) -> int:" in all_context
        # 내부 코드 블록 검증 (전체 메서드 추출 확인)
        assert "def validate_inputs(x: int, y: int) -> bool:" in all_context
        assert "result = a + b" in all_context
        assert "self.value = result" in all_context

    def test_complex_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """복잡한 메서드 추출 테스트."""
        changed_ranges = [LineRange(77, 80), LineRange(64, 84)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        # 선언부 검증
        assert (
            "def multiply_and_format(self, numbers: list[int]) -> dict[str, Any]:"
            in all_context
        )
        # 내부 코드 블록 검증 (전체 메서드 추출 확인)
        assert "def calculate_product(nums: list[int]) -> int:" in all_context
        assert (
            "def format_result(value: int, count: int) -> dict[str, Any]:"
            in all_context
        )
        assert "result = calculate_product(numbers)" in all_context

    def test_nested_inner_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """중첩 내부 함수 추출 테스트."""
        changed_ranges = [LineRange(55, 57)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        # 선언부 검증
        assert "def calculate_product(nums: list[int]) -> int:" in all_context
        # 내부 코드 블록 검증 (전체 함수 추출 확인)
        assert (
            "def multiply_recursive(items: list[int], index: int = 0) -> int:"
            in all_context
        )
        assert "return multiply_recursive(nums)" in all_context
        assert "if not nums:" in all_context

    def test_external_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스 외부 함수 추출 테스트."""
        changed_ranges = [LineRange(110, 111)]  # helper_function 내부 코드 범위
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        # 선언부 검증
        assert "def helper_function(data: dict) -> str:" in all_context
        # 내부 코드 블록 검증 (전체 함수 추출 확인)
        assert "def format_dict_items(items: dict) -> list[str]:" in all_context
        assert "formatted_items = format_dict_items(data)" in all_context
        assert (
            "return f\"Helper processed: {', '.join(formatted_items)}\"" in all_context
        )

    def test_factory_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """팩토리 함수 추출 테스트."""
        changed_ranges = [LineRange(116, 118)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        # 선언부 검증
        assert (
            'def advanced_calculator_factory(mode: str = "basic") -> SampleCalculator:'
            in all_context
        )
        # 내부 코드 블록 검증 (전체 함수 추출 확인)
        assert (
            "def create_calculator_with_mode(calc_mode: str) -> SampleCalculator:"
            in all_context
        )
        assert "def validate_mode(m: str) -> bool:" in all_context
        assert "return create_calculator_with_mode(mode)" in all_context

    def test_method_declaration_only(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """메서드 선언부만 추출 테스트."""
        changed_ranges = [LineRange(26, 26)]  # add_numbers 선언부만
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "def add_numbers(self, a: int, b: int) -> int:" in all_context
        # 메서드 내부 코드는 포함되지 않아야 함
        assert "def validate_inputs" not in all_context

    def test_external_function_declaration_only(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """외부 함수 선언부만 추출 테스트."""
        changed_ranges = [LineRange(100, 100)]  # helper_function 선언부만
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "def helper_function(data: dict) -> str:" in all_context
        # 함수 내부 코드는 포함되지 않아야 함
        assert "def format_dict_items" not in all_context


class TestModuleLevelElements:
    """모듈 레벨 요소 추출 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "language_samples" / "python" / "sample_class.py"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Python용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("python")

    def test_basic_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """기본 상수들 추출 테스트."""
        changed_ranges = [LineRange(7, 8)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "MAX_CALCULATION_STEPS = 100" in all_context
        assert "DEFAULT_PRECISION = 2" in all_context

    def test_dict_constant(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """딕셔너리 상수 추출 테스트."""
        changed_ranges = [LineRange(10, 14)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "CALCULATION_MODES = {" in all_context

    def test_module_bottom_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """모듈 하단 상수들 추출 테스트."""
        changed_ranges = [LineRange(135, 136)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert 'MODULE_VERSION = "1.0.0"' in all_context


class TestMultiRangeExtraction:
    """여러 범위에 걸친 추출 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "language_samples" / "python" / "sample_class.py"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Python용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("python")

    def test_three_cross_functions(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """3개 함수에 걸친 영역 추출 테스트."""
        changed_ranges = [LineRange(88, 129)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) == 5  # 3개 함수 + 2개 import 문
        all_context = "\n".join(contexts)
        assert "def calculate_circle_area(self, radius: float) -> float:" in all_context
        assert "def helper_function(data: dict) -> str:" in all_context
        assert (
            'def advanced_calculator_factory(mode: str = "basic") -> SampleCalculator:'
            in all_context
        )

    def test_two_blocks_cross_functions(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """2개 블록에 걸친 함수 추출 테스트."""
        changed_ranges = [LineRange(26, 30), LineRange(100, 103)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 2
        all_context = "\n".join(contexts)
        assert "def add_numbers(self, a: int, b: int) -> int:" in all_context
        assert "def helper_function(data: dict) -> str:" in all_context

    def test_non_contiguous_ranges(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """비연속적인 여러 범위 추출 테스트."""
        changed_ranges = [
            LineRange(7, 8),  # 파일 상수들
            LineRange(89, 91),  # validate_radius 내부 함수
            LineRange(135, 136),  # 모듈 레벨 상수들
        ]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 2
        all_context = "\n".join(contexts)
        assert "MAX_CALCULATION_STEPS = 100" in all_context
        assert "def validate_radius(r: float) -> bool:" in all_context
        assert 'MODULE_VERSION = "1.0.0"' in all_context


class TestComplexScenarios:
    """복잡한 시나리오 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "language_samples" / "python" / "sample_class.py"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Python용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("python")

    def test_entire_class_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """전체 클래스 추출 테스트."""
        changed_ranges = [LineRange(16, 91)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 1
        all_context = "\n".join(contexts)
        assert "class SampleCalculator:" in all_context
        assert "def __init__(self, initial_value: int = 0):" in all_context
        assert "def add_numbers(self, a: int, b: int) -> int:" in all_context

    def test_class_and_module_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스와 모듈 상수 동시 추출 테스트."""
        changed_ranges = [LineRange(10, 136)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) >= 2
        all_context = "\n".join(contexts)
        assert "class SampleCalculator:" in all_context
        assert 'MODULE_VERSION = "1.0.0"' in all_context


class TestEdgeCases:
    """엣지 케이스 및 에러 처리 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "language_samples" / "python" / "sample_class.py"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Python용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("python")

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
        changed_ranges = [LineRange(15, 16)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # 빈 라인 범위에서도 적절히 처리되어야 함
        assert len(contexts) >= 0
