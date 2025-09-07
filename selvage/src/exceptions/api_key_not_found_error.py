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
            env_var = provider.get_env_var_name()
            super().__init__(
                f"{provider.value} API key not provided. "
                f"Please set the {env_var} environment variable."
            )
        else:
            super().__init__("API key not provided.")
