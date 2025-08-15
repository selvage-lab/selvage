"""
에러 패턴 파서 테스트 모듈

실제 수집된 에러 데이터를 사용하여 패턴 기반 파싱 시스템의
정확성과 성능을 검증합니다.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from selvage.src.models.error_pattern_parser import ErrorPatternParser
from selvage.src.models.error_response import ErrorResponse


class TestErrorPatternParser:
    """에러 패턴 파서 테스트 클래스"""

    @pytest.fixture
    def parser(self) -> ErrorPatternParser:
        """기본 패턴 파서 인스턴스"""
        return ErrorPatternParser()

    @pytest.fixture
    def collected_error_data(self) -> dict[str, Any]:
        """실제 수집된 에러 데이터를 로드합니다."""
        results_file = (
            Path(__file__).parent
            / "results"
            / "context_limit_errors_20250807_020818.json"
        )

        if not results_file.exists():
            pytest.skip("수집된 에러 데이터 파일이 없습니다.")

        with open(results_file, encoding="utf-8") as f:
            return json.load(f)

    def test_parser_initialization(self, parser: ErrorPatternParser):
        """패턴 파서 초기화 테스트"""
        assert parser is not None
        supported_providers = parser.get_supported_providers()
        expected_providers = ["openai", "anthropic", "google", "openrouter"]

        for provider in expected_providers:
            assert provider in supported_providers

    def test_openai_context_limit_error_parsing(self, parser: ErrorPatternParser):
        """OpenAI context limit 에러 파싱 테스트"""
        # 실제 수집된 에러 메시지 시뮬레이션
        mock_error = MagicMock()
        error_message = (
            "Error code: 400 - {'error': {'message': \"This model's maximum context length is 128000 tokens. "
            'However, your messages resulted in 273619 tokens. Please reduce the length of the messages.", '
            "'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}"
        )
        mock_error.__str__ = MagicMock(return_value=error_message)

        # OpenAI 에러는 status_code를 직접 가지지 않음 - 명시적으로 제거
        del mock_error.status_code

        # HTTP response 속성 시뮬레이션
        mock_response = MagicMock(status_code=400)
        mock_response.json.return_value = {
            "error": {
                "message": "This model's maximum context length is 128000 tokens. However, your messages resulted in 273619 tokens.",
                "type": "invalid_request_error",
                "param": "messages",
                "code": "context_length_exceeded",
            }
        }
        mock_error.response = mock_response

        result = parser.parse_error("openai", mock_error)

        assert result.error_type == "context_limit_exceeded"
        assert result.error_code == "context_length_exceeded"
        assert result.http_status_code == 400
        assert result.matched_pattern == "context_limit_exceeded"

        # 토큰 정보 확인
        assert result.token_info is not None
        assert result.token_info.max_tokens == 128000
        assert result.token_info.actual_tokens == 273619

    def test_anthropic_context_limit_error_parsing(self, parser: ErrorPatternParser):
        """Anthropic context limit 에러 파싱 테스트"""
        mock_error = MagicMock()
        error_message = (
            "Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', "
            "'message': 'prompt is too long: 209924 tokens > 200000 maximum'}}"
        )
        mock_error.__str__ = MagicMock(return_value=error_message)

        # Anthropic 에러 속성 시뮬레이션
        mock_error.status_code = 400
        mock_error.type = "invalid_request_error"
        mock_error.body = {
            "type": "error",
            "error": {
                "type": "invalid_request_error",
                "message": "prompt is too long: 209924 tokens > 200000 maximum",
            },
        }

        result = parser.parse_error("anthropic", mock_error)

        assert result.error_type == "context_limit_exceeded"
        assert result.error_code == "invalid_request_error"
        assert result.http_status_code == 400
        assert result.matched_pattern == "context_limit_exceeded"

        # 토큰 정보 확인
        assert result.token_info is not None
        assert result.token_info.actual_tokens == 209924
        assert result.token_info.max_tokens == 200000

    def test_openrouter_context_limit_error_parsing(self, parser: ErrorPatternParser):
        """OpenRouter context limit 에러 파싱 테스트"""
        mock_error = MagicMock()
        # OpenRouter context limit 에러 메시지 시뮬레이션
        error_message = (
            "This endpoint's maximum context length is 1000000 tokens. "
            "However, you requested about 2315418 tokens (2315418 of text input)."
        )
        mock_error.__str__ = MagicMock(return_value=error_message)
        
        # OpenRouter JSON 응답 구조 시뮬레이션
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "error": {
                "message": error_message
            }
        })
        mock_error.response = mock_response

        result = parser.parse_error("openrouter", mock_error)

        assert result.error_type == "context_limit_exceeded"
        assert result.matched_pattern == "context_limit_exceeded"

        # 토큰 정보 확인
        assert result.token_info is not None
        assert result.token_info.max_tokens == 1000000
        assert result.token_info.actual_tokens == 2315418

    def test_google_quota_error_parsing(self, parser: ErrorPatternParser):
        """Google quota 에러 파싱 테스트"""
        mock_error = MagicMock()
        error_message = (
            "429 RESOURCE_EXHAUSTED. You exceeded your current quota, "
            "please check your plan and billing details."
        )
        mock_error.__str__ = MagicMock(return_value=error_message)

        result = parser.parse_error("google", mock_error)

        assert result.error_type == "quota_exceeded"
        assert result.matched_pattern == "quota_exceeded"

    def test_unknown_provider_error(self, parser: ErrorPatternParser):
        """알 수 없는 프로바이더 에러 테스트"""
        mock_error = MagicMock()
        mock_error.__str__ = MagicMock(return_value="Unknown error")

        result = parser.parse_error("unknown_provider", mock_error)

        assert result.error_type == "api_error"
        assert result.matched_pattern is None

    def test_no_matching_pattern_error(self, parser: ErrorPatternParser):
        """매칭되는 패턴이 없는 경우 테스트"""
        mock_error = MagicMock()
        mock_error.__str__ = MagicMock(return_value="Completely unknown error message")

        result = parser.parse_error("openai", mock_error)

        assert result.error_type == "api_error"
        assert result.matched_pattern == "api_error"  # catch-all 패턴

    def test_error_response_integration(self, parser: ErrorPatternParser):
        """ErrorResponse 클래스와의 통합 테스트"""
        # OpenAI 에러 시뮬레이션
        mock_error = MagicMock()
        error_message = (
            "This model's maximum context length is 128000 tokens. "
            "However, your messages resulted in 150000 tokens."
        )
        mock_error.__str__ = MagicMock(return_value=error_message)

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": {"code": "context_length_exceeded"}}
        mock_error.response = mock_response

        # ErrorResponse.from_exception 메서드 테스트
        error_response = ErrorResponse.from_exception(mock_error, "openai")

        assert error_response.error_type == "context_limit_exceeded"
        assert error_response.error_code == "context_length_exceeded"
        assert error_response.provider == "openai"
        assert error_response.is_context_limit_error() is True

        # 토큰 정보가 raw_error에 포함되는지 확인
        assert "actual_tokens" in error_response.raw_error
        assert "max_tokens" in error_response.raw_error
        assert error_response.raw_error["actual_tokens"] == 150000
        assert error_response.raw_error["max_tokens"] == 128000

    @pytest.mark.parametrize(
        "provider,pattern_name",
        [
            ("openai", "context_limit_exceeded"),
            ("anthropic", "context_limit_exceeded"),
            ("google", "quota_exceeded"),
            ("openrouter", "context_limit_exceeded"),
        ],
    )
    def test_pattern_info_retrieval(
        self, parser: ErrorPatternParser, provider: str, pattern_name: str
    ):
        """패턴 정보 조회 테스트"""
        pattern_info = parser.get_pattern_info(provider, pattern_name)

        assert pattern_info is not None
        assert "keywords" in pattern_info
        assert "error_type" in pattern_info

    def test_collected_error_data_validation(
        self, parser: ErrorPatternParser, collected_error_data: dict[str, Any]
    ):
        """실제 수집된 에러 데이터를 사용한 검증 테스트"""
        results = collected_error_data.get("results", [])

        for result_data in results:
            provider = result_data["provider"]
            error_message = result_data["error_message"]

            # 에러 메시지만으로 Mock 에러 생성
            mock_error = MagicMock()
            mock_error.__str__ = MagicMock(return_value=error_message)

            # HTTP 상태 코드와 에러 코드 설정
            if "http_status_code" in result_data:
                mock_error.response = MagicMock()
                mock_error.response.status_code = result_data["http_status_code"]
                
                # OpenRouter의 경우 JSON 응답 구조 추가
                if provider == "openrouter":
                    mock_error.response.text = json.dumps({
                        "error": {
                            "message": error_message
                        }
                    })

            parsing_result = parser.parse_error(provider, mock_error)

            # 기본적인 파싱 성공 확인
            assert parsing_result.error_type is not None
            assert (
                parsing_result.error_type != "parse_error"
            )  # 파싱 자체가 실패하면 안 됨

            # 실제 데이터에서 context limit 관련 에러는 올바르게 분류되어야 함
            if "context" in error_message.lower() and "token" in error_message.lower():
                assert parsing_result.error_type in ["context_limit_exceeded"]

            print(
                f"✅ {provider}: {parsing_result.error_type} (pattern: {parsing_result.matched_pattern})"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
