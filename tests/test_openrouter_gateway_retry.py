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

        # 재시도 횟수 (최대 2회)
        assert retry_obj.stop.max_attempt_number == 2

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


class TestOpenRouterGatewayModelSpecific:
    """OpenRouterGateway 모델별 특수 파라미터 테스트"""

    def test_is_claude_model_detection(self):
        """Claude 모델 식별 함수 테스트"""
        model_info = {
            "full_name": "claude-sonnet-4",
            "provider": ModelProvider.OPENROUTER,
            "openrouter_name": "anthropic/claude-sonnet-4",
            "description": "Test Claude model",
        }
        
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}):
            gateway = OpenRouterGateway(model_info)
            
        # Claude 모델 식별 테스트
        assert gateway._is_claude_model("anthropic/claude-sonnet-4") is True
        assert gateway._is_claude_model("anthropic/claude-haiku-3.5") is True
        assert gateway._is_claude_model("openai/gpt-5") is False
        assert gateway._is_claude_model("google/gemini-2.5-pro") is False

    def test_is_gpt5_model_detection(self):
        """GPT-5 모델 식별 함수 테스트"""
        model_info = {
            "full_name": "gpt-5",
            "provider": ModelProvider.OPENROUTER,
            "openrouter_name": "openai/gpt-5",
            "description": "Test GPT-5 model",
        }
        
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}):
            gateway = OpenRouterGateway(model_info)
            
        # GPT-5 모델 식별 테스트
        assert gateway._is_gpt5_model("openai/gpt-5") is True
        assert gateway._is_gpt5_model("openai/gpt-5-mini") is True
        assert gateway._is_gpt5_model("openai/gpt-5-nano") is True
        assert gateway._is_gpt5_model("openai/gpt-4o") is False
        assert gateway._is_gpt5_model("anthropic/claude-sonnet-4") is False

    def test_gpt5_reasoning_effort_parameter_processing(self):
        """GPT-5 모델의 reasoning_effort 파라미터 처리 테스트"""
        model_info = {
            "full_name": "gpt-5",
            "provider": ModelProvider.OPENROUTER,
            "openrouter_name": "openai/gpt-5",
            "description": "Test GPT-5 model",
            "params": {
                "reasoning_effort": "high",
                "temperature": 0.0,
            },
        }
        
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}):
            gateway = OpenRouterGateway(model_info)
            
        messages = [{"role": "user", "content": "Test message"}]
        
        # _create_request_params 호출하여 파라미터 확인
        params = gateway._create_request_params(messages)
        
        # GPT-5 reasoning_effort 파라미터가 reasoning.effort로 변환되었는지 확인
        assert "reasoning" in params
        assert params["reasoning"]["effort"] == "high"
        assert params["temperature"] == 0.0
        # reasoning_effort 파라미터는 제거되어야 함
        assert "reasoning_effort" not in params

    def test_non_gpt5_model_ignores_reasoning_effort(self):
        """GPT-5가 아닌 모델은 reasoning_effort 파라미터를 무시하는지 테스트"""
        model_info = {
            "full_name": "gemini-2.5-pro",
            "provider": ModelProvider.OPENROUTER,
            "openrouter_name": "google/gemini-2.5-pro",
            "description": "Test Gemini model",
            "params": {
                "reasoning_effort": "high",  # GPT-5가 아니므로 무시되어야 함
                "temperature": 0.0,
            },
        }
        
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}):
            gateway = OpenRouterGateway(model_info)
            
        messages = [{"role": "user", "content": "Test message"}]
        
        # _create_request_params 호출하여 파라미터 확인
        params = gateway._create_request_params(messages)
        
        # reasoning 파라미터가 추가되지 않아야 함
        assert "reasoning" not in params
        # reasoning_effort는 일반 파라미터로 그대로 전달되어야 함
        assert params["reasoning_effort"] == "high"
        assert params["temperature"] == 0.0

    @patch("selvage.src.llm_gateway.openrouter.gateway.console")
    def test_gpt5_reasoning_effort_logging(self, mock_console):
        """GPT-5 reasoning_effort 파라미터 처리 시 로깅 테스트"""
        model_info = {
            "full_name": "gpt-5-high",
            "provider": ModelProvider.OPENROUTER,
            "openrouter_name": "openai/gpt-5",
            "description": "Test GPT-5 High model",
            "params": {
                "reasoning_effort": "high",
            },
        }
        
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}):
            gateway = OpenRouterGateway(model_info)
            
        messages = [{"role": "user", "content": "Test message"}]
        
        # _create_request_params 호출
        gateway._create_request_params(messages)
        
        # 로깅이 호출되었는지 확인
        mock_console.log_info.assert_called_with("GPT-5 추론 강도 설정: effort=high")
