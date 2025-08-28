"""SynthesisAPIClient 테스트"""

from unittest.mock import Mock, patch

import anthropic
import instructor
import pytest
from google import genai

from selvage.src.llm_gateway.openrouter.http_client import OpenRouterHTTPClient
from selvage.src.model_config import ModelInfoDict
from selvage.src.models.model_provider import ModelProvider
from selvage.src.multiturn.synthesis_api_client import SynthesisAPIClient
from selvage.src.utils.token.models import EstimatedCost, SummarySynthesisResponse


class TestSynthesisAPIClient:
    """SynthesisAPIClient 클래스 테스트"""

    @pytest.fixture
    def api_client(self) -> SynthesisAPIClient:
        """SynthesisAPIClient 인스턴스 생성"""
        return SynthesisAPIClient("test-model")

    @pytest.fixture
    def sample_model_info(self) -> ModelInfoDict:
        """테스트용 모델 정보 생성"""
        return {
            "full_name": "gpt-5",
            "aliases": [],
            "description": "테스트 모델",
            "provider": ModelProvider.OPENAI,
            "params": {"temperature": 0.0},
            "thinking_mode": False,
            "pricing": {"input": 2.5, "output": 10.0, "description": "test"},
            "context_limit": 128000,
            "openrouter_name": "openai/gpt-5",
        }

    def test_initialization(self, api_client: SynthesisAPIClient) -> None:
        """API 클라이언트 초기화 테스트"""
        # Then: 모델명이 올바르게 설정되어야 함
        assert api_client.model_name == "test-model"

    @patch("selvage.src.multiturn.synthesis_api_client.get_api_key")
    @patch("selvage.src.multiturn.synthesis_api_client.LLMClientFactory.create_client")
    @patch("selvage.src.multiturn.synthesis_api_client.ModelConfig")
    def test_execute_synthesis_success(
        self,
        mock_model_config_class: Mock,
        mock_create_client: Mock,
        mock_get_api_key: Mock,
        api_client: SynthesisAPIClient,
        sample_model_info: ModelInfoDict,
    ) -> None:
        """성공적인 합성 실행 테스트"""
        # Given: Mock 설정
        mock_config_instance = Mock()
        mock_config_instance.get_model_info.return_value = sample_model_info
        mock_model_config_class.return_value = mock_config_instance
        mock_get_api_key.return_value = "test_api_key"

        # Mock Instructor 클라이언트 설정
        mock_instructor_client = Mock()
        mock_create_client.return_value = mock_instructor_client

        # 성공적인 응답 설정
        mock_structured_response = SummarySynthesisResponse(
            summary="통합된 요약입니다."
        )
        mock_raw_response = Mock()
        mock_raw_response.usage = Mock()
        mock_raw_response.usage.prompt_tokens = 100
        mock_raw_response.usage.completion_tokens = 50

        mock_instructor_client.chat.completions.create_with_completion.return_value = (
            mock_structured_response,
            mock_raw_response,
        )

        # When: 합성 실행
        synthesis_data = {"task": "summary_synthesis", "summaries": ["요약1", "요약2"]}
        system_prompt = "테스트 시스템 프롬프트"

        result, cost = api_client.execute_synthesis(
            synthesis_data, SummarySynthesisResponse, system_prompt
        )

        # Then: 성공적인 결과 반환
        assert result is not None
        assert result.summary == "통합된 요약입니다."
        assert cost is not None
        assert cost.model == "gpt-5"  # sample_model_info의 full_name 사용

    @patch("selvage.src.multiturn.synthesis_api_client.get_api_key")
    def test_execute_synthesis_no_api_key(
        self,
        mock_get_api_key: Mock,
        api_client: SynthesisAPIClient,
    ) -> None:
        """API 키 없을 때 합성 실행 테스트"""
        # Given: API 키 없음
        mock_get_api_key.return_value = ""

        # When: 합성 실행
        synthesis_data = {"task": "summary_synthesis", "summaries": ["요약1"]}
        system_prompt = "테스트 시스템 프롬프트"

        result, cost = api_client.execute_synthesis(
            synthesis_data, SummarySynthesisResponse, system_prompt
        )

        # Then: None과 0 비용 반환
        assert result is None
        assert cost.total_cost_usd == 0.0

    def test_create_request_params_openai(
        self, api_client: SynthesisAPIClient, sample_model_info: ModelInfoDict
    ) -> None:
        """OpenAI 요청 파라미터 생성 테스트"""
        # Given: 메시지와 모델 정보
        messages = [
            {"role": "system", "content": "시스템 프롬프트"},
            {"role": "user", "content": "사용자 메시지"},
        ]

        # When: 요청 파라미터 생성
        params = api_client._create_request_params(
            messages, sample_model_info, SummarySynthesisResponse, instructor.Instructor
        )

        # Then: OpenAI 형식의 파라미터 생성
        assert params["model"] == "gpt-5"
        assert params["messages"] == messages
        assert params["max_completion_tokens"] == 5000
        assert params["reasoning_effort"] == "medium"

    def test_create_request_params_anthropic(
        self, api_client: SynthesisAPIClient
    ) -> None:
        """Anthropic 요청 파라미터 생성 테스트"""
        # Given: Anthropic 모델 정보
        anthropic_model_info = {
            "full_name": "claude-sonnet-4",
            "provider": ModelProvider.ANTHROPIC,
            "thinking_mode": False,
        }
        messages = [
            {"role": "system", "content": "시스템 프롬프트"},
            {"role": "user", "content": "사용자 메시지"},
        ]

        # When: 요청 파라미터 생성
        params = api_client._create_request_params(
            messages,
            anthropic_model_info,
            SummarySynthesisResponse,
            anthropic.Anthropic,
        )

        # Then: Anthropic 형식의 파라미터 생성
        assert params["model"] == "claude-sonnet-4"
        assert params["system"] == "시스템 프롬프트"
        assert params["messages"] == [{"role": "user", "content": "사용자 메시지"}]
        assert params["max_tokens"] == 5000
        assert params["temperature"] == 0.1

    def test_create_request_params_google(self, api_client: SynthesisAPIClient) -> None:
        """Google 요청 파라미터 생성 테스트"""
        # Given: Google 모델 정보
        google_model_info = {
            "full_name": "gemini-2.5-pro",
            "provider": ModelProvider.GOOGLE,
        }
        messages = [
            {"role": "system", "content": "시스템 프롬프트"},
            {"role": "user", "content": "사용자 메시지"},
        ]

        # When: 요청 파라미터 생성
        params = api_client._create_request_params(
            messages, google_model_info, SummarySynthesisResponse, genai.Client
        )

        # Then: Google 형식의 파라미터 생성
        assert params["model"] == "gemini-2.5-pro"
        # contents가 단일 문자열로 결합됨
        assert params["contents"] == "사용자 메시지"
        # generation_config에 system_instruction과 response_schema가 설정됨
        assert params["config"].system_instruction == "시스템 프롬프트"
        assert params["config"].response_schema == SummarySynthesisResponse

    def test_create_request_params_openrouter(
        self, api_client: SynthesisAPIClient
    ) -> None:
        """OpenRouter 요청 파라미터 생성 테스트"""
        # Given: OpenRouter 모델 정보
        openrouter_model_info = {
            "full_name": "test-model",
            "provider": ModelProvider.OPENROUTER,
            "openrouter_name": "test/model",
        }
        messages = [
            {"role": "system", "content": "시스템 프롬프트"},
            {"role": "user", "content": "사용자 메시지"},
        ]

        # When: 요청 파라미터 생성
        params = api_client._create_request_params(
            messages,
            openrouter_model_info,
            SummarySynthesisResponse,
            OpenRouterHTTPClient,
        )

        # Then: OpenRouter 형식의 파라미터 생성
        assert params["model"] == "test/model"
        assert params["messages"] == messages
        assert params["max_tokens"] == 5000
        assert params["temperature"] == 0.1
        assert params["response_format"]["type"] == "json_schema"
        assert (
            params["response_format"]["json_schema"]["name"]
            == "summary_synthesis_response"
        )
        assert params["usage"]["include"] is True

    def test_create_request_params_unsupported_provider(
        self, api_client: SynthesisAPIClient
    ) -> None:
        """지원하지 않는 프로바이더 테스트"""
        # Given: 지원하지 않는 프로바이더
        unsupported_model_info = {
            "full_name": "unsupported-model",
            "provider": "UNSUPPORTED",  # type: ignore
        }
        messages = [{"role": "user", "content": "테스트"}]

        # When & Then: 예외 발생
        with pytest.raises(ValueError, match="지원하지 않는 프로바이더"):
            api_client._create_request_params(
                messages,
                unsupported_model_info,
                SummarySynthesisResponse,
                instructor.Instructor,
            )

    @patch(
        "selvage.src.multiturn.synthesis_api_client.CostEstimator.estimate_cost_from_openai_usage"
    )
    def test_calculate_synthesis_cost_openai(
        self, mock_cost_estimator: Mock, api_client: SynthesisAPIClient
    ) -> None:
        """OpenAI 비용 계산 테스트"""
        # Given: OpenAI 응답과 비용 계산 Mock
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_cost_estimator.return_value = EstimatedCost.get_zero_cost("gpt-5")

        # When: 비용 계산
        cost = api_client._calculate_synthesis_cost(
            ModelProvider.OPENAI, mock_response, "gpt-5"
        )

        # Then: 비용 계산기가 호출되어야 함
        assert cost is not None
        mock_cost_estimator.assert_called_once()

    def test_calculate_synthesis_cost_no_usage(
        self, api_client: SynthesisAPIClient
    ) -> None:
        """usage 정보 없을 때 비용 계산 테스트"""
        # Given: usage 정보가 없는 응답
        mock_response = Mock()
        mock_response.usage = None

        # When: 비용 계산
        cost = api_client._calculate_synthesis_cost(
            ModelProvider.OPENAI, mock_response, "test-model"
        )

        # Then: 0 비용 반환
        assert cost.total_cost_usd == 0.0
        assert cost.model == "test-model"

    def test_call_provider_api_unsupported(
        self, api_client: SynthesisAPIClient
    ) -> None:
        """지원하지 않는 프로바이더 API 호출 테스트"""
        # Given: 지원하지 않는 프로바이더
        mock_client = Mock()
        params = {"test": "params"}

        # When & Then: 예외 발생
        with pytest.raises(ValueError, match="지원하지 않는 프로바이더"):
            api_client._call_provider_api(
                "UNSUPPORTED",
                mock_client,
                params,
                SummarySynthesisResponse,  # type: ignore
            )
