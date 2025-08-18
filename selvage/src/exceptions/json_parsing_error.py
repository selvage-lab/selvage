"""JSON 파싱 관련 예외 클래스"""

from selvage.src.exceptions.llm_gateway_error import LLMGatewayError


class JSONParsingError(LLMGatewayError):
    """JSON 파싱 실패 시 발생하는 예외"""

    def __init__(
        self,
        message: str,
        raw_response: str = "",
        parsing_error: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.raw_response = raw_response
        self.parsing_error = parsing_error

    def __str__(self) -> str:
        error_msg = super().__str__()
        if self.parsing_error:
            error_msg += (
                f" (원인: {type(self.parsing_error).__name__}: {self.parsing_error})"
            )
        return error_msg
