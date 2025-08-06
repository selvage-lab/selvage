from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """LLM API 에러 응답을 구조화한 모델"""
    
    error_type: str
    """에러 유형: 'context_limit_exceeded', 'api_error', 'parse_error', etc."""
    
    error_code: str | None = None
    """Provider별 에러 코드: 'invalid_request_error', 'context_length_exceeded', etc."""
    
    error_message: str
    """에러 메시지"""
    
    http_status_code: int | None = None
    """HTTP 상태 코드"""
    
    provider: str
    """LLM Provider: 'openai', 'anthropic', 'google', 'openrouter'"""
    
    raw_error: dict[str, Any] = Field(default_factory=dict)
    """원본 에러 응답 데이터"""
    
    @classmethod
    def from_exception(cls, error: Exception, provider: str) -> "ErrorResponse":
        """Exception 객체에서 ErrorResponse를 생성합니다.
        
        Args:
            error: 발생한 예외
            provider: LLM Provider 이름
            
        Returns:
            ErrorResponse: 구조화된 에러 응답
        """
        error_message = str(error)
        error_type = "api_error"  # 기본값
        error_code = None
        http_status_code = None
        raw_error = {}
        
        # Provider별 에러 파싱 로직
        if provider == "openai":
            error_type, error_code, http_status_code, raw_error = cls._parse_openai_error(error)
        elif provider == "anthropic":
            error_type, error_code, http_status_code, raw_error = cls._parse_anthropic_error(error)
        elif provider == "google":
            error_type, error_code, http_status_code, raw_error = cls._parse_google_error(error)
        elif provider == "openrouter":
            error_type, error_code, http_status_code, raw_error = cls._parse_openrouter_error(error)
        
        return cls(
            error_type=error_type,
            error_code=error_code,
            error_message=error_message,
            http_status_code=http_status_code,
            provider=provider,
            raw_error=raw_error,
        )
    
    @staticmethod
    def _parse_openai_error(error: Exception) -> tuple[str, str | None, int | None, dict[str, Any]]:
        """OpenAI 에러 파싱"""
        error_message = str(error)
        raw_error = {}
        
        # context_length_exceeded 패턴 감지
        if "context_length_exceeded" in error_message:
            return "context_limit_exceeded", "context_length_exceeded", 400, raw_error
        
        # InstructorRetryException 처리
        if "InstructorRetryException" in str(type(error)):
            if hasattr(error, "last_completion") and hasattr(error.last_completion, "choices"):
                # API 응답에서 더 자세한 정보 추출 가능
                pass
        
        return "api_error", None, None, raw_error
    
    @staticmethod  
    def _parse_anthropic_error(error: Exception) -> tuple[str, str | None, int | None, dict[str, Any]]:
        """Anthropic 에러 파싱"""
        error_message = str(error)
        raw_error = {}
        
        # prompt is too long 패턴 감지
        if "prompt is too long" in error_message:
            return "context_limit_exceeded", "invalid_request_error", 400, raw_error
        
        if "invalid_request_error" in error_message:
            return "api_error", "invalid_request_error", 400, raw_error
        
        return "api_error", None, None, raw_error
    
    @staticmethod
    def _parse_google_error(error: Exception) -> tuple[str, str | None, int | None, dict[str, Any]]:
        """Google 에러 파싱"""
        error_message = str(error)
        raw_error = {}
        
        # RESOURCE_EXHAUSTED 패턴 감지 
        if "RESOURCE_EXHAUSTED" in error_message:
            return "quota_exceeded", "RESOURCE_EXHAUSTED", 429, raw_error
            
        # 실제 context limit 패턴 (향후 확장)
        if "Token limit exceeded" in error_message or "Request payload size exceeds" in error_message:
            return "context_limit_exceeded", "400", 400, raw_error
        
        return "api_error", None, None, raw_error
    
    @staticmethod
    def _parse_openrouter_error(error: Exception) -> tuple[str, str | None, int | None, dict[str, Any]]:
        """OpenRouter 에러 파싱"""
        error_message = str(error)
        raw_error = {}
        
        # HTTP 400 Bad Request 패턴 감지 (context limit으로 추정)
        if "400 Bad Request" in error_message:
            return "context_limit_exceeded", "400", 400, raw_error
            
        # HTTP 404 Not Found
        if "404 Not Found" in error_message:
            return "model_not_found", "404", 404, raw_error
            
        # HTTP 413 Payload Too Large
        if "413" in error_message or "payload too large" in error_message:
            return "context_limit_exceeded", "413", 413, raw_error
        
        return "api_error", None, None, raw_error
    
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