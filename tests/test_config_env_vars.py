"""
환경변수 기반 API 키 관리 기능 테스트 모듈.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from selvage.src.config import get_api_key
from selvage.src.exceptions.api_key_not_found_error import APIKeyNotFoundError
from selvage.src.exceptions.unsupported_provider_error import UnsupportedProviderError
from selvage.src.models.model_provider import ModelProvider


class TestEnvironmentVariableConfig(unittest.TestCase):
    """환경변수 기반 API 키 관리 테스트 클래스."""

    def setUp(self) -> None:
        """테스트 시작 전 설정."""
        # 기존 환경변수 백업
        self.original_env_vars = {}
        # ModelProvider enum을 사용하여 환경변수 매핑 생성

        env_var_mapping = {
            provider: provider.get_env_var_name() for provider in ModelProvider
        }
        for provider, env_var in env_var_mapping.items():
            self.original_env_vars[env_var] = os.getenv(env_var)
            # 테스트를 위해 환경변수 삭제
            if env_var in os.environ:
                del os.environ[env_var]

    def tearDown(self) -> None:
        """테스트 완료 후 정리."""
        # 환경변수 복원
        for env_var, original_value in self.original_env_vars.items():
            if original_value is not None:
                os.environ[env_var] = original_value
            elif env_var in os.environ:
                del os.environ[env_var]

    def test_get_env_var_name(self) -> None:
        """환경변수명 매핑 테스트."""
        self.assertEqual(ModelProvider.OPENAI.get_env_var_name(), "OPENAI_API_KEY")
        self.assertEqual(
            ModelProvider.ANTHROPIC.get_env_var_name(), "ANTHROPIC_API_KEY"
        )
        self.assertEqual(ModelProvider.GOOGLE.get_env_var_name(), "GEMINI_API_KEY")
        self.assertEqual(
            ModelProvider.OPENROUTER.get_env_var_name(), "OPENROUTER_API_KEY"
        )

    def test_get_env_var_name_invalid_provider(self) -> None:
        """지원하지 않는 provider에 대한 테스트."""
        with self.assertRaises(UnsupportedProviderError) as context:
            ModelProvider.from_string("invalid_provider")
        valid_providers = [p.value for p in ModelProvider]
        self.assertIn(
            f"지원하지 않는 provider 'invalid_provider'. 유효한 값: {valid_providers}",
            str(context.exception),
        )

    def test_get_api_key_from_environment(self) -> None:
        """환경변수에서 API 키 가져오기 테스트."""
        test_key = "test_openai_key_12345678"
        os.environ["OPENAI_API_KEY"] = test_key

        api_key = get_api_key(ModelProvider.OPENAI)
        self.assertEqual(api_key, test_key)

    def test_get_api_key_environment_priority(self) -> None:
        """환경변수가 파일보다 우선순위가 높은지 테스트."""
        env_key = "env_key_12345678"
        os.environ["OPENAI_API_KEY"] = env_key

        # 파일 기반 설정이 있어도 환경변수가 우선
        with patch("selvage.src.config.load_config") as mock_load_config:
            mock_config = MagicMock()
            mock_config.__getitem__.return_value = {
                ModelProvider.OPENAI.value: "file_key_12345678"
            }
            mock_load_config.return_value = mock_config

            api_key = get_api_key(ModelProvider.OPENAI)
            self.assertEqual(api_key, env_key)

    def test_get_api_key_not_found(self) -> None:
        """API 키가 없을 때 적절한 예외가 발생하는지 테스트"""
        with self.assertRaises(APIKeyNotFoundError) as context:
            get_api_key(ModelProvider.OPENAI)

        self.assertEqual(context.exception.provider, ModelProvider.OPENAI)

    def test_all_providers_mapping(self) -> None:
        """모든 지원 provider의 환경변수 매핑 테스트."""
        expected_mappings = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GEMINI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
        }

        for provider, expected_env_var in expected_mappings.items():
            with self.subTest(provider=provider):
                self.assertEqual(
                    ModelProvider.from_string(provider).get_env_var_name(),
                    expected_env_var,
                )

    def test_env_vars_integration(self) -> None:
        """환경변수와 파일 설정의 통합 테스트."""
        # 각 provider별로 환경변수 설정 후 확인
        test_keys = {
            "openai": "openai_test_key_12345678",
            "anthropic": "claude_test_key_12345678",
            "google": "google_test_key_12345678",
            "openrouter": "openrouter_test_key_12345678",
        }

        for provider, test_key in test_keys.items():
            with self.subTest(provider=provider):
                env_var = ModelProvider.from_string(provider).get_env_var_name()
                os.environ[env_var] = test_key

                retrieved_key = get_api_key(ModelProvider.from_string(provider))
                self.assertEqual(retrieved_key, test_key)

                # 정리
                del os.environ[env_var]


if __name__ == "__main__":
    unittest.main()
