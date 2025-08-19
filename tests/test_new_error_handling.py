"""
새로운 구조화된 에러 처리 시스템 테스트
"""

from selvage.src.models.error_response import ErrorResponse
from selvage.src.models.model_provider import ModelProvider
from selvage.src.models.review_result import ReviewResult


class TestNewErrorHandling:
    """새로운 에러 처리 시스템 테스트"""

    def test_error_response_creation(self):
        """ErrorResponse 객체 생성 테스트"""
        error = Exception("Test error message")
        provider = ModelProvider.OPENAI

        error_response = ErrorResponse.from_exception(error, provider)

        assert error_response.provider == provider
        assert error_response.error_message == "Test error message"
        assert error_response.error_type == "api_error"  # 기본값

    def test_context_limit_error_detection_openai(self):
        """OpenAI context limit 에러 감지 테스트"""
        error = Exception(
            "This model's maximum context length is 128000 tokens. However, your messages resulted in 150000 tokens. Please reduce the length of the messages."
        )
        error_response = ErrorResponse.from_exception(error, ModelProvider.OPENAI)

        assert error_response.error_type == "context_limit_exceeded"
        assert error_response.is_context_limit_error() is True
        assert error_response.should_retry_with_multiturn() is True

    def test_context_limit_error_detection_anthropic(self):
        """Anthropic context limit 에러 감지 테스트"""
        error = Exception("prompt is too long: 209924 tokens > 200000 maximum")
        error_response = ErrorResponse.from_exception(error, ModelProvider.ANTHROPIC)

        assert error_response.error_type == "context_limit_exceeded"
        assert error_response.is_context_limit_error() is True

    def test_context_limit_error_detection_openrouter(self):
        """OpenRouter context limit 에러 감지 테스트"""
        error = Exception(
            "This endpoint's maximum context length is 1000000 tokens. However, you requested about 2315418 tokens (2315418 of text input)."
        )
        error_response = ErrorResponse.from_exception(error, ModelProvider.OPENROUTER)

        assert error_response.error_type == "context_limit_exceeded"
        assert error_response.is_context_limit_error() is True

    def test_review_result_error_handling(self):
        """ReviewResult 에러 처리 테스트"""
        error = Exception("Test API error")
        review_result = ReviewResult.get_error_result(
            error, "gpt-4", ModelProvider.OPENAI
        )

        assert review_result.success is False
        assert review_result.error_response is not None
        assert review_result.error_response.provider == ModelProvider.OPENAI
        assert review_result.error_response.error_message == "Test API error"
        assert review_result.is_context_limit_error() is False

    def test_review_result_context_limit_error(self):
        """ReviewResult context limit 에러 테스트"""
        error = Exception(
            "This model's maximum context length is 128000 tokens. However, your messages resulted in 200000 tokens. Please reduce the length of the messages."
        )
        review_result = ReviewResult.get_error_result(
            error, "gpt-4", ModelProvider.OPENAI
        )

        assert review_result.success is False
        assert review_result.is_context_limit_error() is True
        assert review_result.should_retry_with_multiturn() is True

    def test_review_result_success(self):
        """ReviewResult 성공 케이스 테스트"""
        from selvage.src.utils.token.models import EstimatedCost, ReviewResponse

        review_response = ReviewResponse.get_empty_response()
        estimated_cost = EstimatedCost.get_zero_cost("gpt-4")

        review_result = ReviewResult.get_success_result(review_response, estimated_cost)

        assert review_result.success is True
        assert review_result.error_response is None
        assert review_result.is_context_limit_error() is False
