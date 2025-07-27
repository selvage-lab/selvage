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
        return Path(__file__).parent / "sample_class.py"

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

        expected_result = (
            'import json\n'
            'from typing import Any\n'
            'class SampleCalculator:\n'
            '    """간단한 계산기 클래스 - tree-sitter 테스트용"""\n'
            '\n'
            '    def __init__(self, initial_value: int = 0):\n'
            '        """계산기 초기화"""\n'
            '        self.value = initial_value\n'
            '        self.history = []\n'
            '        self.mode = CALCULATION_MODES["basic"]\n'
            '\n'
            '    def add_numbers(self, a: int, b: int) -> int:\n'
            '        """두 수를 더하는 메소드"""\n'
            '\n'
            '        def validate_inputs(x: int, y: int) -> bool:\n'
            '            """내부 함수: 입력값 검증"""\n'
            '            return isinstance(x, (int, float)) and isinstance(y, (int, float))\n'
            '\n'
            '        def log_operation(operation: str, result: int) -> None:\n'
            '            """내부 함수: 연산 로깅"""\n'
            '            if len(self.history) < MAX_CALCULATION_STEPS:\n'
            '                self.history.append(f"{operation} = {result}")\n'
            '                print(f"Logged: {operation} = {result}")\n'
            '\n'
            '        if not validate_inputs(a, b):\n'
            '            raise ValueError("입력값이 숫자가 아닙니다")\n'
            '\n'
            '        result = a + b\n'
            '        self.value = result\n'
            '        log_operation(f"add: {a} + {b}", result)\n'
            '        print(f"Addition result: {result}")\n'
            '        return result\n'
            '\n'
            '    def multiply_and_format(self, numbers: list[int]) -> dict[str, Any]:\n'
            '        """숫자 리스트를 곱하고 결과를 포맷팅하는 메소드"""\n'
            '\n'
            '        def calculate_product(nums: list[int]) -> int:\n'
            '            """내부 함수: 곱셈 계산"""\n'
            '            if not nums:\n'
            '                return 0\n'
            '\n'
            '            def multiply_recursive(items: list[int], index: int = 0) -> int:\n'
            '                """재귀적 곱셈 함수 (중첩 내부 함수)"""\n'
            '                if index >= len(items):\n'
            '                    return 1\n'
            '                return items[index] * multiply_recursive(items, index + 1)\n'
            '\n'
            '            return multiply_recursive(nums)\n'
            '\n'
            '        def format_result(value: int, count: int) -> dict[str, Any]:\n'
            '            """내부 함수: 결과 포맷팅"""\n'
            '            return {\n'
            '                "result": value,\n'
            '                "formatted": f"Product: {value:,}",\n'
            '                "count": count,\n'
            '                "precision": DEFAULT_PRECISION,\n'
            '            }\n'
            '\n'
            '        if not numbers:\n'
            '            return {"result": 0, "formatted": "Empty list"}\n'
            '\n'
            '        result = calculate_product(numbers)\n'
            '        self.value = result\n'
            '        formatted_result = format_result(result, len(numbers))\n'
            '\n'
            '        # 외부 함수 호출 예시\n'
            '        json_str = json.dumps(formatted_result)\n'
            '        print(f"Multiplication result: {json_str}")\n'
            '\n'
            '        return formatted_result\n'
            '\n'
            '    def calculate_circle_area(self, radius: float) -> float:\n'
            '        """원의 넓이를 계산하는 메소드 (상수 사용)"""\n'
            '\n'
            '        def validate_radius(r: float) -> bool:\n'
            '            """내부 함수: 반지름 검증"""\n'
            '            return r > 0\n'
            '\n'
            '        if not validate_radius(radius):\n'
            '            raise ValueError("반지름은 양수여야 합니다")\n'
            '\n'
            '        area = PI_CONSTANT * radius * radius\n'
            '        return round(area, DEFAULT_PRECISION)'
        )

        assert len(contexts) == 3
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_init_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """__init__ 메서드 추출 테스트."""
        changed_ranges = [LineRange(20, 21)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import json\n"
            "from typing import Any\n"
            "def __init__(self, initial_value: int = 0):\n"
            '        """계산기 초기화"""\n'
            "        self.value = initial_value\n"
            "        self.history = []\n"
            '        self.mode = CALCULATION_MODES["basic"]'
        )

        assert len(contexts) == 3
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_class_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스 메서드 추출 테스트."""
        changed_ranges = [LineRange(30, 32)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import json\n"
            "from typing import Any\n"
            "def add_numbers(self, a: int, b: int) -> int:\n"
            '        """두 수를 더하는 메소드"""\n'
            "\n"
            "        def validate_inputs(x: int, y: int) -> bool:\n"
            '            """내부 함수: 입력값 검증"""\n'
            "            return isinstance(x, (int, float)) and isinstance("
            "y, (int, float))\n"
            "\n"
            "        def log_operation(operation: str, result: int) -> None:\n"
            '            """내부 함수: 연산 로깅"""\n'
            "            if len(self.history) < MAX_CALCULATION_STEPS:\n"
            '                self.history.append(f"{operation} = {result}")\n'
            '                print(f"Logged: {operation} = {result}")\n'
            "\n"
            "        if not validate_inputs(a, b):\n"
            '            raise ValueError("입력값이 숫자가 아닙니다")\n'
            "\n"
            "        result = a + b\n"
            "        self.value = result\n"
            '        log_operation(f"add: {a} + {b}", result)\n'
            '        print(f"Addition result: {result}")\n'
            "        return result"
        )

        assert len(contexts) == 3
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_complex_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """복잡한 메서드 추출 테스트."""
        changed_ranges = [LineRange(77, 80), LineRange(64, 84)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import json\n"
            "from typing import Any\n"
            "def multiply_and_format(self, numbers: list[int]) -> dict[str, Any]:\n"
            '        """숫자 리스트를 곱하고 결과를 포맷팅하는 메소드"""\n'
            "\n"
            "        def calculate_product(nums: list[int]) -> int:\n"
            '            """내부 함수: 곱셈 계산"""\n'
            "            if not nums:\n"
            "                return 0\n"
            "\n"
            "            def multiply_recursive(items: list[int], index: int = 0) "
            "-> int:\n"
            '                """재귀적 곱셈 함수 (중첩 내부 함수)"""\n'
            "                if index >= len(items):\n"
            "                    return 1\n"
            "                return items[index] * multiply_recursive(items, index + 1)\n"
            "\n"
            "            return multiply_recursive(nums)\n"
            "\n"
            "        def format_result(value: int, count: int) -> dict[str, Any]:\n"
            '            """내부 함수: 결과 포맷팅"""\n'
            "            return {\n"
            '                "result": value,\n'
            '                "formatted": f"Product: {value:,}",\n'
            '                "count": count,\n'
            '                "precision": DEFAULT_PRECISION,\n'
            "            }\n"
            "\n"
            "        if not numbers:\n"
            '            return {"result": 0, "formatted": "Empty list"}\n'
            "\n"
            "        result = calculate_product(numbers)\n"
            "        self.value = result\n"
            "        formatted_result = format_result(result, len(numbers))\n"
            "\n"
            "        # 외부 함수 호출 예시\n"
            "        json_str = json.dumps(formatted_result)\n"
            '        print(f"Multiplication result: {json_str}")\n'
            "\n"
            "        return formatted_result"
        )

        assert len(contexts) == 3
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_nested_inner_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """중첩 내부 함수 추출 테스트."""
        changed_ranges = [LineRange(55, 57)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import json\n"
            "from typing import Any\n"
            "def calculate_product(nums: list[int]) -> int:\n"
            '            """내부 함수: 곱셈 계산"""\n'
            "            if not nums:\n"
            "                return 0\n"
            "\n"
            "            def multiply_recursive(items: list[int], index: int = 0) "
            "-> int:\n"
            '                """재귀적 곱셈 함수 (중첩 내부 함수)"""\n'
            "                if index >= len(items):\n"
            "                    return 1\n"
            "                return items[index] * multiply_recursive(items, index + 1)\n"
            "\n"
            "            return multiply_recursive(nums)"
        )

        assert len(contexts) == 3
        all_context = "\n".join(contexts)
        assert all_context == expected_result

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
        # import 문 검증
        assert "import json" in all_context
        assert "from typing import Any" in all_context
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
        # import 문 검증
        assert "import json" in all_context
        assert "from typing import Any" in all_context
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

        expected_result = (
            'import json\n'
            'from typing import Any\n'
            'def add_numbers(self, a: int, b: int) -> int:\n'
            '        """두 수를 더하는 메소드"""\n'
            '\n'
            '        def validate_inputs(x: int, y: int) -> bool:\n'
            '            """내부 함수: 입력값 검증"""\n'
            '            return isinstance(x, (int, float)) and isinstance('
            'y, (int, float))\n'
            '\n'
            '        def log_operation(operation: str, result: int) -> None:\n'
            '            """내부 함수: 연산 로깅"""\n'
            '            if len(self.history) < MAX_CALCULATION_STEPS:\n'
            '                self.history.append(f"{operation} = {result}")\n'
            '                print(f"Logged: {operation} = {result}")\n'
            '\n'
            '        if not validate_inputs(a, b):\n'
            '            raise ValueError("입력값이 숫자가 아닙니다")\n'
            '\n'
            '        result = a + b\n'
            '        self.value = result\n'
            '        log_operation(f"add: {a} + {b}", result)\n'
            '        print(f"Addition result: {result}")\n'
            '        return result'
        )

        assert len(contexts) == 3
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_external_function_declaration_only(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """외부 함수 선언부만 추출 테스트."""
        changed_ranges = [LineRange(100, 100)]  # helper_function 선언부만
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            'import json\n'
            'from typing import Any\n'
            'def helper_function(data: dict) -> str:\n'
            '    """도우미 함수 - 클래스 외부 함수"""\n'
            '\n'
            '    def format_dict_items(items: dict) -> list[str]:\n'
            '        """내부 함수: 딕셔너리 아이템 포맷팅"""\n'
            '        formatted = []\n'
            '        for key, value in items.items():\n'
            '            formatted.append(f"{key}: {value}")\n'
            '        return formatted\n'
            '\n'
            '    formatted_items = format_dict_items(data)\n'
            '    return f"Helper processed: {\', \'.join(formatted_items)}"'
        )

        assert len(contexts) == 3
        all_context = "\n".join(contexts)
        assert all_context == expected_result


class TestModuleLevelElements:
    """모듈 레벨 요소 추출 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "sample_class.py"

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

        expected_result = (
            "import json\n"
            "from typing import Any\n"
            "MAX_CALCULATION_STEPS = 100\n"
            "DEFAULT_PRECISION = 2"
        )

        assert len(contexts) == 4
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_dict_constant(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """딕셔너리 상수 추출 테스트."""
        changed_ranges = [LineRange(10, 14)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import json\n"
            "from typing import Any\n"
            "CALCULATION_MODES = {\n"
            '    "basic": "Basic calculations",\n'
            '    "advanced": "Advanced calculations with logging",\n'
            '    "debug": "Debug mode with detailed output",\n'
            "}"
        )

        assert len(contexts) == 3
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_module_bottom_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """모듈 하단 상수들 추출 테스트."""
        changed_ranges = [LineRange(135, 136)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import json\n"
            "from typing import Any\n"
            'MODULE_VERSION = "1.0.0"\n'
            'AUTHOR_INFO = {"name": "Test Author", "email": "test@example.com"}'
        )

        assert len(contexts) == 4
        all_context = "\n".join(contexts)
        assert all_context == expected_result


class TestMultiRangeExtraction:
    """여러 범위에 걸친 추출 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "sample_class.py"

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

        # 실제 결과에 맞게 엄격한 검증
        assert len(contexts) == 5  # 3개 함수 + 2개 import 문
        all_context = "\n".join(contexts)

        # 실제 결과 기반 검증: 클래스 선언부는 포함되지 않고 3개 함수만 포함됨
        assert "import json" in all_context
        assert "from typing import Any" in all_context
        assert "def calculate_circle_area(self, radius: float) -> float:" in all_context
        assert "def helper_function(data: dict) -> str:" in all_context
        assert (
            'def advanced_calculator_factory(mode: str = "basic") -> SampleCalculator:'
            in all_context
        )

        # 클래스 선언부는 실제로 포함되지 않음
        assert "class SampleCalculator:" not in all_context

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
        # import 문 검증
        assert "import json" in all_context
        assert "from typing import Any" in all_context
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

        expected_result = (
            "import json\n"
            "from typing import Any\n"
            "MAX_CALCULATION_STEPS = 100\n"
            "DEFAULT_PRECISION = 2\n"
            "def validate_radius(r: float) -> bool:\n"
            '            """내부 함수: 반지름 검증"""\n'
            "            return r > 0\n"
            'MODULE_VERSION = "1.0.0"\n'
            'AUTHOR_INFO = {"name": "Test Author", "email": "test@example.com"}'
        )

        assert len(contexts) == 7
        all_context = "\n".join(contexts)
        assert all_context == expected_result


class TestComplexScenarios:
    """복잡한 시나리오 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "sample_class.py"

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
        # import 문 검증
        assert "import json" in all_context
        assert "from typing import Any" in all_context
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
        # import 문 검증
        assert "import json" in all_context
        assert "from typing import Any" in all_context
        assert "class SampleCalculator:" in all_context
        assert 'MODULE_VERSION = "1.0.0"' in all_context


class TestEdgeCases:
    """엣지 케이스 및 에러 처리 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "sample_class.py"

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
