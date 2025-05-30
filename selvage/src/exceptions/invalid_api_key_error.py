"""
API 키 유효성 검증 실패 시 발생하는 예외 클래스 정의 모듈입니다.
"""

from typing import TYPE_CHECKING

from selvage.src.exceptions.llm_gateway_error import LLMGatewayError

if TYPE_CHECKING:
    from selvage.src.models.model_provider import ModelProvider


class InvalidAPIKeyError(LLMGatewayError):
    """API 키 유효성 검증 실패 시 발생하는 예외"""

    def __init__(self, provider: "ModelProvider", reason: str) -> None:
        self.provider = provider
        self.reason = reason
        super().__init__(
            f"{provider.get_display_name()} API 키가 유효하지 않습니다: {reason}"
        )
