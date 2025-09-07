"""
지원하지 않는 모델일 때 발생하는 예외 클래스 정의 모듈입니다.
"""


class UnsupportedModelError(Exception):
    """지원하지 않는 모델일 때 발생하는 예외"""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        super().__init__(f"Unsupported model: {model_name}")
