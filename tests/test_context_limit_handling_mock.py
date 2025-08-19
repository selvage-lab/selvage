"""Context Limit 처리 로직 Mock 테스트"""

from unittest.mock import MagicMock

from selvage.src.models.error_response import ErrorResponse
from selvage.src.models.model_provider import ModelProvider


class TestContextLimitHandlingMock:
    """Context Limit 에러 처리 로직 Mock 테스트"""

    def test_openai_context_limit_error_response_creation(self):
        """OpenAI context limit 에러에서 ErrorResponse 생성 테스트"""
        # OpenAI context limit 에러 시뮬레이션 - 실제 Exception 클래스 사용
        error_message = (
            "Error code: 400 - {'error': {'message': \"This model's maximum context length is 128000 tokens. "
            'However, your messages resulted in 273619 tokens. Please reduce the length of the messages.", '
            "'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}"
        )

        class MockOpenAIError(Exception):
            def __init__(self, message):
                super().__init__(message)
                # HTTP response 속성 시뮬레이션
                self.response = MagicMock(status_code=400)
                self.response.json.return_value = {
                    "error": {
                        "message": "This model's maximum context length is 128000 tokens. However, your messages resulted in 273619 tokens.",
                        "type": "invalid_request_error",
                        "param": "messages",
                        "code": "context_length_exceeded",
                    }
                }

        mock_error = MockOpenAIError(error_message)

        # ErrorResponse 생성
        error_response = ErrorResponse.from_exception(mock_error, ModelProvider.OPENAI)

        # 검증
        assert error_response.error_type == "context_limit_exceeded"
        assert error_response.error_code == "context_length_exceeded"
        assert error_response.provider == ModelProvider.OPENAI
        assert error_response.is_context_limit_error() is True
        assert error_response.should_retry_with_multiturn() is True

    def test_anthropic_context_limit_error_response_creation(self):
        """Anthropic context limit 에러에서 ErrorResponse 생성 테스트"""
        # Anthropic context limit 에러 시뮬레이션 - 실제 Exception 클래스 사용
        error_message = (
            "Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', "
            "'message': 'prompt is too long: 209924 tokens > 200000 maximum'}}"
        )

        class MockAnthropicError(Exception):
            def __init__(self, message):
                super().__init__(message)
                self.status_code = 400
                self.type = "invalid_request_error"

        mock_error = MockAnthropicError(error_message)

        # ErrorResponse 생성
        error_response = ErrorResponse.from_exception(
            mock_error, ModelProvider.ANTHROPIC
        )

        # 검증
        assert error_response.error_type == "context_limit_exceeded"
        assert error_response.provider == ModelProvider.ANTHROPIC
        assert error_response.is_context_limit_error() is True

    def test_context_limit_error_detection_logic(self):
        """Context limit 에러 감지 로직 테스트"""
        # Context limit 에러인 경우
        context_error = ErrorResponse(
            error_type="context_limit_exceeded",
            error_message="Context limit exceeded",
            provider=ModelProvider.OPENAI,
        )

        assert context_error.is_context_limit_error() is True
        assert context_error.should_retry_with_multiturn() is True

        # 일반 API 에러인 경우
        api_error = ErrorResponse(
            error_type="api_error",
            error_message="General API error",
            provider=ModelProvider.OPENAI,
        )

        assert api_error.is_context_limit_error() is False
        assert api_error.should_retry_with_multiturn() is False
