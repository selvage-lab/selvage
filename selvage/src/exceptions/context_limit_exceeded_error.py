"""
모델의 컨텍스트 크기 제한 초과 시 발생하는 예외 클래스 정의 모듈입니다.
"""

from selvage.src.exceptions.llm_gateway_error import LLMGatewayError


class ContextLimitExceededError(LLMGatewayError):
    """모델의 컨텍스트 크기 제한 초과 시 발생하는 예외"""

    def __init__(
        self, input_tokens: int | None = None, context_limit: int | None = None
    ) -> None:
        message = "모델의 컨텍스트 크기 제한을 초과했습니다."
        if input_tokens is not None:
            message += f" 입력 토큰 수: {input_tokens}"
        if context_limit is not None:
            message += f" / 제한: {context_limit}"
        super().__init__(message)
