import os
import unittest
from unittest.mock import patch

from selvage.src.llm_gateway.gateway_factory import GatewayFactory
from selvage.src.utils.token.models import StructuredReviewResponse

COMMON_TEST_MESSAGES = [
    {"role": "system", "content": "시스템 지시: 코드 리뷰를 수행하세요."},
    {
        "role": "user",
        "content": "이 코드를 검토해주세요: def hello(): print('world')",
    },
]


class TestRequestParamsCreation(unittest.TestCase):
    """프로바이더별 요청 파라미터 생성 테스트"""

    @patch("selvage.src.llm_gateway.openai_gateway.get_api_key")
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=True)
    def test_openai_create_request_params(self, mock_get_api_key):
        """OpenAI 게이트웨이의 요청 파라미터 생성을 테스트합니다."""
        # 설정
        mock_get_api_key.return_value = "fake-api-key"
        gateway = GatewayFactory.create("gpt-5.3-codex")

        # 테스트 메시지
        messages = COMMON_TEST_MESSAGES

        # 테스트 실행
        params = gateway._create_request_params(messages)

        # 검증
        self.assertEqual(params["model"], "gpt-5.3-codex")
        self.assertEqual(params["messages"], messages)
        self.assertEqual(params["reasoning_effort"], "high")  # gpt-5.3-codex 모델의 기본 파라미터

    @patch("selvage.src.llm_gateway.claude_gateway.get_api_key")
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=True)  # OpenRouter 키 없음
    def test_claude_create_request_params(
        self, mock_get_api_key
    ):
        """Claude 게이트웨이의 요청 파라미터 생성을 테스트합니다."""
        # 설정
        mock_get_api_key.return_value = "fake-api-key"
        gateway = GatewayFactory.create("claude-sonnet-5")

        # 테스트 메시지
        messages = COMMON_TEST_MESSAGES

        # 테스트 실행
        params = gateway._create_request_params(messages)

        # 검증 (model은 full_name을 사용)
        self.assertEqual(params["model"], "claude-sonnet-5")
        # Claude는 system 메시지를 별도 파라미터로 분리하므로 user 메시지만 남음
        self.assertEqual(len(params["messages"]), 1)
        self.assertEqual(params["messages"][0]["role"], "user")
        self.assertEqual(params["max_tokens"], 128000)
        self.assertEqual(params["thinking"], {"type": "adaptive"})
        self.assertNotIn("temperature", params)

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "fake-openrouter-key"})
    def test_google_create_request_params_via_openrouter(self):
        """OpenRouter를 통한 Google 모델 요청 파라미터 생성 테스트"""
        # 설정
        gateway = GatewayFactory.create("gemini-3.1-pro")

        # 테스트 메시지
        messages = COMMON_TEST_MESSAGES

        # 테스트 실행
        params = gateway._create_request_params(messages)

        # 검증 - OpenRouter에서는 google/gemini-3.1-pro-preview 형식 사용
        self.assertEqual(params["model"], "google/gemini-3.1-pro-preview")
        self.assertEqual(params["messages"], messages)
        self.assertEqual(params["temperature"], 0.0)

    @patch("selvage.src.llm_gateway.google_gateway.get_api_key")
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=True)  # OpenRouter 키 없음
    def test_google_create_request_params_direct(self, mock_get_api_key):
        """Google Gateway 직접 사용 시 요청 파라미터 생성 테스트"""
        # 설정
        mock_get_api_key.return_value = "fake-api-key"
        gateway = GatewayFactory.create("gemini-3.1-pro")

        # 테스트 메시지
        messages = COMMON_TEST_MESSAGES

        # 테스트 실행
        params = gateway._create_request_params(messages)

        # 검증
        self.assertEqual(params["model"], "gemini-3.1-pro-preview")
        self.assertIn("contents", params)  # Google API 요청 형식에 맞게 변환됨
        self.assertIn("config", params)  # Google API 구성 포함
        # config의 시스템 지시 검증
        self.assertEqual(
            params["config"].system_instruction, "시스템 지시: 코드 리뷰를 수행하세요."
        )
        # 온도 설정 검증
        self.assertEqual(params["config"].temperature, 0.0)
        self.assertEqual(params["config"].response_mime_type, "application/json")
        self.assertEqual(params["config"].response_schema, StructuredReviewResponse)


if __name__ == "__main__":
    unittest.main()
