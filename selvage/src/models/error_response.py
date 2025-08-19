from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from selvage.src.models.model_provider import ModelProvider

from .error_pattern_parser import ErrorPatternParser


class ErrorResponse(BaseModel):
    """LLM API 에러 응답을 구조화한 모델"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    error_type: str
    """에러 유형: 'context_limit_exceeded', 'api_error', 'parse_error', etc."""

    error_code: str | None = None
    """Provider별 에러 코드: 'invalid_request_error', 'context_length_exceeded', etc."""

    error_message: str
    """에러 메시지"""

    http_status_code: int | None = None
    """HTTP 상태 코드"""

    provider: ModelProvider
    """LLM Provider: 'openai', 'anthropic', 'google', 'openrouter'"""

    raw_error: dict[str, Any] = Field(default_factory=dict)
    """원본 에러 응답 데이터"""

    exception: Exception | None = Field(default=None, exclude=True)
    """원본 예외 객체 (직렬화에서 제외)"""

    @classmethod
    def from_exception(
        cls, error: Exception, provider: ModelProvider
    ) -> "ErrorResponse":
        """Exception 객체에서 ErrorResponse를 생성합니다.

        Args:
            error: 발생한 예외
            provider: LLM Provider 이름

        Returns:
            ErrorResponse: 구조화된 에러 응답
        """
        error_message = str(error)
        raw_error = {}

        # 패턴 파서를 사용하여 에러 분석
        try:
            parser = ErrorPatternParser()
            parsing_result = parser.parse_error(provider, error)

            error_type = parsing_result.error_type
            error_code = parsing_result.error_code
            http_status_code = parsing_result.http_status_code

            # 토큰 정보가 있는 경우 raw_error에 추가
            if parsing_result.token_info:
                if parsing_result.token_info.actual_tokens is not None:
                    raw_error["actual_tokens"] = parsing_result.token_info.actual_tokens
                if parsing_result.token_info.max_tokens is not None:
                    raw_error["max_tokens"] = parsing_result.token_info.max_tokens

            # 추가 토큰 정보가 있는 경우 raw_error에 추가
            if parsing_result.additional_token_info:
                raw_error.update(parsing_result.additional_token_info)

            # 매칭된 패턴 정보 추가
            if parsing_result.matched_pattern:
                raw_error["matched_pattern"] = parsing_result.matched_pattern

        except Exception as parse_error:
            # 패턴 파서 오류 시 기본값 사용
            error_type = "parse_error"
            error_code = None
            http_status_code = None
            raw_error["parse_error"] = str(parse_error)

        # error_code를 안전하게 string으로 변환
        safe_error_code = None
        if error_code is not None:
            safe_error_code = str(error_code)

        return cls(
            error_type=error_type,
            error_code=safe_error_code,
            error_message=error_message,
            http_status_code=http_status_code,
            provider=provider,
            raw_error=raw_error,
            exception=error,
        )

    def is_context_limit_error(self) -> bool:
        """Context limit 에러인지 확인합니다.

        Returns:
            bool: Context limit 에러 여부
        """
        return self.error_type == "context_limit_exceeded"

    def should_retry_with_multiturn(self) -> bool:
        """Multiturn 리뷰로 재시도할 수 있는 에러인지 확인합니다.

        Returns:
            bool: Multiturn 재시도 가능 여부
        """
        return self.is_context_limit_error()
