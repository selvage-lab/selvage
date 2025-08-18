"""CLI 에러 처리 개선 테스트"""

import pytest
from unittest.mock import Mock, patch

from selvage.cli import _handle_api_error
from selvage.src.exceptions.openrouter_api_error import (
    OpenRouterAPIError,
    OpenRouterResponseError,
    OpenRouterAuthenticationError,
)
from selvage.src.exceptions.json_parsing_error import JSONParsingError
from selvage.src.models.error_response import ErrorResponse


class TestCLIErrorHandling:
    """CLI 에러 처리 개선 테스트"""

    def test_handle_openrouter_error_function_exists(self):
        """_handle_openrouter_error 함수가 존재하는지 테스트"""
        from selvage.cli import _handle_openrouter_error
        assert callable(_handle_openrouter_error)

    def test_handle_json_parsing_error_function_exists(self):
        """_handle_json_parsing_error 함수가 존재하는지 테스트"""
        from selvage.cli import _handle_json_parsing_error
        assert callable(_handle_json_parsing_error)

    @patch('selvage.cli.console')
    def test_handle_openrouter_authentication_error(self, mock_console):
        """OpenRouter 인증 에러 처리 테스트"""
        from selvage.cli import _handle_openrouter_error
        
        error = OpenRouterAuthenticationError("Invalid API key")
        
        # 특화 핸들러는 예외를 raise하지 않음 (로깅만 수행)
        _handle_openrouter_error(error)
        
        # 인증 오류 메시지와 해결 방법 출력 확인
        mock_console.error.assert_any_call("OpenRouter API 인증 오류")
        mock_console.info.assert_any_call("해결 방법:")
        mock_console.print.assert_any_call("  1. OPENROUTER_API_KEY 환경변수 확인")
        mock_console.print.assert_any_call("  2. API 키 유효성 확인")

    @patch('selvage.cli.console')
    @patch('selvage.cli.config')
    def test_handle_openrouter_response_error_with_debug(self, mock_config, mock_console):
        """OpenRouter 응답 에러 처리 테스트 (디버그 모드)"""
        from selvage.cli import _handle_openrouter_error
        
        # 디버그 모드 활성화
        mock_config.is_debug_mode.return_value = True
        
        raw_response = {"error": "no choices"}
        error = OpenRouterResponseError(
            "API 응답 구조 오류",
            raw_response=raw_response,
            missing_field="choices"
        )
        
        # 특화 핸들러는 예외를 raise하지 않음 (로깅만 수행)
        _handle_openrouter_error(error)
        
        # 응답 구조 오류 메시지 확인
        mock_console.error.assert_any_call("OpenRouter API 응답 구조 오류: API 응답 구조 오류")
        mock_console.error.assert_any_call("누락된 필드: choices")
        mock_console.error.assert_any_call(f"원본 응답: {raw_response}")

    @patch('selvage.cli.console')
    def test_handle_openrouter_general_error(self, mock_console):
        """OpenRouter 일반 에러 처리 테스트"""
        from selvage.cli import _handle_openrouter_error
        
        error = OpenRouterAPIError("General API error")
        
        # 특화 핸들러는 예외를 raise하지 않음 (로깅만 수행)
        _handle_openrouter_error(error)
        
        mock_console.error.assert_any_call("OpenRouter API 오류: General API error")

    @patch('selvage.cli.console')
    @patch('selvage.cli.config')
    def test_handle_json_parsing_error_with_debug(self, mock_config, mock_console):
        """JSON 파싱 에러 처리 테스트 (디버그 모드)"""
        from selvage.cli import _handle_json_parsing_error
        
        # 디버그 모드 활성화
        mock_config.is_debug_mode.return_value = True
        
        parsing_error = ValueError("Invalid JSON")
        raw_response = "invalid json response"
        error = JSONParsingError(
            "JSON 파싱에 실패했습니다",
            raw_response=raw_response,
            parsing_error=parsing_error
        )
        
        # 특화 핸들러는 예외를 raise하지 않음 (로깅만 수행)
        _handle_json_parsing_error(error)
        
        # JSON 파싱 에러 메시지 확인
        mock_console.error.assert_any_call("구조화된 응답 파싱에 실패했습니다")
        mock_console.error.assert_any_call(f"오류: {error}")
        mock_console.error.assert_any_call("디버그 정보:")
        mock_console.error.assert_any_call(f"  파싱 오류: {parsing_error}")
        mock_console.error.assert_any_call(f"  원본 응답 (일부): {raw_response}")

    @patch('selvage.cli.console')
    @patch('selvage.cli.config')
    def test_handle_json_parsing_error_without_debug(self, mock_config, mock_console):
        """JSON 파싱 에러 처리 테스트 (디버그 모드 비활성화)"""
        from selvage.cli import _handle_json_parsing_error
        
        # 디버그 모드 비활성화
        mock_config.is_debug_mode.return_value = False
        
        error = JSONParsingError("JSON 파싱에 실패했습니다")
        
        # 특화 핸들러는 예외를 raise하지 않음 (로깅만 수행)
        _handle_json_parsing_error(error)
        
        # 기본 에러 메시지만 확인
        mock_console.error.assert_any_call("구조화된 응답 파싱에 실패했습니다")
        mock_console.error.assert_any_call(f"오류: {error}")
        # 디버그 정보는 출력되지 않음
        assert not any(call.args[0] == "디버그 정보:" for call in mock_console.error.call_args_list)

    def test_handle_api_error_calls_specific_handlers(self):
        """_handle_api_error가 특정 예외 타입에 대해 특화 핸들러를 호출하는지 테스트"""
        openrouter_error = OpenRouterAPIError("OpenRouter error")
        json_parsing_error = JSONParsingError("JSON error")
        
        # OpenRouter 에러의 경우 특화 핸들러 호출 확인
        with patch('selvage.cli._handle_openrouter_error') as mock_handle_openrouter:
            # ErrorResponse에 exception 속성을 설정 (monkey patching)
            error_response = ErrorResponse.from_exception(openrouter_error, "openrouter")
            error_response.exception = openrouter_error  # 테스트를 위해 추가
            
            with pytest.raises(Exception):
                _handle_api_error(error_response)
            
            mock_handle_openrouter.assert_called_once_with(openrouter_error)
        
        # JSON 파싱 에러의 경우 특화 핸들러 호출 확인
        with patch('selvage.cli._handle_json_parsing_error') as mock_handle_json:
            error_response = ErrorResponse.from_exception(json_parsing_error, "openrouter")
            error_response.exception = json_parsing_error  # 테스트를 위해 추가
            
            with pytest.raises(Exception):
                _handle_api_error(error_response)
            
            mock_handle_json.assert_called_once_with(json_parsing_error)

    @patch('selvage.cli.console')
    def test_handle_api_error_fallback_to_general_handling(self, mock_console):
        """일반적인 에러의 경우 기존 처리 로직을 사용하는지 테스트"""
        general_error = ValueError("General error")
        error_response = ErrorResponse.from_exception(general_error, "openai")
        error_response.exception = general_error  # 테스트를 위해 추가
        
        with pytest.raises(Exception):
            _handle_api_error(error_response)
        
        # 기존 일반 에러 처리 메시지 확인
        mock_console.error.assert_any_call("API 오류 (openai): General error")