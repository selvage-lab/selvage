"""테스트용 샘플 클래스 - tree-sitter 파싱 테스트에 사용됩니다."""

import json
from typing import Any


class SampleCalculator:
    """간단한 계산기 클래스 - tree-sitter 테스트용"""

    def __init__(self, initial_value: int = 0):
        """계산기 초기화"""
        self.value = initial_value
        self.history = []

    def add_numbers(self, a: int, b: int) -> int:
        """두 수를 더하는 메소드"""
        result = a + b
        self.value = result
        self.history.append(f"add: {a} + {b} = {result}")
        print(f"Addition result: {result}")
        return result

    def multiply_and_format(self, numbers: list[int]) -> dict[str, Any]:
        """숫자 리스트를 곱하고 결과를 포맷팅하는 메소드"""
        if not numbers:
            return {"result": 0, "formatted": "Empty list"}

        result = 1
        for num in numbers:
            result *= num

        self.value = result
        formatted_result = {
            "result": result,
            "formatted": f"Product: {result:,}",
            "count": len(numbers),
        }

        # 외부 함수 호출 예시
        json_str = json.dumps(formatted_result)
        print(f"Multiplication result: {json_str}")

        return formatted_result


def helper_function(data: dict) -> str:
    """도우미 함수 - 클래스 외부 함수"""
    return f"Helper processed: {data}"
