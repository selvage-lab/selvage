"""테스트용 샘플 클래스 - tree-sitter 파싱 테스트에 사용됩니다."""

import json
from typing import Any

# 파일 상수들
MAX_CALCULATION_STEPS = 100
DEFAULT_PRECISION = 2
PI_CONSTANT = 3.14159
CALCULATION_MODES = {
    "basic": "Basic calculations",
    "advanced": "Advanced calculations with logging",
    "debug": "Debug mode with detailed output",
}


class SampleCalculator:
    """간단한 계산기 클래스 - tree-sitter 테스트용"""

    def __init__(self, initial_value: int = 0):
        """계산기 초기화"""
        self.value = initial_value
        self.history = []
        self.mode = CALCULATION_MODES["basic"]

    def add_numbers(self, a: int, b: int) -> int:
        """두 수를 더하는 메소드"""

        def validate_inputs(x: int, y: int) -> bool:
            """내부 함수: 입력값 검증"""
            return isinstance(x, (int, float)) and isinstance(y, (int, float))

        def log_operation(operation: str, result: int) -> None:
            """내부 함수: 연산 로깅"""
            if len(self.history) < MAX_CALCULATION_STEPS:
                self.history.append(f"{operation} = {result}")
                print(f"Logged: {operation} = {result}")

        if not validate_inputs(a, b):
            raise ValueError("입력값이 숫자가 아닙니다")

        result = a + b
        self.value = result
        log_operation(f"add: {a} + {b}", result)
        print(f"Addition result: {result}")
        return result

    def multiply_and_format(self, numbers: list[int]) -> dict[str, Any]:
        """숫자 리스트를 곱하고 결과를 포맷팅하는 메소드"""

        def calculate_product(nums: list[int]) -> int:
            """내부 함수: 곱셈 계산"""
            if not nums:
                return 0

            def multiply_recursive(items: list[int], index: int = 0) -> int:
                """재귀적 곱셈 함수 (중첩 내부 함수)"""
                if index >= len(items):
                    return 1
                return items[index] * multiply_recursive(items, index + 1)

            return multiply_recursive(nums)

        def format_result(value: int, count: int) -> dict[str, Any]:
            """내부 함수: 결과 포맷팅"""
            return {
                "result": value,
                "formatted": f"Product: {value:,}",
                "count": count,
                "precision": DEFAULT_PRECISION,
            }

        if not numbers:
            return {"result": 0, "formatted": "Empty list"}

        result = calculate_product(numbers)
        self.value = result
        formatted_result = format_result(result, len(numbers))

        # 외부 함수 호출 예시
        json_str = json.dumps(formatted_result)
        print(f"Multiplication result: {json_str}")

        return formatted_result

    def calculate_circle_area(self, radius: float) -> float:
        """원의 넓이를 계산하는 메소드 (상수 사용)"""

        def validate_radius(r: float) -> bool:
            """내부 함수: 반지름 검증"""
            return r > 0

        if not validate_radius(radius):
            raise ValueError("반지름은 양수여야 합니다")

        area = PI_CONSTANT * radius * radius
        return round(area, DEFAULT_PRECISION)


def helper_function(data: dict) -> str:
    """도우미 함수 - 클래스 외부 함수"""

    def format_dict_items(items: dict) -> list[str]:
        """내부 함수: 딕셔너리 아이템 포맷팅"""
        formatted = []
        for key, value in items.items():
            formatted.append(f"{key}: {value}")
        return formatted

    formatted_items = format_dict_items(data)
    return f"Helper processed: {', '.join(formatted_items)}"


def advanced_calculator_factory(mode: str = "basic") -> SampleCalculator:
    """계산기 팩토리 함수"""

    def create_calculator_with_mode(calc_mode: str) -> SampleCalculator:
        """내부 함수: 모드별 계산기 생성"""
        calc = SampleCalculator()
        if calc_mode in CALCULATION_MODES:
            calc.mode = CALCULATION_MODES[calc_mode]
        return calc

    def validate_mode(m: str) -> bool:
        """내부 함수: 모드 검증"""
        return m in CALCULATION_MODES

    if not validate_mode(mode):
        mode = "basic"

    return create_calculator_with_mode(mode)


# 모듈 레벨 상수
MODULE_VERSION = "1.0.0"
AUTHOR_INFO = {"name": "Test Author", "email": "test@example.com"}
