"""
지원하지 않는 provider일 때 발생하는 예외 클래스 정의 모듈입니다.
"""

from selvage.src.exceptions.llm_gateway_error import LLMGatewayError


class UnsupportedProviderError(LLMGatewayError):
    """지원하지 않는 provider일 때 발생하는 예외"""

    def __init__(self, message: str) -> None:
        super().__init__(message)
