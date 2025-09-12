"""
OpenRouter First 기능 테스트 모듈.
"""

import os
import unittest
from unittest.mock import patch

from selvage.src.config import has_openrouter_api_key
from selvage.src.llm_gateway.gateway_factory import GatewayFactory
from selvage.src.models.model_provider import ModelProvider


class TestOpenRouterFirst(unittest.TestCase):
    """OpenRouter First 기능 테스트 클래스."""

    def setUp(self):
        """테스트 설정."""
        # 환경변수 초기화
        if "OPENROUTER_API_KEY" in os.environ:
            del os.environ["OPENROUTER_API_KEY"]

    def tearDown(self):
        """테스트 정리."""
        # 환경변수 정리
        if "OPENROUTER_API_KEY" in os.environ:
            del os.environ["OPENROUTER_API_KEY"]

    def test_has_openrouter_api_key_true(self):
        """OpenRouter API key가 설정된 경우 테스트."""
        # Given
        os.environ["OPENROUTER_API_KEY"] = "test_key"

        # When
        result = has_openrouter_api_key()

        # Then
        self.assertTrue(result)

    def test_has_openrouter_api_key_false(self):
        """OpenRouter API key가 없는 경우 테스트."""
        # Given
        # OPENROUTER_API_KEY가 설정되지 않은 상태

        # When
        result = has_openrouter_api_key()

        # Then
        self.assertFalse(result)

    def test_has_openrouter_api_key_empty_string(self):
        """OpenRouter API key가 빈 문자열인 경우 테스트."""
        # Given
        os.environ["OPENROUTER_API_KEY"] = ""

        # When
        result = has_openrouter_api_key()

        # Then
        self.assertFalse(result)

    @patch("selvage.src.llm_gateway.gateway_factory.has_openrouter_api_key")
    @patch("selvage.src.llm_gateway.gateway_factory.get_model_info")
    def test_gateway_factory_openrouter_first_claude(
        self, mock_get_model_info, mock_has_key
    ):
        """OpenRouter First로 Claude 모델 게이트웨이 생성 테스트."""
        # Given
        mock_has_key.return_value = True
        mock_get_model_info.return_value = {
            "provider": ModelProvider.ANTHROPIC,
            "openrouter_name": "anthropic/claude-sonnet-4",
        }

        with patch(
            "selvage.src.llm_gateway.openrouter_gateway.OpenRouterGateway"
        ) as mock_gateway:
            # When
            result = GatewayFactory.create("claude-sonnet-4")

            # Then
            mock_gateway.assert_called_once()
            self.assertEqual(result, mock_gateway.return_value)

    @patch("selvage.src.llm_gateway.gateway_factory.has_openrouter_api_key")
    @patch("selvage.src.llm_gateway.gateway_factory.get_model_info")
    def test_gateway_factory_openrouter_first_gpt(
        self, mock_get_model_info, mock_has_key
    ):
        """OpenRouter First로 GPT 모델 게이트웨이 생성 테스트."""
        # Given
        mock_has_key.return_value = True
        mock_get_model_info.return_value = {
            "provider": ModelProvider.OPENAI,
            "openrouter_name": "openai/gpt-5",
        }

        with patch(
            "selvage.src.llm_gateway.openrouter_gateway.OpenRouterGateway"
        ) as mock_gateway:
            # When
            result = GatewayFactory.create("gpt-5")

            # Then
            mock_gateway.assert_called_once()
            self.assertEqual(result, mock_gateway.return_value)

    @patch("selvage.src.llm_gateway.gateway_factory.has_openrouter_api_key")
    @patch("selvage.src.llm_gateway.gateway_factory.get_model_info")
    def test_gateway_factory_fallback_claude(self, mock_get_model_info, mock_has_key):
        """OpenRouter key 없을 때 Claude 모델 폴백 테스트."""
        # Given
        mock_has_key.return_value = False
        mock_get_model_info.return_value = {"provider": ModelProvider.ANTHROPIC}

        with patch(
            "selvage.src.llm_gateway.claude_gateway.ClaudeGateway"
        ) as mock_gateway:
            # When
            result = GatewayFactory.create("claude-sonnet-4")

            # Then
            mock_gateway.assert_called_once()
            self.assertEqual(result, mock_gateway.return_value)

    @patch("selvage.src.llm_gateway.gateway_factory.has_openrouter_api_key")
    @patch("selvage.src.llm_gateway.gateway_factory.get_model_info")
    def test_gateway_factory_fallback_openai(self, mock_get_model_info, mock_has_key):
        """OpenRouter key 없을 때 OpenAI 모델 폴백 테스트."""
        # Given
        mock_has_key.return_value = False
        mock_get_model_info.return_value = {"provider": ModelProvider.OPENAI}

        with patch(
            "selvage.src.llm_gateway.openai_gateway.OpenAIGateway"
        ) as mock_gateway:
            # When
            result = GatewayFactory.create("gpt-5")

            # Then
            mock_gateway.assert_called_once()
            self.assertEqual(result, mock_gateway.return_value)

    @patch("selvage.src.llm_gateway.gateway_factory.has_openrouter_api_key")
    @patch("selvage.src.llm_gateway.gateway_factory.get_model_info")
    def test_gateway_factory_fallback_google(self, mock_get_model_info, mock_has_key):
        """OpenRouter key 없을 때 Google 모델 폴백 테스트."""
        # Given
        mock_has_key.return_value = False
        mock_get_model_info.return_value = {"provider": ModelProvider.GOOGLE}

        with patch(
            "selvage.src.llm_gateway.google_gateway.GoogleGateway"
        ) as mock_gateway:
            # When
            result = GatewayFactory.create("gemini-2.5-pro")

            # Then
            mock_gateway.assert_called_once()
            self.assertEqual(result, mock_gateway.return_value)

    @patch("selvage.src.llm_gateway.gateway_factory.has_openrouter_api_key")
    @patch("selvage.src.llm_gateway.gateway_factory.get_model_info")
    def test_gateway_factory_unsupported_provider(
        self, mock_get_model_info, mock_has_key
    ):
        """지원하지 않는 provider 에러 테스트."""
        # Given
        mock_has_key.return_value = False
        mock_get_model_info.return_value = {"provider": "unsupported_provider"}

        # When & Then
        with self.assertRaises(ValueError) as context:
            GatewayFactory.create("unknown-model")

        self.assertIn("Unsupported provider", str(context.exception))


if __name__ == "__main__":
    unittest.main()
