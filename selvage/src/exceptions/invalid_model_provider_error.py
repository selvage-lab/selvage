"""
잘못된 모델 제공자일 때 발생하는 예외 클래스 정의 모듈입니다.
"""

from typing import TYPE_CHECKING

from selvage.src.exceptions.llm_gateway_error import LLMGatewayError

if TYPE_CHECKING:
    from selvage.src.models.model_provider import ModelProvider


class InvalidModelProviderError(LLMGatewayError):
    """잘못된 모델 제공자일 때 발생하는 예외"""

    def __init__(self, model_name: str, expected_provider: "ModelProvider") -> None:
        self.model_name = model_name
        self.expected_provider = expected_provider
        super().__init__(
            f"{model_name}은(는) {expected_provider.get_display_name()} 모델이 아닙니다."
        )
