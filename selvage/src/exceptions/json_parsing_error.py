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

    @classmethod
    def from_parsing_exception(
        cls,
        source_error: Exception,
        api_name: str,
        raw_response: str | None = None,
    ) -> "JSONParsingError":
        """파싱 예외를 JSONParsingError로 변환합니다.

        Args:
            source_error: 원본 파싱 예외
            api_name: API 이름 (예: "Google API", "Anthropic API")
            raw_response: 원본 응답 텍스트 (선택사항)

        Returns:
            변환된 JSONParsingError 인스턴스
        """
        truncated_response = cls._truncate_response(raw_response)

        return cls(
            message=f"{api_name} 응답 파싱 실패: {str(source_error)}",
            raw_response=truncated_response,
            parsing_error=source_error,
        )

    @staticmethod
    def _truncate_response(response: str | None, max_length: int = 500) -> str:
        """응답 텍스트를 적절한 길이로 자릅니다.

        Args:
            response: 원본 응답 텍스트
            max_length: 최대 길이 (기본값: 500)

        Returns:
            잘린 응답 텍스트
        """
        if not response:
            return ""

        if len(response) > max_length:
            return response[:max_length] + "..."

        return response
