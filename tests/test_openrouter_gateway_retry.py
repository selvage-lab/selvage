"""OpenRouterGateway retry 로직 및 검증 함수 테스트"""

from unittest.mock import Mock, patch

import pytest

from selvage.src.exceptions.openrouter_api_error import (
    OpenRouterConnectionError,
    OpenRouterResponseError,
)
from selvage.src.llm_gateway.openrouter.gateway import OpenRouterGateway
from selvage.src.models.model_provider import ModelProvider


class TestOpenRouterGatewayRetry:
    """OpenRouterGateway retry 기능 테스트"""

    def setup_method(self):
        """각 테스트 전에 실행되는 설정"""
        self.model_info = {
            "full_name": "anthropic/claude-3-sonnet",
            "provider": ModelProvider.OPENROUTER,
            "openrouter_name": "anthropic/claude-3-sonnet",
            "description": "Test OpenRouter model",  # description 필드 추가
        }
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}):
            self.gateway = OpenRouterGateway(self.model_info)

    def test_retry_decorator_applied_to_review_code(self):
        """OpenRouterGateway의 _review_code_with_retry에 특화된 retry 데코레이터가 적용되었는지 테스트"""
        # _review_code_with_retry 메서드에 retry 관련 속성이 있는지 확인
        assert hasattr(self.gateway._review_code_with_retry, "retry")

        # tenacity retry 객체의 속성들 확인
        retry_obj = self.gateway._review_code_with_retry.retry

        # 재시도 횟수 (최대 3회)
        assert retry_obj.stop.max_attempt_number == 3

        # 지수 백오프 설정 (multiplier=1, min=1, max=8)
        wait_obj = retry_obj.wait
        assert wait_obj.multiplier == 1
        assert wait_obj.min == 1
        assert wait_obj.max == 8

        # OpenRouter 특화 재시도 대상 예외 타입 확인
        retry_condition = retry_obj.retry
        exception_types = retry_condition.exception_types
        assert OpenRouterResponseError in exception_types
        assert OpenRouterConnectionError in exception_types
        assert ConnectionError in exception_types
        assert TimeoutError in exception_types

    def test_validate_api_response_method_exists(self):
        """_validate_api_response 메서드가 존재하는지 테스트"""
        assert hasattr(self.gateway, "_validate_api_response")
        assert callable(self.gateway._validate_api_response)

    def test_extract_response_content_method_exists(self):
        """_extract_response_content 메서드가 존재하는지 테스트"""
        assert hasattr(self.gateway, "_extract_response_content")
        assert callable(self.gateway._extract_response_content)

    def test_validate_structured_response_method_exists(self):
        """_validate_structured_response 메서드가 존재하는지 테스트"""
        assert hasattr(self.gateway, "_validate_structured_response")
        assert callable(self.gateway._validate_structured_response)

    def test_validate_api_response_raises_openrouter_response_error_no_choices(self):
        """choices가 없는 경우 OpenRouterResponseError 발생 테스트"""
        mock_response = Mock()
        mock_response.choices = []
        raw_data = {"error": "no choices"}

        with pytest.raises(OpenRouterResponseError) as exc_info:
            self.gateway._validate_api_response(mock_response, raw_data)

        error = exc_info.value
        assert "choices가 없습니다" in str(error)
        assert error.raw_response == raw_data
        assert error.missing_field == "choices"

    def test_extract_response_content_raises_openrouter_response_error_no_content(self):
        """content가 없는 경우 OpenRouterResponseError 발생 테스트"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = None
        raw_data = {"choices": [{"message": {"content": None}}]}

        with pytest.raises(OpenRouterResponseError) as exc_info:
            self.gateway._extract_response_content(mock_response, raw_data)

        error = exc_info.value
        assert "content가 없습니다" in str(error)
        assert error.raw_response == raw_data
        assert error.missing_field == "content"

    def test_extract_response_content_returns_content_when_valid(self):
        """유효한 content가 있는 경우 올바르게 반환하는지 테스트"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "test content"
        raw_data = {"choices": [{"message": {"content": "test content"}}]}

        result = self.gateway._extract_response_content(mock_response, raw_data)

        assert result == "test content"

    def test_validate_structured_response_raises_error_when_none(self):
        """구조화된 응답이 None인 경우 OpenRouterResponseError 발생 테스트"""
        with pytest.raises(OpenRouterResponseError) as exc_info:
            self.gateway._validate_structured_response(None, "test response text")

        error = exc_info.value
        assert "유효한 JSON을 파싱할 수 없습니다" in str(error)

    def test_validate_structured_response_passes_when_valid(self):
        """유효한 구조화된 응답인 경우 예외가 발생하지 않는지 테스트"""
        mock_response = Mock()
        # 예외가 발생하지 않아야 함
        self.gateway._validate_structured_response(mock_response, "test response text")

    @patch("selvage.src.llm_gateway.openrouter.gateway.console")
    def test_validate_api_response_logs_debug_info_when_debug_mode(self, mock_console):
        """디버그 모드에서 원본 응답이 로깅되는지 테스트"""
        mock_console.is_debug_mode.return_value = True

        mock_response = Mock()
        mock_response.choices = []
        raw_data = {"error": "no choices"}

        with pytest.raises(OpenRouterResponseError):
            self.gateway._validate_api_response(mock_response, raw_data)

        # 디버그 모드에서 원본 응답이 로깅되었는지 확인
        mock_console.error.assert_any_call(f"원본 응답: {raw_data}")

    @patch("selvage.src.llm_gateway.openrouter.gateway.console")
    def test_extract_response_content_logs_debug_info_when_debug_mode(
        self, mock_console
    ):
        """디버그 모드에서 원본 응답이 로깅되는지 테스트"""
        mock_console.is_debug_mode.return_value = True

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = None
        raw_data = {"choices": [{"message": {"content": None}}]}

        with pytest.raises(OpenRouterResponseError):
            self.gateway._extract_response_content(mock_response, raw_data)

        # 디버그 모드에서 원본 응답이 로깅되었는지 확인
        mock_console.error.assert_any_call(f"원본 응답: {raw_data}")
