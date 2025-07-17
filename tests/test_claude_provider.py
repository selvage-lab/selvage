"""
ClaudeProvider enum 테스트 모듈.
"""

import unittest

from selvage.src.exceptions.unsupported_provider_error import UnsupportedProviderError
from selvage.src.models.claude_provider import ClaudeProvider


class TestClaudeProvider(unittest.TestCase):
    """ClaudeProvider enum 테스트 클래스."""

    def test_from_string_valid_values(self):
        """유효한 문자열로 ClaudeProvider 생성 테스트."""
        test_cases = [
            ("anthropic", ClaudeProvider.ANTHROPIC),
            ("ANTHROPIC", ClaudeProvider.ANTHROPIC),
            ("openrouter", ClaudeProvider.OPENROUTER),
            ("OPENROUTER", ClaudeProvider.OPENROUTER),
        ]

        for input_str, expected in test_cases:
            with self.subTest(input_str=input_str):
                result = ClaudeProvider.from_string(input_str)
                self.assertEqual(result, expected)

    def test_from_string_invalid_values(self):
        """잘못된 문자열로 ClaudeProvider 생성 시 예외 발생 테스트."""
        invalid_values = ["invalid", "", "openai", "google"]

        for invalid_value in invalid_values:
            with self.subTest(invalid_value=invalid_value):
                with self.assertRaises(UnsupportedProviderError):
                    ClaudeProvider.from_string(invalid_value)

    def test_get_display_name(self):
        """display name 반환 테스트."""
        test_cases = [
            (ClaudeProvider.ANTHROPIC, "Anthropic"),
            (ClaudeProvider.OPENROUTER, "OpenRouter"),
        ]

        for provider, expected_display in test_cases:
            with self.subTest(provider=provider):
                result = provider.get_display_name()
                self.assertEqual(result, expected_display)

    def test_get_env_var_name(self):
        """환경변수 이름 반환 테스트."""
        test_cases = [
            (ClaudeProvider.ANTHROPIC, "ANTHROPIC_API_KEY"),
            (ClaudeProvider.OPENROUTER, "OPENROUTER_API_KEY"),
        ]

        for provider, expected_env_var in test_cases:
            with self.subTest(provider=provider):
                result = provider.get_env_var_name()
                self.assertEqual(result, expected_env_var)


if __name__ == "__main__":
    unittest.main()
