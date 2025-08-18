"""JSONParsingError 예외 클래스 테스트"""

import pytest

from selvage.src.exceptions.json_parsing_error import JSONParsingError
from selvage.src.exceptions.llm_gateway_error import LLMGatewayError


class TestJSONParsingError:
    """JSONParsingError 클래스 테스트"""

    def test_basic_exception_creation(self):
        """기본 예외 생성 테스트"""
        error_message = "JSON 파싱에 실패했습니다"
        error = JSONParsingError(error_message)
        
        assert str(error) == error_message
        assert error.raw_response == ""
        assert error.parsing_error is None

    def test_exception_with_raw_response(self):
        """raw_response가 있는 예외 테스트"""
        error_message = "JSON 파싱에 실패했습니다"
        raw_response = '{"invalid": json}'
        
        error = JSONParsingError(error_message, raw_response=raw_response)
        
        assert str(error) == error_message
        assert error.raw_response == raw_response
        assert error.parsing_error is None

    def test_exception_with_parsing_error(self):
        """parsing_error가 있는 예외 테스트"""
        error_message = "JSON 파싱에 실패했습니다"
        parsing_error = ValueError("Invalid JSON format")
        
        error = JSONParsingError(error_message, parsing_error=parsing_error)
        
        expected_str = f"{error_message} (원인: ValueError: {parsing_error})"
        assert str(error) == expected_str
        assert error.parsing_error == parsing_error

    def test_exception_with_all_parameters(self):
        """모든 파라미터가 있는 예외 테스트"""
        error_message = "JSON 파싱에 실패했습니다"
        raw_response = '{"malformed": json,}'
        parsing_error = SyntaxError("Unexpected token")
        
        error = JSONParsingError(
            error_message, 
            raw_response=raw_response, 
            parsing_error=parsing_error
        )
        
        expected_str = f"{error_message} (원인: SyntaxError: {parsing_error})"
        assert str(error) == expected_str
        assert error.raw_response == raw_response
        assert error.parsing_error == parsing_error

    def test_inheritance_from_llm_gateway_error(self):
        """LLMGatewayError 상속 테스트"""
        error = JSONParsingError("테스트 메시지")
        
        assert isinstance(error, LLMGatewayError)
        assert isinstance(error, Exception)

    def test_str_method_without_parsing_error(self):
        """parsing_error가 None일 때 __str__ 메서드 테스트"""
        error_message = "기본 에러 메시지"
        error = JSONParsingError(error_message, parsing_error=None)
        
        assert str(error) == error_message

    def test_str_method_with_empty_parsing_error(self):
        """빈 parsing_error와 함께하는 __str__ 메서드 테스트"""
        error_message = "기본 에러 메시지"
        empty_error = Exception("")
        
        error = JSONParsingError(error_message, parsing_error=empty_error)
        
        expected_str = f"{error_message} (원인: Exception: )"
        assert str(error) == expected_str