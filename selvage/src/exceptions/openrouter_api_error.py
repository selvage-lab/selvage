"""OpenRouter API 관련 예외 클래스들"""

from selvage.src.exceptions.llm_gateway_error import LLMGatewayError


class OpenRouterAPIError(LLMGatewayError):
    """OpenRouter API 관련 기본 예외 클래스"""

    def __init__(
        self,
        message: str,
        raw_response: dict | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.raw_response = raw_response
        self.status_code = status_code


class OpenRouterResponseError(OpenRouterAPIError):
    """OpenRouter API 응답 구조 문제 시 발생하는 예외"""

    def __init__(
        self,
        message: str,
        raw_response: dict | None = None,
        missing_field: str | None = None,
    ) -> None:
        super().__init__(message, raw_response)
        self.missing_field = missing_field


class OpenRouterConnectionError(OpenRouterAPIError):
    """OpenRouter API 연결 문제 시 발생하는 예외"""

    pass


class OpenRouterAuthenticationError(OpenRouterAPIError):
    """OpenRouter API 인증 문제 시 발생하는 예외 (재시도 금지)"""

    pass
