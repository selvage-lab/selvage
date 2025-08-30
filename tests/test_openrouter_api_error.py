"""OpenRouter API 관련 예외 클래스들 테스트"""

import pytest

from selvage.src.exceptions.openrouter_api_error import (
    OpenRouterAPIError,
    OpenRouterResponseError,
    OpenRouterConnectionError,
    OpenRouterAuthenticationError,
)
from selvage.src.exceptions.llm_gateway_error import LLMGatewayError


class TestOpenRouterAPIError:
    """OpenRouterAPIError 기본 클래스 테스트"""

    def test_basic_exception_creation(self):
        """기본 예외 생성 테스트"""
        error_message = "OpenRouter API 오류"
        error = OpenRouterAPIError(error_message)
        
        assert str(error) == error_message
        assert error.raw_response is None
        assert error.status_code is None

    def test_exception_with_raw_response(self):
        """raw_response가 있는 예외 테스트"""
        error_message = "API 응답 오류"
        raw_response = {"error": "Invalid request"}
        
        error = OpenRouterAPIError(error_message, raw_response=raw_response)
        
        assert str(error) == error_message
        assert error.raw_response == raw_response
        assert error.status_code is None

    def test_exception_with_status_code(self):
        """status_code가 있는 예외 테스트"""
        error_message = "HTTP 오류"
        status_code = 500
        
        error = OpenRouterAPIError(error_message, status_code=status_code)
        
        assert str(error) == error_message
        assert error.status_code == status_code
        assert error.raw_response is None

    def test_exception_with_all_parameters(self):
        """모든 파라미터가 있는 예외 테스트"""
        error_message = "완전한 오류"
        raw_response = {"error": "Server error"}
        status_code = 503
        
        error = OpenRouterAPIError(
            error_message, 
            raw_response=raw_response, 
            status_code=status_code
        )
        
        assert str(error) == error_message
        assert error.raw_response == raw_response
        assert error.status_code == status_code

    def test_inheritance_from_llm_gateway_error(self):
        """LLMGatewayError 상속 테스트"""
        error = OpenRouterAPIError("테스트 메시지")
        
        assert isinstance(error, LLMGatewayError)
        assert isinstance(error, Exception)


class TestOpenRouterResponseError:
    """OpenRouterResponseError 클래스 테스트"""

    def test_basic_exception_creation(self):
        """기본 예외 생성 테스트"""
        error_message = "응답 구조 오류"
        error = OpenRouterResponseError(error_message)
        
        assert str(error) == error_message
        assert error.raw_response is None
        assert error.missing_field is None

    def test_exception_with_missing_field(self):
        """missing_field가 있는 예외 테스트"""
        error_message = "필드 누락"
        missing_field = "choices"
        
        error = OpenRouterResponseError(error_message, missing_field=missing_field)
        
        assert str(error) == error_message
        assert error.missing_field == missing_field

    def test_exception_with_all_parameters(self):
        """모든 파라미터가 있는 예외 테스트"""
        error_message = "완전한 응답 오류"
        raw_response = {"incomplete": "response"}
        missing_field = "content"
        
        error = OpenRouterResponseError(
            error_message, 
            raw_response=raw_response, 
            missing_field=missing_field
        )
        
        assert str(error) == error_message
        assert error.raw_response == raw_response
        assert error.missing_field == missing_field

    def test_inheritance_from_openrouter_api_error(self):
        """OpenRouterAPIError 상속 테스트"""
        error = OpenRouterResponseError("테스트 메시지")
        
        assert isinstance(error, OpenRouterAPIError)
        assert isinstance(error, LLMGatewayError)
        assert isinstance(error, Exception)


class TestOpenRouterConnectionError:
    """OpenRouterConnectionError 클래스 테스트"""

    def test_basic_exception_creation(self):
        """기본 예외 생성 테스트"""
        error_message = "연결 오류"
        error = OpenRouterConnectionError(error_message)
        
        assert str(error) == error_message

    def test_inheritance_from_openrouter_api_error(self):
        """OpenRouterAPIError 상속 테스트"""
        error = OpenRouterConnectionError("테스트 메시지")
        
        assert isinstance(error, OpenRouterAPIError)
        assert isinstance(error, LLMGatewayError)
        assert isinstance(error, Exception)

    def test_with_inherited_parameters(self):
        """상속된 파라미터와 함께 테스트"""
        error_message = "네트워크 연결 실패"
        raw_response = {"timeout": True}
        status_code = 408
        
        error = OpenRouterConnectionError(
            error_message, 
            raw_response=raw_response, 
            status_code=status_code
        )
        
        assert str(error) == error_message
        assert error.raw_response == raw_response
        assert error.status_code == status_code


class TestOpenRouterAuthenticationError:
    """OpenRouterAuthenticationError 클래스 테스트"""

    def test_basic_exception_creation(self):
        """기본 예외 생성 테스트"""
        error_message = "인증 오류"
        error = OpenRouterAuthenticationError(error_message)
        
        assert str(error) == error_message

    def test_inheritance_from_openrouter_api_error(self):
        """OpenRouterAPIError 상속 테스트"""
        error = OpenRouterAuthenticationError("테스트 메시지")
        
        assert isinstance(error, OpenRouterAPIError)
        assert isinstance(error, LLMGatewayError)
        assert isinstance(error, Exception)

    def test_with_inherited_parameters(self):
        """상속된 파라미터와 함께 테스트"""
        error_message = "API 키 인증 실패"
        raw_response = {"error": "Invalid API key"}
        status_code = 401
        
        error = OpenRouterAuthenticationError(
            error_message, 
            raw_response=raw_response, 
            status_code=status_code
        )
        
        assert str(error) == error_message
        assert error.raw_response == raw_response
        assert error.status_code == status_code


class TestExceptionHierarchy:
    """예외 계층 구조 테스트"""

    def test_all_exceptions_are_openrouter_api_errors(self):
        """모든 예외가 OpenRouterAPIError의 하위 클래스인지 테스트"""
        response_error = OpenRouterResponseError("테스트")
        connection_error = OpenRouterConnectionError("테스트")
        auth_error = OpenRouterAuthenticationError("테스트")
        
        assert isinstance(response_error, OpenRouterAPIError)
        assert isinstance(connection_error, OpenRouterAPIError)
        assert isinstance(auth_error, OpenRouterAPIError)

    def test_all_exceptions_are_llm_gateway_errors(self):
        """모든 예외가 LLMGatewayError의 하위 클래스인지 테스트"""
        api_error = OpenRouterAPIError("테스트")
        response_error = OpenRouterResponseError("테스트")
        connection_error = OpenRouterConnectionError("테스트")
        auth_error = OpenRouterAuthenticationError("테스트")
        
        assert isinstance(api_error, LLMGatewayError)
        assert isinstance(response_error, LLMGatewayError)
        assert isinstance(connection_error, LLMGatewayError)
        assert isinstance(auth_error, LLMGatewayError)