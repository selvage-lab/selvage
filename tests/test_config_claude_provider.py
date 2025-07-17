"""
Claude Provider 설정 기능 테스트 모듈.
"""

import unittest
from unittest.mock import MagicMock, patch

from selvage.src.config import get_claude_provider, set_claude_provider
from selvage.src.models.claude_provider import ClaudeProvider


class TestClaudeProviderConfig(unittest.TestCase):
    """Claude Provider 설정 기능 테스트 클래스."""

    @patch("selvage.src.config.load_config")
    def test_get_claude_provider_with_anthropic(self, mock_load_config):
        """설정에 anthropic이 설정된 경우 테스트."""
        mock_config = MagicMock()
        mock_config.__contains__.side_effect = lambda key: key == "claude"
        mock_config.__getitem__.return_value = {"provider": "anthropic"}
        mock_load_config.return_value = mock_config

        result = get_claude_provider()
        self.assertEqual(result, ClaudeProvider.ANTHROPIC)

    @patch("selvage.src.config.load_config")
    def test_get_claude_provider_with_openrouter(self, mock_load_config):
        """설정에 openrouter가 설정된 경우 테스트."""
        mock_config = MagicMock()
        mock_config.__contains__.side_effect = lambda key: key == "claude"
        mock_config.__getitem__.return_value = {"provider": "openrouter"}
        mock_load_config.return_value = mock_config

        result = get_claude_provider()
        self.assertEqual(result, ClaudeProvider.OPENROUTER)

    @patch("selvage.src.config.load_config")
    def test_get_claude_provider_default_value(self, mock_load_config):
        """설정이 없을 때 기본값(anthropic) 반환 테스트."""
        mock_config = MagicMock()
        mock_config.__contains__.return_value = False
        mock_load_config.return_value = mock_config

        result = get_claude_provider()
        self.assertEqual(result, ClaudeProvider.ANTHROPIC)

    @patch("selvage.src.config.load_config")
    def test_get_claude_provider_no_provider_key(self, mock_load_config):
        """claude 섹션은 있지만 provider 키가 없을 때 기본값 반환 테스트."""
        mock_config = MagicMock()
        mock_config.__contains__.side_effect = lambda key: key == "claude"
        mock_config.__getitem__.return_value = {"other_key": "value"}
        mock_load_config.return_value = mock_config

        result = get_claude_provider()
        self.assertEqual(result, ClaudeProvider.ANTHROPIC)

    @patch("selvage.src.config.load_config")
    def test_get_claude_provider_invalid_value(self, mock_load_config):
        """잘못된 설정값이 있을 때 기본값 반환 테스트."""
        mock_config = MagicMock()
        mock_config.__contains__.side_effect = lambda key: key == "claude"
        mock_config.__getitem__.return_value = {"provider": "invalid_provider"}
        mock_load_config.return_value = mock_config

        result = get_claude_provider()
        self.assertEqual(result, ClaudeProvider.ANTHROPIC)

    @patch("selvage.src.config.save_config")
    @patch("selvage.src.config.load_config")
    @patch("selvage.src.config.console")
    def test_set_claude_provider_success(
        self, mock_console, mock_load_config, mock_save_config
    ):
        """Claude provider 설정 성공 테스트."""
        mock_config = {}
        mock_load_config.return_value = mock_config

        result = set_claude_provider(ClaudeProvider.OPENROUTER)

        self.assertTrue(result)
        self.assertEqual(mock_config["claude"]["provider"], "openrouter")
        mock_save_config.assert_called_once_with(mock_config)

    @patch("selvage.src.config.save_config")
    @patch("selvage.src.config.load_config")
    @patch("selvage.src.config.console")
    def test_set_claude_provider_with_existing_config(
        self, mock_console, mock_load_config, mock_save_config
    ):
        """기존 설정이 있는 상태에서 provider 변경 테스트."""
        mock_config = {"claude": {"provider": "anthropic"}}
        mock_load_config.return_value = mock_config

        result = set_claude_provider(ClaudeProvider.OPENROUTER)

        self.assertTrue(result)
        self.assertEqual(mock_config["claude"]["provider"], "openrouter")
        mock_save_config.assert_called_once_with(mock_config)

    @patch("selvage.src.config.save_config")
    @patch("selvage.src.config.load_config")
    @patch("selvage.src.config.console")
    def test_set_claude_provider_error_handling(
        self, mock_console, mock_load_config, mock_save_config
    ):
        """Claude provider 설정 시 오류 처리 테스트."""
        mock_load_config.side_effect = Exception("설정 로드 실패")

        result = set_claude_provider(ClaudeProvider.OPENROUTER)

        self.assertFalse(result)
        mock_console.error.assert_called_once()
        mock_save_config.assert_not_called()


if __name__ == "__main__":
    unittest.main()
