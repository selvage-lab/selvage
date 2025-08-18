"""
API 키가 없을 때 발생하는 예외 클래스 정의 모듈입니다.
"""

from typing import TYPE_CHECKING

from selvage.src.exceptions.llm_gateway_error import LLMGatewayError

if TYPE_CHECKING:
    from selvage.src.models.model_provider import ModelProvider


class APIKeyNotFoundError(LLMGatewayError):
    """API 키가 없을 때 발생하는 예외"""

    def __init__(self, provider: "ModelProvider" = None, message: str = None) -> None:
        self.provider = provider
        if message:
            super().__init__(message)
        elif provider:
            message = "API 키가 제공되지 않았습니다. API 키를 설정하세요."
            super().__init__(message)
        else:
            super().__init__("API 키가 제공되지 않았습니다.")
