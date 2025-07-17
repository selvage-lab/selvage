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
    def test_openai_create_request_params(self, mock_get_api_key):
        """OpenAI 게이트웨이의 요청 파라미터 생성을 테스트합니다."""
        # 설정
        mock_get_api_key.return_value = "fake-api-key"
        gateway = GatewayFactory.create("gpt-4o")

        # 테스트 메시지
        messages = COMMON_TEST_MESSAGES

        # 테스트 실행
        params = gateway._create_request_params(messages)

        # 검증
        self.assertEqual(params["model"], "gpt-4o")
        self.assertEqual(params["messages"], messages)
        self.assertEqual(params["temperature"], 0.0)  # 모델의 기본 파라미터

    @patch("selvage.src.llm_gateway.claude_gateway.get_api_key")
    @patch("selvage.src.llm_gateway.gateway_factory.get_claude_provider")
    def test_claude_create_request_params(
        self, mock_get_claude_provider, mock_get_api_key
    ):
        """Claude 게이트웨이의 요청 파라미터 생성을 테스트합니다."""
        # 설정
        from selvage.src.models.claude_provider import ClaudeProvider

        mock_get_claude_provider.return_value = ClaudeProvider.ANTHROPIC
        mock_get_api_key.return_value = "fake-api-key"
        gateway = GatewayFactory.create("claude-sonnet-4")

        # 테스트 메시지
        messages = COMMON_TEST_MESSAGES

        # 테스트 실행
        params = gateway._create_request_params(messages)

        # 검증
        self.assertEqual(params["model"], "claude-sonnet-4-20250514")
        self.assertEqual(params["messages"], messages)
        self.assertEqual(params["max_tokens"], 8192)  # Claude 특정 파라미터
        self.assertEqual(params["temperature"], 0.0)  # 모델의 기본 파라미터

    @patch("selvage.src.llm_gateway.google_gateway.get_api_key")
    def test_google_create_request_params(self, mock_get_api_key):
        """Google 게이트웨이의 요청 파라미터 생성을 테스트합니다."""
        # 설정
        mock_get_api_key.return_value = "fake-api-key"
        gateway = GatewayFactory.create("gemini-2.5-pro")

        # 테스트 메시지
        messages = COMMON_TEST_MESSAGES

        # 테스트 실행
        params = gateway._create_request_params(messages)

        # 검증
        self.assertEqual(params["model"], "gemini-2.5-pro")
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
